from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Dependency:
    quest_id: str
    optional: bool=False
    def __post_init__(self)->None:
        if not self.quest_id.strip(): raise ValueError("Dependency quest_id cannot be empty.")
