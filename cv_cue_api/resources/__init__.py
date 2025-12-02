"""
CV-CUE API Resources

Import all resources to trigger their registration with the CVCueClient.

When this module is imported, the @BaseResource.register() decorators
on each resource class will execute, adding them to the CVCueClient's registry.
"""

from .managed_devices import ManagedDevicesResource
from .filters import Filter, FilterBuilder

__all__ = ['ManagedDevicesResource', 'Filter', 'FilterBuilder']
