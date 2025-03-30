import functools
from collections.abc import Callable
from typing import Concatenate, ParamSpec, TypeVar

import typer
from sqlalchemy.exc import SQLAlchemyError

from app.utils.logger import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def handle_cli_errors(
    operation_name: str = None,
    exit_on_error: bool = True,
    log_error: bool = True,
):
    """
    Decorator for handling CLI command errors uniformly.

    Args:
        operation_name: Name of the operation for error messages
        exit_on_error: Whether to exit the CLI on error
        log_error: Whether to log the error
    """

    def decorator(func: Callable[Concatenate[P], R]) -> Callable[Concatenate[P], R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cmd_name = operation_name or func.__name__.replace("_", " ")

            try:
                typer.echo(f"Starting {cmd_name}...")
                result = func(*args, **kwargs)
                typer.echo(f"{cmd_name.capitalize()} completed successfully!")
                return result

            except SQLAlchemyError as e:
                error_msg = f"Database error during {cmd_name}: {str(e)}"
                if log_error:
                    logger.error(error_msg, exc_info=True)
                typer.echo(error_msg, err=True)
                if exit_on_error:
                    raise typer.Exit(1) from e
                raise

            except Exception as e:
                error_msg = f"Error during {cmd_name}: {str(e)}"
                if log_error:
                    logger.error(error_msg, exc_info=True)
                typer.echo(error_msg, err=True)
                if exit_on_error:
                    raise typer.Exit(1) from e
                raise

        return wrapper

    return decorator


def handle_async_cli_errors(
    operation_name: str = None,
    exit_on_error: bool = True,
    log_error: bool = True,
):
    """
    Decorator for handling async CLI command errors uniformly.

    Args:
        operation_name: Name of the operation for error messages
        exit_on_error: Whether to exit the CLI on error
        log_error: Whether to log the error
    """

    def decorator(func: Callable[Concatenate[P], R]) -> Callable[Concatenate[P], R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cmd_name = operation_name or func.__name__.replace("_", " ")

            try:
                typer.echo(f"Starting {cmd_name}...")
                result = await func(*args, **kwargs)
                typer.echo(f"{cmd_name.capitalize()} completed successfully!")
                return result

            except SQLAlchemyError as e:
                error_msg = f"Database error during {cmd_name}: {str(e)}"
                if log_error:
                    logger.error(error_msg, exc_info=True)
                typer.echo(error_msg, err=True)
                if exit_on_error:
                    raise typer.Exit(1) from e
                raise

            except Exception as e:
                error_msg = f"Error during {cmd_name}: {str(e)}"
                if log_error:
                    logger.error(error_msg, exc_info=True)
                typer.echo(error_msg, err=True)
                if exit_on_error:
                    raise typer.Exit(1) from e
                raise

        return wrapper

    return decorator
