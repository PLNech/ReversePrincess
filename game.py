import json
from json import JSONDecodeError
from typing import Any

import gradio as gr
import ollama

PROMPT_INTRO = ("You are a princess imprisoned in a dragon's dungeon castle! "
                "And worse, your prince doesn't seem very good at saving anyone. "
                "Can you escape the castle to go rescue this cute loser?"
                "\n You start your journey in the following room:")
SYSTEM = "You are a story generator."


def vote(data: gr.LikeData):
    # TODO Use the vote!
    if data.liked:
        print("You upvoted this response: " + data.value)
    else:
        print("You downvoted this response: " + data.value)


def oracle(question: str, is_json: bool = True) -> str:
    response = ollama.chat(model="gemma", format="json" if is_json else "", messages=[
        {
            "role": "user",
            "content": question,
        },
    ])
    response: str = response["message"]
    # print(f"{question} -> {response}")
    content = response['content'] if "content" in response else response
    return content


def make_options(input_prompt: str = None,
                 retries: int = 3) -> list[str]:
    # options = ["ACTION 1", "ACTION 2", "ACTION 3"]
    prompt = (f"{SYSTEM} {input_prompt}. Generate three options and reply in JSON, "
              f"with your three options under the key 'options', as an array of strings.")
    for _ in range(retries):
        values: dict[str, Any] = json.loads(oracle(prompt))
        if 'options' in values:  # "MODEL IS STUPID"
            return values['options']
    raise SystemError(f"Failed to make options after {retries} retries...")


def game_step(choice: str, inventory: list[str],
              retries: int = 3) -> tuple[str, list[str]]:
    # return random.choice(["How are you?", "I love you", "I'm very hungry"])
    for _ in range(retries):
        prompt = (f"The princess chose {choice}. Her inventory was {inventory}. "
                  f"What happens next to her? Don't mention the choice, just the action and consequences. "
                  f"Reply in a short, descriptive sentence, as a string under the key 'story'. "
                  "Add a key 'inventory' with a list of strings describing her updated inventory.")
        next_step = oracle(prompt)
        print(next_step)
        try:
            next_step = json.loads(next_step)
            if all([key in next_step for key in ["story", "inventory"]]):
                story: str = next_step["story"]
                new_inventory: list[str] = next_step["inventory"]
                return story, new_inventory
            else:
                print(f"Missing story/inventory: {next_step}")
        except (ValueError, TypeError, JSONDecodeError) as e:
            print(f"Error {type(e)}: {e}")
            continue
    raise SystemError(f"Failed to generate story+inventory after {retries} tries...")


def respond(button: str, inventory: list[str], chat_history):
    bot_message, new_inventory = game_step(button, inventory)
    print(f"B:{button}")
    print(f"M:{bot_message}")
    print(f"NI:{new_inventory}")
    if new_inventory is None or new_inventory[0] is "None":
        new_inventory = inventory
    try:
        prompt_specific_options = f"The story so far: {chat_history}. The inventory was: {inventory} and is now: {new_inventory}." \
                                  f"What can I do next, phrased from my first-person perspective? Give me three options: " \
                                  f"the first one should be safe and boring. " \
                                  f"the second one should be daring and adventurous. " \
                                  f"the third one should be funky and wacky, try to be fun. " \
                                  "Try to balance options to use different inventory items, when relevant. "
        options = make_options(prompt_specific_options)
        print(f"Buttons: {options}")
        assert len(options) == 3, "Bad options!"
    except [AssertionError, JSONDecodeError] as e:
        print(f"Bad options! {options}")
        raise
    chat_history.append((button, bot_message))

    return options[0], options[1], options[2], chat_history, new_inventory


if __name__ == '__main__':
    import gradio as gr

    print("Running game!")
    with gr.Blocks(title="Reverse Princess Simulator") as demo:
        with gr.Row() as row1:
            chatbot = gr.Chatbot(label="Damsell in Prowess", value=[(None, PROMPT_INTRO)], scale=3)
            with gr.Column(scale=1) as col:
                print("Loading initial inventory...", end="")
                stuff: list[str] = make_options(
                    "The princess has three objects with her: the first is a versatile tool, "
                    "the second an item of tremendous personal value, "
                    "the third a surprising thing to have for a princess which makes the story fun.")
                print(f"Stuff: {stuff}")
                # FIXME: Replace with List? Dataframe? Any tabular data UI
                inventory = gr.Dropdown(label="Inventory",
                                        choices=stuff,
                                        value=stuff[0],
                                        scale=1)

        with gr.Row() as row2:
            print("Loading initial choice... ", end="")
            options = make_options(PROMPT_INTRO + " The story starts with just three options of rooms in the castle "
                                                  "where the princess could be locked in.")
            print(f"Buttons: {options}")

            action1 = gr.Button(f"Once upon a time, the princess was locked in {options[0]}. ")
            action2 = gr.Button(f"Once upon a time, the princess was locked in {options[1]}. ")
            action3 = gr.Button(f"Once upon a time, the princess was locked in {options[2]}. ")

        action1.click(respond, [action1, inventory, chatbot], [action1, action2, action3, chatbot, inventory])
        action2.click(respond, [action2, inventory, chatbot], [action1, action2, action3, chatbot, inventory])
        action3.click(respond, [action3, inventory, chatbot], [action1, action2, action3, chatbot, inventory])

        # chatbot.like(vote, None, None)
    demo.queue()
    demo.launch()
