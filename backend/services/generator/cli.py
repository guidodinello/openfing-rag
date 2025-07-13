import typer
from rich.console import Console

from services.generator.schemas.domain import SearchContext
from shared.database.service_dependencies import create_chat_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors

app = typer.Typer(
    help="🤖 OpenFing Chat Generator CLI",
    no_args_is_help=True,
)
console = Console()


@app.command(name="test-chat")
@handle_cli_errors(operation_name="Test chat")
def test_chat(
    query: str = typer.Argument(..., help="Test query"),
    lesson_id: int = typer.Option(None, help="Optional lesson ID filter"),
) -> None:
    """Test the chat functionality."""
    console.print(f"🤖 Testing chat with query: {query}", style="blue")

    with get_db_session() as db:
        service = create_chat_service(db)

        search_context = SearchContext(
            query=query,
            lesson_id=lesson_id,
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
