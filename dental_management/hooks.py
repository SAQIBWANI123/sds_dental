def post_init_hook(env):
    """Give the administrator access to the dental menus right after install."""
    manager = env.ref('dental_management.group_dental_manager', raise_if_not_found=False)
    if not manager:
        return
    field = 'group_ids' if 'group_ids' in env['res.users']._fields else 'groups_id'
    for xmlid in ('base.user_admin', 'base.user_root'):
        user = env.ref(xmlid, raise_if_not_found=False)
        if user:
            user.write({field: [(4, manager.id)]})
