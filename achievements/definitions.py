"""Definitions for individual achievements."""
from dataclasses import dataclass


@dataclass
class Achievement:
    key: str
    title: str
    text: str
    unlocked: bool = True

    def __hash__(self):
        return hash(self.key)

    def __str__(self):
        return f"{repr(self):<20}: {self.title}|{self.text} ({'🔓' if self.unlocked else '🔒'})"

    def __repr__(self):
        """A representation for the achievement, ideally under 20 chars."""
        return f"A[{self.key}]"


@dataclass
class RollAchievement(Achievement):
    """An achievement which triggers on a specific roll."""
    trigger: int = -1

    def __init__(self, trigger: int, title: str, text: str, unlocked: bool = False):
        assert 0 <= trigger <= 10, "Trigger should be a valid d10 value."
        self.trigger = trigger
        key = f"roll_{trigger}"
        super().__init__(key, title, text, unlocked)

    def __repr__(self):
        return f"{super().__repr__()}(Roll {self.trigger})"


achievements_list: list[Achievement] = [
    Achievement("hello", "First achievement", "Hello you :3"),
    RollAchievement(1, "Roll fail 🎲", "C'est terrible ce qui t'arrive mec, TERRIBLE !"),
    RollAchievement(8, "Roll 8", "Lucky 8 🍀"),

    RollAchievement(10, "Roll win 🌈", "Living the life 😎")
]
achievements_map: dict[str, Achievement] = {a.key: a for a in achievements_list}
achievements_rolls: list[RollAchievement] = [a for a in achievements_list if type(a) is RollAchievement]
# achievements_sequence = [a for a in achievements_list if a.type == Type.SEQUENCE]
# achievements_history = [a for a in achievements_list if a.type == Type.HISTORY]
# achievements_other = [a for a in achievements_list if a.type == Type.OTHER]

if __name__ == '__main__':
    print("Achievements:")
    for a in achievements_list:
        print(a)
