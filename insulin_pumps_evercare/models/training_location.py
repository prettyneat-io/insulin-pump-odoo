from odoo import fields, models


class TrainingLocation(models.Model):
    """Training locations for insulin pump patients."""
    _name = 'insulin.training.location'
    _description = 'Insulin Pump Training Location'

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

