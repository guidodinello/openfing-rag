from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from shared.database.models.base import Base

ModelType = TypeVar("ModelType", bound="Base")


class BaseSeeder(ABC):
    """Base seeder class for populating test data using repository pattern."""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def run(self) -> None:
        """Override this method to implement seeding logic."""
        raise NotImplementedError

    def get_random_records(
        self,
        model: type[ModelType],
        columns: None | (InstrumentedAttribute | Sequence[InstrumentedAttribute]) = None,
        limit: None | int = None,
        filters: None | list = None,
        raise_if_empty: bool = True,
    ) -> list[Any] | list[tuple]:
        """
        Get random records from a table with flexible column selection.

        Args:
            model: SQLAlchemy model class
            columns: Single column or sequence of columns to select
            limit: Optional number of records to return
            filters: Optional list of filter conditions
            raise_if_empty: Whether to raise an error if no records found

        Returns:
            List of values if single column selected, List of tuples if multiple columns
        """
        if columns is None:
            columns = [model.id]
        elif not isinstance(columns, (list, tuple)):
            columns = [columns]

        query: Select = select(*columns) if len(columns) > 1 else select(columns[0])
        query = query.select_from(model)

        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)

        query = query.order_by(func.random())
        if limit:
            query = query.limit(limit)

        result = self.db.execute(query)

        if len(columns) == 1:
            results = result.scalars().all()
        else:
            results = result.all()

        if not results and raise_if_empty:
            raise ValueError(
                f"No records found for {model.__name__}. Please seed it first.",
            )

        return results

    def get_related_records(
        self,
        model: type[ModelType],
        relations: InstrumentedAttribute | list[InstrumentedAttribute],
        limit: None | int = None,
        filters: None | list = None,
        raise_if_empty: bool = True,
    ) -> list[tuple]:
        """
        Get random records with their related columns.

        Args:
            model: SQLAlchemy model class
            relations: Single column or list of related columns to fetch
            limit: Optional number of records to return
            filters: Optional list of filter conditions
            raise_if_empty: Whether to raise an error if no records found

        Returns:
            List of tuples containing (id, relation1, relation2, ...)
        """
        relation_columns = [relations] if not isinstance(relations, list) else relations

        columns = [model.id] + relation_columns
        return self.get_random_records(
            model,
            columns=columns,
            limit=limit,
            filters=filters,
            raise_if_empty=raise_if_empty,
        )
