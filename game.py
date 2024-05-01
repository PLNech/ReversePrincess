import json
from functools import lru_cache
from json import JSONDecodeError
from typing import Any

import gradio as gr
import ollama

PROMPT_INTRO = ("The year is 2077 and the world is a cyberpunk utopia. "
                "But you are a princess, and you're imprisoned in a dragon's dungeon in his virtual reality castle! "
                "And worse, your beloved prince got trapped - he doesn't seem so good at saving anyone, even his ass. "
                "Can you escape the castle to go rescue this cute loser?"
                "\n You start your journey in the following room:")
SYSTEM = "You are a story generator."
BUTTON_BEGIN = "Once upon a time, the princess was locked in"

DEBUG_LOCAL_INIT = False


def vote(data: gr.LikeData):
    # TODO Use the vote!
    if data.liked:
        print("You upvoted this response: " + data.value)
    else:
        print("You downvoted this response: " + data.value)


model_preferences = [  # Ordered by storytelling capability, prove me wrong
    "llama3:70b-text-q2_K ",
    "llama3:latest",
    "dolphin-mistral:latest",
    "dolphin-mistral:7b-v2-q3_K_S",
    "gemma:latest",
    "gemma:7b",
    "llama2-uncensored:70b",
    "llama2-uncensored:latest",
    "stablelm2:latest",
    "wizard-vicuna-uncensored:30b",
    "zephyr:latest"
]


@lru_cache(maxsize=1)
def choose_model() -> str:
    print("Choosing model...")
    models = ollama.list()
    local_models = [m["name"] for m in
                    sorted(models["models"], key=lambda m: m["details"]["parameter_size"], reverse=True)]

    for choice in model_preferences:
        if choice in local_models:
            print(f"Found preferred model {choice}!")
            return choice
    print("No preferred model available, returning your local model with highes # of parameters.")
    return local_models[0]


def oracle(question: str, is_json: bool = True) -> str:
    model_name = choose_model()
    response = ollama.chat(model=model_name, format="json" if is_json else "", messages=[
        {
            "role": "user",
            "content": question,
        },
    ])
    response: [dict, str] = response["message"]
    content = response["content"] if "content" in response else response
    clean = content.strip("\n ")
    return clean


def make_options(input_prompt: str = None,
                 retries: int = 3) -> [list[str], str]:
    # options = ["ACTION 1", "ACTION 2", "ACTION 3"]
    prompt = (f"{SYSTEM} {input_prompt}. Generate three options and reply in JSON, "
              f"with your three options under the key 'options', as an array of strings. Don't use the word 'option'.")
    print(f"P[{prompt}]->")
    for _ in range(retries):
        oracle_response = oracle(prompt)
        values: dict[str, Any] = json.loads(oracle_response)
        if "options" in values:  # "MODEL IS STUPID"
            print(f"\n->{oracle_response}")
            return values["options"], oracle_response
    raise SystemError(f"Failed to make options after {retries} retries...")


def game_step(choice: str, inventory: list[str],
              retries: int = 5) -> tuple[str, list[str]]:
    for _ in range(retries):
        example_response = {"story":
                                "You unlock the door and see a room full of books.",
                            "inventory": ["A weirdly-shaped golden key", "Your map of the underground networks",
                                          "A mirror connected to the world\'s magic information field"]}
        prompt = (f"The princess chose {choice}. Her inventory was {inventory}. "
                  f"What happens next to her? Don't mention the choice, just the action and consequences. "
                  f"Reply in a short, descriptive sentence, as a string under the key 'story'. "
                  "If she gets or loses an item as a consequence, add an 'inventory' key "
                  "with an updated list of strings describing her belongings she currently holds. "
                  f"Example response: {json.dumps(example_response)}")
        print(f"{prompt}")
        next_step: str = oracle(prompt)
        print(f"->{next_step}")
        try:
            next_data: dict[str, Any] = json.loads(next_step)
            if all([key in next_step for key in ["story", "inventory"]]):
                story: str = next_data["story"]
                new_inventory: list[str] = next_data["inventory"]
                if len(new_inventory) < 3:
                    inventory = [*inventory, *new_inventory][:3]
                return story, new_inventory
            else:
                print(f"Missing story/inventory: {next_data}")
        except (ValueError, TypeError, JSONDecodeError) as e:
            print(f"Error {type(e)}: {e}")
            continue
    raise SystemError(f"Failed to generate story+inventory after {retries} tries...")


