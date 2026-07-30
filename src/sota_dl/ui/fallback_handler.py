# src/sota_dl/ui/fallback_handler.py

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.padding import Padding

from sota_dl.core.event_bus import EventBus, ExtractorFallbackEvent


class FallbackUIHandler:
    """Subscribes to extractor fallback events and renders terminal warning banners."""

    def __init__(self, console: Console, event_bus: EventBus):
        self.console = console
        self.event_bus = event_bus
        self.event_bus.subscribe(ExtractorFallbackEvent, self._render_fallback_banner)

    async def _render_fallback_banner(self, event: ExtractorFallbackEvent) -> None:
        """Renders a styled Rich alert panel informing the user of the failover."""

        text = Text()
        text.append("⚠️ Primary Extractor Blocked\n", style="bold yellow")
        text.append(
            "YouTube anti-bot protection detected standard requests.\n\n",
            style="dim white",
        )

        text.append("Failing over to: ", style="dim white")
        text.append(f"{event.fallback_target}\n", style="bold cyan")
        text.append("Direct mobile REST extraction engaged...", style="italic green")

        panel = Panel(
            Padding(text, (0, 1)),
            title="[bold yellow]⚡ Failover Active[/bold yellow]",
            border_style="yellow",
            expand=False,
        )

        self.console.print("\n")
        self.console.print(Align.center(panel))
        self.console.print("\n")
