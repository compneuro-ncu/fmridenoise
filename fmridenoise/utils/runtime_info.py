from dataclasses import dataclass


@dataclass
class RuntimeInfo:
    input_args: str
    version: str
