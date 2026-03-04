import datetime
import logging
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, UniqueConstraint, or_
from sqlalchemy.orm import relationship

from ckan.model import Session, Package, meta

log = logging.getLogger(__name__)

dataset_relationship_table = Table(
    'dataset_relationship_custom',
    meta.metadata,
    Column('id', String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column('subject_id', String(36), ForeignKey('package.id', ondelete='CASCADE'), nullable=False),
    Column('object_id', String(36), ForeignKey('package.id', ondelete='CASCADE'), nullable=False),
    Column('created', DateTime, default=datetime.datetime.utcnow),
    UniqueConstraint('subject_id', 'object_id', name='uq_dataset_relationship_custom'),
)


class DatasetRelationship:
    def __init__(self, subject_id, object_id):
        self.id = str(uuid.uuid4())
        self.subject_id = subject_id
        self.object_id = object_id
        self.created = datetime.datetime.utcnow()

    @classmethod
    def create(cls, subject_id, object_id):
        # Normalize order to avoid duplicates in both directions
        if cls.exists(subject_id, object_id):
            return None
        rel = cls(subject_id, object_id)
        Session.add(rel)
        Session.commit()
        return rel

    @classmethod
    def exists(cls, subject_id, object_id):
        return Session.query(cls).filter(
            or_(
                (cls.subject_id == subject_id) & (cls.object_id == object_id),
                (cls.subject_id == object_id) & (cls.object_id == subject_id),
            )
        ).first() is not None

    @classmethod
    def delete(cls, subject_id, object_id):
        rel = Session.query(cls).filter(
            or_(
                (cls.subject_id == subject_id) & (cls.object_id == object_id),
                (cls.subject_id == object_id) & (cls.object_id == subject_id),
            )
        ).first()
        if rel:
            Session.delete(rel)
            Session.commit()
            return True
        return False

    @classmethod
    def get_for_dataset(cls, dataset_id):
        """Get all related dataset IDs for a given dataset (both directions)."""
        rows = Session.query(cls).filter(
            or_(
                cls.subject_id == dataset_id,
                cls.object_id == dataset_id,
            )
        ).all()
        related_ids = []
        for row in rows:
            if row.subject_id == dataset_id:
                related_ids.append(row.object_id)
            else:
                related_ids.append(row.subject_id)
        return related_ids

    @classmethod
    def get_for_dataset_as_subject(cls, dataset_id):
        """Get dataset IDs where this dataset is the subject (created the link)."""
        rows = Session.query(cls).filter(
            cls.subject_id == dataset_id
        ).all()
        return [row.object_id for row in rows]

    @classmethod
    def get_for_dataset_as_object(cls, dataset_id):
        """Get dataset IDs where this dataset is the object (linked TO by another)."""
        rows = Session.query(cls).filter(
            cls.object_id == dataset_id
        ).all()
        return [row.subject_id for row in rows]

    @classmethod
    def set_for_dataset(cls, dataset_id, related_ids):
        """Sync the related datasets for a given dataset.
        Only manages relationships where dataset_id is the subject.
        Adds missing and removes stale relationships.
        """
        current_ids = set(cls.get_for_dataset_as_subject(dataset_id))
        new_ids = set(related_ids)

        to_add = new_ids - current_ids
        to_remove = current_ids - new_ids

        for rid in to_add:
            rel = cls(dataset_id, rid)
            Session.add(rel)

        for rid in to_remove:
            rel = Session.query(cls).filter(
                (cls.subject_id == dataset_id) & (cls.object_id == rid)
            ).first()
            if rel:
                Session.delete(rel)

        Session.commit()


def init_tables():
    if not dataset_relationship_table.exists():
        dataset_relationship_table.create()
        log.info('dataset_relationship_custom table created')
    else:
        log.info('dataset_relationship_custom table already exists')


# Map the class to the table
from sqlalchemy.orm import mapper as sa_mapper
try:
    sa_mapper(DatasetRelationship, dataset_relationship_table)
except Exception:
    # Already mapped
    pass
