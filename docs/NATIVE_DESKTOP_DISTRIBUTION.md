# Native Desktop Distribution and First-Run Setup

FTB Quest Maker can be packaged as a standalone Windows or Linux desktop application. The packaged entrypoint opens the instance-discovery launcher directly, so end users do not need to invoke Python or start the localhost editor service manually.

## First-run setup

The desktop application opens a setup dialog the first time it starts. The user chooses:

- the application workspace;
- optional launcher or instance search roots;
- whether editor sessions open a browser automatically; and
- the maximum number of discovered instances.

Preferences are stored atomically at `~/.ftb-quest-maker/preferences.json`. Invalid or unsupported preference files are ignored safely and replaced in memory with defaults; the corrupt file is not overwritten until the user saves new settings.

The same setup can be completed without the graphical dialog:

```bash
python -m generator quest-maker-setup \
  --workspace ~/.ftb-quest-maker \
  --max-instances 500
```

Add custom roots or disable automatic browser opening:

```bash
python -m generator quest-maker-setup \
  --root /path/to/PrismLauncher/instances \
  --root /path/to/CurseForge/Instances \
  --no-browser
```

Reopen the setup dialog from the launcher with **Preferences…**, or force it at startup:

```bash
python -m generator quest-maker-launch --reset-setup
```

## Native build plan

Inspect the deterministic build command without running PyInstaller:

```bash
python -m generator quest-maker-native-build --platform windows --dry-run
python -m generator quest-maker-native-build --platform linux --dry-run
```

Create a native build on the current target operating system:

```bash
python -m generator quest-maker-native-build --platform auto
```

Native builds must be produced on their target operating system. A Windows executable must be built on Windows, and the Linux executable must be built on Linux.

The optional desktop build dependency can be installed with:

```bash
python -m pip install ".[desktop]"
```

Target-specific helper scripts are included:

```text
packaging/build_windows.ps1
packaging/build_linux.sh
packaging/ftb_quest_maker.spec
packaging/ftb-quest-maker.desktop
```

The PyInstaller specification creates a windowed `FTBQuestMaker` executable and includes the `content`, `generator`, and `model` packages used by scanners, planners, validators, and the local editor.

## Persistent launcher behavior

Saved preferences control normal launcher startup. The launcher remembers the last opened instance, selects it after the next discovery pass, and keeps each instance in an isolated workspace. First-run setup creates the workspace, `workspaces`, and `logs` directories before the application begins normal operation.

## Audit

Run the distribution and setup contract:

```bash
python -m generator native-distribution-audit
```

Generate the tracked report:

```bash
python -m generator native-distribution-audit \
  --format json \
  --output reports/native-distribution-audit.json
```

The audit verifies preference persistence, corrupt-file recovery, deterministic Windows/Linux build plans, target-specific executable names, cross-build rejection, standalone entrypoint wiring, helper build recipes, and launcher integration.

## Installer and AppImage packaging

After the native binary is built, continue with `quest-maker-package-build` and the update-feed commands documented in [`DESKTOP_INSTALLERS_AND_UPDATES.md`](DESKTOP_INSTALLERS_AND_UPDATES.md).
