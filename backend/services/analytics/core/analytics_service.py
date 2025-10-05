from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

from shared.config import get_settings
from shared.logging import get_logger

from services.analytics.schemas.domain import DatabaseMetrics, VectorSpaceMetrics

logger = get_logger(__name__)
settings = get_settings()


class AnalyticsService:
    def __init__(self, db: duckdb.DuckDBPyConnection):
        self.db = db

    def _basic_counts_query(self):
        return self.db.execute("""
            SELECT
                COUNT(DISTINCT c.id) as total_courses,
                COUNT(DISTINCT l.id) as total_lessons,
                COUNT(DISTINCT t.id) as total_transcriptions,
                SUM(CASE
                    WHEN t.transcription_metadata->>'vectorized' = 'true'
                    THEN 1 ELSE 0
                END) as vectorized_transcriptions
            FROM pg.courses c
            LEFT JOIN pg.lessons l ON c.id = l.course_id
            LEFT JOIN pg.transcriptions t ON l.id = t.lesson_id
        """).fetchone()

    def _chunk_stats_query(self):
        return self.db.execute("""
            SELECT
                COUNT(*) as total_chunks,
                AVG(LENGTH(content)) as avg_size,
                MEDIAN(LENGTH(content)) as median_size,
                STDDEV(LENGTH(content)) as stddev_size,
                MIN(LENGTH(content)) as min_size,
                MAX(LENGTH(content)) as max_size,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY LENGTH(content)) as p25,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY LENGTH(content)) as p75,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY LENGTH(content)) as p90,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY LENGTH(content)) as p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY LENGTH(content)) as p99
            FROM pg.chunks
        """).fetchone()

    def _get_chunk_sizes(self) -> list[int]:
        """Get all chunk sizes for histogram."""
        return self.db.execute("SELECT LENGTH(content) FROM pg.chunks").fetchall()

    def _transcriptions_by_course_query(self):
        return self.db.execute("""
            SELECT
                c.code,
                COUNT(t.id) as transcription_count
            FROM pg.courses c
            LEFT JOIN pg.lessons l ON c.id = l.course_id
            LEFT JOIN pg.transcriptions t ON l.id = t.lesson_id
            WHERE t.id IS NOT NULL
            GROUP BY c.code
            ORDER BY transcription_count DESC
        """).fetchall()

    def _chunks_by_course_query(self):
        return self.db.execute("""
                SELECT
                    c.code,
                    COUNT(v.uuid) as chunk_count
                FROM pg.courses c
                LEFT JOIN pg.lessons l ON c.id = l.course_id
                LEFT JOIN pg.chunks v ON v.course_id = c.id
                WHERE v.uuid IS NOT NULL
                GROUP BY c.code
                ORDER BY chunk_count DESC
            """).fetchall()

    def _timing_dist_query(self):
        return self.db.execute("""
                SELECT
                    t.transcription_metadata->>'timing_accuracy' as timing_type,
                    COUNT(*) as count
                FROM pg.transcriptions t
                WHERE t.transcription_metadata->>'vectorized' = 'true'
                GROUP BY timing_type
                ORDER BY count DESC
            """).fetchall()

    def _vectorization_timing_query(self):
        return self.db.execute("""
            SELECT
                MIN(t.transcription_metadata->>'vectorized_at') as earliest,
                MAX(t.transcription_metadata->>'vectorized_at') as latest
            FROM pg.transcriptions t
            WHERE t.transcription_metadata->>'vectorized' = 'true'
        """).fetchone()

    def _storage_query(self):
        return self.db.execute("PRAGMA database_size").fetchone()

    def _vector_table_size_query(self):
        return self.db.execute("SELECT COUNT(*) as row_count FROM pg.chunks").fetchone()

    def _embeddings_query(self, limit: int):
        return self.db.execute(f"""
                SELECT embedding::float8[]
                FROM pg.chunks
                ORDER BY random()
                LIMIT {limit}
            """).fetchall()

    def _chunk_stats(self):
        chunk_stats = self._chunk_stats_query()

        total_chunks = chunk_stats[0] if chunk_stats else 0
        chunk_size_dist = {
            "mean": chunk_stats[1],
            "median": chunk_stats[2],
            "stddev": chunk_stats[3],
            "min": chunk_stats[4],
            "max": chunk_stats[5],
            "p25": chunk_stats[6],
            "p75": chunk_stats[7],
            "p90": chunk_stats[8],
            "p95": chunk_stats[9],
            "p99": chunk_stats[10],
        }

        return total_chunks, chunk_size_dist

    def _timing_accuracy(self):
        timing_dist = self._timing_dist_query()
        return {row[0]: row[1] for row in timing_dist if row[0]}

    def _vectorization_timing(self):
        timing = self._vectorization_timing_query()

        return {
            "earliest": timing[0] if timing and timing[0] else "N/A",
            "latest": timing[1] if timing and timing[1] else "N/A",
        }

    def _storage_stats(self, chunk_size_dist):
        storage = self._storage_query()

        vector_table_size = self._vector_table_size_query()

        return {
            "total_size": storage[0] if storage else "N/A",
            "vector_table_size": vector_table_size[0] if vector_table_size else "N/A",
            "avg_bytes_per_chunk": chunk_size_dist.get("mean", 0),
        }

    def full_report(self) -> DatabaseMetrics:
        """Analyze vectorization metrics from the database using DuckDB."""

        # Query 1: Basic counts
        total_courses, total_lessons, total_transcriptions, vectorized = self._basic_counts_query()

        # Query 2: Chunk counts and size distribution
        total_chunks, chunk_size_dist = self._chunk_stats()

        # Query 3: Transcriptions by course
        transcriptions_by_course = self._transcriptions_by_course_query()

        # Query 4: Chunks by course
        chunks_by_course = self._chunks_by_course_query()

        # Query 5: Timing accuracy distribution
        timing_accuracy = self._timing_accuracy()

        # Query 6: Vectorization timing
        vectorization_timing = self._vectorization_timing()

        # Query 7: Storage statistics
        storage_stats = self._storage_stats(chunk_size_dist)

        # Vector space analysis
        vector_metrics = self.analyze_vector_space()

        return DatabaseMetrics(
            total_transcriptions=total_transcriptions or 0,
            vectorized_transcriptions=vectorized or 0,
            total_chunks=total_chunks,
            total_courses=total_courses or 0,
            total_lessons=total_lessons or 0,
            avg_chunks_per_transcription=total_chunks / vectorized if vectorized > 0 else 0,
            chunk_size_distribution=chunk_size_dist,
            transcriptions_by_course=transcriptions_by_course,
            chunks_by_course=chunks_by_course,
            vectorization_timing=vectorization_timing,
            timing_accuracy_distribution=timing_accuracy,
            storage_stats=storage_stats,
            vector_metrics=vector_metrics,
        )

    def analyze_vector_space(self, sample_size: int = 1_000) -> VectorSpaceMetrics | None:
        logger.info("Performing vector space analysis...")
        logger.debug(f"sampling {sample_size} embeddings")

        """Analyze vector space properties."""
        # Sample embeddings for analysis (full dataset might be too large)
        result = self._embeddings_query(limit=sample_size)
        if not result:
            return None
        embeddings = np.array([np.array(row[0]) for row in result])

        # Calculate average cosine similarity to nearest neighbor
        similarities = cosine_similarity(embeddings)
        np.fill_diagonal(similarities, -1)  # Exclude self-similarity

        # PCA analysis - variance explained
        n_samples, n_features = embeddings.shape
        pca = PCA(n_components=min(50, n_samples, n_features))
        pca.fit(embeddings)

        nearest_similarities = similarities.max(axis=1)
        variance_explained = pca.explained_variance_ratio_

        return VectorSpaceMetrics(
            avg_similarity_to_nearest=float(nearest_similarities.mean()),
            similarity_distribution={
                "mean": float(similarities[similarities > -1].mean()),
                "median": float(np.median(similarities[similarities > -1])),
                "std": float(similarities[similarities > -1].std()),
                "min": float(similarities[similarities > -1].min()),
                "max": float(similarities[similarities > -1].max()),
            },
            dimensionality_variance=variance_explained,
            total_variance_explained=float(variance_explained.sum()),
        )

    @staticmethod
    def write_report(metrics: DatabaseMetrics, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(metrics))

    def create_visualizations(self, metrics: DatabaseMetrics, output_dir: Path):
        """Generate comprehensive visualizations from database metrics."""
        output_dir.mkdir(exist_ok=True)

        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["figure.dpi"] = 300
        plt.rcParams["font.size"] = 10

        # 1. Vectorization status pie chart
        if metrics.total_transcriptions > 0:
            fig, ax = plt.subplots(figsize=(8, 6))
            vectorized = metrics.vectorized_transcriptions
            not_vectorized = metrics.total_transcriptions - vectorized

            ax.pie(
                [vectorized, not_vectorized],
                labels=["Vectorized", "Not Vectorized"],
                autopct="%1.1f%%",
                colors=["#2ecc71", "#e74c3c"],
                startangle=90,
            )
            ax.set_title("Transcription Vectorization Status")
            plt.tight_layout()
            plt.savefig(output_dir / "vectorization_status.png")
            plt.close()

        # 2. Chunk size distribution
        if metrics.chunk_size_distribution:
            fig, ax = plt.subplots(figsize=(10, 6))
            stats = metrics.chunk_size_distribution

            positions = [1, 2, 3, 4, 5]
            values = [
                stats["min"],
                stats["p25"],
                stats["median"],
                stats["p75"],
                stats["max"],
            ]
            labels = ["Min", "25%", "Median", "75%", "Max"]

            ax.bar(positions, values, tick_label=labels)
            ax.set_ylabel("Characters")
            ax.set_title("Chunk Size Distribution")
            ax.axhline(
                stats["mean"],
                color="red",
                linestyle="--",
                label=f"Mean: {stats['mean']:.0f}",
            )
            ax.legend()
            ax.grid(axis="y", alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_dir / "chunk_size_distribution.png")
            plt.close()

        if metrics.chunk_size_distribution:
            sizes = np.array([s[0] for s in self._get_chunk_sizes()])
            p99 = metrics.chunk_size_distribution["p99"]

            # Focus on main distribution (up to 99th percentile)
            main_sizes = sizes[sizes <= p99]

            fig, ax = plt.subplots(figsize=(12, 7))

            # Create histogram with appropriate bins
            n_bins = min(50, len(np.unique(main_sizes)))
            ax.hist(main_sizes, bins=n_bins, edgecolor="black", alpha=0.7, color="#3498db")

            ax.set_xlabel("Chunk Size (characters)", fontsize=12)
            ax.set_ylabel("Frequency", fontsize=12)
            ax.set_title(
                f"Chunk Size Distribution (up to 99th percentile)\n"
                f"{len(main_sizes):,} of {len(sizes):,} chunks ({len(main_sizes) / len(sizes) * 100:.1f}%)",
                fontsize=14,
                fontweight="bold",
            )

            # Key statistics as vertical lines
            stats_to_show = [
                ("median", "green", "Median"),
                ("mean", "orange", "Mean"),
                ("p95", "red", "95th"),
            ]

            for stat_key, color, label in stats_to_show:
                value = metrics.chunk_size_distribution[stat_key]
                ax.axvline(value, color=color, linestyle="--", linewidth=2, label=f"{label}: {value:.0f}")

            ax.legend(fontsize=10, loc="upper right")
            ax.grid(axis="y", alpha=0.3)

            # Add outlier info
            outlier_count = len(sizes) - len(main_sizes)
            if outlier_count > 0:
                ax.text(
                    0.98,
                    0.97,
                    f"Outliers excluded: {outlier_count:,} chunks (>{p99:.0f} chars)\n"
                    f"Max outlier: {metrics.chunk_size_distribution['max']:,.0f} chars",
                    transform=ax.transAxes,
                    verticalalignment="top",
                    horizontalalignment="right",
                    fontsize=9,
                    bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.7),
                )

            plt.tight_layout()
            plt.savefig(output_dir / "chunk_size_histogram.png", dpi=300)
            plt.close()

        # 3. Top courses by transcriptions
        if metrics.transcriptions_by_course:
            fig, ax = plt.subplots(figsize=(10, 8))
            courses, counts = zip(*metrics.transcriptions_by_course[:20], strict=False)

            y_pos = np.arange(len(courses))
            ax.barh(y_pos, counts)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(courses)
            ax.invert_yaxis()
            ax.set_xlabel("Number of Transcriptions")
            ax.set_title("Top 20 Courses by Transcription Count")
            ax.grid(axis="x", alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_dir / "top_courses_transcriptions.png")
            plt.close()

        # 4. Top courses by chunks
        if metrics.chunks_by_course:
            fig, ax = plt.subplots(figsize=(10, 8))
            courses, counts = zip(*metrics.chunks_by_course[:20], strict=False)

            y_pos = np.arange(len(courses))
            ax.barh(y_pos, counts)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(courses)
            ax.invert_yaxis()
            ax.set_xlabel("Number of Chunks")
            ax.set_title("Top 20 Courses by Chunk Count")
            ax.grid(axis="x", alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_dir / "top_courses_chunks.png")
            plt.close()

        # 5. Timing accuracy distribution
        if metrics.timing_accuracy_distribution:
            fig, ax = plt.subplots(figsize=(8, 6))
            accuracies, counts = zip(*metrics.timing_accuracy_distribution, strict=False)

            ax.bar(accuracies, counts)
            ax.set_xlabel("Timing Accuracy Type")
            ax.set_ylabel("Count")
            ax.set_title("Timing Accuracy Distribution")
            ax.grid(axis="y", alpha=0.3)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(output_dir / "timing_accuracy.png")
            plt.close()

        # 6. PCA variance explained
        if metrics.vector_metrics and metrics.vector_metrics.dimensionality_variance is not None:
            fig, ax = plt.subplots(figsize=(10, 6))
            variance = metrics.vector_metrics.dimensionality_variance

            cumsum = np.cumsum(variance)
            ax.plot(range(1, len(variance) + 1), cumsum, marker="o", markersize=3)
            ax.set_xlabel("Number of Components")
            ax.set_ylabel("Cumulative Variance Explained")
            ax.set_title("PCA: Cumulative Variance Explained")
            ax.grid(alpha=0.3)
            ax.axhline(0.95, color="red", linestyle="--", label="95% variance")
            ax.legend()
            plt.tight_layout()
            plt.savefig(output_dir / "pca_variance.png")
            plt.close()

        print(f"Visualizations saved to {output_dir}/")


@contextmanager
def get_db() -> Iterator[duckdb.DuckDBPyConnection]:
    DUCKDB_ATTACH_URL = (
        f"host={settings.DATABASE.HOST} "
        f"port={settings.DATABASE.PORT} "
        f"user={settings.DATABASE.USER} "
        f"password={settings.DATABASE.PASSWORD.get_secret_value()} "
        f"dbname={settings.DATABASE.DB}"
    )

    con = duckdb.connect()
    con.execute("INSTALL postgres")
    con.execute("LOAD postgres")

    con.execute(f"ATTACH '{DUCKDB_ATTACH_URL}' AS pg (TYPE POSTGRES, SCHEMA 'rag')")

    try:
        yield con
    finally:
        con.close()


def create_analytics_service(db: duckdb.DuckDBPyConnection) -> AnalyticsService:
    return AnalyticsService(db=db)
