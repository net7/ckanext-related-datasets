import logging

import ckan.plugins.toolkit as toolkit
from ckan.logic import validate

from ckanext.related_datasets.model import DatasetRelationship

log = logging.getLogger(__name__)


@toolkit.side_effect_free
def related_datasets_list(context, data_dict):
    """List all datasets related to a given dataset.

    :param id: the id or name of the dataset
    :returns: list of dicts with id, name, title
    """
    toolkit.check_access('related_datasets_list', context, data_dict)

    pkg_id = _get_package_id(data_dict.get('id'))
    related_ids = DatasetRelationship.get_for_dataset(pkg_id)

    from ckanext.related_datasets.helpers import get_related_datasets_direct
    return get_related_datasets_direct(pkg_id)


def related_datasets_create(context, data_dict):
    """Create a relationship between two datasets.

    :param subject_id: the id or name of the first dataset
    :param object_id: the id or name of the second dataset
    """
    toolkit.check_access('related_datasets_create', context, data_dict)

    subject_id = _get_package_id(data_dict.get('subject_id'))
    object_id = _get_package_id(data_dict.get('object_id'))

    if subject_id == object_id:
        raise toolkit.ValidationError({'object_id': ['Cannot relate a dataset to itself']})

    rel = DatasetRelationship.create(subject_id, object_id)
    if rel is None:
        return {'message': 'Relationship already exists'}

    return {'message': 'Relationship created', 'id': rel.id}


def related_datasets_delete(context, data_dict):
    """Delete a relationship between two datasets.

    :param subject_id: the id or name of the first dataset
    :param object_id: the id or name of the second dataset
    """
    toolkit.check_access('related_datasets_delete', context, data_dict)

    subject_id = _get_package_id(data_dict.get('subject_id'))
    object_id = _get_package_id(data_dict.get('object_id'))

    deleted = DatasetRelationship.delete(subject_id, object_id)
    if not deleted:
        raise toolkit.ObjectNotFound('Relationship not found')

    return {'message': 'Relationship deleted'}


def _get_package_id(id_or_name):
    """Resolve a package name to its ID via direct DB query."""
    if not id_or_name:
        raise toolkit.ValidationError({'id': ['Missing value']})
    from ckan.model import Session, Package
    pkg = Session.query(Package).filter(
        (Package.id == id_or_name) | (Package.name == id_or_name)
    ).first()
    if not pkg:
        raise toolkit.ObjectNotFound(
            'Dataset not found: {}'.format(id_or_name)
        )
    return pkg.id
