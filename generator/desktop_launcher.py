from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Callable, Iterable

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


def launch_desktop(
    *,
    workspace_root: Path = DEFAULT_LAUNCHER_WORKSPACE,
    search_roots: Iterable[InstanceSearchRoot | tuple[str, Path] | Path] | None = None,
    open_browser: bool = True,
    discovery: InstanceDiscoveryResult | None = None,
) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError as exc:  # pragma: no cover - depends on Python distribution
        raise RuntimeError("the desktop launcher requires Python's tkinter module") from exc

    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on display availability
        raise RuntimeError("the desktop launcher requires a graphical desktop session") from exc

    root.title("FTB Quest Maker")
    root.geometry("980x560")
    root.minsize(760, 420)
    workspace_root = Path(workspace_root).expanduser()
    current_result = discovery or discover_modpack_instances(search_roots)
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
        if result.instances:
            tree.selection_set(result.instances[0].instance_id)

    def refresh() -> None:
        try:
            render(discover_modpack_instances(search_roots))
        except (OSError, ValueError) as exc:
            messagebox.showerror("Discovery failed", str(exc), parent=root)

    def launch(instance: DiscoveredInstance | None) -> None:
        try:
            process = start_editor_process(
                instance,
                workspace_root=workspace_root,
                open_browser=open_browser,
            )
        except OSError as exc:
            messagebox.showerror("Editor launch failed", str(exc), parent=root)
            return
        label = _instance_label(instance) if instance else "an empty project"
        status_var.set(f"Started editor for {label} (PID {process.pid})")

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
    ttk.Button(footer, text="Install project…", command=install_bundle).pack(side="left")
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
    root.mainloop()
    return 0
