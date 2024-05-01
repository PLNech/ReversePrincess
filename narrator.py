import json
import random
from json import JSONDecodeError
from typing import Any

from state import GameState
from oracle import Oracle


class GameNarrator:
    _PRE_PROMPT = (
        f"You are the narrator of the story, you must write in the style of Brandon Sanderson. "
        f"You must always refer to the main character as the princess or she, "
        f"and always describe scene in the third person.\n"
    )

    introduction = (
        f"This is the story of a lonely princess, locked away in the highest room of a tall castle.\n"
        f"In the tower lives a dragon that guard the castle. "
        f"She was expecting her prince to save her, passing time Reading Simone De Beauvoir.\n"
        f"Yet, when she learned the poor lad spent too much time on 4chan "
        f"and might become a dumb masculinist if nothing is done, she took things in her hands.\n"
        f"This is it, she must rescue him from the patriarchy !\n"
        f"Locked in her room, she has made her backpack and is looking for a way out."
    )

    @staticmethod
    def describe_current_situation(game_state: GameState) -> tuple[str, str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"The story so far is the follow : \n"
            f"{game_state.history_so_far()}\n"
            f"The princess current location is {game_state.current_location}\n"
            f"The princess current goal is {game_state.current_objective}\n"
            f"Make a quick description of the current situation for the princess."
        )
        return Oracle.predict(prompt)

    @staticmethod
    def display_information(game_state: GameState) -> str:
        return (
            f"Location: {game_state.current_location}\n"
            f"Objective: {game_state.current_objective}\n"
        )

    @staticmethod
    def generate_options(situation: str = None, retries: int = 3) -> tuple[list[str], str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"The princess current situation is the following:\n"
            f"{situation}\n"
            f"What could she try ? Generate three options and reply in valid JSON "
            f"with your three options under the key 'options', as an array of strings. "
            f"Every option should be short, under 10 words. "
            f"For example :\n"
            '{"options": ["She tries to open the cell door.", "She looks around for a solution.", "She waits for an opportunity."]}'
        )
        for _ in range(retries):
            try:
                options, response = Oracle.predict(prompt)
                values: dict[str, Any] = json.loads(options)
                if "options" in values:  # "MODEL IS STUPID"
                    assert type(values["options"]) is list and type(values["options"][0]) is str
                    return values["options"], response
            except (JSONDecodeError, AssertionError, IndexError) as exc:
                print(f"Validation failed: {exc}")
                continue
        raise SystemError(f"Failed to generate options after {retries} retries...")

    @staticmethod
    def describe_action_result(game_state: GameState, action: str) -> tuple[str, str]:
        result = random.randint(0, 10)
        if result > 9:
            result = "This action works even better than expected !"
        elif result > 0:
            result = "This action works as intended."
        else:
            result = (
                "This action doesn't work at all, putting the princess in difficulty."
            )

        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"The history of what happened so far :\n"
            f"{game_state.history_so_far()}"
            f"The princess choose the following action :\n"
            f"{action}\n"
            f"{result}\n"
            f"Describe what happen to her in two or three short sentences."
        )
        return Oracle.predict(prompt)

    @staticmethod
    def current_location(game_state: GameState) -> tuple[str, str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"Given the following story :\n"
            f"{game_state.history_so_far()}"
            f"Where is the princess ?"
        )
        return Oracle.predict(prompt)

    @staticmethod
    def current_objective(game_state: GameState) -> tuple[str, str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"Given the following story :\n"
            f"{game_state.history_so_far()}"
            f"What is the short term goal of the princess ?"
        )
        return Oracle.predict(prompt)
