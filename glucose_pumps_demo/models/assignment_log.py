from odoo import fields, models


class AssignmentLog(models.Model):
    """Log of device assignments to patients."""
    _name = 'glucose.assignment.log'
    _description = 'Glucose Pump Assignment Log'
    _order = 'installation_date desc'

    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        required=True,
        domain="[('is_patient', '=', True)]",
        ondelete='cascade'
    )
    equipment_id = fields.Many2one(
        'stock.lot',
        string='Equipment',
        required=True,
        ondelete='cascade'
    )
    assignment_type = fields.Selection([
        ('primary', 'Primary'),
        ('holiday_pump', 'Holiday Pump'),
    ], string='Assignment Type', required=True)
    
    installation_date = fields.Date(
        string='Installation Date',
        required=True,
        default=fields.Date.today
    )
    replacement_date = fields.Date(
        string='Replacement Date',
        help='Date when this device was replaced'
    )
    
    # Computed fields for convenience
    patient_internal_id = fields.Char(
        related='patient_id.patient_internal_id',
        string='Patient Internal ID',
        store=True
    )
    equipment_serial = fields.Char(
        related='equipment_id.name',
        string='Equipment SN',
        store=True
    )
