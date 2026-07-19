#!/usr/bin/env sh
set -eu
VERSION="${1:-0.1.0}"
python -m generator quest-maker-native-build --platform linux
python -m generator quest-maker-package-build --platform linux --version "$VERSION"
