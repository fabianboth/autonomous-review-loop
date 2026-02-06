from importlib.metadata import version
from typing import Annotated

import typer

from reviewloop_cli.init import init as init_command

app = typer.Typer(
    name="reviewloop",
    help="Autonomous review loop - automates the review-fix-push cycle.",
    add_completion=False,
    invoke_without_command=True,
)
app.command(name="init", help="Initialize reviewloop in a project.")(init_command)


def _version_callback(value: bool) -> None:
    if value:
        print(f"reviewloop v{version('reviewloop')}")
        raise typer.Exit


@app.callback()
def callback(
    ctx: typer.Context,
    _version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version and exit."),
    ] = None,
) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit


def main() -> None:
    app()
