"""
Tests for Filter and FilterBuilder classes.
"""

import pytest
import json
from cv_cue_api.resources.filters import Filter, FilterBuilder


class TestFilter:
    """Test cases for the Filter class."""

    def test_filter_creation(self):
        """Test creating a basic filter."""
        f = Filter("name", "contains", "Arista")
        assert f.property == "name"
        assert f.operator == "contains"
        assert f.value == ["Arista"]

    def test_filter_value_list_conversion(self):
        """Test that single values are converted to lists."""
        f1 = Filter("active", "equals", True)
        assert f1.value == [True]

        f2 = Filter("model", "contains", ["AP-555", "AP-635"])
        assert f2.value == ["AP-555", "AP-635"]

    def test_operator_mapping(self):
        """Test that operator names are correctly mapped to API operators."""
        test_cases = [
            ("equals", "="),
            ("lessThan", "<"),
            ("greaterThan", ">"),
            ("lessThanOrEquals", "<="),
            ("greaterThanOrEquals", ">="),
            ("notEquals", "!="),
            ("contains", "contains"),
            ("notContains", "notcontains"),
        ]

        for friendly_op, expected_api_op in test_cases:
            f = Filter("test", friendly_op, "value")
            assert f.to_dict()["operator"] == expected_api_op

    def test_to_dict(self):
        """Test conversion to dictionary."""
        f = Filter("name", "contains", ["Arista"])
        result = f.to_dict()

        assert result == {
            "property": "name",
            "operator": "contains",
            "value": ["Arista"],
        }

    def test_to_json_string(self):
        """Test conversion to JSON string."""
        f = Filter("active", "equals", True)
        json_str = str(f)

        # Parse it back to verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["property"] == "active"
        assert parsed["operator"] == "="
        assert parsed["value"] == [True]

    def test_invalid_operator(self):
        """Test that invalid operators raise ValueError."""
        with pytest.raises(ValueError, match="Invalid operator"):
            Filter("test", "invalid_operator", "value")

    def test_repr(self):
        """Test __repr__ method."""
        f = Filter("name", "contains", ["Arista"])
        repr_str = repr(f)
        assert "Filter" in repr_str
        assert "name" in repr_str
        assert "contains" in repr_str


class TestFilterBuilder:
    """Test cases for the FilterBuilder class."""

    def test_filter_builder_creation(self):
        """Test creating a FilterBuilder."""
        fb = FilterBuilder("AND")
        assert fb.operator == "AND"
        assert len(fb.filters) == 0

    def test_invalid_operator(self):
        """Test that invalid operators raise ValueError."""
        with pytest.raises(ValueError, match="Operator must be"):
            FilterBuilder("INVALID")

    def test_add_filter(self):
        """Test adding filters using add() method."""
        fb = FilterBuilder("AND")
        fb.add("name", "contains", "Arista")

        assert len(fb) == 1
        assert fb.filters[0].property == "name"
        assert fb.filters[0].operator == "contains"

    def test_contains_method(self):
        """Test the contains() convenience method."""
        fb = FilterBuilder()
        fb.contains("name", "Arista")

        assert len(fb) == 1
        assert fb.filters[0].operator == "contains"

    def test_equals_method(self):
        """Test the equals() convenience method."""
        fb = FilterBuilder()
        fb.equals("active", True)

        assert len(fb) == 1
        assert fb.filters[0].operator == "equals"

    def test_not_contains_method(self):
        """Test the not_contains() convenience method."""
        fb = FilterBuilder()
        fb.not_contains("name", "Test")

        assert len(fb) == 1
        assert fb.filters[0].operator == "notContains"

    def test_comparison_methods(self):
        """Test comparison convenience methods."""
        fb = FilterBuilder()
        fb.greater_than("count", 10)
        fb.less_than("age", 100)
        fb.greater_than_or_equals("score", 50)
        fb.less_than_or_equals("limit", 200)
        fb.not_equals("status", "inactive")

        assert len(fb) == 5
        assert fb.filters[0].operator == "greaterThan"
        assert fb.filters[1].operator == "lessThan"
        assert fb.filters[2].operator == "greaterThanOrEquals"
        assert fb.filters[3].operator == "lessThanOrEquals"
        assert fb.filters[4].operator == "notEquals"

    def test_method_chaining(self):
        """Test that methods can be chained."""
        fb = FilterBuilder("AND")
        result = fb.contains("name", "Arista").equals("active", True)

        assert result is fb  # Same instance
        assert len(fb) == 2

    def test_to_params_empty(self):
        """Test to_params() with no filters."""
        fb = FilterBuilder()
        params = fb.to_params()

        assert params == {}

    def test_to_params_with_filters(self):
        """Test to_params() with filters."""
        fb = FilterBuilder("AND")
        fb.contains("name", "Arista").equals("active", True)

        params = fb.to_params()

        assert "operator" in params
        assert params["operator"] == "AND"
        assert "filter" in params
        assert len(params["filter"]) == 2
        assert isinstance(params["filter"][0], str)  # Should be JSON strings

        # Verify the JSON strings are valid
        filter1 = json.loads(params["filter"][0])
        assert filter1["property"] == "name"
        assert filter1["operator"] == "contains"

    def test_to_params_or_operator(self):
        """Test to_params() with OR operator."""
        fb = FilterBuilder("OR")
        fb.contains("name", "AP-555").contains("name", "AP-635")

        params = fb.to_params()
        assert params["operator"] == "OR"

    def test_len(self):
        """Test __len__ method."""
        fb = FilterBuilder()
        assert len(fb) == 0

        fb.add("test1", "equals", "value1")
        assert len(fb) == 1

        fb.add("test2", "equals", "value2")
        assert len(fb) == 2

    def test_repr(self):
        """Test __repr__ method."""
        fb = FilterBuilder("AND")
        fb.contains("name", "Arista")

        repr_str = repr(fb)
        assert "FilterBuilder" in repr_str
        assert "AND" in repr_str


class TestFilterIntegration:
    """Integration tests for filters."""

    def test_complete_filter_workflow(self):
        """Test complete workflow of building and using filters."""
        # Build filters
        fb = FilterBuilder("AND")
        fb.contains("name", "Arista")
        fb.contains("name", "5D:BF")
        fb.equals("active", True)

        # Convert to params
        params = fb.to_params()

        # Verify structure matches API expectations
        assert params["operator"] == "AND"
        assert len(params["filter"]) == 3

        # Verify each filter is valid JSON
        for filter_json in params["filter"]:
            parsed = json.loads(filter_json)
            assert "property" in parsed
            assert "operator" in parsed
            assert "value" in parsed
            assert isinstance(parsed["value"], list)

    def test_recreate_original_example(self):
        """Test recreating the original filter_usage_example.py format."""
        # Original structure
        filter_opts_1 = {
            "property": "name",
            "operator": "contains",
            "value": ["Arista"],
        }

        filter_opts_2 = {
            "property": "name",
            "operator": "contains",
            "value": ["5D:BF"],
        }

        # Using Filter class
        filter1 = Filter("name", "contains", ["Arista"])
        filter2 = Filter("name", "contains", ["5D:BF"])

        # Verify they produce the same output
        assert filter1.to_dict() == filter_opts_1
        assert filter2.to_dict() == filter_opts_2
        assert str(filter1) == json.dumps(filter_opts_1)
        assert str(filter2) == json.dumps(filter_opts_2)
