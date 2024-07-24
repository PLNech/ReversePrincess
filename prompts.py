"""Example:
Stuck in AI box chat with guardian, comicbook, technological comic, art by Picasso,
in the style of , Marvel DC comics, accent lighting,
"""

IMAGE_STYLES = {
    "TIMELESS": "timeless child book illustration, bright watercolor, aged book, cute illustration",
    "PIXELS": "pixel art character, in full body view, Modern Line Icon, Vector Line Art, Icon Design, "
              "Bold Outline, Solid Color, Pixel Perfect, Isolate, black background, Minimalistic, Bold Colors",
    "ENKI": "in the style of enki bilal, Enki Bilal's style, futuristic tones, watercolor pencils, best quality",
    "MOEBIUS": "comicbook, art by Moebius, cyberpunk comic, bold coloring, accent lighting, elegant complex picture",
}
IMAGE_STYLE_NAMES: list[str] = [s for s in sorted(IMAGE_STYLES.keys())]
IMAGE_STYLE_DEFAULT: str = "MOEBIUS"
