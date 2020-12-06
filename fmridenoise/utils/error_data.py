from dataclasses import dataclass, asdict
from fmridenoise.utils.entities import build_path


@dataclass
class ErrorData:
    critical: bool
    entities: dict
    source_name: str
    message: str

    @classmethod
    def warning(cls, entities: dict, source: object, message: str) -> "ErrorData":
        return ErrorData(critical=False, entities=entities, source_name=source.__class__.__name__, message=message)

    @classmethod
    def error(cls, entities: dict, source: object, message: str) -> "ErrorData":
        return ErrorData(critical=True, entities=entities, source_name=source.__class__.__name__, message=message)

    def asdict(self):
        return asdict(self)

    def build_message(self) -> str:
        pattern = "[subject-{subject} ][session-{session} ][task-{task} ][run-{run} ][pipeline-{pipeline} ]"
        return f"{build_path(self.entities, pattern)}({self.source_name}):\t{self.message}"
