#!/usr/bin/env python3
import argparse
import random

rng = random.SystemRandom()

VISUAL = {
    "method": [
        "woodcut", "linocut", "screen print", "letterpress", "rubber stamp", "spray stencil",
        "cut paper collage", "torn magazine collage", "photocopy zine", "gouache", "watercolor wash",
        "ink brush", "ballpoint sketch", "marker on cardboard", "chalk on a blackboard", "oil pastel",
        "embroidery", "cross stitch", "knitting chart", "mosaic tiles", "stained glass", "neon tubes",
        "hand painted shop sign", "enamel sign", "glazed ceramic", "tape on a wall", "LED dot matrix",
        "old CRT screen", "thermal receipt printer", "airbrush", "clay model photo", "glossy 3D render",
        "chrome and glass render", "holographic foil", "flash film photo", "long exposure photo",
        "infrared photo", "x-ray image", "thermal camera image", "satellite image", "microscope image",
        "blueprint", "technical pen drawing", "map engraving", "banknote engraving", "vinyl sticker",
        "felt shapes", "sticky notes on glass", "strict Swiss grid typography", "brutalist web page",
        "acid rave flyer", "Y2K chrome", "halftone newspaper photo", "children's crayon drawing",
        "pencil on graph paper", "spray paint graffiti", "light painting", "shadow puppets",
        "folded paper", "string and pins", "wet ink on tissue", "carved wood relief", "chalk on pavement",
    ],
    "color": [
        "one ink only", "black and white with one accent", "two colors that clash",
        "colors taken from the subject's material", "full color with one hue in charge",
        "very pale and high key", "very dark and low key", "fluorescent", "only earth colors",
        "metallic", "colors of a place at a set hour", "gray with one warm spot",
        "cold colors only", "warm colors only", "the colors of a machine screen", "colors of food",
    ],
    "layout": [
        "subject huge and cropped by the edges", "subject tiny in a large empty field",
        "seen from straight above", "seen from far below", "one detail very close",
        "one thing repeated many times", "split into two halves", "the text is the image",
        "strong diagonal", "low and off center", "deep layers from front to back",
        "a crowd of small parts", "a single line across the frame", "framed by something in front",
        "upside down or turned", "one big shape and nothing else",
    ],
    "type": [
        "hand lettered", "cut out letters", "stencil letters", "tall condensed", "very wide",
        "old style serif", "typewriter", "flowing script", "stacked words", "type on a curve",
        "only small type", "one giant word", "letters built from the subject", "mixed found letters",
        "no type at all if allowed", "type set vertically",
    ],
}

TEXT = {
    "voice": [
        "a witness in first person", "instructions in second person", "a plain list",
        "a short letter", "overheard dialogue", "a public notice", "numbered steps",
        "one long sentence", "short fragments", "question and answer", "a log with entries",
        "a note left for someone", "a review by someone tired", "a label on a box",
    ],
    "entry": [
        "a sound", "a smell", "a single object", "a number that matters", "a mistake",
        "a rule", "a place", "an hour of the day", "the ending", "a body feeling",
        "a thing that is missing", "a price", "a complaint", "a habit",
    ],
    "register": [
        "plain", "formal", "dry", "warm", "blunt", "playful", "terse", "careful", "nervous", "proud",
    ],
}

ANCHOR = [
    "ladder", "bicycle", "glove", "mirror", "bread", "magnet", "compass", "hinge", "fog", "bee",
    "copper", "thread", "lamp", "drum", "sponge", "scissors", "ice", "cactus", "radio", "bridge",
    "key", "feather", "brick", "orange", "train", "coin", "bone", "cloud", "button", "mushroom",
    "wire", "fan", "tooth", "bell", "window", "kite", "ash", "honey", "nail", "moth", "paint",
    "tent", "elevator", "umbrella", "cassette", "dice", "spoon", "candle", "lock", "stairs",
    "battery", "garden hose", "skateboard", "laundry", "traffic cone", "ticket", "alarm clock",
    "snail", "cable", "balloon", "ring", "knot", "crane", "pump", "mask", "barcode", "tire",
    "zip", "comb", "fork", "parachute", "chair", "puddle", "smoke", "chili", "rice", "sand",
    "escalator", "satellite dish", "lemon", "goat", "camel", "bamboo", "lantern", "scooter",
    "vending machine", "pigeon", "ceiling fan", "water tank", "mango", "plastic chair", "antenna",
    "glass bottle", "sunflower", "cardboard box", "headphones", "rug", "tea glass", "bus",
]

SETTING = [
    "a desert town at noon", "a mountain village above the clouds", "a rooftop in a huge city",
    "a parking lot after closing", "a tropical market in the rain", "a frozen lake", "a rice terrace",
    "a highway service station", "a night bus", "a dense housing block courtyard", "a jungle river",
    "a shopping mall basement", "a steppe under a big sky", "a ferry crossing a wide river",
    "an industrial suburb", "a cable car station", "a salt flat", "a volcanic island",
    "a pine forest in snow", "a stadium after the match", "a subway platform", "a hot spring town",
    "an orchard in bloom", "a border crossing", "a fishing harbor in the tropics", "a canyon",
    "a university dorm", "a wind farm", "a crowded old bazaar", "a new town still being built",
    "a riverside at dusk in a hot country", "a ski lift", "a tea plantation", "an airport at 3am",
    "a car wash", "a hilltop monastery", "a laundromat", "a container port", "a savanna road",
    "a glass office tower", "a village wedding tent", "a lighthouse on a cold coast",
]

KINDS = {"visual": VISUAL, "text": TEXT}


def roll(kind):
    pools = dict(KINDS[kind]) if kind in KINDS else {**VISUAL, **TEXT}
    out = {name: rng.choice(items) for name, items in pools.items()}
    out["setting"] = rng.choice(SETTING)
    out["anchor"] = rng.choice(ANCHOR)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", nargs="?", default="visual", choices=["visual", "text", "idea"])
    ap.add_argument("--only", help="roll one axis again, for example --only method")
    args = ap.parse_args()
    seed = roll(args.kind)
    if args.only:
        seed = {args.only: seed.get(args.only, rng.choice(ANCHOR))}
    for k, v in seed.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
