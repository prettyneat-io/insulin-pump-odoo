from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Extend product.template for insulin pump settings."""
    _inherit = 'product.template'

    is_insulin_pump_product = fields.Boolean(
        string='Insulin Pump Product',
        default=False,
        help='Check if this product is an insulin pump device'
    )
    is_rma_product = fields.Boolean(
        string='RMA Replacement Product',
        default=False,
        help='Check if this product is used for RMA replacements only'
    )


class ResConfigSettings(models.TransientModel):
    """Insulin Pumps configuration settings."""
    _inherit = 'res.config.settings'

    # Note: Many2many not supported in res.config.settings
    # Insulin pump products are identified by is_insulin_pump_product boolean on product.template
    # RMA product is identified by is_rma_product boolean on product.template
    
    insulin_pumps_return_location_id = fields.Many2one(
        'stock.location',
        string='Return Location',
        domain="[('usage', '=', 'internal')]",
        help='Location for returned devices',
        config_parameter='insulin_pumps.return_location_id',
    )
    insulin_pumps_replacement_alert_days = fields.Integer(
        string='Replacement Alert Days',
        default=30,
        help='Days before replacement date to trigger alert',
        config_parameter='insulin_pumps.replacement_alert_days',
    )
    insulin_pumps_default_allocated_quantity = fields.Integer(
        string='Default Allocated Quantity',
        default=10,
        help='Default monthly allocated quantity for consumables',
        config_parameter='insulin_pumps.default_allocated_quantity',
    )
    insulin_pumps_default_critical_threshold = fields.Integer(
        string='Default Critical Threshold',
        default=13,
        help='Default monthly critical threshold for consumables',
        config_parameter='insulin_pumps.default_critical_threshold',
    )
    insulin_pumps_enable_warnings = fields.Boolean(
        string='Enable Threshold Warnings',
        default=True,
        config_parameter='insulin_pumps.enable_threshold_warnings',
    )
    insulin_pumps_helpdesk_email = fields.Char(
        string='Helpdesk Email',
        default='tandemsupport@evercaremedical.eu',
        config_parameter='insulin_pumps.helpdesk_email',
    )

