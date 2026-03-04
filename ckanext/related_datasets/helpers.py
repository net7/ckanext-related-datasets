import logging

import ckan.plugins.toolkit as toolkit
from ckan.model import Session, Package

from ckanext.related_datasets.model import DatasetRelationship

log = logging.getLogger(__name__)


def get_related_datasets(pkg_id):
    """Get related datasets for display in templates.
    Uses package_show with a recursion guard flag.
    """
    if not pkg_id:
        return []

    related_ids = DatasetRelationship.get_for_dataset(pkg_id)
    result = []
    for rid in related_ids:
        try:
            pkg = toolkit.get_action('package_show')(
                {'ignore_auth': True, '_related_datasets_skip': True},
                {'id': rid}
            )
            result.append({
                'id': pkg['id'],
                'name': pkg['name'],
                'title': pkg.get('title', pkg['name']),
                'notes': pkg.get('notes', ''),
            })
        except toolkit.ObjectNotFound:
            log.warning('Related dataset %s not found, skipping', rid)
    return result


def get_related_datasets_direct(pkg_id):
    """Get datasets that this dataset links TO (where pkg_id is the subject).
    Returns a list of dicts with id, name, title.
    """
    if not pkg_id:
        return []

    related_ids = DatasetRelationship.get_for_dataset_as_subject(pkg_id)
    if not related_ids:
        return []

    packages = Session.query(Package).filter(
        Package.id.in_(related_ids),
        Package.state == 'active',
    ).all()
    return [{'id': pkg.id, 'name': pkg.name,
             'title': pkg.title or pkg.name, 'notes': pkg.notes or ''}
            for pkg in packages]


def get_all_related_datasets_direct(pkg_id):
    """Get ALL related datasets (both directions) via direct DB query.
    Returns a list of dicts with id, name, title.
    """
    if not pkg_id:
        return []

    related_ids = DatasetRelationship.get_for_dataset(pkg_id)
    if not related_ids:
        return []

    packages = Session.query(Package).filter(
        Package.id.in_(related_ids),
        Package.state == 'active',
    ).all()
    return [{'id': pkg.id, 'name': pkg.name,
             'title': pkg.title or pkg.name, 'notes': pkg.notes or ''}
            for pkg in packages]


def get_related_datasets_ids(pkg_id):
    """Get just the IDs of related datasets (for form hidden inputs).
    Returns only datasets where pkg_id is the subject (user-created links).
    """
    if not pkg_id:
        return []
    return DatasetRelationship.get_for_dataset_as_subject(pkg_id)


def get_linked_from_datasets_direct(pkg_id):
    """Get datasets that link TO this dataset (where pkg_id is the object).
    Returns a list of dicts with id, name, title.
    """
    if not pkg_id:
        return []

    related_ids = DatasetRelationship.get_for_dataset_as_object(pkg_id)
    if not related_ids:
        return []

    packages = Session.query(Package).filter(
        Package.id.in_(related_ids),
        Package.state == 'active',
    ).all()
    return [{'id': pkg.id, 'name': pkg.name,
             'title': pkg.title or pkg.name, 'notes': pkg.notes or ''}
            for pkg in packages]
