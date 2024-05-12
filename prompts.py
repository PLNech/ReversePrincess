IMAGE_STYLES = {
    "TIMELESS": "timeless child book illustration, bright watercolor, aged book, cute illustration",
    "PIXELS": "low-resolution pixel art, dark background lofi rendering",
    "ENKI": "in the style of enki bilal, futuristic watercolor pencils",
    "MOEBIUS": "in the style of moebius comic book futuristic pencil drawing, bold coloring, realistic drawing"
}
IMAGE_STYLE_NAMES: list[str] = [s for s in sorted(IMAGE_STYLES.keys())]
IMAGE_STYLE_DEFAULT: str = "MOEBIUS"
