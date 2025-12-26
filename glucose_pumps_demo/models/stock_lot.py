from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    """Extend stock.lot to add glucose pump equipment fields."""
    _inherit = 'stock.lot'

    is_glucose_pump = fields.Boolean(
        string='Is Glucose Pump',
        compute='_compute_is_glucose_pump',
        store=True
    )
    
    pump_state = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('scrapped', 'Scrapped'),
    ], string='Pump State', default='available', tracking=True)
    
    # Link to patient
    assigned_patient_id = fields.Many2one(
        'res.partner',
        string='Assigned Patient',
        domain="[('is_patient', '=', True)]"
    )
    
    assignment_type = fields.Selection([
        ('primary', 'Primary'),
        ('holiday_pump', 'Holiday Pump'),
    ], string='Assignment Type')
    
    installation_date = fields.Date(string='Installation Date')
    
    # Related patient fields for list view
    patient_internal_id = fields.Char(
        related='assigned_patient_id.patient_internal_id',
        string='Patient Internal ID',
        store=True
    )
    
    # Assignment history for this device
    assignment_log_ids = fields.One2many(
        'glucose.assignment.log',
        'equipment_id',
        string='Assignment History'
    )

    is_rma_device = fields.Boolean(
        string='Is RMA Device',
        compute='_compute_is_rma_device',
        store=True,
        help='Indicates if this device is an RMA replacement device'
    )

    def write(self, vals):
        """Handle assignment changes when editing from the Equipment form."""
        # Track patient assignment changes
        if 'assigned_patient_id' in vals:
            for record in self:
                if not record.is_glucose_pump:
                    continue
                
                old_patient = record.assigned_patient_id
                new_patient_id = vals.get('assigned_patient_id')
                new_assignment_type = vals.get('assignment_type', record.assignment_type or 'primary')
                
                # Unassign from old patient if there was one
                if old_patient and old_patient.id != new_patient_id:
                    # Set replacement date on old assignment log
                    old_log = self.env['glucose.assignment.log'].search([
                        ('patient_id', '=', old_patient.id),
                        ('equipment_id', '=', record.id),
                        ('replacement_date', '=', False),
                    ], limit=1)
                    if old_log:
                        old_log.replacement_date = fields.Date.today()
                    
                    # Unlink from patient's device fields
                    if record.assignment_type == 'primary' and old_patient.primary_device_id.id == record.id:
                        old_patient.with_context(skip_device_sync=True).primary_device_id = False
                    elif record.assignment_type == 'holiday_pump' and old_patient.holiday_pump_id.id == record.id:
                        old_patient.with_context(skip_device_sync=True).holiday_pump_id = False
        
        result = super().write(vals)
        
        # Handle new patient assignment after the write
        if 'assigned_patient_id' in vals:
            for record in self:
                if not record.is_glucose_pump:
                    continue
                
                if record.assigned_patient_id:
                    new_patient = record.assigned_patient_id
                    assignment_type = record.assignment_type or 'primary'
                    
                    # Check if assignment log already exists
                    existing_log = self.env['glucose.assignment.log'].search([
                        ('patient_id', '=', new_patient.id),
                        ('equipment_id', '=', record.id),
                        ('assignment_type', '=', assignment_type),
                        ('replacement_date', '=', False),
                    ], limit=1)
                    
                    if not existing_log:
                        # Create new assignment log
                        installation_date = record.installation_date or new_patient.installation_date or fields.Date.today()
                        self.env['glucose.assignment.log'].create({
                            'patient_id': new_patient.id,
                            'equipment_id': record.id,
                            'assignment_type': assignment_type,
                            'installation_date': installation_date,
                        })
                    
                    # Update patient's device fields (with context to prevent recursion)
                    if assignment_type == 'primary' and new_patient.primary_device_id.id != record.id:
                        new_patient.with_context(skip_device_sync=True).primary_device_id = record.id
                    elif assignment_type == 'holiday_pump' and new_patient.holiday_pump_id.id != record.id:
                        new_patient.with_context(skip_device_sync=True).holiday_pump_id = record.id
                    
                    # Set pump state to assigned if not already
                    if record.pump_state != 'assigned':
                        record.with_context(skip_assignment_sync=True).pump_state = 'assigned'
        
        return result

    def action_unassign_device(self):
        """Unassign the device from the patient."""
        for lot in self:
            if lot.pump_state != 'assigned' or not lot.assigned_patient_id:
                continue
            
            patient = lot.assigned_patient_id
            assignment_type = lot.assignment_type
            sn = lot.name
            patient_id = patient.patient_internal_id

            # 1. Unlink from patient
            if assignment_type == 'primary':
                patient.primary_device_id = False
            elif assignment_type == 'holiday_pump':
                patient.holiday_pump_id = False

            # 2. Transfer back to return location (Logic to be implemented or simplified for now)
            # For now, we just set the state. The spec mentions "Transfer back to return location".
            # This usually involves creating a stock.picking or stock.move.
            # I'll check if there's a return location configured.
            
            # 3. Leave notes in chatter
            patient_msg = f"Device SN {sn} unassigned." if assignment_type == 'primary' else f"Holiday Pump SN {sn} unassigned."
            patient.message_post(body=patient_msg)
            
            lot_msg = f"Patient ID {patient_id} unassigned" if assignment_type == 'primary' else f"Patient ID {patient_id} unassigned (holiday pump)"
            lot.message_post(body=lot_msg)

            # 4. Set equipment State to 'available'
            lot.write({
                'pump_state': 'available',
                'assigned_patient_id': False,
                'assignment_type': False,
            })

    def action_scrap_device(self):
        """Scrap the device."""
        for lot in self:
            patient = lot.assigned_patient_id
            sn = lot.name

            # 1. Unlink from patient
            if patient:
                if lot.assignment_type == 'primary':
                    patient.primary_device_id = False
                elif lot.assignment_type == 'holiday_pump':
                    patient.holiday_pump_id = False
                
                # 3. Leave note in patient
                patient.message_post(body=f"Device SN {sn} scrapped")

            # 2. Move equipment to Scrap location (Logic to be implemented)
            
            # 4. Set equipment State to 'scrapped'
            lot.write({
                'pump_state': 'scrapped',
                'assigned_patient_id': False,
                'assignment_type': False,
            })

    def action_replace_device_wizard(self):
        """Open the Replace Device Modal.
        
        Only available for primary devices that are currently assigned.
        """
        self.ensure_one()
        
        # Validate this is a primary device
        if self.assignment_type != 'primary':
            raise ValidationError(
                "Device replacement is only available for primary devices. "
                "Holiday pumps cannot be replaced through this workflow."
            )
        
        # Validate device is assigned
        if self.pump_state != 'assigned' or not self.assigned_patient_id:
            raise ValidationError(
                "Device replacement is only available for devices that are currently assigned to a patient."
            )
        
        return {
            'name': 'Replace Device',
            'type': 'ir.actions.act_window',
            'res_model': 'glucose.replace.device.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_old_device_id': self.id},
        }

    @api.depends('product_id', 'product_id.product_tmpl_id.is_glucose_pump_product')
    def _compute_is_glucose_pump(self):
        """Check if this lot belongs to a glucose pump product."""
        for lot in self:
            if lot.product_id and lot.product_id.product_tmpl_id:
                lot.is_glucose_pump = lot.product_id.product_tmpl_id.is_glucose_pump_product
            else:
                lot.is_glucose_pump = False

    @api.depends('product_id', 'product_id.product_tmpl_id.is_rma_product')
    def _compute_is_rma_device(self):
        """Check if this lot belongs to an RMA product."""
        for lot in self:
            if lot.product_id and lot.product_id.product_tmpl_id:
                lot.is_rma_device = lot.product_id.product_tmpl_id.is_rma_product
            else:
                lot.is_rma_device = False

    @api.constrains('assigned_patient_id', 'assignment_type', 'pump_state')
    def _check_single_device_per_type(self):
        """Ensure a patient cannot have more than one device of each type assigned."""
        for lot in self:
            if not lot.is_glucose_pump or lot.pump_state != 'assigned':
                continue
            if not lot.assigned_patient_id or not lot.assignment_type:
                continue
            
            # Check for other assigned devices of the same type for this patient
            other_devices = self.search([
                ('id', '!=', lot.id),
                ('assigned_patient_id', '=', lot.assigned_patient_id.id),
                ('assignment_type', '=', lot.assignment_type),
                ('pump_state', '=', 'assigned'),
            ])
            
            if other_devices:
                device_type_label = 'Primary' if lot.assignment_type == 'primary' else 'Holiday Pump'
                raise ValidationError(
                    f"Patient {lot.assigned_patient_id.name} already has an assigned {device_type_label} device "
                    f"({other_devices[0].name}). A patient can only have one {device_type_label} device at a time."
                )

    @api.constrains('is_rma_device', 'assigned_patient_id', 'assignment_type', 'pump_state')
    def _check_rma_device_constraints(self):
        """Enforce RMA device assignment constraints.
        
        RMA devices can only be assigned:
        - As replacements for malfunctioning primary devices (via replacement workflow)
        - Cannot be assigned as initial primary device for new patients
        - Cannot be assigned as holiday pumps
        """
        # Skip constraint check if called from the replace device wizard
        if self.env.context.get('allow_rma_assignment'):
            return
        
        for lot in self:
            if not lot.is_rma_device or lot.pump_state != 'assigned':
                continue
            
            # RMA devices cannot be assigned as holiday pumps
            if lot.assignment_type == 'holiday_pump':
                raise ValidationError(
                    f"RMA device '{lot.name}' cannot be assigned as a holiday pump. "
                    "RMA devices can only be used as replacements for malfunctioning primary devices."
                )
            
            # Check if this is a valid replacement (via replacement workflow)
            # The replacement workflow sets allow_rma_assignment context
            # If we get here without that context for a primary assignment,
            # it means someone is trying to assign an RMA device directly
            if lot.assignment_type == 'primary' and lot.assigned_patient_id:
                # Check if this device has never been assigned before (initial assignment)
                assignment_count = self.env['glucose.assignment.log'].search_count([
                    ('equipment_id', '=', lot.id),
                ])
                # If there are no assignment logs yet, this is an initial assignment
                # which is not allowed for RMA devices
                if assignment_count == 0:
                    raise ValidationError(
                        f"RMA device '{lot.name}' cannot be assigned as an initial primary device. "
                        "RMA devices can only be used as replacements for malfunctioning primary devices "
                        "through the 'Replace Device' workflow."
                    )
