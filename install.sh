#!/bin/sh

pyinstaller --onefile vtestgen.py && sudo cp dist/vtestgen /usr/bin/vtestgen
