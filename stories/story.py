from dataclasses import dataclass


@dataclass
class Story:
    character: str = "princess"
    pronouns: str = "she/her"


if __name__ == '__main__':
    story = Story("princess", "she/her")
    PRE_PROMPT = (
        f"You generate short story bits in simple english and write compelling adventure games "
        f"made of few-sentence descriptions and actions. "
        f"You must always refer to the main character as {story.character} or {story.pronouns}, "
        f"and always describe the scene in their third person subjective voice.\n"
        "When possible you use simple words from the basic english vocabulary to keep the story readable for kids.\n"
        "You will generate a small part of the story, answering directly this request:\n"
    )
    print(PRE_PROMPT)
