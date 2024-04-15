import json
from ast import literal_eval
from json import JSONDecodeError

import gradio as gr
import random
import time
import gradio as gr
import ollama

PROMPT_INTRO = ("You are a princess emprisoned in a dragon's dungeon castle! "
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


def oracle(question: str, json: bool = True) -> str:
    response = ollama.chat(model="gemma", format="json" if json else "", messages=[
        {
            "role": "user",
            "content": question,
        },
    ])
    response: str = response["message"]
    # print(f"{question} -> {response}")
    return response['content'] if "content" in response else response


def make_options(input_prompt: str = None) -> list[str]:
    # options = ["ACTION 1", "ACTION 2", "ACTION 3"]
    prompt = (f"{SYSTEM} {input_prompt}. Generate three options and reply in JSON, "
              f"with your three options under the key 'options', as an array of strings.")
    options = oracle(prompt)
    values = json.loads(options)
    assert 'options' in values, "MODEL IS STUPID"
    return values['options']


def game_step(choice: str) -> str:
    # return random.choice(["How are you?", "I love you", "I'm very hungry"])
    prompt = (f"The princess chose {choice}. "
              f"What happens next to her? Don't mention the choice, just the action and consequences. "
              f"Reply in a short, descriptive sentence.")
    next_step = oracle(prompt, json=False)
    print(next_step)
    return next_step


if __name__ == '__main__':
    import gradio as gr
    import random

    print("Running game!")
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(value=[(None, PROMPT_INTRO)])
        with gr.Row() as row:
            options = make_options("The story starts with just three options of rooms in the castle "
                                   "where the princess could be.")
            action1 = gr.Button(f"The story starts in: {options[0]}")
            action2 = gr.Button(f"The story starts in: {options[1]}")
            action3 = gr.Button(f"The story starts in: {options[2]}")


        def respond(button, chat_history):
            bot_message = game_step(button)
            print(f"B:{button}")
            print(f"M:{bot_message}")
            try:
                options = make_options(
                    f"The story so far: {chat_history}. "
                    f"What can I do next, phrased from my perspective?")
                print(f"Buttons: {options}")
                assert len(options) == 3, "Bad options!"
            except [AssertionError, JSONDecodeError] as e:
                print(f"Bad options! {options}")
                raise
            chat_history.append((button, bot_message))
            return options[0], options[1], options[2], chat_history


        action1.click(respond, [action1, chatbot], [action1, action2, action3, chatbot])
        action2.click(respond, [action2, chatbot], [action1, action2, action3, chatbot])
        action3.click(respond, [action3, chatbot], [action1, action2, action3, chatbot])

        chatbot.like(vote, None, None)  # Adding this line causes the like/dislike icons to appear in your chatbot

    demo.queue()
    demo.launch()
