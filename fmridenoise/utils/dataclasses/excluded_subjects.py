from dataclasses import dataclass, field
from typing import Set


@dataclass
class ExcludedSubjects:
    pipeline_name: str
    task: str
    session: str = field(default=None)
    run: int = field(default=None)
    excluded: Set[str] = field(default_factory=set)

    def is_same_group(self, other):
        if not isinstance(other, ExcludedSubjects):
            return False
        else:
            return self.task == other.task and self.session == other.session and self.run == other.run

    @property
    def entities(self):
        return {'task': self.task, 'session': self.session, 'pipeline': self.pipeline_name, 'run': self.run}
