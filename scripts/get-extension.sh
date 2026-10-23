#!/usr/bin/env bash
# Downloads the latest Solvecha extension build into ./solvecha-extension
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf solvecha-extension solvecha.zip
curl -fsSL -o solvecha.zip https://github.com/Solvecha/solvecha-extension/releases/latest/download/solvecha-chrome.zip
unzip -q solvecha.zip -d solvecha-extension
rm solvecha.zip
echo "Extension unpacked to $(pwd)/solvecha-extension"
