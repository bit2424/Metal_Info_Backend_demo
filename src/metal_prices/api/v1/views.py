"""
API views for Metal Prices.
"""
import logging

import attr
from django.db.models import Max
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from metal_prices.models import MetalPrice
from shared.mixins import CamelSnakeCaseMixin

from .serializers import (
    ErrorResponseSerializer,
    FetchRequestSerializer,
    FetchResponseSerializer,
    MetalPriceSerializer,
)
from .services import ExternalAPIError, MetalPriceService

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class MetalPriceListView(CamelSnakeCaseMixin, generics.ListAPIView):
    """
    GET /api/v1/metal-prices/
    List the latest batch of metal prices.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MetalPriceSerializer

    # Inject service
    metal_price_service: MetalPriceService = attr.ib(factory=MetalPriceService)

    def get_queryset(self):
        """
        Return the latest batch of metal prices.
        Optionally filter by symbols query parameter.
        """
        # Get the most recent fetched_at timestamp
        latest_fetch = MetalPrice.objects.aggregate(
            latest=Max("fetched_at")
        )["latest"]

        if not latest_fetch:
            return MetalPrice.objects.none()

        queryset = MetalPrice.objects.filter(fetched_at=latest_fetch)

        # Optional filtering by symbols (comma-separated)
        symbols_param = self.request.query_params.get("symbols")
        if symbols_param:
            symbol_list = [s.strip() for s in symbols_param.split(",")]
            queryset = queryset.filter(symbol__in=symbol_list)

        return queryset.order_by("symbol")

    def list(self, request, *args, **kwargs):
        """List all latest metal prices with custom response format."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        latest_fetch = queryset.first()
        fetched_at = latest_fetch.fetched_at if latest_fetch else None

        return Response({
            "success": True,
            "count": queryset.count(),
            "fetched_at": fetched_at,
            "data": serializer.data,
        })


@attr.s(auto_attribs=True)
class MetalPriceDetailView(CamelSnakeCaseMixin, generics.RetrieveAPIView):
    """
    GET /api/v1/metal-prices/{symbol}/
    Retrieve the latest price data for a specific metal.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MetalPriceSerializer
    lookup_field = "symbol"

    # Inject service
    metal_price_service: MetalPriceService = attr.ib(factory=MetalPriceService)

    def get_object(self):
        """Get the latest price for the specified symbol."""
        symbol = self.kwargs.get("symbol")
        metal_price = self.metal_price_service.get_price_by_symbol(symbol)

        if not metal_price:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Metal with symbol '{symbol}' not found")

        return metal_price

    def retrieve(self, request, *args, **kwargs):
        """Retrieve metal price with custom response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            "success": True,
            "data": serializer.data,
        })


@attr.s(auto_attribs=True)
class FetchMetalPricesView(CamelSnakeCaseMixin, APIView):
    """
    POST /api/v1/metal-prices/fetch/
    Trigger fetching metal prices from external API and store results.
    """

    permission_classes = [permissions.AllowAny]

    # Inject service
    metal_price_service: MetalPriceService = attr.ib(factory=MetalPriceService)

    def post(self, request):
        """
        Fetch metal prices from external API and store in database.

        Request body (optional):
        {
            "metals": ["Tense", "Troma"]  // Specific metals to fetch
        }
        """
        # Validate request data
        request_serializer = FetchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        metals = request_serializer.validated_data.get("metals")

        try:
            result = self.metal_price_service.fetch_and_store_prices(metals=metals)

            # Serialize response
            response_serializer = FetchResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=True)

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except ExternalAPIError as e:
            logger.error(f"External API error: {e}")
            error_serializer = ErrorResponseSerializer(data={
                "success": False,
                "error": f"Failed to fetch from external API: {str(e)}"
            })
            error_serializer.is_valid(raise_exception=True)

            return Response(
                error_serializer.data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.exception(f"Unexpected error in fetch view: {e}")
            error_serializer = ErrorResponseSerializer(data={
                "success": False,
                "error": str(e)
            })
            error_serializer.is_valid(raise_exception=True)

            return Response(
                error_serializer.data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
