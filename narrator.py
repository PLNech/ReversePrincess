import json
import random
from json import JSONDecodeError
from typing import Any

import gradio as gr

from oracle import Oracle
from prompts import PRE_PROMPT
from state import GameState


class GameNarrator:

    @staticmethod
    def describe_current_situation(game_state: GameState) -> tuple[str, str]:
        print("DESCRIBING SITUATION... ", end="")
        prompt = (
            f"{PRE_PROMPT} determine the current situation of the princess. "
            f"The story so far is the following: \n"
            f"{game_state.history_so_far()}\n"
            f"The princess is currently at this location: {game_state.current_location}\n"
            f"The princess has the following goal: {game_state.current_objective}\n"
            f"Make a quick description under 20 words of her current situation. "
            f"Check your work to make it short enough."
        )
        prediction, source = Oracle.predict(prompt)
        print(prediction)
        return prediction, source

    @staticmethod
    def display_information(game_state: GameState) -> str:
        return (
            f"Location: {game_state.current_location}\n"
            f"Objective: {game_state.current_objective}\n"
        )

    @staticmethod
    def generate_options(situation: str = None, retries: int = 3) -> tuple[list[str], str]:
        prompt = (
            f"{PRE_PROMPT} Generate three potential actions the princess could do now."
            f"The current situation for the princess is the following:\n"
            f"{situation}\n"
            f"What could she try? Generate three options and reply in valid JSON "
            f"with your three options under the key 'options', as an array of strings. "
            f"Every option should be a short, complete subject-verb-object phrase with an action verb, under 15 words. "
            f"For example :\n"
            '{"options": ["She tries to open the cell door.", '
            '"She looks around for a solution to the puzzle.", '
            '"She waits for an opportunity to reason him."]}'
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
    def describe_action_result(game_state: GameState, action: str) -> tuple[str, str, int]:
        print("DESCRIBING ACTION... ", end="")
        result_score = random.randint(0, 10)
        if result_score > 9:
            result = "This action works even better than expected !"
        elif result_score > 5:
            result = "The action works as intended."
        elif result_score > 3:
            result = "The action partially works, partially fails."
        elif result_score > 2:
            result = "This action fails."
        else:
            result = (
                "This action fails epic, putting the princess in big trouble."
            )

        prompt = (
            f"{PRE_PROMPT} Determine what happens after this action."
            f"The history so far:\n"
            f"{game_state.history_so_far()}"
            f"The princess chose to do: '{action}'\n"
            f"The result determined by a d10 dice roll was {result_score}/10: '{result}'\n"
            f"Describe what happens to her next in a maximum of three short sentences."
        )
        gr.Info(f"Describing action result: \"{action} -> {result}\"")
        prediction, source = Oracle.predict(prompt)
        print(prediction)
        return prediction, source, result_score

    @staticmethod
    def current_location(game_state: GameState) -> tuple[str, str]:
        print("LOCATING... ", end="")
        prompt = (
            f"{GameNarrator._PRE_PROMPT} determine the current location of the princess. "
            f"Given the following story:\n"
            f"{game_state.history_so_far()}"
            f"Where is the princess? Reply in a few words. Examples:\n"
            f"- In the wine cellar\n"
            f"- On the roof under strong winds\n"
            f"- In the kitchen\n"
        )
        gr.Info(f"Locating princess...")
        prediction, source = Oracle.predict(prompt)
        print(prediction)
        return prediction, source

    @staticmethod
    def current_objective(game_state: GameState) -> tuple[str, str]:
        print("OBJECTIVE... ", end="")
        prompt = (
            f"{PRE_PROMPT} Determine the current goal of the princess."
            f"Given the following story :\n"
            f"{game_state.history_so_far()}"
            f"What is the short-term goal of the princess? Reply in a few words. Examples:\n"
            "- Getting out of the room.\n"
            "- Opening the treasure chest.\n"
            "- Solving the enigma.\n"
        )
        gr.Info(f"Clarifying goal...")
        prediction, source = Oracle.predict(prompt)
        print(prediction)
        return prediction, source
