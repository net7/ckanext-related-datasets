import ckan.plugins.toolkit as toolkit


def related_datasets_id_exists(value, context):
    """Validate that a dataset with the given ID exists."""
    if not value:
        return value
    try:
        toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': value}
        )
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid('Dataset not found: {}'.format(value))
    return value
