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
    installation_date = fields.Date(
        string='Installation Date',
        default=fields.Date.context_today,
        help='Date when the primary device was installed'
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
        records = super().create(vals_list)
        # Handle device assignments for newly created patients
        for record in records:
            if record.is_patient:
                if record.primary_device_id:
                    record._assign_device(record.primary_device_id, 'primary')
                if record.holiday_pump_id:
                    record._assign_device(record.holiday_pump_id, 'holiday_pump')
        return records

    def write(self, vals):
        # Skip device sync if called from stock.lot to prevent recursion
        if self.env.context.get('skip_device_sync'):
            return super().write(vals)
        
        # Track device changes for patients
        if 'primary_device_id' in vals or 'holiday_pump_id' in vals:
            for record in self:
                if not record.is_patient:
                    continue
                
                # Handle primary device change
                if 'primary_device_id' in vals:
                    old_device = record.primary_device_id
                    new_device_id = vals.get('primary_device_id')
                    
                    # Unassign old device if there was one
                    if old_device and old_device.id != new_device_id:
                        record._unassign_device(old_device, 'primary')
                    
                    # Assign new device if provided
                    if new_device_id and (not old_device or old_device.id != new_device_id):
                        new_device = self.env['stock.lot'].browse(new_device_id)
                        # We need to call this after super().write()
                
                # Handle holiday pump change
                if 'holiday_pump_id' in vals:
                    old_device = record.holiday_pump_id
                    new_device_id = vals.get('holiday_pump_id')
                    
                    # Unassign old device if there was one
                    if old_device and old_device.id != new_device_id:
                        record._unassign_device(old_device, 'holiday_pump')
        
        result = super().write(vals)
        
        # Now handle new device assignments after the write
        if 'primary_device_id' in vals or 'holiday_pump_id' in vals:
            for record in self:
                if not record.is_patient:
                    continue
                
                if 'primary_device_id' in vals and record.primary_device_id:
                    # Check if this device already has an active assignment log for this patient
                    existing_log = self.env['glucose.assignment.log'].search([
                        ('patient_id', '=', record.id),
                        ('equipment_id', '=', record.primary_device_id.id),
                        ('assignment_type', '=', 'primary'),
                        ('replacement_date', '=', False),
                    ], limit=1)
                    if not existing_log:
                        record._assign_device(record.primary_device_id, 'primary')
                
                if 'holiday_pump_id' in vals and record.holiday_pump_id:
                    existing_log = self.env['glucose.assignment.log'].search([
                        ('patient_id', '=', record.id),
                        ('equipment_id', '=', record.holiday_pump_id.id),
                        ('assignment_type', '=', 'holiday_pump'),
                        ('replacement_date', '=', False),
                    ], limit=1)
                    if not existing_log:
                        record._assign_device(record.holiday_pump_id, 'holiday_pump')
        
        return result

    def _assign_device(self, device, assignment_type):
        """Assign a device to this patient and create assignment log."""
        self.ensure_one()
        
        # Update device state
        device.write({
            'pump_state': 'assigned',
            'assigned_patient_id': self.id,
            'assignment_type': assignment_type,
            'installation_date': self.installation_date or fields.Date.today(),
        })
        
        # Create assignment log
        self.env['glucose.assignment.log'].create({
            'patient_id': self.id,
            'equipment_id': device.id,
            'assignment_type': assignment_type,
            'installation_date': self.installation_date or fields.Date.today(),
        })

    def _unassign_device(self, device, assignment_type):
        """Unassign a device from this patient."""
        self.ensure_one()
        
        # Set replacement date on assignment log
        log = self.env['glucose.assignment.log'].search([
            ('patient_id', '=', self.id),
            ('equipment_id', '=', device.id),
            ('assignment_type', '=', assignment_type),
            ('replacement_date', '=', False),
        ], limit=1)
        if log:
            log.replacement_date = fields.Date.today()
        
        # Update device state
        device.write({
            'pump_state': 'available',
            'assigned_patient_id': False,
            'assignment_type': False,
        })

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

    @api.constrains('holiday_pump_id', 'holiday_pump_return_date')
    def _check_holiday_pump_return_date(self):
        """Holiday pump return date is mandatory when a holiday pump is assigned."""
        for partner in self:
            if partner.holiday_pump_id and not partner.holiday_pump_return_date:
                raise models.ValidationError(
                    "Holiday Pump Return Date is mandatory when a holiday pump is assigned."
                )

    @api.constrains('primary_device_id', 'holiday_pump_id')
    def _check_rma_device_assignment(self):
        """Prevent direct assignment of RMA devices to patients.
        
        RMA devices can only be assigned through the Replace Device workflow.
        """
        # Skip if called from the replace device wizard context
        if self.env.context.get('allow_rma_assignment') or self.env.context.get('skip_device_sync'):
            return
        
        for partner in self:
            if not partner.is_patient:
                continue
            
            # Check primary device
            if partner.primary_device_id and partner.primary_device_id.is_rma_device:
                # Check if this device already has assignment logs (meaning it was properly assigned via replacement)
                existing_logs = self.env['glucose.assignment.log'].search([
                    ('equipment_id', '=', partner.primary_device_id.id),
                    ('patient_id', '=', partner.id),
                ])
                if not existing_logs:
                    raise models.ValidationError(
                        f"RMA device '{partner.primary_device_id.name}' cannot be assigned as an initial primary device. "
                        "RMA devices can only be used as replacements for malfunctioning primary devices "
                        "through the 'Replace Device' workflow."
                    )
            
            # RMA devices can never be assigned as holiday pumps
            if partner.holiday_pump_id and partner.holiday_pump_id.is_rma_device:
                raise models.ValidationError(
                    f"RMA device '{partner.holiday_pump_id.name}' cannot be assigned as a holiday pump. "
                    "RMA devices can only be used as replacements for malfunctioning primary devices."
                )
