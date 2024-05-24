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
    def __init__(
        self,
        files,
        name,
        clk_name="clk",
        clk_period="10",
        sim_time="1000",
        timescale="1ns",
    ):
        try:
            self.ports = []
            self.name = ""
            self.clk = clk_name
            self.period = clk_period
            self.sim_time = sim_time
            self.timescale = timescale
            self.inputs = files
            for file in files:
                with open(file, "r") as f:
                    self._text = f.read()
                    _name = self.parse_name()
                    if _name == name:
                        logging.debug(f"Module {name} has been found in {file}")
                        self.name = _name
                        self.ports = self.parse_ports()
                        break
            if not self.name:
                raise ValueError(f"Module {name} has not been found")
        except:
            raise

    def parse_name(self):
        match = re.search(r"module\s+(\w+)", self._text)
        if match:
            logging.debug(f"{self.name} ")
            return match.group(1)
        else:
            raise ValueError("Module name has not been found")

    def parse_ports(self) -> list[Port]:
        ports = []
        match = re.search(r"\s*module.*\(([a-zA-Z0-9 \[\]:\n\r_, \/]*)\);", self._text)
        if match:
            self._text = match.group(1)
        else:
            raise ValueError("Ports have not been found")

        io_matches = re.findall(
            r"(input|inout|output)\s+(wire|reg)?\s*(\[\s*\d*\s*:\s*\d*\s*\])?\s*(\w+)?",
            self._text,
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
                    ports.append(Port(name=name, dir=dir, type=type, size=size))
                except:
                    raise
            return ports
        else:
            raise ValueError("Ports have not been found")

    def generate_tb(self):
        if not self.name:
            self.name = self.parse_name()
        if not self.ports:
            self.ports = self.parse_ports()

        name = self.name
        ports = self.ports

        text = ""
        text += f"`timescale {self.timescale} / {self.timescale}\n\n"
        text += f"module {name}_tb;\n"
        for port in ports:
            if port.name == self.clk:
                port.type = "reg"
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
        text += f"    #{self.sim_time};\n"
        text += "    $stop;\n"
        text += "  end\n"

        text += "\nendmodule\n"
        return text

    def generate_do(self):
        if not self.name:
            self.name = self.parse_name()
        if not self.ports:
            self.ports = self.parse_ports()

        text = ""
        text += "onerror {resume}\n"
        text += "quietly WaveActivateNextPane {} 0\n\n"
        text += f"add wave /{self.name + '_tb'}/*\n"
        text += f"add wave /{self.name + '_tb'}/DUT/*\n\n"
        text += f"update\n"
        return text

    def generate_make(self):
        if not self.name:
            self.name = self.parse_name()
        if not self.ports:
            self.ports = self.parse_ports()

        text = ""
        text += f".PHONY: all clean compile run\n\n"
        for src in self.inputs:
            text += f'SRC+="{src}"\n'
        text += f'SRC+="{self.name + "_tb.sv"}"\n'
        text += "\n"
        text += "all: clean compile run\n\n"
        text += "clean:\n\tvdel -all\n\n"
        text += "compile:\n\tvlib work\n\tvlog -sv $(SRC)\n\n"
        text += f"run:\n\tvsim -gui -suppress 10000 -quiet work.{self.name + '_tb'} -do \"{self.name + '_tb.do'}\" -do \"run -all\"\\\n"
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
        module = Module(
            files=inputs,
            name="register_map",
            clk_name="clk",
            clk_period="25",
            sim_time="100",
            timescale="1ns",
        )
        tb_text = module.generate_tb()
        tb_do = module.generate_do()
        tb_make = module.generate_make()
        with open(name + "_tb.sv", "w") as file:
            file.write(tb_text)
        with open(name + "_tb.do", "w") as file:
            file.write(tb_do)
        with open(name + "_tb.mk", "w") as file:
            file.write(tb_make)
    except:
        raise


if __name__ == "__main__":
    main()
