"""Explicit JSON value type for external tool and event payloads."""

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
