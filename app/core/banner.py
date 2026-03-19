"""启动横幅"""

from typing import Optional

import pyfiglet
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_banner(app_name: str = "Flower", version: str = "0.1.0") -> None:
    """打印美观的启动横幅"""

    banner_text = pyfiglet.figlet_format(app_name, font="slant")

    title = Text(banner_text, style="bold magenta")
    subtitle = Text(f"v{version} • 智能助手", style="bright_blue")

    console.print()
    panel = Panel(
        title,
        border_style="bold magenta",
        box=ROUNDED,
        expand=False,
        padding=(0, 2),
    )
    console.print(panel)
    console.print(f"  {subtitle}")
    console.print()


def print_success(message: str) -> None:
    """打印成功消息"""
    console.print(f"  ✅ [bold green]{message}[/bold green]")


def print_info(message: str) -> None:
    """打印信息消息"""
    console.print(f"  ℹ️ [blue]{message}[/blue]")


def print_warning(message: str) -> None:
    """打印警告消息"""
    console.print(f"  ⚠️ [yellow]{message}[/yellow]")


def print_error(message: str) -> None:
    """打印错误消息"""
    console.print(f"  ❌ [bold red]{message}[/bold red]")


def print_ready(
    port: int = 8000,
    docs_url: str = "/docs",
    extra_info: Optional[dict[str, str]] = None,
) -> None:
    """打印就绪信息表"""

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", width=16)
    table.add_column(style="white")

    url = f"[underline green]http://localhost:{port}{docs_url}[/underline green]"
    table.add_row("📍 文档", url)
    table.add_row("🩺 健康检查", f"http://localhost:{port}/health")

    if extra_info:
        for key, value in extra_info.items():
            table.add_row(key, value)

    console.print()
    console.print(
        Panel(
            table,
            title="🚀 [bold green]服务已就绪[/bold green]",
            border_style="bold green",
            box=ROUNDED,
            expand=False,
            padding=(1, 2),
        )
    )
    console.print()


def print_shutdown(app_name: str = "Flower") -> None:
    """打印关闭消息"""
    console.print()
    console.print(
        Panel(
            Text(f"👋 {app_name} 正在关闭...再见！", style="dim"),
            border_style="dim",
            box=ROUNDED,
            expand=False,
        )
    )
    console.print()


def print_init_step(step_name: str) -> None:
    """打印初始化步骤"""
    console.print(f"  ⚙️  [dim]初始化中[/dim] [yellow]{step_name}[/yellow]...", end=" ")


def print_init_complete(step_name: str) -> None:
    """打印初始化完成"""
    console.print("[green]完成[/green]")


def print_platforms(platforms: list[str]) -> None:
    """打印已注册平台"""
    if platforms:
        text = ", ".join(platforms)
        console.print(f"  🚪 [blue]网关已就绪:[/blue] [white]{text}[/white]")
    else:
        console.print("  🚪 [blue]未注册平台[/blue]")


def print_schedulers_started(schedulers: list[str]) -> None:
    """打印调度器启动完成"""
    text = ", ".join(schedulers)
    print_success(f"调度器已启动: {text}")
