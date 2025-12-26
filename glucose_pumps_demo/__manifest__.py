{
    'name': 'Glucose Pumps Demo Data',
    'version': '18.0.1.0.0',
    'category': 'Medical',
    'summary': 'Demo data for Glucose Pumps addon development',
    'description': """
        This module provides demo data for developing and testing the Glucose Pumps addon.
        
        Includes:
        - Demo glucose pump products
        - RMA replacement device product
        - Stock locations for returns
        - Equipment/lot serial numbers
        - Demo patients with internal IDs
        - Training locations
        - Patient Administrators group with demo users
        - Consumables allocation records
    """,
    'author': 'PrettyNeat Software',
    'website': 'https://www.prettyneat.io',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'stock',
        'product',
        'mail',
        'website',
    ],
    'data': [
        'security/glucose_pumps_security.xml',
        'security/ir.model.access.csv',
        'data/res_config_settings_data.xml',
        'views/res_partner_views.xml',
        'views/stock_lot_views.xml',
        'views/replace_device_wizard_views.xml',
        'views/glucose_pumps_views.xml',
        'data/ir_sequence_data.xml',
        'data/training_location_data.xml',
        'data/product_data.xml',
        'data/stock_location_data.xml',
        'data/stock_lot_data.xml',
        'data/stock_quant_data.xml',
        'data/res_partner_data.xml',
        'data/assignment_log_data.xml',
        'data/consumables_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
