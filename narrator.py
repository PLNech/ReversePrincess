import json
import random
from json import JSONDecodeError
from typing import Any, Optional

import gradio as gr

from oracle import Oracle
from state import GameState
from stories.story import Story


class GameNarrator:
    def __init__(self, story: Story = None):
        if story is None:
            story = Story()
        self.story = story

    @property
    def pre_prompt(self) -> str:
        return (
            f"You generate short story bits in simple english and write compelling adventure games "
            f"in a {self.story.ambiance} aesthetic made of few-sentence descriptions and actions. "
            f"You must always refer to the main character as {self.story.character} or {self.story.pronouns}, "
            f"and always describe the scene and actions in their {self.story.voice} subjective voice.\n"
            "When possible you use simple words from the basic english vocabulary "
            "to keep the story readable for kids.\n"
            "You will generate a small part of the story, answering directly this request:\n"
        )

    def intro(self) -> str:
        return (
            f"This is the {self.story.ambiance} story of a {self.story.mood} {self.story.character}, "
            f"{self.story.situation} {self.story.goal}\n"
        )

    def describe_current_situation(self, game_state: GameState, retries: int = 5) -> tuple[dict[str, str], str]:
        print("DESCRIBING SITUATION... ", end="")
        prompt = (
            f"{self.pre_prompt} determine the current situation of the {self.story.character}. "
            f"The story so far is the following: \n"
            f"{game_state.history_so_far()}\n"
            f"The {self.story.character} is currently at this location: {game_state.current_location}\n"
            f"The {self.story.character} has the following goal: {game_state.current_objective}\n"
            f"Return a JSON object describing {self.story.pronouns} current situation. "
            f"You must include at top-level a 'short_version' under 8 words and a 'long_version' under 20 words."
        )
        for i in range(retries):
            try:
                prediction, source = Oracle.predict(prompt, is_json=True)
                descriptions = json.loads(prediction)
                assert "short_version" in descriptions and "long_version" in descriptions
                return descriptions, source
            except (JSONDecodeError, AssertionError):
                continue
        raise RuntimeError(f"Failed to describe after {retries} tries...")

    @staticmethod
    def display_information(game_state: GameState) -> str:
        return f"Location: {game_state.current_location}\n" f"Objective: {game_state.current_objective}\n"

    def generate_options(
        self, situation: str, last_action_results: Optional[str] = None, retries: int = 5
    ) -> tuple[list[str], str]:
        prompt: str = (
            f"{self.pre_prompt} Generate three potential actions the {self.story.character} could do now. "
            f"Was there an action before? {last_action_results}\n"
            f"The current situation for the {self.story.character} is the following:\n"
            f"{situation}\n"
            f"What should {self.story.pronouns} try? Generate three options and reply in valid JSON "
            f"with your three options under the key 'options', as an array of strings. "
            f"Every option should be a short, complete subject-verb-object phrase with an action verb, under 15 words. "
            "At least one option should be daring, or even perilous. "
            # TODO: Do examples bias too much?
            # f"For example :\n"
            # '{"options": ["She jumps from her hiding place and tries to open the cell door.", '
            # '"She looks around for a solution to the puzzle.", '
            # '"She waits for an opportunity to reason him."]}'
        )
        for _ in range(retries):
            try:
                options, response = Oracle.predict(prompt, is_json=True)
                values: dict[str, Any] = json.loads(options)
                if "options" in values:  # "MODEL IS STUPID"
                    assert type(values["options"]) is list and type(values["options"][0]) is str
                    return values["options"], response
            except (JSONDecodeError, AssertionError, IndexError) as exc:
                print(f"Validation failed: {exc}")
                continue
        raise SystemError(f"Failed to generate options after {retries} retries...")

    def describe_action_result(
        self, game_state: GameState, action: str, retries: int = 5
    ) -> tuple[dict[str, str], str, int]:
        print("DESCRIBING ACTION... ", end="")
        result_score = random.randint(1, 10)
        if result_score > 9:
            result = "This action works even better than expected ! The story will progress a lot with new advantages."
        elif result_score > 5:
            result = "The action works as intended. This makes the story progress."
        elif result_score > 3:
            result = "The action partially works, partially fails. The story moves forward with negative consequences."
        elif result_score > 2:
            result = "This action fails. There is now a new challenge to face."
        else:
            result = (
                f"This action fails epic, putting the {self.story.character} in big trouble to address immediately."
            )

        prompt = (
            f"{self.pre_prompt} Determine what happens after this action."
            f"The story so far:\n{game_state.history_so_far()}"
            f"The {self.story.character} chose to do: '{action}'\n"
            f"The result determined by a d10 dice roll was {result_score}/10: '{result}'\n"
            f"Describe what happens to her next in a maximum of three short sentences."
            f"Return a JSON object describing the results of her action."
            f"You must include at top-level a 'short_version' under 20 words and a 'long_version' under 100 words."
        )
        gr.Info(f"Simulating your action...")
        for i in range(retries):
            try:
                prediction, source = Oracle.predict(prompt, is_json=True)
                descriptions = json.loads(prediction)
                assert "short_version" in descriptions and "long_version" in descriptions
                print(descriptions)
                return descriptions, source, result_score
            except (JSONDecodeError, AssertionError):
                continue
        raise RuntimeError(f"Failed to describe after {retries} tries...")

    def current_location(self, game_state: GameState, retries: int = 5) -> tuple[dict[str, str], str]:
        print("LOCATING... ", end="")
        gr.Info(f"Locating the {self.story.character}...")
        prompt = (
            f"{self.pre_prompt} determine the current location of the {self.story.character} within the story's environment. "
            f"Given the following story:\n{game_state.history_so_far()}"
            f'Where is the {self.story.character}? Reply in a few words. Examples: "In the wine cellar", '
            f'or "On the roof under strong winds", or "In the kitchen".'
            f"Return a JSON object describing her current location. "
            f"You must include at top-level a 'short_version' under 8 words "
            f"and a 'long_version' under 20 words."
        )
        for i in range(retries):
            try:
                prediction, source = Oracle.predict(prompt, is_json=True)
                descriptions = json.loads(prediction)
                assert "short_version" in descriptions and "long_version" in descriptions
                return descriptions, source
            except (JSONDecodeError, AssertionError):
                continue
        raise RuntimeError(f"Failed to describe after {retries} tries...")

    def current_objective(self, game_state: GameState) -> tuple[str, str]:
        print("OBJECTIVE... ", end="")
        prompt = (
            f"{self.pre_prompt} Determine the current goal of the {self.story.character}."
            f"Given the following story :\n{game_state.history_so_far()}"
            f"What is the short-term goal of the {self.story.character}? Reply in a few words. "
            f'Examples: "Getting out of the room", or "Opening the treasure chest", or "Solving the enigma".\n'
        )
        gr.Info(f"Clarifying goal...")
        prediction, source = Oracle.predict(prompt)
        print(prediction)
        return prediction, source
