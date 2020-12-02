from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ErrorData:
    critical: bool
    entities: dict
    source_name: str
    message: str

    @classmethod
    def warning(cls, entities: dict, source: object, message: str) -> ErrorData:
        return ErrorData(critical=False, entities=entities, source_name=source.__class__.__name__, message=message)

    @classmethod
    def error(cls, entities: dict, source: object, message: str) -> ErrorData:
        return ErrorData(critical=True, entities=entities, source_name=source.__class__.__name__, message=message)
