import argparse
import logging
import re


class Port:
    def __init__(self, name, dir, type, size):
        self.name = name
        if dir != "input" and dir != "output" and dir != "inout":
            raise ValueError("Port type should be: `input`, `output` or `inout`")
        self.dir = dir
        self.type = type
        self.size = size

class Module:
    def __init__(self, file, name, clk_name, clk_period, sim_time, timescale="1ns"):
        try:
            with open(file, "r") as f:
                self._text = f.read()
                self._name = ""
                self._ports = []
                self.clk = clk_name
                self.period = clk_period
                self.sim_time = sim_time
                self.timescale = timescale
                if self.name() != name:
                    raise ValueError(f"Module {name} has not been found")
        except:
            raise

    def name(self):
        if len(self._name) == 0:
            match = re.search(r"module\s+(\w+)", self._text)
            if match:
                self._name = match.group(1)
                logging.debug(f"{self._name} ")
            else:
                raise ValueError("Module name has not been found")
        return self._name

    def ports(self) -> list[Port]:
        if len(self._ports) == 0:
            match = re.search(
                r"\s*module.*\(([a-zA-Z0-9 \[\]:\n\r_, \/]*)\);", self._text
            )
            if match:
                text = match.group(1)
            else:
                raise ValueError("Ports have not been found")

            io_matches = re.findall(
                r"(input|inout|output)\s+(wire|reg)?\s*(\[\s*\d*\s*:\s*\d*\s*\])?\s*(\w+)?",
                text,
            )
            if io_matches:
                for match in io_matches:
                    if match[0]:
                        dir = match[0]
                    else:
                        raise ValueError(
                            "Port direction (input/output/inout) has not been found"
                        )
                    type = match[1] if match[1] else "wire"
                    size = str(match[2]).replace(" ", "") if match[2] else ""
                    if match[3]:
                        name = match[3]
                    else:
                        raise ValueError("Port name has not been found")

                    logging.debug(f"{dir} {type} {size} {name}")

                    try:
                        self._ports.append(
                            Port(name=name, dir=dir, type=type, size=size)
                        )
                    except:
                        raise
            else:
                raise ValueError("Ports have not been found")
        return self._ports

    def generate_tb(self):
        name = self.name()
        ports = self.ports()
        text = ""
        text += f"`timescale {self.timescale} / {self.timescale}\n\n"
        text += f"module {name}_tb;\n"
        for port in ports:
            text += "  "
            text += port.type + " "
            text += "" if len(port.size) == 0 else port.size + " "
            text += port.name
            text += ";\n"
        text += "\n"
        text += f"  {name} DUT (\n"
        port_num = 1
        for port in ports:
            text += "    "
            text += "." + port.name + f"({port.name})"
            if port_num != len(ports):
                text += ","
            text += "\n"
            port_num += 1
        text += f"  );\n\n"

        text += "  initial begin\n"
        text += f"    {self.clk} = 0;\n"
        text += "    forever begin\n"
        text += f"      #{self.period} {self.clk} = ~{self.clk};\n"
        text += "    end\n"
        text += "  end\n\n"

        text += "  initial begin\n"
        text += f"    #{self.sim_time}\n"
        text += "    $stop\n"
        text += "  end\n"

        text += "\nendmodule\n"
        return text


def main():
    parser = argparse.ArgumentParser(description="Verilog testbench template generator")
    parser.add_argument("input", nargs="+", help="Input verilog sources")
    parser.add_argument("name", help="Name of the module under testing")
    parser.add_argument("-v", action="store_true", help="Verbosity")
    args = parser.parse_args()

    if args.v:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    inputs = args.input
    name = args.name

    try:
        module = Module(inputs[0], "register_map", "clk", "10", "1000")
        module.name()
        module.ports()
        tb_text = module.generate_tb()
        with open(name + "_tb.sv", "w") as file:
            file.write(tb_text)
    except:
        raise


if __name__ == "__main__":
    main()
