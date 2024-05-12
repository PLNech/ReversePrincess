from collections import defaultdict
from typing import Optional

import gradio as gr

from achievements.definitions import achievements_map, achievements_rolls, achievements_sequence


def display_raw(title: str, text: str):
    # FIXME: Warnings are bad they have a big "WARNING" non-parameterized title
    #  There must be a better way
    gr.Warning(f"🏆 Achievement: {title}\t\t\t\n🔸{text}🔸")


def display(key: str):
    if key in achievements_map:
        achievement = achievements_map[key]
        display_raw(achievement.title, achievement.text)
        achievement.unlocked = True
    else:
        gr.Error(f"Failed to find data for achievement \"{key}\"...")


def update_achievements(chat_history: list[list[Optional[str]]], state: dict) -> str:
    """Computes the state of achievements given a game state."""
    if "hello" not in state["achievements"]:
        display("hello")
        state["achievements"]["hello"] = True
    if "rolls" in state:
        check_rolls(state)
        check_sequence_achievements(state)
    if chat_history is not None and len(chat_history) > 0:
        check_history(chat_history, state)

    achievement_text = "# Achievements  \n"
    current_achievements = state.get("achievements", None)

    # VISIBLE ACHIEVEMENTS
    # Rolls
    achievement_text += "## Rolls  \n"
    for roll in achievements_rolls:
        if roll.key in current_achievements:
            achievement_text += f"### 🔓 {roll.title}  \n{roll.text}  \n"
    # Sequences
    achievement_text += "## Sequences  \n"
    for sequence in achievements_sequence:
        if sequence.key in current_achievements:
            achievement_text += f"### 🔓 {sequence.title}  \n{sequence.text}  \n"

    # TODO SECRET ACHIEVEMENTS
    return achievement_text


def check_rolls(state: dict) -> None:
    rolls = state["rolls"]
    for achievement in achievements_rolls:
        if achievement.key not in state["achievements"]:
            if achievement.trigger in rolls:
                display(achievement.key)
                state["achievements"][achievement.key] = True


def check_sequence_achievements(state: dict) -> None:
    sequence = "".join(str(i) for i in state["rolls"])

    for achievement in achievements_sequence:
        if achievement.key not in state["achievements"]:
            if achievement.sequence in sequence:
                display(achievement.key)
                state["achievements"][achievement.key] = True


def check_history(chat_history: list[list[Optional[str]]], state: dict) -> None:
    score_ai_words, score_ai_avoid = 0, 0
    fulltext = ",".join([t for h in chat_history for t in h if t is not None])

    if "delve" in fulltext:
        count_delve = fulltext.count("delve")
        if count_delve > 1 and "delve_1" not in state["achievements"]:
            display_raw("Delve First 💡", "Delving like the pros my dude!")
            state["achievements"]["delve_1"] = True
        if count_delve > 2 and "delve_2" not in state["achievements"]:
            display_raw("Delve the Second 👑", "Let's delve into bad language habits.")
            state["achievements"]["delve_2"] = True
        if count_delve > 3 and "delve_3" not in state["achievements"]:
            display_raw("Delve the Third 🥉", "Delve, delve and delve again!")
            state["achievements"]["delve_3"] = True
        if count_delve > 5 and "delve_5" not in state["achievements"]:
            display_raw("D-D-D-D-DELVE", "Let's delve into the intricate world of delving.")
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
                score_ai_avoid += 1
    if score_ai_words > 0 or score_ai_avoid > 0:
        print(f"Found AI words! Total AI word scores: {score_ai_words}, {score_ai_avoid}")


def init_achievements() -> gr.State:
    store = gr.State(value=defaultdict(lambda: dict))
    store.value["rolls"] = []
    store.value["achievements"] = {}
    return store
