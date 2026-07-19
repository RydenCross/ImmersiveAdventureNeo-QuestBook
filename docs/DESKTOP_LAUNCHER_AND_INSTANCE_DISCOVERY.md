# Desktop launcher and automatic instance discovery

FTB Quest Maker can discover supported Minecraft instances and open the visual editor without requiring a terminal command or a manually typed installation path.

Start the desktop launcher:

```bash
python -m generator quest-maker-launch
```

The launcher searches the normal operating-system locations used by:

- Minecraft Launcher
- CurseForge
- Prism Launcher
- MultiMC
- Modrinth App
- ATLauncher
- GDLauncher

It reads only small launcher metadata files and directory names. It does not start Minecraft or execute mod code.

The launcher lists the detected pack name, launcher, Minecraft version, loader, mod count, FTB Quests installation state, and resolved game directory. Double-click an instance or choose **Open selected instance** to start the existing localhost editor on an automatically assigned port. **Install project** verifies and installs a selected `.ftbqproj` bundle with the existing atomic backup workflow.

List discovered instances without opening the desktop window:

```bash
python -m generator quest-instance-discover
python -m generator quest-instance-discover --format json --output instances.json
```

Search a custom launcher directory:

```bash
python -m generator quest-instance-discover --root /path/to/launcher/instances
python -m generator quest-maker-launch --root /path/to/launcher/instances
```

The browser editor also exposes `GET /api/v1/instances`. Its **Install to instance** action presents discovered instances instead of asking for a manually typed filesystem path.

The desktop launcher uses Python's standard `tkinter` module and the existing dependency-free localhost editor service. Per-instance editor data is stored under `~/.ftb-quest-maker/workspaces/` by default and is excluded from repository releases.

Validate the feature with:

```bash
python -m generator desktop-launcher-audit
python -m generator desktop-launcher-audit \
  --format json \
  --output reports/desktop-launcher-audit.json
```
