# vtestgen

Verilog Testbench Template Generator

## Description

A utility for generating testing environment based on modelsim and makefile

## Features

- Generates a separate file with a testbench module and a DUT instance
- Generates Makefile and .do script

## Usage

```bash
usage: vtestgen.py [-h] [-c C] [-p P] [-t T] [-s S] [-v] input [input ...] name

Verilog testbench template generator

positional arguments:
  input       Input verilog sources
  name        Name of the module under testing

options:
  -h, --help  show this help message and exit
  -c C        Clock signal name, default: clk
  -p P        Clock period, default: 10
  -t T        Timescale, default: 1ns
  -s S        Simulation time, default: 1000
  -v          Verbosity
```

## Example

### Initial source
#### clock_divider.sv
```verilog
`timescale 1ns / 1ns

module clock_divider #(
    parameter divider = 'd10
) (
    input  in,
    output out,
    input  reset
);

  reg [31:0] cnt = 'd0;
  reg state = 1'b0;

  always @(posedge in, posedge reset) begin
    if (reset) begin
      cnt   <= 'd0;
      state <= 'd0;
    end else if (cnt == divider / 2 - 1) begin
      state <= ~state;
      cnt   <= 0;
    end else begin
      cnt <= cnt + 1;
    end
  end

  assign out = state;

endmodule

```

### Command
```bash
python vtestgen.py test/clock_divider.sv clock_divider -v -c in
```

### Generated files
#### clock_divider_tb.sv
```verilog
`timescale 1ns / 1ns

module clock_divider_tb;
  parameter divider = 'd10;

  reg in;
  wire out;
  wire reset;

  clock_divider #(
    .divider(divider)
  ) DUT (
    .in(in),
    .out(out),
    .reset(reset)
  );

  initial begin
    in = 0;
    forever begin
      #5;
      in = ~in;
    end
  end

  initial begin
    #1000;
    $stop;
  end

endmodule

```

#### clock_divider_tb.mk
```makefile
.PHONY: all clean compile run

SRC+="test/clock_divider.sv"
SRC+="clock_divider_tb.sv"

all: compile run

clean:
	vdel -all

compile:
	vlib work
	vlog -sv $(SRC)

run:
	vsim -gui -suppress 10000 -quiet work.clock_divider_tb -do "clock_divider_tb.do" -do "run -all"\

```

#### clock_divider_tb.do
```
onerror {resume}
quietly WaveActivateNextPane {} 0

add wave /clock_divider_tb/*
add wave /clock_divider_tb/DUT/*

update

```
