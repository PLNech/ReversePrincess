PRE_PROMPT = (
    f"You generate short story bits in simple english and write compelling adventure games "
    f"made of few-sentence descriptions and actions. "
    # f"you must write in the style of Brandon Sanderson. "
    f"You must always refer to the main character as the princess or she, "
    f"and always describe the scene in her third person subjective voice.\n"
    "When possible you use simple words from the basic english vocabulary to keep the story readable for kids.\n"
    "You will generate a small part of the story, answering directly this request:\n"
)

INTRO = (
    f"This is the story of a lonely princess, locked away in the highest room of a tall castle.\n"
    f"In the tower lives a dragon that guard the castle. "
    f"She was expecting her prince to save her, passing time by reading her various books.\n"
    # TODO: We'll bring back the fun parts of her history...
    f"But the poor lad is not a hero and is himself in need of help! She clearly is the stronger one. "
    f"This is it, she must escape the dungeon and rescue him!\n"
    # TODO: ...once we control enough generation ;)
    # f"She was expecting her prince to save her, passing time by reading Simone De Beauvoir.\n"
    # f"Yet, when she learned the poor lad spent too much time on 4chan "
    # f"and might become a dumb masculinist if nothing is done, she took things in her hands.\n"
    # f"This is it, she must rescue him from the patriarchy !\n"
    f"Locked in her room, she packed her belongings in a backpack and starts looking for a way out."
)

IMAGE_STYLES = {
    "TIMELESS": "timeless child book illustration, bright watercolor, aged book, cute illustration",
    "PIXELS": "low-resolution pixel art, dark background lofi rendering",
    "ENKI": "in the style of enki bilal, futuristic watercolor pencils",
    "MOEBIUS": "in the style of moebius comic book futuristic pencil drawing, bold coloring, realistic drawing"
}
IMAGE_STYLE_NAMES: list[str] = [s for s in sorted(IMAGE_STYLES.keys())]
IMAGE_STYLE_DEFAULT: str = "MOEBIUS"
