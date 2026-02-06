from __future__ import annotations

import os
import shutil
import stat
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import Annotated

import readchar
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


class InitMode(StrEnum):
    CLAUDE_CODE = "claude-code"
    SCRIPT = "script"


def _templates_path() -> Path:
    source = files("reviewloop_cli.templates")
    path = Path(str(source))
    if not path.is_dir():
        print("Error: template files not found. The reviewloop package may be corrupted — try reinstalling.")
        raise typer.Exit(code=1)
    return path


def _strip_frontmatter(content: str) -> str:
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return content
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1 :]).lstrip("\n")
    return content


def _get_target_files(mode: InitMode) -> list[str]:
    if mode == InitMode.CLAUDE_CODE:
        return [
            ".claude/skills/reviewloop/SKILL.md",
            ".claude/skills/reviewloop/scripts/review-wait.sh",
            ".claude/skills/reviewloop/scripts/review-comments.sh",
        ]
    return [
        "scripts/reviewloop/review-wait.sh",
        "scripts/reviewloop/review-comments.sh",
        "scripts/reviewloop/reviewPrompt.txt",
    ]


def _check_existing_files(target_dir: Path, mode: InitMode, force: bool) -> bool:
    existing = [f for f in _get_target_files(mode) if (target_dir / f).exists()]
    if not existing:
        return True
    print("The following files already exist:")
    for f in existing:
        print(f"  - {f}")
    if force:
        print("Overwriting (--force).")
        return True
    return typer.confirm("Overwrite?", default=False)


def _make_executable(path: Path) -> None:
    if os.name == "nt":
        return
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _copy_scripts(templates: Path, scripts_dir: Path) -> list[str]:
    scripts_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for name in ("review-wait.sh", "review-comments.sh"):
        src = templates / "scripts" / name
        dst = scripts_dir / name
        shutil.copy2(src, dst)
        _make_executable(dst)
        created.append(str(dst))
    return created


def _init_claude_code(target_dir: Path, templates: Path) -> list[str]:
    skill_dir = target_dir / ".claude" / "skills" / "reviewloop"
    scripts_dir = skill_dir / "scripts"
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_src = templates / "SKILL.md"
    skill_dst = skill_dir / "SKILL.md"
    shutil.copy2(skill_src, skill_dst)

    created = [str(skill_dst)]
    created.extend(_copy_scripts(templates, scripts_dir))
    return created


def _init_script(target_dir: Path, templates: Path) -> list[str]:
    scripts_dir = target_dir / "scripts" / "reviewloop"
    created = _copy_scripts(templates, scripts_dir)

    skill_content = (templates / "SKILL.md").read_text(encoding="utf-8")
    prompt_content = _strip_frontmatter(skill_content)
    prompt_content = prompt_content.replace(".claude/skills/reviewloop/scripts/", "scripts/reviewloop/")
    prompt_path = scripts_dir / "reviewPrompt.txt"
    prompt_path.write_text(prompt_content, encoding="utf-8")
    created.append(str(prompt_path))

    return created


def _print_summary(created_files: list[str], target_dir: Path) -> None:
    print(f"\nInitialized reviewloop in {target_dir}\n")
    print("Created files:")
    for f in created_files:
        print(f"  {f}")


def _get_key() -> str:
    key = readchar.readkey()
    if key in (readchar.key.UP, readchar.key.CTRL_P):
        return "up"
    if key in (readchar.key.DOWN, readchar.key.CTRL_N):
        return "down"
    if key == readchar.key.ENTER:
        return "enter"
    if key == readchar.key.ESC:
        return "escape"
    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt
    return key


def _select_with_arrows(options: dict[str, str], title: str, default: str | None = None) -> str:
    keys = list(options.keys())
    selected = keys.index(default) if default and default in keys else 0

    def _build_panel() -> Panel:
        table = Table.grid(padding=(0, 2))
        table.add_column(width=3)
        table.add_column()
        for i, key in enumerate(keys):
            marker = "[cyan]\u25b6[/cyan]" if i == selected else " "
            label = f"[bold cyan]{key}[/bold cyan]" if i == selected else f"[dim]{key}[/dim]"
            table.add_row(marker, f"{label}  [dim]{options[key]}[/dim]")
        table.add_row("", "")
        table.add_row("", "[dim]\u2191/\u2193 navigate, Enter select, Esc cancel[/dim]")
        return Panel(table, title=f"[bold]{title}[/bold]", border_style="cyan", padding=(1, 2))

    console.print()
    with Live(_build_panel(), console=console, transient=True, auto_refresh=False) as live:
        while True:
            try:
                key = _get_key()
            except KeyboardInterrupt:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(code=1) from None
            if key == "up":
                selected = (selected - 1) % len(keys)
            elif key == "down":
                selected = (selected + 1) % len(keys)
            elif key == "enter":
                return keys[selected]
            elif key == "escape":
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(code=1)
            live.update(_build_panel(), refresh=True)


def _prompt_mode() -> InitMode:
    choices = {
        "Claude Code": "installs as a Claude Code skill",
        "Script based": "creates standalone scripts + prompt file",
    }
    selected = _select_with_arrows(choices, "Initialization mode", default="Claude Code")
    if selected == "Script based":
        return InitMode.SCRIPT
    return InitMode.CLAUDE_CODE


def _resolve_target_dir(project_name: str | None, here: bool) -> Path:
    if here:
        return Path.cwd()
    if project_name is None:
        name: str = str(typer.prompt("Project folder name"))
    else:
        name = project_name
    if name == ".":
        return Path.cwd()
    target = Path.cwd() / name
    target.mkdir(parents=True, exist_ok=True)
    return target


def init(
    project_name: Annotated[str | None, typer.Argument(help="Target directory name for initialization.")] = None,
    mode: Annotated[InitMode | None, typer.Option("--mode", help="Initialization mode.")] = None,
    here: Annotated[bool, typer.Option("--here", help="Initialize in the current directory.")] = False,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files without confirmation.")] = False,
) -> None:
    if project_name is not None and here:
        print("Error: cannot specify both a project name and --here.")
        raise typer.Exit(code=1)

    target_dir = _resolve_target_dir(project_name, here)

    if mode is None:
        mode = _prompt_mode()

    if not _check_existing_files(target_dir, mode, force):
        print("Aborted.")
        raise typer.Exit(code=1)

    templates = _templates_path()

    if mode == InitMode.CLAUDE_CODE:
        created = _init_claude_code(target_dir, templates)
    else:
        created = _init_script(target_dir, templates)

    _print_summary(created, target_dir)
