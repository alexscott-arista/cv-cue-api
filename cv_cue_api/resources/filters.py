"""
Filter classes for CV-CUE API query parameters.

Provides a clean API for building filter objects that are automatically
converted to URL-encoded JSON strings when used in API calls.
"""

import json
from typing import List, Any


class Filter:
    """
    Represents a single filter for CV-CUE API queries.

    When converted to string, produces a JSON string suitable for use
    as a query parameter in API requests.
    """

    # Friendly operator names mapped to actual API operator strings
    OPERATOR_MAP = {
        "equals": "=",
        "lessThan": "<",
        "greaterThan": ">",
        "lessThanOrEquals": "<=",
        "greaterThanOrEquals": ">=",
        "notEquals": "!=",
        "contains": "contains",
        "notContains": "notcontains",
    }

    VALID_OPERATORS = list(OPERATOR_MAP.keys())

    def __init__(self, property: str, operator: str, value: Any):
        """
        Initialize a filter.

        Args:
            property: The property/field name to filter on (e.g., "name", "macaddress")
            operator: The comparison operator (e.g., "contains", "equals", "in")
            value: The value or list of values to filter by

        Raises:
            ValueError: If operator is not valid

        Example:
            >>> filter1 = Filter("name", "contains", ["Arista"])
            >>> filter2 = Filter("active", "equals", True)
            >>> filter3 = Filter("model", "in", ["AP-555", "AP-635"])
        """
        if operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Invalid operator '{operator}'. "
                f"Must be one of: {', '.join(self.VALID_OPERATORS)}"
            )

        self.property = property
        self.operator = operator
        # Ensure value is always a list for consistency
        self.value = value if isinstance(value, list) else [value]

    def to_dict(self) -> dict:
        """
        Convert filter to dictionary representation.

        Returns:
            Dictionary with property, operator (mapped to API format), and value keys
        """
        # Map the friendly operator name to the actual API operator string
        api_operator = self.OPERATOR_MAP.get(self.operator, self.operator)

        return {
            "property": self.property,
            "operator": api_operator,
            "value": self.value,
        }

    def __str__(self) -> str:
        """
        Convert filter to JSON string for use in API query parameters.

        Returns:
            JSON string representation of the filter
        """
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"Filter(property={self.property!r}, operator={self.operator!r}, value={self.value!r})"


class FilterBuilder:
    """
    Helper class for building multiple filters with a fluent API.

    Provides convenience methods for common filter operations and
    combines multiple filters with AND/OR operators.
    """

    def __init__(self, operator: str = "AND"):
        """
        Initialize the filter builder.

        Args:
            operator: Logical operator to combine filters ("AND" or "OR", default: "AND")
        """
        if operator not in ["AND", "OR"]:
            raise ValueError("Operator must be 'AND' or 'OR'")

        self.filters: List[Filter] = []
        self.operator = operator

    def add(self, property: str, operator: str, value: Any) -> 'FilterBuilder':
        """
        Add a filter to the builder.

        Args:
            property: The property/field name to filter on
            operator: The comparison operator
            value: The value or list of values to filter by

        Returns:
            Self for method chaining

        Example:
            >>> fb = FilterBuilder()
            >>> fb.add("name", "contains", ["Arista"]).add("active", "equals", True)
        """
        self.filters.append(Filter(property, operator, value))
        return self

    def contains(self, property: str, value: str) -> 'FilterBuilder':
        """
        Add a 'contains' filter.

        Args:
            property: The property name
            value: Value(s) to check for containment

        Returns:
            Self for method chaining
        """
        return self.add(property, "contains", value)

    def equals(self, property: str, value: Any) -> 'FilterBuilder':
        """
        Add an 'equals' filter.

        Args:
            property: The property name
            value: Value to match exactly

        Returns:
            Self for method chaining
        """
        return self.add(property, "equals", value)

    def not_contains(self, property: str, value: str) -> 'FilterBuilder':
        """
        Add a 'notContains' filter.

        Args:
            property: The property name
            value: Value(s) to check for non-containment

        Returns:
            Self for method chaining
        """
        return self.add(property, "notContains", value)

    def not_equals(self, property: str, value: Any) -> 'FilterBuilder':
        """
        Add a 'notEquals' filter.

        Args:
            property: The property name
            value: Value to exclude

        Returns:
            Self for method chaining
        """
        return self.add(property, "notEquals", value)

    def greater_than(self, property: str, value: Any) -> 'FilterBuilder':
        """
        Add a 'greaterThan' filter.

        Args:
            property: The property name
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        return self.add(property, "greaterThan", value)

    def less_than(self, property: str, value: Any) -> 'FilterBuilder':
        """
        Add a 'lessThan' filter.

        Args:
            property: The property name
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        return self.add(property, "lessThan", value)

    def greater_than_or_equals(self, property: str, value: Any) -> 'FilterBuilder':
        """
        Add a 'greaterThanOrEquals' filter.

        Args:
            property: The property name
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        return self.add(property, "greaterThanOrEquals", value)

    def less_than_or_equals(self, property: str, value: Any) -> 'FilterBuilder':
        """
        Add a 'lessThanOrEquals' filter.

        Args:
            property: The property name
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        return self.add(property, "lessThanOrEquals", value)

    def to_params(self) -> dict:
        """
        Convert filters to API query parameters.

        Returns:
            Dictionary with 'filter' and 'operator' keys suitable for API requests

        Example:
            >>> fb = FilterBuilder("AND")
            >>> fb.contains("name", "Arista").equals("active", True)
            >>> params = fb.to_params()
            >>> # params = {
            >>> #     "operator": "AND",
            >>> #     "filter": ['{"property": "name", ...}', '{"property": "active", ...}']
            >>> # }
        """
        if not self.filters:
            return {}

        return {
            "operator": self.operator,
            "filter": [str(f) for f in self.filters],
        }

    def __len__(self) -> int:
        """Return the number of filters."""
        return len(self.filters)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"FilterBuilder(operator={self.operator!r}, filters={self.filters!r})"
