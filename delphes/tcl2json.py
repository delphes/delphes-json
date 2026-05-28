import json

from argparse import ArgumentParser
from pathlib import Path

from .tcl2py import tcl2py


def main():
    parser = ArgumentParser()
    parser.add_argument("card", help="detector card file name")

    args = parser.parse_args()

    card_file = Path(args.card)
    content = tcl2py(card_file)

    namespace = {}
    exec(content, namespace)
    card = namespace["card"]

    print(json.dumps(card, indent=4))


if __name__ == "__main__":
    main()
