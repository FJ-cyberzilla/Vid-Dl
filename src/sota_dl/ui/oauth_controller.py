import io
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.padding import Padding

from sota_dl.core.event_bus import EventBus, OAuth2RequiredEvent

# Optional import check for qrcode
try:
    import qrcode  # type: ignore

    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class OAuth2Controller:
    """
    Subscribes to OAuth2 events and renders interactive device login prompts
    with QR codes.
    """

    def __init__(self, console: Console, event_bus: EventBus):
        self.console = console
        self.event_bus = event_bus
        self.event_bus.subscribe(OAuth2RequiredEvent, self._render_oauth2_prompt)

    def _generate_ascii_qr(self, url: str) -> str:
        """Generates an ASCII/Unicode QR code string from a URL."""
        if not HAS_QRCODE:
            return ""

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Output ASCII block characters to a string buffer
        stream = io.StringIO()
        qr.print_ascii(out=stream, invert=True)
        return stream.getvalue()

    def _render_oauth2_prompt(self, event: OAuth2RequiredEvent) -> None:
        """
        Renders a styled Rich panel with responsive layout
        (Horizontal for Desktop, Vertical for Mobile).
        """

        # 1. Text Instructions
        text_content = Text()
        text_content.append("YouTube Action Required\n\n", style="bold red")

        text_content.append("1. Scan QR code OR open link:\n", style="dim white")
        text_content.append(f"   {event.auth_url}\n\n", style="bold cyan underline")

        text_content.append("2. Enter authorization code:\n", style="dim white")
        text_content.append(
            f"   {event.user_code}   \n\n", style="bold black on bright_yellow"
        )

        text_content.append(
            "⏳ Waiting for authorization...\n(Auto-resumes upon approval)",
            style="italic green",
        )

        # 2. ASCII QR Code
        qr_string = self._generate_ascii_qr(event.auth_url)

        # 3. Dynamic Responsive Layout Switching
        # Termux/Mobile screens (< 70 cols) break side-by-side QR matrices.
        is_narrow_screen = self.console.width < 70

        if is_narrow_screen or not qr_string:
            # 📱 Mobile Layout: Vertical Stack (Top to Bottom)
            grid = Table.grid(expand=True, padding=(1, 0))
            grid.add_column(justify="center")
            grid.add_row(Align.center(text_content))

            if qr_string:
                grid.add_row(Align.center(Text(qr_string, style="bright_white")))
        else:
            # 🖥️ Desktop Layout: Horizontal Side-by-Side
            grid = Table.grid(expand=False, padding=(0, 2))
            grid.add_column(justify="left", vertical="middle")
            grid.add_column(justify="center", vertical="middle")
            grid.add_row(text_content, Text(qr_string, style="bright_white"))

        # 4. Wrap Grid inside Panel
        panel = Panel(
            Padding(grid, (1, 1)),
            title="[bold yellow]🔐 OAuth2 Device Authentication[/bold yellow]",
            subtitle="[dim]Press Ctrl+C to cancel[/dim]",
            border_style="yellow",
            expand=False,
        )

        self.console.print("\n")
        self.console.print(Align.center(panel))
        self.console.print("\n")
