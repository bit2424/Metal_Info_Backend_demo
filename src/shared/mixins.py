"""
DRF mixins for common functionality.
"""
from rest_framework import serializers


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelSnakeCaseMixin:
    """
    Mixin to automatically convert request data from camelCase to snake_case
    and response data from snake_case to camelCase.
    """

    def get_serializer(self, *args, **kwargs):
        """Convert request data to snake_case before serialization."""
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())

        # Convert camelCase to snake_case in request data
        if "data" in kwargs:
            data = kwargs["data"]
            if isinstance(data, dict):
                kwargs["data"] = {camel_to_snake(key): value for key, value in data.items()}
            elif isinstance(data, list):
                kwargs["data"] = [
                    {camel_to_snake(key): value for key, value in item.items()}
                    if isinstance(item, dict) else item
                    for item in data
                ]

        return serializer_class(*args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """Convert response data to camelCase."""
        response = super().finalize_response(request, response, *args, **kwargs)

        if hasattr(response, "data") and isinstance(response.data, (dict, list)):
            response.data = self._convert_to_camel(response.data)

        return response

    def _convert_to_camel(self, data):
        """Recursively convert keys to camelCase."""
        if isinstance(data, dict):
            return {snake_to_camel(key): self._convert_to_camel(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_camel(item) for item in data]
        return data
