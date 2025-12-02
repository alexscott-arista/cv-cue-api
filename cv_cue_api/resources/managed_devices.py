"""
Managed Devices resource for CV-CUE API.

This module provides access to managed device (Access Point) operations.
"""

from .base import BaseResource
from .filters import Filter, FilterBuilder
from typing import Optional, List, Dict, Any, Union


@BaseResource.register('managed_devices')
class ManagedDevicesResource(BaseResource):
    """
    Managed device (Access Point) management operations.

    Provides methods for listing and managing access points in the CV-CUE system.
    """

    def list_aps(
        self,
        startindex: int = 0,
        pagesize: int = 10,
        totalcountrequired: bool = False,
        locationid: Optional[int] = None,
        sortby: str = "boxid",
        ascending: bool = True,
        fetchradios: bool = True,
        populatemeshinfo: bool = False,
        populatewiredinterfaces: bool = False,
        filters: Optional[Union[FilterBuilder, List[Filter]]] = None,
        filter_operator: str = "AND",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch a paged list of managed devices (Access Points).

        This API is used to fetch a paged managed device list. Users with the roles
        [superuser, administrator, operator, and viewer] can access this API.

        Args:
            startindex: Start index of the requested paged data (default: 0)
            pagesize: Page size of the requested paged data (default: 10)
            totalcountrequired: Populate total count in response (default: False)
            locationid: The ID of the location for which the operation is intended
            sortby: Column to sort by (default: "boxid")
            ascending: Sort in ascending order (default: True)
            fetchradios: Fetch managed device radio information (default: True)
            populatemeshinfo: Populate managed device mesh link information (default: False)
            populatewiredinterfaces: Populate wired interface information (default: False)
            filters: FilterBuilder or list of Filter objects for advanced filtering
            filter_operator: Logical operator for filters ("AND" or "OR", default: "AND")
            **kwargs: Additional query parameters including simple filters:
                - macaddress: List[str] - MAC addresses to filter
                - boxid: List[int] - Box IDs to filter
                - active: bool - Active status
                - placed: bool - Placed status
                - name: List[str] - Device names
                - model: List[str] - Device models
                - ipaddress: List[str] - IPv4 or IPv6 addresses
                - groupname: List[str] - Group names
                - vendorname: List[str] - Vendor names
                - softwareversion: List[str] - Software versions
                - quarantinestatus: List[str] - Quarantine statuses
                - powersource: List[str] - Power sources
                - devicemode: List[str] - Device modes
                - meshenabled: bool - Mesh enabled status
                - networktag: List[str] - Network tags
                - And many more (see API documentation)

        Returns:
            Dict containing:
                - data: List of managed device objects
                - totalCount: Total count of devices (if totalcountrequired=True)
                - pagingSessionId: Session ID for pagination

        Example (simple filters):
            >>> client = CVCueClient()
            >>> client.login()
            >>> devices = client.managed_devices.list_aps(
            ...     pagesize=50,
            ...     active=True,
            ...     model=["AP-555"]
            ... )
            >>> print(f"Found {len(devices['managedDevices'])} devices")

        Example (advanced filters):
            >>> from cv_cue_api.resources.filters import FilterBuilder
            >>> fb = FilterBuilder("AND")
            >>> fb.contains("name", "Arista").contains("name", "5D:BF")
            >>> devices = client.managed_devices.list_aps(
            ...     pagesize=10,
            ...     filters=fb
            ... )
        """
        # Build query parameters
        params = {
            "startindex": startindex,
            "pagesize": pagesize,
            "totalcountrequired": totalcountrequired,
            "sortby": sortby,
            "ascending": ascending,
            "fetchradios": fetchradios,
            "populatemeshinfo": populatemeshinfo,
            "populatewiredinterfaces": populatewiredinterfaces,
        }

        # Add optional locationid if provided
        if locationid is not None:
            params["locationid"] = locationid

        # Handle Filter objects if provided
        if filters is not None:
            if isinstance(filters, FilterBuilder):
                # FilterBuilder provides both filter and operator
                filter_params = filters.to_params()
                params.update(filter_params)
            elif isinstance(filters, list):
                # List of Filter objects
                params["filter"] = [str(f) for f in filters]
                params["operator"] = filter_operator

        # Add any additional query parameters
        params.update(kwargs)

        # Required API version header
        headers = {"Version": "19"}

        return self._request(
            "GET",
            "/manageddevices/aps",
            params=params,
            headers=headers
        )

    def get_all_aps(
        self,
        pagesize: int = 100,
        filters: Optional[Union[FilterBuilder, List[Filter]]] = None,
        filter_operator: str = "AND",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch all managed devices (Access Points) across all pages.

        This is a convenience method that automatically handles pagination
        and returns all devices matching the filters.

        Args:
            pagesize: Number of devices to fetch per page (default: 100)
            filters: FilterBuilder or list of Filter objects
            filter_operator: Logical operator for filters ("AND" or "OR")
            **kwargs: Additional query parameters

        Returns:
            List of all managed device objects

        Example:
            >>> client = CVCueClient()
            >>> client.login()
            >>> all_devices = client.managed_devices.get_all_aps(active=True)
            >>> print(f"Total devices: {len(all_devices)}")
        """
        all_devices = []
        startindex = 0

        while True:
            response = self.list_aps(
                startindex=startindex,
                pagesize=pagesize,
                totalcountrequired=False,
                filters=filters,
                filter_operator=filter_operator,
                **kwargs
            )

            devices = response.get("managedDevices", [])
            if not devices:
                break

            all_devices.extend(devices)

            # Check if there are more pages
            if len(devices) < pagesize:
                break

            startindex += pagesize

        return all_devices
