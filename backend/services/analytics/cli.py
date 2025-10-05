from pathlib import Path

import typer
from rich.console import Console

from shared.decorators.cli_error_handlers import handle_cli_errors

from services.analytics.core.analytics_service import AnalyticsService, create_analytics_service, get_db

console = Console()
app = typer.Typer(help="📊 Database Analytics CLI", no_args_is_help=True)


@handle_cli_errors
@app.command("full-report")
def full_report(
    output_dir: Path = typer.Option(Path("./db_analysis"), help="Output directory for visualizations"),
    plots: bool = typer.Option(True, help="Generate Plots"),
):
    """Analyze vectorization metrics from database."""

    with get_db() as db:
        service = create_analytics_service(db)
        metrics = service.full_report()
        # console.print(metrics)

        AnalyticsService.write_report(metrics, path=output_dir / "database_metrics.txt")

        if plots:
            service.create_visualizations(metrics, output_dir)
