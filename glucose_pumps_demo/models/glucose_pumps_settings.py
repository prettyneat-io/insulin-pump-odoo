from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Extend product.template for glucose pump settings."""
    _inherit = 'product.template'

    is_glucose_pump_product = fields.Boolean(
        string='Glucose Pump Product',
        default=False,
        help='Check if this product is a glucose pump device'
    )
    is_rma_product = fields.Boolean(
        string='RMA Replacement Product',
        default=False,
        help='Check if this product is used for RMA replacements only'
    )


class ResConfigSettings(models.TransientModel):
    """Glucose Pumps configuration settings."""
    _inherit = 'res.config.settings'

    # Note: Many2many not supported in res.config.settings
    # Glucose pump products are identified by is_glucose_pump_product boolean on product.template
    # RMA product is identified by is_rma_product boolean on product.template
    
    glucose_pumps_return_location_id = fields.Many2one(
        'stock.location',
        string='Return Location',
        domain="[('usage', '=', 'internal')]",
        help='Location for returned devices',
        config_parameter='glucose_pumps.return_location_id',
    )
    glucose_pumps_replacement_alert_days = fields.Integer(
        string='Replacement Alert Days',
        default=30,
        help='Days before replacement date to trigger alert',
        config_parameter='glucose_pumps.replacement_alert_days',
    )
    glucose_pumps_default_threshold = fields.Integer(
        string='Default Consumables Threshold',
        default=13,
        help='Default monthly consumables threshold',
        config_parameter='glucose_pumps.default_consumables_threshold',
    )
    glucose_pumps_enable_warnings = fields.Boolean(
        string='Enable Threshold Warnings',
        default=True,
        config_parameter='glucose_pumps.enable_threshold_warnings',
    )
    glucose_pumps_helpdesk_email = fields.Char(
        string='Helpdesk Email',
        default='tandemsupport@evercaremedical.eu',
        config_parameter='glucose_pumps.helpdesk_email',
    )
