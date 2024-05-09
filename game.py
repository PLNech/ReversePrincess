import datetime
import json
from dataclasses import dataclass
from typing import Any, Optional

import gradio as gr
from PIL.Image import Image

from achievements.logic import init_achievements
from achievements.logic import update_achievements
from narrator import GameNarrator
from oracle import choose_model
from prompts import INTRO, IMAGE_STYLE_NAMES, IMAGE_STYLES, IMAGE_STYLE_DEFAULT
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


def respond(button: str, chat_history, json_src: str, achievements: dict):
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

    :param button: user choice
    :param chat_history: stateful history so far
    :param achievements: state of achievements and related data
    :param json_src: maintain displayed JSON until generation updates it
    :return:
    """
    print(f"Choice: {button}")
    chat_history.append((button, None))  # Add immediately the player's chosen action
    yield "", "", "", chat_history, "", json_src

    action_results, json_output, d10 = GameNarrator.describe_action_result(game_state, button)
    game_state.update([action_results["short_description"], action_results["long_description"]])
    achievements["rolls"].append(d10)
    chat_history.append((None, f"## Action Result: rolled a {d10}/10\n###  {action_results['short_description']}  \n"
                               f"{action_results['long_description']}"
                         ))  # Display action result
    yield "", "", "", chat_history, "", json_output

    descriptions, json_output = GameNarrator.describe_current_situation(game_state)
    game_state.update([action_results["long_description"], descriptions["long_description"]])
    # Then display resulting position
    chat_history.append((None, f"## {descriptions['short_description']}\n{descriptions['long_description']}"))
    yield "", "", "", chat_history, "", json_output

    location, _ = GameNarrator.current_location(game_state)
    objective, _ = GameNarrator.current_objective(game_state)
    game_state.update(None, location["short_description"], objective)

    new_situation = GameNarrator.display_information(game_state)
    print(f"FINAL SITUATION: {new_situation}")
    new_options, response = GameNarrator.generate_options(new_situation)
    print(f"FINAL OPTIONS: {new_options}")
    yield new_options[0], new_options[1], new_options[2], chat_history, new_situation, response


def update_image(chat_history, style):
    last_action_text = ",".join([x for x in chat_history[-1] if x is not None])
    gr.Info(f"Generating action image in style {style}: {last_action_text[:20]}...")
    image: Image = text2image(f"{last_action_text}", IMAGE_STYLES[style])
    return image


if __name__ == "__main__":
    print("Running game!")
    game_state = GameState(INTRO)

    if DEBUG_LOCAL_INIT:
        current_situation = {"long_description": INTRO}
        options = ["Do a barrel roll", "Dance him to death", "What would Jesus do???"]
        json_str = json.dumps(options)
        current_info = GameNarrator.display_information(game_state)
        initial_image = None
    else:
        current_situation, _ = GameNarrator.describe_current_situation(game_state)
        options, json_str = GameNarrator.generate_options(current_situation["long_description"])
        current_info = "INFO"
        initial_image = text2image(current_situation["short_description"], fast=True)

    # Theme quickly generated using https://www.gradio.app/guides/theming-guide - try it and change some more!
    theme = gr.themes.Soft(
        text_size="md",
        spacing_size="lg",
        radius_size="lg",
    ).set(
        body_background_fill='*block_background_fill',
        body_text_size='*text_lg'
    )
    with gr.Blocks(title="Reverse Princess Simulator", css="footer{display:none !important}",
                   theme=theme, analytics_enabled=False) as demo:
        achievements_store: gr.State = init_achievements()

        with gr.Tabs() as tabs:
            with gr.Tab(label="The Game"):
                with gr.Row(elem_classes=["box_main"]) as row1:
                    with gr.Column(scale=3, elem_classes=["box_chat"]):
                        chatbot = gr.Chatbot(
                            label="Damsell in Prowess",
                            elem_classes=["box_chatbot"],
                            value=[[None, INTRO]],
                            scale=3,
                            height=512
                        )

                        with gr.Row(elem_classes=["box_buttons"]) as row2:
                            print("Loading initial choice... ", end="")
                            print(f"Buttons: {options}")

                            action1 = gr.Button(f"{options[0]}")
                            action2 = gr.Button(f"{options[1]}")
                            action3 = gr.Button(f"{options[2]}")

                    with gr.Column(scale=1, elem_classes=["box_info"]) as col:
                        situation = gr.TextArea(
                            label="Current situation",
                            value=current_info,
                            scale=1,
                        )

                        image_style = gr.Dropdown(label="Illustration style", interactive=True,
                                                  choices=IMAGE_STYLE_NAMES, value=IMAGE_STYLE_DEFAULT)
                        illustration = gr.Image(show_label=False, value=initial_image, interactive=False)
                        json_view = gr.Json(value=json_str, label="Last oracle reply", scale=2)
            with gr.Tab(label="Achievements"):
                    achievements_display = gr.Markdown()

        outputs = [action1, action2, action3, chatbot, situation, json_view]
        inputs = [chatbot, json_view, achievements_store]

        action1.click(respond, [action1, *inputs], outputs)
        action2.click(respond, [action2, *inputs], outputs)
        action3.click(respond, [action3, *inputs], outputs)

        chatbot.change(update_image, [chatbot, image_style], illustration)
        chatbot.change(update_achievements, [chatbot, achievements_store], [achievements_display])

    demo.queue()
    demo.launch(allowed_paths=["static/"], favicon_path="static/princess.ico")
