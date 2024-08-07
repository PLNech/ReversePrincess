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
from prompts import IMAGE_STYLE_NAMES, IMAGE_STYLES, IMAGE_STYLE_DEFAULT
from state import GameState
from stories.story import story_cat_moon, story_rforest, Story
from visuals.diffuse import text2image

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

    action_results, json_output, d10 = narrator.describe_action_result(game_state, button)
    game_state.update([action_results["short_version"], action_results["long_version"]])
    achievements["rolls"].append(d10)
    chat_history.append(
        (
            None,
            f"## Action Result: rolled a {d10}/10 🔷\n###  {action_results['short_version']}  \n"
            f"{action_results['long_version']}",
        )
    )  # Display action result
    yield "", "", "", chat_history, "", json_output

    # TODO: I think in the end this step makes the actions less impactful,
    #  As a player I often don't see much link between previous action and next options
    # descriptions, json_output = narrator.describe_current_situation(game_state)
    # game_state.update([action_results["long_version"], descriptions["long_version"]])
    ## Then display resulting position
    # chat_history.append((None, f"## {descriptions['short_version']}\n{descriptions['long_version']}"))
    # yield "", "", "", chat_history, "", json_output

    location, _ = narrator.current_location(game_state)
    objective, _ = narrator.current_objective(game_state)
    game_state.update(None, location["short_version"], objective)

    new_situation = narrator.display_information(game_state)
    print(f"FINAL SITUATION: {new_situation}")
    new_options, response = narrator.generate_options(new_situation, action_results["long_version"])
    print(f"FINAL OPTIONS: {new_options}")
    yield new_options[0], new_options[1], new_options[2], chat_history, new_situation, response


def update_image(chat_history, style):
    history_texts = [c for x in chat_history for c in x if c is not None]
    selected = [t for t in history_texts if len(t) < 140]  # CLIP: 77 tokens
    selected_history = selected if selected else history_texts
    last_action_text = ",".join([x for x in selected_history])
    if "##" in last_action_text:
        try:
            last_action_text = last_action_text.split("##")[2]
        except Exception:
            pass

    # gr.Info(f"Generating action image in style {style}: {last_action_text[:20]}...")
    image: Image = text2image(f"{last_action_text}", IMAGE_STYLES[style])
    return image


def generate_caption(story: Story, situation: str) -> str:
    return f"The player character {story.character} is {story.mood} - {story.pronouns} situation {current_situation['short_version']}"


if __name__ == "__main__":
    print("Running game!")
    narrator = GameNarrator(story=story_rforest)  # Or e.g. (story=story_cat_moon)
    intro = narrator.intro()
    game_state = GameState(intro, narrator.story.situation, narrator.story.goal)

    if DEBUG_LOCAL_INIT:
        current_situation = {"long_version": intro}
        options = ["Do a barrel roll", "Dance him to death", "What would Jesus do???"]
        json_str = json.dumps(options)
        current_info = narrator.display_information(game_state)
        initial_image = None
    else:
        current_situation, _ = narrator.describe_current_situation(game_state)
        options, json_str = narrator.generate_options(current_situation["long_version"])
        current_info = "INFO"
        initial_image = text2image(generate_caption(story=narrator.story, situation=current_situation["short_version"]), fast=True)

    # Theme quickly generated using https://www.gradio.app/guides/theming-guide - try it and change some more!
    theme = gr.themes.Soft(
        text_size="md",
        spacing_size="lg",
        radius_size="lg",
    ).set(body_background_fill="*block_background_fill", body_text_size="*text_lg")
    with gr.Blocks(
            title="Reverse Princess Simulator", css="footer{display:none !important}", theme=theme,
            analytics_enabled=False
    ) as demo:
        achievements_store: gr.State = init_achievements()

        with gr.Tabs() as tabs:
            with gr.Tab(label="The Game"):
                with gr.Row(elem_classes=["box_main"]) as row1:
                    with gr.Column(scale=3, elem_classes=["box_chat"]):
                        chatbot = gr.Chatbot(
                            label="Damsell in Prowess",
                            elem_classes=["box_chatbot"],
                            value=[[None, intro]],
                            scale=3,
                            height="80%",
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

                        image_style = gr.Dropdown(
                            label="Illustration style",
                            interactive=True,
                            choices=IMAGE_STYLE_NAMES,
                            value=IMAGE_STYLE_DEFAULT,
                        )
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
        chatbot.change(update_achievements, [chatbot, achievements_store], [achievements_display],
                       show_progress="minimal")

    demo.queue()
    demo.launch(allowed_paths=["static/"], favicon_path="static/princess.ico")
