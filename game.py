import datetime
import json
import time
from typing import Any
from dataclasses import dataclass
from functools import lru_cache
from json import JSONDecodeError
from GameState import GameState
from GameNarrator import GameNarrator
import gradio as gr
import ollama

PROMPT_INTRO = (
    "The year is 1900 and the whole western world is delighted by the Paris _Exposition Universelle_. "
    "But you are a princess, and you're imprisoned by a bad guy in a Hotel Particulier in Paris!"
    "And worse, your beloved prince got trapped - he doesn't seem so good at saving anyone, even his ass. "
    "Can you escape the castle to go rescue this cute loser?"
    "\n You start your journey in the following room:"
)
SYSTEM = "You are a story generator."
BUTTON_BEGIN = "Once upon a time, the princess was locked in"

DEBUG_LOCAL_INIT = False


def vote(data: gr.LikeData):
    # TODO Use the vote!
    if data.liked:
        print("You upvoted this response: " + data.value)
    else:
        print("You downvoted this response: " + data.value)


@dataclass
class Generation:
    prompt: str
    response: str
    extra: dict[str, Any]


def save_options(prompt: str, response: str, extra: dict) -> None:
    data = Generation(prompt, response, extra)
    timestamp = int(datetime.datetime.now().timestamp())
    with open(f"generated/{timestamp}.json", "w") as file:
        json.dump(data.__dict__, file)


def respond(button: str, chat_history, situation, json_view):
    action_result = GameNarrator.describe_action_result(game_state, button)
    chat_history.append((button, action_result))

    current_situation = GameNarrator.describe_current_situation(game_state)
    chat_history.append((None, current_situation))

    location = GameNarrator.current_location(game_state)
    objective = GameNarrator.current_objective(game_state)
    game_state.update([action_result, current_situation], location, objective)

    situation = GameNarrator.display_information(game_state)
    options, response = GameNarrator.generate_options(game_state)
    json_view = response
    return options[0], options[1], options[2], chat_history, situation, json_view


if __name__ == "__main__":
    print("Running game!")
    game_state = GameState(GameNarrator.introduction)

    with gr.Blocks(title="Reverse Princess Simulator") as demo:
        with gr.Row() as row1:
            chatbot = gr.Chatbot(
                label="Damsell in Prowess",
                value=[[None, GameNarrator.introduction]],
                scale=3,
            )
            with gr.Column(scale=1) as col:
                situation = gr.TextArea(
                    label="Current situation",
                    value=(GameNarrator.display_information(game_state)),
                    scale=1,
                )
                json_view = gr.Json(value=None, label="Last oracle reply", scale=2)

        with gr.Row() as row2:
            print("Loading initial choice... ", end="")
            current_situation = GameNarrator.describe_current_situation(game_state)
            options, json_str = GameNarrator.generate_options(current_situation)
            print(f"Buttons: {options}")

            action1 = gr.Button(f"{options[0]}")
            action2 = gr.Button(f"{options[1]}")
            action3 = gr.Button(f"{options[2]}")

        outputs = [action1, action2, action3, chatbot, situation, json_view]

        action1.click(
            respond,
            [action1, chatbot, situation, json_view],
            outputs,
        )
        action2.click(
            respond,
            [action2, chatbot, situation, json_view],
            outputs,
        )
        action3.click(
            respond,
            [action3, chatbot, situation, json_view],
            outputs,
        )

        # chatbot.like(vote, None, None)
    demo.queue()
    demo.launch(allowed_paths=["static/"], favicon_path="static/princess.ico")
