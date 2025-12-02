"""
Base resource class for all CV-CUE API resources.
"""

class BaseResource:
    """
    Base class for all API resources.

    Provides common functionality for making requests and registering
    resources with the CVCueClient.
    """

    def __init__(self, client):
        """
        Initialize the resource with a reference to the client.

        Args:
            client: The CVCueClient instance that owns this resource
        """
        self.client = client

    def _request(self, method: str, path: str, **kwargs):
        """
        Convenience wrapper for client.request.

        Args:
            method: HTTP method
            path: API endpoint path
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response
        """
        return self.client.request(method, path, **kwargs)

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a resource with the CVCueClient.

        Usage:
            @BaseResource.register('managed_devices')
            class ManagedDevicesResource(BaseResource):
                pass

        Args:
            name: The attribute name to access this resource on the client
        """
        def decorator(resource_class):
            from ..cv_cue_client import CVCueClient
            CVCueClient.register_resource(name, resource_class)
            return resource_class
        return decorator
