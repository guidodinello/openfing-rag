from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True, slots=True)
class VectorSpaceMetrics:
    """Vector space analysis metrics."""

    avg_similarity_to_nearest: float
    similarity_distribution: dict[str, float]
    dimensionality_variance: np.ndarray
    total_variance_explained: float


@dataclass(frozen=True, slots=True)
class DatabaseMetrics:
    """Metrics extracted from the database."""

    total_transcriptions: int
    vectorized_transcriptions: int
    total_chunks: int
    total_courses: int
    total_lessons: int
    avg_chunks_per_transcription: float
    chunk_size_distribution: dict[str, Any]
    transcriptions_by_course: list[tuple[str, int]]
    chunks_by_course: list[tuple[str, int]]
    vectorization_timing: dict[str, Any]
    timing_accuracy_distribution: dict[str, int]
    storage_stats: dict[str, Any]
    vector_metrics: VectorSpaceMetrics | None = None

    def __str__(self) -> str:
        lines = [
            "DATABASE VECTORIZATION METRICS",
            "=" * 60,
            "",
            "OVERVIEW",
            "-" * 60,
            f"Total Courses:              {self.total_courses:,}",
            f"Total Lessons:              {self.total_lessons:,}",
            f"Total Transcriptions:       {self.total_transcriptions:,}",
            f"Vectorized:                 {self.vectorized_transcriptions:,}",
            f"Not Vectorized:             {self.total_transcriptions - self.vectorized_transcriptions:,}",
            f"Vectorization Rate:         {(self.vectorized_transcriptions / self.total_transcriptions * 100) if self.total_transcriptions > 0 else 0:.2f}%",
            "",
            "CHUNK STATISTICS",
            "-" * 60,
            f"Total Chunks:               {self.total_chunks:,}",
            f"Avg Chunks/Transcription:   {self.avg_chunks_per_transcription:.1f}",
        ]

        if self.chunk_size_distribution:
            lines.extend(
                [
                    "",
                    "CHUNK SIZE DISTRIBUTION (characters)",
                    "-" * 60,
                    f"Min:                        {self.chunk_size_distribution.get('min', 0)}",
                    f"25th Percentile:            {self.chunk_size_distribution.get('p25', 0):.0f}",
                    f"Median (50th):              {self.chunk_size_distribution.get('median', 0):.0f}",
                    f"Mean:                       {self.chunk_size_distribution.get('mean', 0):.0f}",
                    f"75th Percentile:            {self.chunk_size_distribution.get('p75', 0):.0f}",
                    f"90th Percentile:            {self.chunk_size_distribution.get('p90', 0):.0f}",
                    f"95th Percentile:            {self.chunk_size_distribution.get('p95', 0):.0f}",
                    f"99th Percentile:            {self.chunk_size_distribution.get('p99', 0):.0f}",
                    f"Max:                        {self.chunk_size_distribution.get('max', 0)}",
                    f"Std Dev:                    {self.chunk_size_distribution.get('stddev', 0):.0f}",
                ]
            )

        if self.timing_accuracy_distribution:
            lines.extend(
                [
                    "",
                    "TIMING ACCURACY DISTRIBUTION",
                    "-" * 60,
                ],
            )
            for accuracy, count in self.timing_accuracy_distribution.items():
                pct = (count / self.vectorized_transcriptions * 100) if self.vectorized_transcriptions > 0 else 0
                lines.append(f"  {accuracy:20s} {count:5,d} ({pct:5.1f}%)")

        if self.storage_stats:
            lines.extend(
                [
                    "",
                    "STORAGE STATISTICS",
                    "-" * 60,
                    f"Total DB Size:              {self.storage_stats.get('total_size', 'N/A')}",
                    f"Vector Table Size:          {self.storage_stats.get('vector_table_size', 'N/A')}",
                    f"Avg Bytes per Chunk:        {self.storage_stats.get('avg_bytes_per_chunk', 0):.0f}",
                ],
            )

        if self.vector_metrics:
            lines.extend(
                [
                    "",
                    "VECTOR SPACE ANALYSIS",
                    "-" * 60,
                    f"Avg Similarity to Nearest:  {self.vector_metrics.avg_similarity_to_nearest:.4f}",
                    f"Variance Explained (PCA):   {self.vector_metrics.total_variance_explained:.2%}",
                ],
            )

        lines.extend(
            [
                "",
                "TOP 10 COURSES BY TRANSCRIPTIONS",
                "-" * 60,
            ],
        )

        for course, count in self.transcriptions_by_course[:10]:
            lines.append(f"  {course:20s} {count:4d}")

        lines.extend(
            [
                "",
                "TOP 10 COURSES BY CHUNKS",
                "-" * 60,
            ],
        )

        for course, count in self.chunks_by_course[:10]:
            lines.append(f"  {course:20s} {count:6,d}")

        if self.vectorization_timing:
            lines.extend(
                [
                    "",
                    "VECTORIZATION TIMING",
                    "-" * 60,
                    f"Earliest:                   {self.vectorization_timing.get('earliest', 'N/A')}",
                    f"Latest:                     {self.vectorization_timing.get('latest', 'N/A')}",
                ],
            )

        return "\n".join(lines)
