import secrets
from datetime import datetime, timedelta, timezone

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.config import get_settings
from shared.database.models.api_key import ApiKeyScope
from shared.database.repository_dependencies import get_user_repository
from shared.database.service_dependencies import create_api_key_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors

settings = get_settings()

console = Console()
app = typer.Typer(
    help="🔐 Security and secrets management CLI",
    no_args_is_help=True,
)


@handle_cli_errors
@app.command()
def generate_jwt_secret() -> None:
    """Generate a secure JWT secret key"""
    secret = secrets.token_hex(32)

    console.print("\n[bold green]🔑 Generated JWT Secret Key[/bold green]")
    console.print(Panel(f"[bold]{secret}[/bold]", title="JWT Secret Key", border_style="green"))
    console.print("\n[yellow]Add this to your .env file:[/yellow]")
    console.print(f"[dim]JWT__SECRET_KEY={secret}[/dim]")
    console.print(f"\n[dim]Length: {len(secret)} characters | Entropy: 256 bits[/dim]")


@handle_cli_errors
@app.command()
def generate_hmac_secret() -> None:
    """Generate a secure HMAC secret for API keys"""
    secret = secrets.token_hex(32)

    console.print("\n[bold blue]🔐 Generated HMAC Secret[/bold blue]")
    console.print(Panel(f"[bold]{secret}[/bold]", title="HMAC Secret", border_style="blue"))
    console.print("\n[yellow]Add this to your .env file:[/yellow]")
    console.print(f"[dim]API_KEYS__HMAC_SECRET={secret}[/dim]")
    console.print(f"\n[dim]Length: {len(secret)} characters | Entropy: 256 bits[/dim]")


@handle_cli_errors
@app.command()
def generate_all() -> None:
    """Generate both JWT and HMAC secrets."""
    jwt_secret = secrets.token_hex(32)
    hmac_secret = secrets.token_hex(32)

    table = Table(title="Security Secrets", border_style="magenta")
    table.add_column("Type", style="bold")
    table.add_column("Secret", style="dim")
    table.add_column("Environment Variable", style="yellow")

    table.add_row("JWT Secret", jwt_secret, "JWT__SECRET_KEY")
    table.add_row("HMAC Secret", hmac_secret, "API_KEYS__HMAC_SECRET")

    console.print(table)

    console.print("\n[yellow]Add these to your .env file:[/yellow]")
    console.print(f"[dim]JWT__SECRET_KEY={jwt_secret}[/dim]")
    console.print(f"[dim]API_KEYS__HMAC_SECRET={hmac_secret}[/dim]")


@handle_cli_errors
@app.command()
def create_api_key(
    username: str = typer.Argument(..., help="Username to create API key for"),
    name: str = typer.Argument(..., help="Human-readable name for the API key"),
    scope: ApiKeyScope = typer.Option(ApiKeyScope.READ, help="Permission scope for the API key"),
    expires_days: int | None = typer.Option(None, help="Days until expiration (none = never expires)"),
) -> None:
    """Create a new API key for a user"""
    with get_db_session() as db:
        api_key_service = create_api_key_service(db)

        user = get_user_repository(db).get_by(username=username)
        if not user:
            console.print(f"[red]❌ User '{username}' not found[/red]")
            raise typer.Exit(1)

        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        plain_key, api_key_model = api_key_service.register_api_key(
            user_id=user.id,
            name=name,
            scope=scope,
            expires_at=expires_at,
        )

        db.commit()

        console.print("\n[bold green]✅ API Key Created Successfully[/bold green]")

        info_table = Table(border_style="green")
        info_table.add_column("Property", style="bold")
        info_table.add_column("Value")

        info_table.add_row("User", f"{user.username} ({user.email})")
        info_table.add_row("Name", name)
        info_table.add_row("Scope", scope.value)
        info_table.add_row("Expires", expires_at.isoformat() if expires_at else "Never")
        info_table.add_row("Created", api_key_model.created_at.isoformat())

        console.print(info_table)

        console.print(
            Panel(
                f"[bold]{plain_key}[/bold]",
                title="🔑 API Key (Save this securely - it won't be shown again!)",
                border_style="red",
            ),
        )


if __name__ == "__main__":
    app()
