import json
import random
from json import JSONDecodeError
from typing import Any

from oracle import Oracle
from state import GameState


class GameNarrator:
    _PRE_PROMPT = (
        f"You are the narrator of the story, you must write in the style of Brandon Sanderson. "
        f"You must always refer to the main character as the princess or she, "
        f"and always describe scene in the third person.\n"
    )

    introduction = (
        f"This is the story of a lonely princess, locked away in the highest room of a tall castle.\n"
        f"In the tower lives a dragon that guard the castle. "
        f"She was expecting her prince to save her, passing time by reading Simone De Beauvoir.\n"
        f"Yet, when she learned the poor lad spent too much time on 4chan "
        f"and might become a dumb masculinist if nothing is done, she took things in her hands.\n"
        f"This is it, she must rescue him from the patriarchy !\n"
        f"Locked in her room, she has made her backpack and is looking for a way out."
    )

    @staticmethod
    def describe_current_situation(game_state: GameState) -> tuple[str, str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"The story so far is the following: \n"
            f"{game_state.history_so_far()}\n"
            f"The princess is currently at this location: {game_state.current_location}\n"
            f"The princess has the following goal: {game_state.current_objective}\n"
            f"Make a quick description under 20 words of her current situation. "
            f"Check your work to make it short enough."
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
            f"The current situation for the princess is the following:\n"
            f"{situation}\n"
            f"What could she try? Generate three options and reply in valid JSON "
            f"with your three options under the key 'options', as an array of strings. "
            f"Every option should be short, under 10 words. "
            f"For example :\n"
            '{"options": ["She tries to open the cell door.", '
            '"She looks around for a solution.", '
            '"She waits for an opportunity."]}'
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

    @staticmethod
    def describe_action_result(game_state: GameState, action: str) -> tuple[str, str]:
        result_score = random.randint(0, 10)
        if result_score > 9:
            result = "This action works even better than expected !"
        elif result_score > 5:
            result = "The action works as intended."
        elif result_score > 3.5:
            result = "The action partially works, partially fails."
        elif result_score > 2:
            result = "This action fails."
        else:
            result = (
                "This action fails epic, putting the princess in big trouble."
            )

        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"The history so far:\n"
            f"{game_state.history_so_far()}"
            f"The princess chose to do: '{action}'\n"
            f"The result was {result_score}/10: '{result}'\n"
            f"Describe what happens to her next in a maximum of three short sentences."
        )
        return Oracle.predict(prompt)

    @staticmethod
    def current_location(game_state: GameState) -> tuple[str, str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"Given the following story:\n"
            f"{game_state.history_so_far()}"
            f"Where is the princess? Reply in a few words. Examples:\n"
            f"- In the wine cellar\n"
            f"- On the roof under strong winds\n"
            f"- In the kitchen\n"
        )
        return Oracle.predict(prompt)

    @staticmethod
    def current_objective(game_state: GameState) -> tuple[str, str]:
        prompt = (
            f"{GameNarrator._PRE_PROMPT}"
            f"Given the following story :\n"
            f"{game_state.history_so_far()}"
            f"What is the short-term goal of the princess? Reply in a few words. Examples:\n"
            "- Getting out of the room.\n"
            "- Opening the treasure chest.\n"
            "- Solving the enigma.\n"
        )
        return Oracle.predict(prompt)
