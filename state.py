from typing import Optional


class GameState:
    history: list = []
    current_location: str = "Her room at the top of the dragon's tower"
    current_objective: str = "Get out of her room"

    def __init__(self, introduction: str):
        self.history.append(introduction)

    def history_so_far(self) -> str:
        return "\n".join(x for x in self.history) + "\n"

    def update(self, step: list[str] = None, location: Optional[str] = None, objective: Optional[str] = None):
        if step is not None:
            self.history.extend(step)
        if location is not None:
            self.current_location = location
        if objective is not None:
            self.current_objective = objective
