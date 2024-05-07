from typing import Optional


class GameState:
    history: list = []
    current_location: str = "The first room"
    current_objective: str = "Get out of her room"

    def __init__(self, introduction: str):
        self.history.append(introduction)

    def history_so_far(self) -> str:
        return "\n".join(x for x in self.history) + "\n"

    def update(self, steps: list[str] = None, location: Optional[str] = None, objective: Optional[str] = None):
        if type(steps) is str:
            raise ValueError("Expecting array!")
        if steps is not None:
            self.history.extend(steps)
        if location is not None:
            self.current_location = location
        if objective is not None:
            self.current_objective = objective
