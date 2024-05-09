from collections import defaultdict
from typing import Optional

import gradio as gr


def display(title: str, text: str):
    # FIXME: Warnings are bad they have a big "WARNING" non-parameterized title
    #  There must be a better way
    gr.Warning(f"🏆 Achievement: {title}\t\t\t\n🔸{text}🔸")


def update_achievements(chat_history: list[list[Optional[str]]], state: dict) -> str:
    if "hello" not in state["achievements"]:
        display("First achievement", "Hello you :3")
        state["achievements"]["hello"] = True
    if "rolls" in state:
        check_rolls(state)
        check_sequence_achievements(state)
    if chat_history is not None and len(chat_history) > 0:
        check_history(chat_history, state)

    current_achievements = f"Current achievements: {state.get('achievements', None)}"
    print(current_achievements)
    return current_achievements


def check_rolls(state: dict) -> None:
    rolls = state["rolls"]
    if "roll_1" not in state["achievements"]:
        if 1 in rolls:
            display("Roll fail 🎲", "C'est terrible ce qui t'arrive mec, TERRIBLE !")
            state["achievements"]["roll_1"] = True
    if "roll_8" not in state["achievements"]:
        if 8 in rolls:
            display("Roll 8", "Lucky 8 🍀")
            state["achievements"]["roll_8"] = True
    if "roll_10" not in state["achievements"]:
        if 10 in rolls:
            display("Roll win 🌈", "Living the life 😎")
            state["achievements"]["roll_10"] = True


def check_sequence_achievements(state: dict) -> None:
    sequence = "".join(str(i) for i in state["rolls"])

    if "roll_111" not in state["achievements"]:
        if "111" in sequence:
            display("Epic fail", "Worst. Game. Ever.")
            state["achievements"]["roll_111"] = True

    if "roll_123" not in state["achievements"]:
        if "123" in sequence:
            display("Et 1, et 2, et 3", "One Two Three? 🥙🔥🏟️")
            state["achievements"]["roll_123"] = True

    if "roll_420" not in state["achievements"]:
        if "420" in sequence:
            display("4:20 my dude", "HIGH AS A KITE")
            state["achievements"]["roll_420"] = True

    if "roll_421" not in state["achievements"]:
        if "421" in sequence:
            display("Un p'tit 421 ?", "I'd rather be playing dice lol")
            state["achievements"]["roll_421"] = True

    if "roll_555" not in state["achievements"]:
        if "555" in sequence:
            display("555", "🎸 if you're 5-5-5 I'm 666 🤟")
            state["achievements"]["roll_555"] = True

    if "roll_666" not in state["achievements"]:
        if "666" in sequence:
            display("666 🦹", "Diabolically partial success!")
            state["achievements"]["roll_666"] = True


def check_history(chat_history: list[list[Optional[str]]], state: dict) -> None:
    score_ai_words, score_ai_avoid = 0, 0
    fulltext = ",".join([t for h in chat_history for t in h if t is not None])

    if "delve" in fulltext:
        count_delve = fulltext.count("delve")
        if count_delve > 1 and "delve_1" not in state["achievements"]:
            display("Delve First 💡", "Delving like the pros my dude!")
            state["achievements"]["delve_1"] = True
        if count_delve > 2 and "delve_2" not in state["achievements"]:
            display("Delve the Second 👑", "Let's delve into bad language habits.")
            state["achievements"]["delve_2"] = True
        if count_delve > 3 and "delve_3" not in state["achievements"]:
            display("Delve the Third 🥉", "Delve, delve and delve again!")
            state["achievements"]["delve_3"] = True
        if count_delve > 5 and "delve_5" not in state["achievements"]:
            display("D-D-D-D-DELVE", "Let's delve into the intricate world of delving.")
            state["achievements"]["delve_5"] = True

    with open("./achievements/data/100_ai_words.txt", "r") as f:
        words = [w.strip() for w in f.readlines() if not w.startswith("#")]
        for word in words:
            if word in fulltext:
                print(f"Found {word} in history!")
                score_ai_words += 1

    with open("./achievements/data/100_to_avoid.txt", "r") as f:
        words = [w.strip() for w in f.readlines() if not w.startswith("#")]
        for word in words:
            if word in fulltext:
                print(f"Found {word} in history!")
                score_ai_words += 1
    with open("./achievements/data/100_ai_words.txt", "r") as f:
        words = [w.strip() for w in f.readlines() if not w.startswith("#")]
        for word in words:
            if word in fulltext:
                print(f"Found {word} in history!")
                score_ai_avoid += 1
    if score_ai_words > 0 or score_ai_avoid > 0:
        print(f"Found AI words! Total AI word scores: {score_ai_words}, {score_ai_avoid}")


def init_achievements() -> gr.State:
    store = gr.State(value=defaultdict(lambda: dict))
    store.value["rolls"] = []
    store.value["achievements"] = {}
    return store
