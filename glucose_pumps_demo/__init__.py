from . import models

def post_init_hook(env):
    """Post-installation hook to enable Lots & Serial Numbers and Multi-Locations."""
    # Enable Lots & Serial Numbers and Multi-Locations for all users
    group_production_lot = env.ref('stock.group_production_lot', raise_if_not_found=False)
    group_multi_locations = env.ref('stock.group_stock_multi_locations', raise_if_not_found=False)
    group_user = env.ref('base.group_user', raise_if_not_found=False)
    
    if group_production_lot and group_user:
        group_user.write({'implied_ids': [(4, group_production_lot.id)]})
    
    if group_multi_locations and group_user:
        group_user.write({'implied_ids': [(4, group_multi_locations.id)]})
