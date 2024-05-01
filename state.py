class GameState:
    history: list = []
    current_location = "Her room at the top of the dragon's tower"
    current_objective = "Get out of her room"

    def __init__(self, introduction: str):
        self.history.append(introduction)

    def history_so_far(self) -> str:
        return "\n".join(x for x in self.history) + "\n"

    def update(self, step: list[str], location: str, objective: str):
        self.history.extend(step)
        self.current_location = location
        self.current_objective = objective
