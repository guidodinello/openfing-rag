from collections.abc import Iterable
from typing import Any, Generic, Protocol, TypeVar

from sqlalchemy import ColumnElement, and_, or_, select
from sqlalchemy.orm import Session


class HasId(Protocol):
    id: ColumnElement[int]


T = TypeVar("T", bound=HasId)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: type[T], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def get_by_ids(self, ids: list[int]) -> dict[int, T]:
        return {
            record.id: record
            for record in self.db.execute(
                select(self.model).where(self.model.id.in_(ids)),
            )
            .scalars()
            .all()
        }

    def get_by(self, **criteria) -> T | None:
        conditions = [getattr(self.model, key) == value for key, value in criteria.items()]
        return self.db.execute(
            select(self.model).where(*conditions),
        ).scalar_one_or_none()

    def get_all(self, limit: int | None = 100, offset: int = 0) -> list[T]:
        return self.db.execute(select(self.model).limit(limit).offset(offset)).scalars().all()

    def create(self, **data) -> T:
        instance = self.model(**data)
        self.db.add(instance)
        self.db.flush()
        return instance

    def bulk_create(self, records_data: list[dict[str, Any]]) -> list[T]:
        instances = [self.model(**data) for data in records_data]
        self.db.add_all(instances)
        self.db.flush()
        return instances

    def delete(self, instance: T) -> None:
        self.db.delete(instance)
        self.db.flush()

    def update_or_create(self, defaults: dict[str, Any], **criteria) -> tuple[T, bool]:
        """
        Update existing record or create new one.
        Returns (instance, created_flag)
        """
        if not (instance := self.get_by(**criteria)):
            instance_data = {**criteria, **defaults}
            return self.create(**instance_data), True

        for key, value in defaults.items():
            if hasattr(instance, key):
                # Handle metadata fields specially
                if key.endswith("_metadata") and hasattr(instance, key):
                    existing_metadata = getattr(instance, key) or {}
                    new_metadata = value or {}
                    setattr(instance, key, {**existing_metadata, **new_metadata})
                else:
                    setattr(instance, key, value)
        self.db.flush()
        return instance, False

    def bulk_update_or_create(
        self,
        records_data: list[dict[str, Any]],
        unique_fields: list[str],
    ) -> dict[str, int]:
        if not records_data:
            return {"created": 0, "updated": 0}

        return self._process_bulk_records(
            records_data,
            unique_fields,
            self._fetch_existing_records(records_data, unique_fields),
        )

    def _extract_unique_combinations(
        self,
        records_data: list[dict[str, Any]],
        unique_fields: list[str],
    ) -> list[tuple]:
        """Extract unique field combinations from records data."""
        return [tuple(record.get(field) for field in unique_fields) for record in records_data]

    def _build_lookup_conditions(
        self,
        unique_combinations: list[tuple],
        unique_fields: list[str],
    ) -> list:
        """Build SQLAlchemy conditions for fetching existing records."""
        conditions = []
        for unique_combo in unique_combinations:
            record_conditions = [
                getattr(self.model, field) == value
                for _, (field, value) in enumerate(
                    zip(unique_fields, unique_combo, strict=False),
                )
                if value is not None
            ]
            if record_conditions:
                conditions.append(
                    (and_(*record_conditions) if len(record_conditions) > 1 else record_conditions[0]),
                )
        return conditions

    def _fetch_existing_records(
        self,
        records_data: list[dict[str, Any]],
        unique_fields: list[str],
    ) -> dict[tuple, T]:
        """Fetch all existing records that match the unique field combinations."""
        conditions = self._build_lookup_conditions(
            self._extract_unique_combinations(records_data, unique_fields),
            unique_fields,
        )

        if not conditions:
            return {}

        query = select(self.model).where(or_(*conditions))
        results = self.db.execute(query).scalars().all()

        # Create lookup dict: (field1_value, field2_value, ...) -> record
        return {tuple(getattr(record, field) for field in unique_fields): record for record in results}

    def _update_existing_record(
        self,
        record: T,
        record_data: dict[str, Any],
        unique_fields: list[str],
    ) -> None:
        """Update an existing record with new data."""
        for field, value in record_data.items():
            if field not in unique_fields and hasattr(record, field):
                if field.endswith("_metadata") and getattr(record, field):
                    existing_metadata = getattr(record, field) or {}
                    new_metadata = value or {}
                    setattr(record, field, {**existing_metadata, **new_metadata})
                else:
                    setattr(record, field, value)

    def _process_bulk_records(
        self,
        records_data: Iterable[dict[str, Any]],
        unique_fields: list[str],
        existing_records: dict[tuple, T],
    ) -> dict[str, int]:
        """Process all records for bulk update or create."""
        created_count, updated_count = 0, 0
        new_records = []

        for record_data in records_data:
            key = tuple(record_data.get(field) for field in unique_fields)

            if key in existing_records:
                self._update_existing_record(
                    existing_records[key],
                    record_data,
                    unique_fields,
                )
                updated_count += 1
            else:
                new_records.append(self.model(**record_data))
                created_count += 1

        if new_records:
            self.db.add_all(new_records)
        self.db.flush()

        return {"created": created_count, "updated": updated_count}
