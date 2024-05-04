import datetime
import json
from dataclasses import dataclass
from typing import Any, Optional

import gradio as gr
from PIL.Image import Image

from narrator import GameNarrator
from oracle import choose_model
from prompts import INTRO
from state import GameState
from visuals.diffuse import text2image

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
SAVE = True


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
    model: str
    extra: dict[str, Any]


def save_generation(prompt: str, response: str, model: Optional[str] = None, extra: Optional[dict] = None) -> None:
    if model is None:
        model = choose_model()
    data = Generation(prompt, response, model, extra)
    timestamp = int(datetime.datetime.now().timestamp())
    with open(f"generated/{timestamp}.json", "w") as file:
        json.dump(data.__dict__, file)


def respond(button: str, chat_history, json_src):
    """
    Respond to the user's choice, advancing the story.

    The response flows along these steps:
    - User Choice
    - Action result/D10 = describe(choice)
    - Update state with long description
    - Location = curLocation(state)
    - Objective = curLocation(state)
    - Update state with location+objective
    - New situation = display(location+objective)
    - New options = generate3(new situation)

    :param button:
    :param chat_history:
    :param json_src:
    :return:
    """
    print(f"Choice: {button}")
    chat_history.append((button, None))  # Add immediately the player's chosen action
    yield "", "", "", chat_history, "", None, json_src

    action_result, _, d10 = GameNarrator.describe_action_result(game_state, button)
    chat_history.append((None, f"## Action Result: D10->{d10}\n###{action_result}"))  # Display action result
    yield "", "", "", chat_history, "", None, json_src

    descriptions, _ = GameNarrator.describe_current_situation(game_state)
    game_state.update([action_result, descriptions["long_description"]])
    # Then display resulting position
    chat_history.append((None, f"## {descriptions['short_description']}\n{descriptions['long_description']}"))
    yield "", "", "", chat_history, "", None, json_src

    location, _ = GameNarrator.current_location(game_state)
    objective, _ = GameNarrator.current_objective(game_state)
    game_state.update(None, location, objective)

    new_situation = GameNarrator.display_information(game_state)
    print(f"FINAL SITUATION: {new_situation}")
    new_options, response = GameNarrator.generate_options(new_situation)
    print(f"FINAL OPTIONS: {new_options}")
    yield new_options[0], new_options[1], new_options[2], chat_history, new_situation, None, response

    yield new_options[0], new_options[1], new_options[2], chat_history, new_situation, response


if __name__ == "__main__":
    print("Running game!")
    game_state = GameState(INTRO)

    if DEBUG_LOCAL_INIT:
        current_situation = INTRO
        options = ["Do a barrel roll", "Dance him to death", "What would Jesus do???"]
        json_str = json.dumps(options)
        current_info = GameNarrator.display_information(game_state)
    else:
        current_situation, _ = GameNarrator.describe_current_situation(game_state)
        options, json_str = GameNarrator.generate_options(current_situation["long_description"])
        current_info = "INFO"

    # Theme quickly generated using https://www.gradio.app/guides/theming-guide - try it and change some more!
    theme = gr.themes.Soft(
        text_size="lg",
        spacing_size="lg",
        radius_size="lg",
    ).set(
        body_background_fill='*block_background_fill',
        body_text_size='*text_lg'
    )
    with gr.Blocks(title="Reverse Princess Simulator", css="footer{display:none !important}", theme=theme
                   ) as demo:
        with gr.Row(elem_classes=["box_chat"]) as row1:
            chatbot = gr.Chatbot(
                label="Damsell in Prowess",
                elem_classes=["box_chatbot"],
                value=[[None, INTRO]],
                scale=3,
                height=768
            )
            with gr.Column(scale=1, elem_classes=["box_info"]) as col:
                situation = gr.TextArea(
                    label="Current situation",
                    value=current_info,
                    scale=1,
                )
                json_view = gr.Json(value=json_str, label="Last oracle reply", scale=2)

        with gr.Row(elem_classes=["box_buttons"]) as row2:
            print("Loading initial choice... ", end="")
            print(f"Buttons: {options}")

            action1 = gr.Button(f"{options[0]}")
            action2 = gr.Button(f"{options[1]}")
            action3 = gr.Button(f"{options[2]}")

        outputs = [action1, action2, action3, chatbot, situation, json_view]

        action1.click(respond, [action1, chatbot, json_view], outputs)
        action2.click(respond, [action2, chatbot, json_view], outputs)
        action3.click(respond, [action3, chatbot, json_view], outputs)

    demo.queue()
    demo.launch(allowed_paths=["static/"], favicon_path="static/princess.ico")
