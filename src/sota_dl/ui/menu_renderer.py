"""UI Renderer for the application menus."""

from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from sota_dl.config.colors import THEME, MUTED, ACCENT, TEXT
from sota_dl.config.settings import COOKIES_PATH
from sota_dl.ui.banners import render_main_banner, console


def render_dashboard(output_path: Path) -> None:
    """Render the main menu dashboard."""
    render_main_banner()

    # Dashboard layout: Info and Menu in a structured grid
    dashboard = Table(box=None, expand=True, padding=(0, 0))
    dashboard.add_column(justify="center")

    # Display route information in a compact panel
    info_panel = Panel(
        f"[bold {ACCENT}]STORAGE :[/] [white]{output_path}[/]\n"
        f"[bold {ACCENT}]COOKIES :[/] [white]{COOKIES_PATH}[/]",
        border_style=MUTED,
        padding=(0, 2),
        title=f"[bold {THEME}]SYSTEM STATUS[/]",
    )

    # Main Menu Table for better alignment
    menu_table = Table(box=None, show_header=False, padding=(0, 1))
    menu_table.add_column("ID", justify="right", style=ACCENT)
    menu_table.add_column("Command", style=f"bold {TEXT}")

    menu_table.add_row("1", "EXTRACT VIDEO STREAM (MP4/MKV)")
    menu_table.add_row("2", "EXTRACT AUDIO STREAM (MP3/M4A)")
    menu_table.add_row("3", "CONFIGURE SYSTEM PARAMETERS")
    menu_table.add_row("4", "TERMINATE SESSION")

    menu_panel = Panel(
        menu_table,
        title=f"[bold {THEME}]PRIMARY COMMANDS[/]",
        border_style=THEME,
        padding=(1, 2),
    )

    dashboard.add_row(info_panel)
    dashboard.add_row(menu_panel)

    console.print(dashboard)


def render_settings_menu(cookies_path: Path, download_path: Path) -> None:
    """Render settings table."""
    settings_table = Table(box=None, show_header=False, padding=(0, 1))
    settings_table.add_column("ID", justify="right", style=ACCENT)
    settings_table.add_column("Option", style=TEXT)

    settings_table.add_row("1", "UPDATE COOKIES DATASOURCE")
    settings_table.add_row("2", "OVERRIDE DOWNLOAD PATH")
    settings_table.add_row("3", "AUTO-EXTRACT COOKIES (CHROME)")
    settings_table.add_row("4", "RETURN TO COMMAND CENTER")

    console.print(
        Panel(
            f"[dim]SOURCE:[/dim] {cookies_path}\n"
            f"[dim]TARGET:[/dim] {download_path}\n\n",
            title=f"[bold {THEME}]SYSTEM CONFIGURATION[/]",
            border_style=THEME,
            padding=(1, 2),
        )
    )
    console.print(Panel(settings_table, border_style=MUTED, padding=(1, 2)))


def get_menu_selection(prompt_text: str, choices: list[str]) -> str:
    """Prompt the user for a menu selection."""
    return Prompt.ask(
        f"[{THEME}]{prompt_text}[/]",
        choices=choices,
    )
