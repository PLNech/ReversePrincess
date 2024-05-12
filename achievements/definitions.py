"""Definitions for individual achievements."""
from dataclasses import dataclass


@dataclass
class Achievement:
    key: str
    title: str
    text: str
    # TODO: Leverage unlocked as single state of achievement unlocking
    unlocked: bool = True

    def __hash__(self):
        return hash(self.key)

    def __str__(self):
        return f"{repr(self):<20}: {self.title:>20}  |  {self.text:<50} ({'🔓' if self.unlocked else '🔒'})"

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


@dataclass
class SequenceAchievement(Achievement):
    """An achievement which triggers on a specific sequence of rolls."""
    sequence: str = "..."

    def __init__(self, sequence: str, title: str, text: str, unlocked: bool = False):
        self.sequence = sequence
        key = f"seq_{sequence}"
        super().__init__(key, title, text, unlocked)

    def __repr__(self):
        return f"{super().__repr__()}(Seq {self.sequence})"


achievements_list: list[Achievement] = [
    Achievement("hello", "First achievement 🕊️", "Hello you :3"),
    RollAchievement(1, "Roll fail 🎲", "C'est terrible ce qui t'arrive mec, TERRIBLE !"),
    RollAchievement(8, "Roll 8", "Lucky 8 🍀"),
    RollAchievement(10, "Roll win 🌈", "Living the life 😎"),
    SequenceAchievement("13", "Hey you :3", "It's dangerous to go alone, take this 🍀"),
    SequenceAchievement("00", "Double Zero 🎯", "What are the chances??"),
    SequenceAchievement("007", "Agent Bond 🔫", "Quite a bad roll though"),
    SequenceAchievement("420", "4:20 my dude", "HIGH AS A KITE"),
    SequenceAchievement("421", "Un p'tit 421 ?", "I'd rather be playing dice lol"),
    SequenceAchievement("555", "555 🔥", "🎸 if you're 5-5-5 I'm 666 🤟"),
    SequenceAchievement("666", "666 🦹", "Diabolically partial success!"),
    SequenceAchievement("777", "🎰 777 🎰", "CASINO MODE! ALL PLAY IS NOW FREE 💸"),
]
achievements_map: dict[str, Achievement] = {a.key: a for a in achievements_list}
achievements_rolls: list[RollAchievement] = [a for a in filter(lambda a: type(a) is RollAchievement, achievements_list)]
achievements_sequence: list[SequenceAchievement] = [
    a for a in filter(lambda a: type(a) is SequenceAchievement, achievements_list)]

if __name__ == '__main__':
    print("Achievements:")
    for a in achievements_list:
        print(a)
