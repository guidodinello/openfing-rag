# app/database/seeders/base.py
from typing import Any, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute


class BaseSeeder:
    """Base seeder class for populating test data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self):
        """Override this method to implement seeding logic."""
        raise NotImplementedError

    async def get_random_records(
        self,
        model: type,
        columns: None
        | (InstrumentedAttribute | Sequence[InstrumentedAttribute]) = None,
        limit: None | int = None,
        filters: None | list = None,
        raise_if_empty: bool = True,
    ) -> list[Any] | list[tuple]:
        """
        Get random records from a table with flexible column selection.

        Args:
            model: SQLAlchemy model class
            columns: Single column or sequence of columns to select (defaults to id if None)
            limit: Optional number of records to return
            filters: Optional list of filter conditions
            raise_if_empty: Whether to raise an error if no records found

        Returns:
            List of values if single column selected, List of tuples if multiple columns
        """
        # Default to id column if none specified
        if columns is None:
            columns = [model.id]
        elif not isinstance(columns, (list, tuple)):
            columns = [columns]

        # Create base query
        query: Select = select(*columns) if len(columns) > 1 else select(columns[0])

        # Add filters if any
        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)

        # Add random ordering and limit
        query = query.order_by(func.random())
        if limit:
            query = query.limit(limit)

        # Execute query
        result = await self.db.execute(query)

        # Handle results based on whether single or multiple columns
        if len(columns) == 1:
            results = result.scalars().all()
        else:
            results = result.all()

        # Handle empty results
        if not results and raise_if_empty:
            raise ValueError(
                f"No records found for {model.__name__}. Please seed it first."
            )

        return results

    async def get_related_records(
        self,
        model: type,
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
        # Convert single relation to list for consistent handling
        relation_columns = [relations] if not isinstance(relations, list) else relations

        # Create query with all requested columns
        columns = [model.id] + relation_columns
        return await self.get_random_records(
            model,
            columns=columns,
            limit=limit,
            filters=filters,
            raise_if_empty=raise_if_empty,
        )
