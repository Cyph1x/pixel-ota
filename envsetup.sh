#!/bin/bash
set -e

# uv makes things easier
pip3 install uv --break-system-packages

# make the virtual environment
if [ -d ".venv" ]; then
    rm -rf ".venv"
fi
python3 -m uv venv --seed --python 3.13

# Activate the virtual environment
source .venv/bin/activate
python3 --version

# install uv
pip install --upgrade uv
python3 -m uv pip install --compile-bytecode -r requirements.txt