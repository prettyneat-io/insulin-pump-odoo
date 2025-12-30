from odoo import fields, models


class TrainingLocation(models.Model):
    """Training locations for glucose pump patients."""
    _name = 'glucose.training.location'
    _description = 'Glucose Pump Training Location'

    name = fields.Char(
        string='Name',
        required=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Patients trained at this location
    patient_ids = fields.One2many(
        'res.partner',
        'training_location_id',
        string='Patients',
        domain="[('is_patient', '=', True)]"
    )
