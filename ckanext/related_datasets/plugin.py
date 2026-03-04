import json
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.related_datasets import helpers
from ckanext.related_datasets.logic import action, auth
from ckanext.related_datasets.model import DatasetRelationship, init_tables

log = logging.getLogger(__name__)


class RelatedDatasetsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_resource('fanstatic', 'ckanext-related-datasets')
        init_tables()

    # IActions
    def get_actions(self):
        return {
            'related_datasets_list': action.related_datasets_list,
            'related_datasets_create': action.related_datasets_create,
            'related_datasets_delete': action.related_datasets_delete,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'related_datasets_list': auth.related_datasets_list,
            'related_datasets_create': auth.related_datasets_create,
            'related_datasets_delete': auth.related_datasets_delete,
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_related_datasets': helpers.get_related_datasets,
            'get_related_datasets_direct': helpers.get_related_datasets_direct,
            'get_all_related_datasets_direct': helpers.get_all_related_datasets_direct,
            'get_linked_from_datasets_direct': helpers.get_linked_from_datasets_direct,
            'get_related_datasets_ids': helpers.get_related_datasets_ids,
        }

    # IClick
    def get_commands(self):
        import click

        @click.group()
        def related_datasets():
            """Related datasets management commands."""
            pass

        @related_datasets.command()
        def init_db():
            """Initialize the dataset_relationship_custom table."""
            init_tables()
            click.echo('Table initialized.')

        return [related_datasets]

    # IPackageController
    def after_dataset_create(self, context, pkg_dict):
        self._sync_related_datasets(context, pkg_dict)
        return pkg_dict

    def after_dataset_update(self, context, pkg_dict):
        self._sync_related_datasets(context, pkg_dict)
        return pkg_dict

    def after_dataset_show(self, context, pkg_dict):
        # Skip during internal operations (validation, indexing, etc.)
        if context.get('_related_datasets_skip'):
            return pkg_dict

        # Only inject related datasets data for API/template rendering,
        # not during internal package_show calls (e.g. within package_update)
        if context.get('for_update') or context.get('for_indexing'):
            return pkg_dict

        pkg_id = pkg_dict.get('id')
        if pkg_id:
            pkg_dict['related_datasets'] = helpers.get_related_datasets_direct(pkg_id)
            pkg_dict['linked_from_datasets'] = helpers.get_linked_from_datasets_direct(pkg_id)

        return pkg_dict

    def _sync_related_datasets(self, context, pkg_dict):
        """Process related_datasets_ids from form submission."""
        # The form submits related_datasets_ids as a comma-separated string
        related_ids_str = None

        # Check in the raw data from the form
        try:
            from ckan.common import request
            if request and hasattr(request, 'form'):
                related_ids_str = request.form.get('related_datasets_ids', '')
        except Exception:
            pass

        if related_ids_str is None:
            # Try from pkg_dict extras
            related_ids_str = pkg_dict.get('related_datasets_ids', '')

        if related_ids_str is not None:
            related_ids = [
                rid.strip() for rid in related_ids_str.split(',')
                if rid.strip()
            ]
            DatasetRelationship.set_for_dataset(pkg_dict['id'], related_ids)
