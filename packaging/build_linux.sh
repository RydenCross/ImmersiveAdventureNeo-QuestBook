#!/usr/bin/env sh
set -eu
python -m pip install '.[desktop]'
python -m generator quest-maker-native-build --platform linux
