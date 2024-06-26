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


class Parameter:
    def __init__(self, name, size, default_value):
        self.name = name
        self.size = size
        self.default_value = default_value


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
            self.period = str(int(int(clk_period) / 2))
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
                        self.params = self.parse_params()
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

    def parse_params(self) -> list[Parameter]:
        params = []
        match = re.search(r"\s*module.*(\([\S\s]*\))*\s+\(([\S\s]*)\);", self._text)
        text = []
        if match:
            text = match.group(1)

        if not text:
            logging.debug(f"Parameters have not been found")
            return []

        param_matches = re.findall(
            r"\s*parameter\s+(\[.*\])?\s*(\w+)\s*=\s*([\S]+)",
            text,
        )
        if param_matches:
            for match in param_matches:
                size = match[0] if match[0] else ""
                if match[1]:
                    name = match[1]
                else:
                    raise ValueError("Parameter name has not been found")
                if match[2]:
                    default_value = match[2]
                else:
                    raise ValueError("Parameter default value has not been found")

                logging.debug(f"parameter {size} {name} = {default_value}")
                params.append(
                    Parameter(name=name, size=size, default_value=default_value)
                )
        return params

    def parse_ports(self) -> list[Port]:
        ports = []
        match = re.search(
            r"\s*module\s+\w*\s*#?\s*(\([\S\s]*\))?\s*\(([\S\s]*?)\);", self._text
        )
        if match:
            text = match.group(2)
            logging.debug(text)
        else:
            raise ValueError("Ports have not been found")

        io_matches = re.findall(
            r"(input|inout|output)?\s+(wire|reg)?\s*(\[.*\])?\s*(\w+)\s*[,;\n\r)]",
            text,
        )
        logging.debug(io_matches)

        if io_matches:
            for match in io_matches:
                logging.debug(match)
                dir = match[0]
                name = match[3]
                if not name:
                    raise ValueError("Port name has not been found")
                logging.debug(f"Port name: {name}")
                if not dir:
                    logging.debug("Direction not found, parse the entire file")
                    pattern = (
                        r"(input|inout|output)\s+(wire|reg)?\s*(\[.*\])?\s*"
                        + match[3]
                        + "\s*;"
                    )
                    match = re.findall(
                        pattern,
                        self._text,
                    )
                    match = match[0]
                    logging.debug(match)
                    dir = match[0]
                    if not dir:
                        raise ValueError(
                            "Port direction (input/output/inout) has not been found"
                        )

                type = match[1] if match[1] else "wire"
                size = str(match[2]).replace(" ", "") if match[2] else ""
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
        if not self.params:
            self.params = self.parse_params()

        name = self.name
        ports = self.ports
        params = self.params
        clk_found = False

        text = ""
        text += f"`timescale {self.timescale} / {self.timescale}\n\n"
        text += f"module {name}_tb;\n"
        for param in params:
            text += "  parameter "
            text += "" if len(param.size) == 0 else param.size + " "
            text += f"{param.name} = {param.default_value};\n"
        text += "\n"
        for port in ports:
            if port.name == self.clk:
                clk_found = True
                port.type = "reg"
            elif port.dir == "input":
                port.type = "reg"
            elif port.dir == "output":
                port.type = "wire"
            text += "  "
            text += port.type + " "
            text += "" if len(port.size) == 0 else port.size + " "
            text += port.name
            text += ";\n"
        text += "\n"

        param_num = 1
        if params:
            text += f"  {name} #(\n"
            for param in params:
                text += f"    .{param.name}({param.name})"
                if param_num != len(params):
                    text += ","
                text += "\n"

            text += f"  ) DUT (\n"
        else:
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

        if clk_found:
            text += "  initial begin\n"
            text += f"    {self.clk} = 0;\n"
            text += "    forever begin\n"
            text += f"      #{self.period};\n"
            text += f"      {self.clk} = ~{self.clk};\n"
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

        text = ""
        text += "onerror {resume}\n"
        text += "quietly WaveActivateNextPane {} 0\n\n"
        text += "radix -hexadecimal\n\n"
        text += f"add wave /{self.name + '_tb'}/*\n"
        text += f"add wave /{self.name + '_tb'}/DUT/*\n\n"
        text += f"update\n"
        return text

    def generate_make(self):
        if not self.name:
            self.name = self.parse_name()

        text = ""
        text += f".PHONY: all clean compile run\n\n"
        for src in self.inputs:
            text += f'SRC+="{src}"\n'
        text += f'SRC+="{self.name + "_tb.sv"}"\n'
        text += "\n"
        text += "all: compile run\n\n"
        text += "clean:\n\tvdel -all\n\n"
        text += "compile:\n\tvlib work\n\tvlog -sv $(SRC)\n\n"
        text += f"run:\n\tvsim -gui -suppress 10000 -quiet work.{self.name + '_tb'} -do \"{self.name + '_tb.do'}\" -do \"run -all\"\\\n"
        return text


def main():
    parser = argparse.ArgumentParser(description="Verilog testbench template generator")
    parser.add_argument("input", nargs="+", help="Input verilog sources")
    parser.add_argument("name", help="Name of the module under testing")
    parser.add_argument("-c", help="Clock signal name, default: clk")
    parser.add_argument("-p", help="Clock period, default: 10")
    parser.add_argument("-t", help="Timescale, default: 1ns")
    parser.add_argument("-s", help="Simulation time, default: 1000")
    parser.add_argument("-v", action="store_true", help="Verbosity")
    args = parser.parse_args()

    if args.v:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    inputs = args.input
    name = args.name
    clk = args.c if args.c else "clk"
    clk_period = args.p if args.p else "10"
    timescale = args.t if args.t else "1ns"
    sim_time = args.s if args.s else "1000"

    try:
        module = Module(
            files=inputs,
            name=name,
            clk_name=clk,
            clk_period=clk_period,
            sim_time=sim_time,
            timescale=timescale,
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
