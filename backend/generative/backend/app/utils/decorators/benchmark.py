import asyncio
import datetime
import functools
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar

from app.utils.logger import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


# TODO: create a decorator that times the function and outputs a benchmarks .json
# esta bueno para comandos de la cli que toman tiempo como el transcribe con whisper
# deberia guardar en el log los parametros asi sabemos cosas como el modelo usado cuando se llamo
# a la funcion
# TODO: is not working, breaks the container startup
def benchmark_cli(
    output_dir: str | Path = "benchmarks",
    include_args: bool = True,
) -> Callable[[Callable[Concatenate[P], R]], Callable[Concatenate[P], R]]:
    """
    Decorator for benchmarking CLI commands and saving metrics to JSON files.

    Args:
        output_dir: Directory to save benchmark files
        include_args: Whether to include function arguments in the benchmark data
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    def decorator(func: Callable[Concatenate[P], R]) -> Callable[Concatenate[P], R]:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = datetime.time.perf_counter()
            start_process_time = time.process_time()

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception:
                success = False
                raise
            finally:
                # Capture metrics even if there's an error
                end_time = time.perf_counter()
                end_process_time = time.process_time()

                metrics = _create_benchmark_data(
                    func_name=func.__name__,
                    wall_time=end_time - start_time,
                    cpu_time=end_process_time - start_process_time,
                    success=success,
                    args=args if include_args else None,
                    kwargs=kwargs if include_args else None,
                )

                _save_benchmark(metrics, output_path)

            return result

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            start_process_time = time.process_time()

            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception:
                success = False
                raise
            finally:
                # Capture metrics even if there's an error
                end_time = time.perf_counter()
                end_process_time = time.process_time()

                metrics = _create_benchmark_data(
                    func_name=func.__name__,
                    wall_time=end_time - start_time,
                    cpu_time=end_process_time - start_process_time,
                    success=success,
                    args=args if include_args else None,
                    kwargs=kwargs if include_args else None,
                )

                _save_benchmark(metrics, output_path)

            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def _create_benchmark_data(
    func_name: str,
    wall_time: float,
    cpu_time: float,
    success: bool,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create benchmark data dictionary."""
    benchmark_data = {
        "timestamp": datetime.now().isoformat(),
        "function": func_name,
        "wall_time_seconds": round(wall_time, 3),
        "cpu_time_seconds": round(cpu_time, 3),
        "success": success,
    }

    if args:
        # Convert args to strings to ensure JSON serialization
        benchmark_data["args"] = [str(arg) for arg in args]
    if kwargs:
        # Convert kwargs values to strings to ensure JSON serialization
        benchmark_data["kwargs"] = {k: str(v) for k, v in kwargs.items()}

    return benchmark_data


def _save_benchmark(metrics: dict[str, Any], output_dir: Path) -> None:
    """Save benchmark data to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_{metrics['function']}_{timestamp}.json"
    output_path = output_dir / filename

    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        logger.info(f"Benchmark data saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save benchmark data: {e}")