def respond(choice: str, chat_history, inventory: list[str]):
    bot_message, new_inventory = game_step(choice, inventory)
    print(f"C  Choice:{choice}")
    print(f"S  Story:{bot_message}")
    print(f"NI New Inventory:{new_inventory}")
    if new_inventory is None or new_inventory[0] == "None":
        new_inventory = inventory
    try:
        prompt_specific_options = f"The story so far: {chat_history}. My choice is now: {choice}. " \
                                  f"The inventory was: {inventory} and is now: {new_inventory}. " \
                                  f"What can I do next, phrased from my first-person perspective? " \
                                  f"Give me three options: the first one should be safe, even if potentially dull. " \
                                  f"the second one should be daring and more adventurous. " \
                                  f"the third one should be funky and wacky, try to be fun if you can make a joke. " \
                                  "Try to balance options to use different inventory items, when some are relevant. " \
                                  "Keep each option short, as it will be displayed on a button. "
        options, json_str = make_options(prompt_specific_options)
        print(f"Buttons: {options}")
        assert len(options) == 3, "Bad options!"
    except [AssertionError, JSONDecodeError] as exc:
        print(f"Bad options! {exc} -> {options}")
        raise
    chat_history.append((choice, bot_message))

    try:
        assert type(inventory) is list and type(inventory[0]) is str
    except AssertionError as exc:
        print(f"Failed inventory: {exc} - defaulting to {inventory}")
        new_inventory = ["A butterfly"]
    return options[0], options[1], options[2], chat_history, "\n".join(["- " + n for n in new_inventory]), json_str


if __name__ == '__main__':
    import gradio as gr

    gr.set_static_paths(paths=["static/"])

    print("Running game!")

    print("Loading initial inventory... ", end="")
    if DEBUG_LOCAL_INIT:
        print("DEBUG LocalInit activated! Initial options are hardcoded for quick iteration")
        options = ['A trusty multitool that can cut, saw, and hammer its way out of any situation.',
                   "The family heirloom locket with  a lock of her mother's hair, passed down through generations.",
                   'A pet tarantula named Mr. Whiskers who has a knack for sensing danger and warns of impending doom.']
    else:
        options, _ = make_options(
            "The princess has three objects with her: the first is a versatile tool, "
            "the second an item of tremendous personal value, "
            "the third a surprising thing to have for a princess which makes the story fun.")
    stuff: list[str] = options
    print(f"Stuff: {stuff}")

    print("Loading initial choice... ", end="")
    if DEBUG_LOCAL_INIT:
        options = ["The damp cell with rusty bars", "The luxurious suite with a malfunctioning holographic display",
                   "The cold storage room filled with ancient technology"]
        json_str = json.dumps({"options": options})
    else:
        options, json_str = make_options(
            PROMPT_INTRO + " The story starts with just three options of rooms in the castle "
                           "where the princess could be locked in.")
    print(f"Buttons: {options}")

    # UI
    with gr.Blocks(title="Reverse Princess Simulator", css="footer{display:none !important}",
                   theme=gr.themes.Soft()) as demo:
        with gr.Row() as body:  # Outer layout is horizontal
            with gr.Column(scale=4) as col1:  # Story & Choices
                chatbot = gr.Chatbot(label="Damsell in Prowess", value=[(None, PROMPT_INTRO)], scale=3)
                with gr.Row() as buttons:  # Options
                    action1 = gr.Button(f"{BUTTON_BEGIN} {options[0]}.")
                    action2 = gr.Button(f"{BUTTON_BEGIN} {options[1]}.")
                    action3 = gr.Button(f"{BUTTON_BEGIN} {options[2]}.")

            with gr.Column(scale=1) as col2:  # Infos & Metadata
                # FIXME: Replace with List? Dataframe? Any tabular data UI
                inventory_view = gr.TextArea(label="Inventory",
                                             value="\n".join(["- " + s for s in stuff]),
                                             scale=1)
                json_view = gr.Json(value=json_str, label="Last oracle reply", scale=2)

        # Interactions must be mapped inside a gradio.Blocks context
        outputs = [action1, action2, action3, chatbot, inventory_view, json_view]
        action1.click(respond, [action1, chatbot, inventory_view], outputs)
        action2.click(respond, [action2, chatbot, inventory_view], outputs)
        action3.click(respond, [action3, chatbot, inventory_view], outputs)

    # chatbot.like(vote, None, None)
    demo.queue()
    demo.launch(allowed_paths=["static/"], favicon_path="static/princess.ico")
