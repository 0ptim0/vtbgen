import argparse
import logging


class Port:
    def __init__(self, name, type, size):
        self._name = name
        if type != "input" and type != "output" and type != "inout":
            raise ValueError("Port type should be: `input`, `output` or `inout`")
        self._type = type
        self._size = size

    def type(self, type):
        self._type = type

    def type(self):
        return self._type

    def size(self, size):
        self._size = size

    def size(self):
        return self._size

    def name(self, name):
        self._name = name

    def name(self):
        return self._name


def main():
    parser = argparse.ArgumentParser(description="Verilog testbench template generator")
    parser.add_argument("input", nargs="+", help="Input verilog sources")
    parser.add_argument("name", help="Name of the tested core")
    parser.add_argument("-v", action="store_true", help="Verbosity")
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    inputs = args.input
    name = args.name


if __name__ == "__main__":
    main()
