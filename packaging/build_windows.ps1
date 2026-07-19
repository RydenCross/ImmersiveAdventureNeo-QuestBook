$ErrorActionPreference = "Stop"
python -m pip install ".[desktop]"
python -m generator quest-maker-native-build --platform windows
