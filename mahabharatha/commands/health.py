import click
from rich.console import Console
from rich.table import Table

from mahabharatha.config import MahabharathaConfig
from mahabharatha.llm import ClaudeProvider, OllamaProvider

console = Console()


@click.command()
def health():
    """Check the health and availability of MAHABHARATHA components (LLM, Providers)."""
    config = MahabharathaConfig.load()

    console.print("[bold blue]MAHABHARATHA System Health Check[/bold blue]")
    console.print(f"Active Provider: [bold green]{config.llm.provider}[/bold green]")
    console.print("-" * 40)

    # Initialize correct provider for health check
    if config.llm.provider == "ollama":
        provider = OllamaProvider(model=config.llm.model, hosts=config.llm.endpoints)
    else:
        # Claude provider uses CLI
        provider = ClaudeProvider()

    health_data = provider.check_health()

    if health_data["status"] == "ok":
        console.print("[bold green]✔ LLM Provider is Healthy[/bold green]")
    else:
        console.print("[bold red]✘ LLM Provider Health Check Failed[/bold red]")

    if config.llm.provider == "ollama":
        table = Table(title=f"Ollama Infrastructure (Model: {config.llm.model})")
        table.add_column("Host", style="cyan")
        table.add_column("Reachable", style="magenta")
        table.add_column("Model Downloaded", style="green")

        for host in health_data.get("hosts", []):
            table.add_row(
                host["host"],
                "[green]Yes[/green]" if host["reachable"] else "[red]No[/red]",
                "[green]Yes[/green]" if host.get("has_model") else "[red]No[/red]",
            )
        console.print(table)
    else:
        console.print(f"Claude CLI found: {'[green]Yes[/green]' if health_data.get('cli_found') else '[red]No[/red]'}")
        if health_data.get("error"):
            console.print(f"[red]Error: {health_data['error']}[/red]")

    console.print("-" * 40)
    console.print("[dim]Use 'mahabharatha config' to update provider settings.[/dim]")
