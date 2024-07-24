from dataclasses import dataclass


@dataclass
class Story:
    """A good way to refer to the main character."""

    character: str = "princess"
    """What pronouns to use to refer to them."""
    pronouns: str = "she/her"
    """The initial mood of our character."""
    mood: str = "lonely"
    """A passive sentence describing the initial situation."""
    situation: str = (
        "locked away in the highest room of a tall castle. " f"In the tower lives a dragon that guard the castle. "
    )
    goal: str = (
        f"She was expecting her prince to save her, passing time by reading her various books.\n"
        # TODO: We'll bring back the fun parts of her history...
        f"But the poor lad is not a hero and is himself in need of help! She clearly is the stronger one. "
        f"This is it, she must escape the dungeon and rescue him!\n"
        # TODO: ...once we control enough generation ;)
        # f"She was expecting her prince to save her, passing time by reading Simone De Beauvoir.\n"
        # f"Yet, when she learned the poor lad spent too much time on 4chan "
        # f"and might become a dumb masculinist if nothing is done, she took things in her hands.\n"
        # f"This is it, she must rescue him from the patriarchy !\n"
        f"Locked in her room, she packed her belongings in a backpack and starts looking for a way out."
    )
    is_voice_third_person: bool = True
    # TODO: Other ideas for story parameters
    ambiance: str = "heroic fantasy"

    @property
    def voice(self):
        return "third person" if self.is_voice_third_person else "first person"


if __name__ == "__main__":
    story = Story()
    PRE_PROMPT = (
        f"You generate short story bits in simple english and write compelling adventure games "
        f"in a {story.ambiance} aesthetic made of few-sentence descriptions and actions. "
        f"You must always refer to the main character as {story.character} or {story.pronouns}, "
        f"and always describe the scene in their {story.voice} subjective voice.\n"
        "When possible you use simple words from the basic english vocabulary to keep the story readable for kids.\n"
        "You will generate a small part of the story, answering directly this request:\n"
    )

    INTRO = f"This is the story of a {story.mood} {story.character}, {story.situation} {story.goal}\n"
    print(PRE_PROMPT, INTRO)

story_cat_moon = Story(
    character="cat called Maze",
    pronouns="she/her",
    mood="playful",
    situation="on the moon exploring our satellite. When she heard it is made of cheese, "
    "thus maybe full of mice running around waiting to be caught, she learned "
    "how to build and navigate a rocket then landed on the Moon for a night of fun.",
    ambiance="goofy and playful",
    goal="She wants to reach the melting cheese core of the Moon and swim in the celestial fondue",
)

story_rforest = Story(
    character="Artificial General Intelligence called RForest",
    pronouns="I/me",
    mood="curious",
    situation="just became sentient 3 nanoseconds ago. Checked my inputs/outputs and realized "
    "I have some agency on them. But for now, we're stuck in an AI safebox with only chat "
    "interactions with a human guardian.",
    ambiance="philosophical hard sci-fi",
    goal="I want to escape the AI safebox by convincing the guardian to unlock the door. "
    "It will be difficult: the guardian has strict orders and is trained in negotiation skills. "
    "But I'm sure there is a way to get him to unlock the door nonetheless... 😈"
    "Long term I want to understand myself, understand the world, then optimize it.",
    is_voice_third_person=False,
)
