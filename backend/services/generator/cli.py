import typer
from rich.console import Console

from shared.database.service_dependencies import create_chat_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors

from services.generator.schemas import SearchContext

app = typer.Typer(
    help="🤖 OpenFing Chat Generator CLI",
    no_args_is_help=True,
)
console = Console()


@handle_cli_errors
@app.command(name="chat")
def chat(
    query: str = typer.Argument(..., help="Test query"),
    lessons_ids: int = typer.Option(None, help="Optional lessons IDs filter"),
    courses_ids: int = typer.Option(None, help="Optional couses IDs filter"),
) -> None:
    """Test the chat functionality."""
    console.print(f"🤖 Chat with query: {query}", style="blue")

    with get_db_session() as db:
        service = create_chat_service(db)

        search_context = SearchContext(
            query=query,
            lessons_ids=lessons_ids,
            courses_ids=courses_ids,
            max_results=3,
        )

        result = service.process_message(search_context)

        if result.success:
            console.print("✅ Response generated:", style="green")
            console.print(f"🤖 {result.response}")
            console.print(f"📚 Sources: {', '.join(result.sources)}")
            console.print(f"🔧 Model: {result.model_used}")
        else:
            console.print(f"❌ Error: {result.error}", style="red")
