param(
    [string]$Version = "0.1.0"
)
$ErrorActionPreference = "Stop"
python -m generator quest-maker-native-build --platform windows
python -m generator quest-maker-package-build --platform windows --version $Version
