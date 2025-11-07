#!/bin/bash
set -e

echo "setting up phytjon build"
python3 -m venv .venv

souce .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "Dependencies installed successfully"
