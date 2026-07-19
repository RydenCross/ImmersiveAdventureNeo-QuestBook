from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Callable, Iterable

from generator.desktop_setup import (
    DEFAULT_PREFERENCES_PATH,
    DesktopPreferences,
    complete_first_run_setup,
    load_desktop_preferences,
    save_desktop_preferences,
    update_last_instance,
)
from generator.instance_discovery import (
    DiscoveredInstance,
    InstanceDiscoveryResult,
    InstanceSearchRoot,
    discover_modpack_instances,
)
from generator.project_bundle import install_project_bundle

DEFAULT_LAUNCHER_WORKSPACE = Path.home() / ".ftb-quest-maker"


@dataclass(frozen=True, slots=True)
class EditorLaunchPlan:
    command: tuple[str, ...]
    workspace: str
    source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "command": list(self.command),
            "workspace": self.workspace,
            "source": self.source,
        }


def build_editor_launch_plan(
    instance: DiscoveredInstance | None,
    *,
    workspace_root: Path = DEFAULT_LAUNCHER_WORKSPACE,
    open_browser: bool = True,
    python_executable: str | None = None,
) -> EditorLaunchPlan:
    workspace_root = Path(workspace_root).expanduser()
    identity = instance.instance_id if instance else "untitled"
    workspace = workspace_root / "workspaces" / identity
    command = [
        python_executable or sys.executable,
        "-m",
        "generator",
        "quest-editor-serve",
    ]
    source = ""
    if instance is not None:
        source = instance.game_directory
        command.append(source)
    command.extend(("--workspace", workspace.as_posix(), "--port", "0"))
    if not open_browser:
        command.append("--no-browser")
    return EditorLaunchPlan(tuple(command), workspace.as_posix(), source)


