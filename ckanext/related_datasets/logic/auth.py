import ckan.plugins.toolkit as toolkit


def related_datasets_list(context, data_dict):
    """Anyone can list related datasets."""
    return {'success': True}


def related_datasets_create(context, data_dict):
    """Only users who can edit the subject dataset can create relationships."""
    user = context.get('user')
    subject_id = data_dict.get('subject_id')
    if not subject_id:
        return {'success': False, 'msg': 'subject_id is required'}
    try:
        toolkit.check_access('package_update', context, {'id': subject_id})
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False, 'msg': 'Not authorized to edit this dataset'}


def related_datasets_delete(context, data_dict):
    """Only users who can edit the subject dataset can delete relationships."""
    user = context.get('user')
    subject_id = data_dict.get('subject_id')
    if not subject_id:
        return {'success': False, 'msg': 'subject_id is required'}
    try:
        toolkit.check_access('package_update', context, {'id': subject_id})
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False, 'msg': 'Not authorized to edit this dataset'}
