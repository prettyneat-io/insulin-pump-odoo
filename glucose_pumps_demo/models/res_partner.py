from odoo import api, fields, models


class ResPartner(models.Model):
    """Extend res.partner to add patient-specific fields."""
    _inherit = 'res.partner'

    is_patient = fields.Boolean(
        string='Is Patient',
        default=False,
        help='Check if this contact is a glucose pump patient'
    )
    
    # Patient Information fields
    patient_internal_id = fields.Char(
        string='Patient Internal ID',
        readonly=True,
        copy=False,
        help='Auto-generated patient ID in format YYYY-NNN'
    )
    patient_date_of_birth = fields.Date(
        string='Date of Birth'
    )
    patient_id_number = fields.Char(
        string='ID Number',
        help='National ID or passport number'
    )
    patient_phone = fields.Char(
        string='Patient Phone'
    )
    patient_locality = fields.Char(
        string='Locality',
        help='Patient locality (e.g., Mosta)'
    )
    
    # Linked devices
    primary_device_id = fields.Many2one(
        'stock.lot',
        string='Current Primary Device',
        domain="[('is_glucose_pump', '=', True), ('pump_state', '=', 'available')]"
    )
    holiday_pump_id = fields.Many2one(
        'stock.lot',
        string='Current Holiday Pump',
        domain="[('is_glucose_pump', '=', True), ('pump_state', '=', 'available')]"
    )
    holiday_pump_return_date = fields.Date(
        string='Holiday Pump Return Date'
    )
    
    # Training location
    training_location_id = fields.Many2one(
        'glucose.training.location',
        string='Training Location'
    )
    
    # Assignment history
    assignment_log_ids = fields.One2many(
        'glucose.assignment.log',
        'patient_id',
        string='Assignment History'
    )
    
    # Consumables
    consumables_allocation_ids = fields.One2many(
        'glucose.consumables.allocation',
        'patient_id',
        string='Consumables Allocations'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_patient') and not vals.get('patient_internal_id'):
                vals['patient_internal_id'] = self._generate_patient_internal_id()
        return super().create(vals_list)

    def _generate_patient_internal_id(self):
        """Generate patient internal ID in format YYYY-NNN."""
        current_year = fields.Date.today().year
        
        # Find the highest sequence number for this year
        last_patient = self.search([
            ('is_patient', '=', True),
            ('patient_internal_id', 'like', f'{current_year}-%')
        ], order='patient_internal_id desc', limit=1)
        
        if last_patient and last_patient.patient_internal_id:
            try:
                last_seq = int(last_patient.patient_internal_id.split('-')[1])
            except (ValueError, IndexError):
                last_seq = 0
        else:
            last_seq = 0
        
        new_seq = last_seq + 1
        return f'{current_year}-{new_seq:03d}'

    @api.constrains('is_patient', 'is_company')
    def _check_patient_not_company(self):
        """Only individuals (not companies) can be patients."""
        for partner in self:
            if partner.is_patient and partner.is_company:
                raise models.ValidationError(
                    "Only individuals (not companies) can be marked as patients."
                )
