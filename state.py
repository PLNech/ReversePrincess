from typing import Optional


class GameState:
    history: list = []

    def __init__(self, introduction: str, location: str = "The first room", objective: str = "Get out of her room"):
        self.history.append(introduction)
        self.current_location: str = location
        self.current_objective: str = objective

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
