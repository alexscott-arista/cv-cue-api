"""
Tests for ManagedDevicesResource class.
"""

import pytest
from unittest.mock import call
from cv_cue_api.resources.managed_devices import ManagedDevicesResource
from cv_cue_api.resources.filters import Filter, FilterBuilder


class TestManagedDevicesResource:
    """Test cases for ManagedDevicesResource."""

    def test_resource_initialization(self, mock_client):
        """Test that resource initializes with client reference."""
        resource = ManagedDevicesResource(mock_client)
        assert resource.client == mock_client

    def test_list_aps_default_params(self, mock_client, sample_managed_devices_response):
        """Test list_aps with default parameters."""
        mock_client.request.return_value = sample_managed_devices_response

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps()

        # Verify the request was made correctly
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args

        assert call_args[0][0] == "GET"  # method
        assert call_args[0][1] == "/manageddevices/aps"  # path
        assert call_args[1]["params"]["startindex"] == 0
        assert call_args[1]["params"]["pagesize"] == 10
        assert call_args[1]["headers"]["Version"] == "19"

        # Verify the result
        assert result == sample_managed_devices_response
        assert len(result["managedDevices"]) == 2

    def test_list_aps_custom_params(self, mock_client, sample_managed_devices_response):
        """Test list_aps with custom parameters."""
        mock_client.request.return_value = sample_managed_devices_response

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps(
            startindex=20,
            pagesize=50,
            totalcountrequired=True,
            locationid=123,
            sortby="name",
            ascending=False,
            fetchradios=False,
        )

        call_args = mock_client.request.call_args
        params = call_args[1]["params"]

        assert params["startindex"] == 20
        assert params["pagesize"] == 50
        assert params["totalcountrequired"] is True
        assert params["locationid"] == 123
        assert params["sortby"] == "name"
        assert params["ascending"] is False
        assert params["fetchradios"] is False

    def test_list_aps_with_filter_builder(self, mock_client, sample_managed_devices_response):
        """Test list_aps with FilterBuilder."""
        mock_client.request.return_value = sample_managed_devices_response

        # Create filters
        fb = FilterBuilder("AND")
        fb.contains("name", "Arista").equals("active", True)

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps(filters=fb)

        call_args = mock_client.request.call_args
        params = call_args[1]["params"]

        # Verify filters were added
        assert "filter" in params
        assert "operator" in params
        assert params["operator"] == "AND"
        assert len(params["filter"]) == 2

    def test_list_aps_with_filter_list(self, mock_client, sample_managed_devices_response):
        """Test list_aps with list of Filter objects."""
        mock_client.request.return_value = sample_managed_devices_response

        # Create individual filters
        filters = [
            Filter("name", "contains", "Arista"),
            Filter("active", "equals", True),
        ]

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps(filters=filters, filter_operator="OR")

        call_args = mock_client.request.call_args
        params = call_args[1]["params"]

        # Verify filters were added
        assert "filter" in params
        assert "operator" in params
        assert params["operator"] == "OR"
        assert len(params["filter"]) == 2

    def test_list_aps_with_kwargs(self, mock_client, sample_managed_devices_response):
        """Test list_aps with additional kwargs."""
        mock_client.request.return_value = sample_managed_devices_response

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps(
            active=True,
            model=["AP-555"],
            macaddress=["AA:BB:CC:DD:EE:FF"]
        )

        call_args = mock_client.request.call_args
        params = call_args[1]["params"]

        # Verify kwargs were added to params
        assert params["active"] is True
        assert params["model"] == ["AP-555"]
        assert params["macaddress"] == ["AA:BB:CC:DD:EE:FF"]

    def test_get_all_aps_single_page(self, mock_client, sample_managed_devices_response):
        """Test get_all_aps with single page of results."""
        mock_client.request.return_value = sample_managed_devices_response

        resource = ManagedDevicesResource(mock_client)
        result = resource.get_all_aps(pagesize=100)

        # Should only call once since all results fit in one page
        mock_client.request.assert_called_once()

        # Should return the list of devices
        assert len(result) == 2
        assert result == sample_managed_devices_response["managedDevices"]

    def test_get_all_aps_multiple_pages(self, mock_client):
        """Test get_all_aps with multiple pages of results."""
        # Create mock responses for pagination
        page1 = {
            "managedDevices": [{"boxid": i, "name": f"AP-{i}"} for i in range(100)],
            "totalCount": 250,
        }
        page2 = {
            "managedDevices": [{"boxid": i, "name": f"AP-{i}"} for i in range(100, 200)],
            "totalCount": 250,
        }
        page3 = {
            "managedDevices": [{"boxid": i, "name": f"AP-{i}"} for i in range(200, 250)],
            "totalCount": 250,
        }

        mock_client.request.side_effect = [page1, page2, page3]

        resource = ManagedDevicesResource(mock_client)
        result = resource.get_all_aps(pagesize=100)

        # Should call three times for pagination
        assert mock_client.request.call_count == 3

        # Verify startindex was incremented correctly
        calls = mock_client.request.call_args_list
        assert calls[0][1]["params"]["startindex"] == 0
        assert calls[1][1]["params"]["startindex"] == 100
        assert calls[2][1]["params"]["startindex"] == 200

        # Should return all 250 devices
        assert len(result) == 250

    def test_get_all_aps_empty_result(self, mock_client):
        """Test get_all_aps with empty results."""
        mock_client.request.return_value = {"managedDevices": []}

        resource = ManagedDevicesResource(mock_client)
        result = resource.get_all_aps()

        # Should return empty list
        assert result == []
        assert mock_client.request.call_count == 1

    def test_get_all_aps_with_filters(self, mock_client, sample_managed_devices_response):
        """Test get_all_aps with filters."""
        mock_client.request.return_value = sample_managed_devices_response

        fb = FilterBuilder("AND")
        fb.contains("name", "Test")

        resource = ManagedDevicesResource(mock_client)
        result = resource.get_all_aps(filters=fb)

        call_args = mock_client.request.call_args
        params = call_args[1]["params"]

        # Verify filters were passed through
        assert "filter" in params
        assert "operator" in params


class TestManagedDevicesResourceIntegration:
    """Integration tests for ManagedDevicesResource."""

    def test_list_aps_response_structure(self, mock_client, sample_managed_devices_response):
        """Test that list_aps returns expected response structure."""
        mock_client.request.return_value = sample_managed_devices_response

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps(pagesize=10)

        # Verify response has expected keys
        assert "managedDevices" in result
        assert "totalCount" in result
        assert "pagingSessionId" in result

        # Verify device structure
        device = result["managedDevices"][0]
        assert "boxid" in device
        assert "name" in device
        assert "macaddress" in device
        assert "model" in device

    def test_complex_filter_scenario(self, mock_client, sample_managed_devices_response):
        """Test complex filtering scenario."""
        mock_client.request.return_value = sample_managed_devices_response

        # Build complex filter
        fb = FilterBuilder("AND")
        fb.contains("name", "AP")
        fb.equals("active", True)
        fb.greater_than("boxid", 100)
        fb.not_contains("model", "old")

        resource = ManagedDevicesResource(mock_client)
        result = resource.list_aps(
            pagesize=50,
            totalcountrequired=True,
            filters=fb,
            sortby="name",
            ascending=True,
        )

        call_args = mock_client.request.call_args
        params = call_args[1]["params"]

        # Verify all parameters were set correctly
        assert params["pagesize"] == 50
        assert params["totalcountrequired"] is True
        assert params["sortby"] == "name"
        assert params["ascending"] is True
        assert len(params["filter"]) == 4
        assert params["operator"] == "AND"