def start_editor_process(
    instance: DiscoveredInstance | None,
    *,
    workspace_root: Path = DEFAULT_LAUNCHER_WORKSPACE,
    open_browser: bool = True,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> subprocess.Popen[bytes]:
    plan = build_editor_launch_plan(
        instance,
        workspace_root=workspace_root,
        open_browser=open_browser,
    )
    Path(plan.workspace).mkdir(parents=True, exist_ok=True)
    return popen(plan.command, cwd=Path.cwd())


def _instance_label(instance: DiscoveredInstance) -> str:
    version = instance.minecraft_version or "unknown"
    loader = instance.loader or "unknown loader"
    return f"{instance.name} — {version} / {loader}"


def _saved_search_roots(preferences: DesktopPreferences) -> tuple[InstanceSearchRoot, ...]:
    return tuple(
        InstanceSearchRoot("Saved", Path(path)) for path in preferences.search_roots
    )


def launch_desktop(
    *,
    workspace_root: Path | None = None,
    search_roots: Iterable[InstanceSearchRoot | tuple[str, Path] | Path] | None = None,
    open_browser: bool | None = None,
    discovery: InstanceDiscoveryResult | None = None,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    force_first_run: bool = False,
) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError as exc:  # pragma: no cover - depends on Python distribution
        raise RuntimeError("the desktop launcher requires Python's tkinter module") from exc

    preference_load = load_desktop_preferences(preferences_path)
    preferences = preference_load.preferences

    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on display availability
        raise RuntimeError("the desktop launcher requires a graphical desktop session") from exc

    root.title("FTB Quest Maker")
    root.geometry("980x560")
    root.minsize(760, 420)

    def preferences_dialog(*, first_run: bool) -> DesktopPreferences | None:
        result: DesktopPreferences | None = None
        dialog = tk.Toplevel(root)
        dialog.title("FTB Quest Maker — First-run setup" if first_run else "Preferences")
        dialog.transient(root)
        dialog.grab_set()
        dialog.resizable(True, False)

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text=(
                "Choose where projects are stored and which extra launcher folders are scanned."
            ),
            wraplength=620,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        workspace_var = tk.StringVar(value=preferences.workspace_root)
        browser_var = tk.BooleanVar(value=preferences.open_browser)
        max_var = tk.StringVar(value=str(preferences.max_instances))
        roots = list(preferences.search_roots)

        ttk.Label(frame, text="Workspace").grid(row=1, column=0, sticky="w")
        workspace_entry = ttk.Entry(frame, textvariable=workspace_var, width=64)
        workspace_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 8))

        def choose_workspace() -> None:
            selected = filedialog.askdirectory(
                title="Choose the FTB Quest Maker workspace",
                parent=dialog,
            )
            if selected:
                workspace_var.set(selected)

        ttk.Button(frame, text="Browse…", command=choose_workspace).grid(
            row=2, column=2, padx=(8, 0), pady=(2, 8)
        )

        ttk.Label(frame, text="Additional launcher or instance roots").grid(
            row=3, column=0, columnspan=3, sticky="w"
        )
        roots_box = tk.Listbox(frame, height=5, width=72)
        roots_box.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        for item in roots:
            roots_box.insert("end", item)

        def add_root() -> None:
            selected = filedialog.askdirectory(
                title="Choose a launcher or instance directory",
                parent=dialog,
            )
            if selected and selected not in roots:
                roots.append(selected)
                roots_box.insert("end", selected)

        def remove_root() -> None:
            indices = tuple(int(item) for item in roots_box.curselection())
            for index in reversed(indices):
                roots.pop(index)
                roots_box.delete(index)

        root_buttons = ttk.Frame(frame)
        root_buttons.grid(row=4, column=2, sticky="n", padx=(8, 0), pady=(2, 8))
        ttk.Button(root_buttons, text="Add…", command=add_root).pack(fill="x")
        ttk.Button(root_buttons, text="Remove", command=remove_root).pack(
            fill="x", pady=(6, 0)
        )

        ttk.Checkbutton(
            frame,
            text="Open the browser automatically when an editor starts",
            variable=browser_var,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 8))
        ttk.Label(frame, text="Maximum discovered instances").grid(
            row=6, column=0, sticky="w"
        )
        ttk.Entry(frame, textvariable=max_var, width=10).grid(
            row=6, column=1, sticky="w", pady=(2, 8)
        )

        actions = ttk.Frame(frame)
        actions.grid(row=7, column=0, columnspan=3, sticky="e", pady=(12, 0))

        def save() -> None:
            nonlocal result
            try:
                setup = complete_first_run_setup(
                    preferences_path=preferences_path,
                    workspace_root=Path(workspace_var.get()),
                    search_roots=(Path(item) for item in roots),
                    open_browser=browser_var.get(),
                    max_instances=int(max_var.get()),
                )
            except (OSError, TypeError, ValueError) as exc:
                messagebox.showerror("Invalid preferences", str(exc), parent=dialog)
                return
            result = setup.preferences
            dialog.destroy()

        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="Save", command=save).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()
        return result

    if force_first_run or not preferences.first_run_complete:
        updated = preferences_dialog(first_run=True)
        if updated is None:
            root.destroy()
            return 0
        preferences = updated

    configured_workspace = (
        Path(workspace_root).expanduser()
        if workspace_root is not None
        else Path(preferences.workspace_root)
    )
    configured_roots = (
        search_roots if search_roots is not None else _saved_search_roots(preferences)
    )
    configured_browser = preferences.open_browser if open_browser is None else open_browser
    current_result = discovery or discover_modpack_instances(
        configured_roots,
        max_instances=preferences.max_instances,
    )
    instance_by_id: dict[str, DiscoveredInstance] = {}

    header = ttk.Frame(root, padding=12)
    header.pack(fill="x")
    ttk.Label(header, text="FTB Quest Maker", font=("TkDefaultFont", 16, "bold")).pack(
        side="left"
    )
    status_var = tk.StringVar(value="Discovering Minecraft instances…")
    ttk.Label(header, textvariable=status_var).pack(side="right")

    columns = ("name", "launcher", "minecraft", "loader", "mods", "questbook", "path")
    tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
    headings = {
        "name": "Instance",
        "launcher": "Launcher",
        "minecraft": "Minecraft",
        "loader": "Loader",
        "mods": "Mods",
        "questbook": "FTB Quests",
        "path": "Game directory",
    }
    widths = {
        "name": 170,
        "launcher": 120,
        "minecraft": 85,
        "loader": 100,
        "mods": 55,
        "questbook": 80,
        "path": 330,
    }
    for column in columns:
        tree.heading(column, text=headings[column])
        tree.column(column, width=widths[column], minwidth=50, stretch=column == "path")
    tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    footer = ttk.Frame(root, padding=(12, 4, 12, 12))
    footer.pack(fill="x")

    def selected_instance() -> DiscoveredInstance | None:
        selected = tree.selection()
        return instance_by_id.get(selected[0]) if selected else None

    def render(result: InstanceDiscoveryResult) -> None:
        nonlocal current_result
        current_result = result
        tree.delete(*tree.get_children())
        instance_by_id.clear()
        for instance in result.instances:
            instance_by_id[instance.instance_id] = instance
            tree.insert(
                "",
                "end",
                iid=instance.instance_id,
                values=(
                    instance.name,
                    instance.launcher,
                    instance.minecraft_version or "—",
                    (
                        f"{instance.loader} {instance.loader_version}".strip()
                        if instance.loader
                        else "—"
                    ),
                    instance.mod_count,
                    "yes" if instance.has_ftb_quests else "no",
                    instance.game_directory,
                ),
            )
        status_var.set(
            f"{len(result.instances)} instance{'s' if len(result.instances) != 1 else ''} found"
        )
        preferred = preferences.last_instance_id
        if preferred and preferred in instance_by_id:
            tree.selection_set(preferred)
        elif result.instances:
            tree.selection_set(result.instances[0].instance_id)

    def refresh() -> None:
        try:
            render(
                discover_modpack_instances(
                    configured_roots,
                    max_instances=preferences.max_instances,
                )
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Discovery failed", str(exc), parent=root)

    def launch(instance: DiscoveredInstance | None) -> None:
        nonlocal preferences
        try:
            process = start_editor_process(
                instance,
                workspace_root=configured_workspace,
                open_browser=configured_browser,
            )
            if instance is not None:
                preferences = update_last_instance(
                    preferences,
                    instance.instance_id,
                    path=preferences_path,
                )
        except OSError as exc:
            messagebox.showerror("Editor launch failed", str(exc), parent=root)
            return
        label = _instance_label(instance) if instance else "an empty project"
        status_var.set(f"Started editor for {label} (PID {process.pid})")

    def edit_preferences() -> None:
        nonlocal preferences, configured_workspace, configured_roots, configured_browser
        updated = preferences_dialog(first_run=False)
        if updated is None:
            return
        preferences = updated
        configured_workspace = Path(preferences.workspace_root)
        configured_roots = _saved_search_roots(preferences)
        configured_browser = preferences.open_browser
        refresh()

    def add_folder() -> None:
        selected = filedialog.askdirectory(title="Choose a Minecraft instance folder", parent=root)
        if not selected:
            return
        result = discover_modpack_instances((InstanceSearchRoot("Custom", Path(selected)),))
        if not result.instances:
            messagebox.showwarning(
                "No instance detected",
                "The selected directory does not contain a recognizable Minecraft instance.",
                parent=root,
            )
            return
        merged = tuple(
            {
                item.game_directory: item
                for item in (*current_result.instances, *result.instances)
            }.values()
        )
        render(
            InstanceDiscoveryResult(
                schema_version=current_result.schema_version,
                searched_roots=current_result.searched_roots + result.searched_roots,
                instances=tuple(
                    sorted(merged, key=lambda item: (item.name.casefold(), item.game_directory))
                ),
                inaccessible_roots=(
                    current_result.inaccessible_roots + result.inaccessible_roots
                ),
            )
        )

    def install_bundle() -> None:
        instance = selected_instance()
        if instance is None:
            messagebox.showwarning("Select an instance", "Choose an instance first.", parent=root)
            return
        bundle = filedialog.askopenfilename(
            title="Choose a portable Quest Maker project",
            filetypes=(("FTB Quest Maker project", "*.ftbqproj"), ("All files", "*")),
            parent=root,
        )
        if not bundle:
            return
        result = install_project_bundle(Path(bundle), Path(instance.game_directory), force=False)
        if result.is_clean:
            messagebox.showinfo(
                "Questbook installed",
                f"Installed {result.installed_files} files into {instance.name}.\n"
                f"Backup: {result.backup or 'not required'}",
                parent=root,
            )
            refresh()
        else:
            messagebox.showerror(
                "Installation failed",
                "\n".join(result.errors),
                parent=root,
            )

    ttk.Button(footer, text="Refresh", command=refresh).pack(side="left")
    ttk.Button(footer, text="Add folder…", command=add_folder).pack(side="left", padx=6)
    ttk.Button(footer, text="Preferences…", command=edit_preferences).pack(side="left")
    ttk.Button(footer, text="Install project…", command=install_bundle).pack(
        side="left", padx=6
    )
    ttk.Button(footer, text="Open empty editor", command=lambda: launch(None)).pack(
        side="right"
    )
    ttk.Button(
        footer,
        text="Open selected instance",
        command=lambda: launch(selected_instance()),
    ).pack(side="right", padx=6)
    tree.bind("<Double-1>", lambda _event: launch(selected_instance()))

    render(current_result)
    if preference_load.warnings:
        status_var.set(preference_load.warnings[0])
    root.mainloop()
    return 0
