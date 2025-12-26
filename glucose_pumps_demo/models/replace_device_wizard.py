from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class GlucoseReplaceDeviceWizard(models.TransientModel):
    _name = 'glucose.replace.device.wizard'
    _description = 'Replace Glucose Pump Device'

    # Current device information (display only)
    old_device_id = fields.Many2one(
        'stock.lot', 
        string='Current Device SN', 
        readonly=True,
        required=True
    )
    patient_id = fields.Many2one(
        'res.partner', 
        related='old_device_id.assigned_patient_id', 
        string='Patient Name', 
        readonly=True
    )
    patient_internal_id = fields.Char(
        related='patient_id.patient_internal_id',
        string='Patient Internal ID',
        readonly=True
    )
    installation_date = fields.Date(
        related='old_device_id.installation_date', 
        string='Installation Date', 
        readonly=True
    )
    
    # Replacement details
    replacement_reason = fields.Selection([
        ('malfunction', 'Malfunction'),
        ('damage', 'Damage'),
        ('other', 'Other'),
    ], string='Replacement Reason', required=True)
    
    replacement_notes = fields.Text(string='Replacement Notes')
    
    new_device_id = fields.Many2one(
        'stock.lot', 
        string='Replacement Device SN', 
        required=True,
        domain="[('is_rma_device', '=', True), ('pump_state', '=', 'available')]",
        help='Only RMA devices in available state can be selected for replacement'
    )

    @api.constrains('old_device_id')
    def _check_old_device_is_primary(self):
        """Replacement is only available for primary devices."""
        for wizard in self:
            if wizard.old_device_id and wizard.old_device_id.assignment_type != 'primary':
                raise ValidationError(
                    "Device replacement is only available for primary devices. "
                    "Holiday pumps cannot be replaced through this workflow."
                )

    @api.constrains('new_device_id')
    def _check_new_device_is_rma(self):
        """Only RMA devices can be used for replacement."""
        for wizard in self:
            if wizard.new_device_id:
                if not wizard.new_device_id.is_rma_device:
                    raise ValidationError(
                        "Only RMA replacement devices can be selected for device replacement. "
                        "Please select a device from the RMA product category."
                    )
                if wizard.new_device_id.pump_state != 'available':
                    raise ValidationError(
                        f"The selected replacement device '{wizard.new_device_id.name}' is not available. "
                        f"Current state: {wizard.new_device_id.pump_state}"
                    )

    def action_replace(self):
        """Execute the device replacement workflow."""
        self.ensure_one()
        
        old_device = self.old_device_id
        new_device = self.new_device_id
        patient = self.patient_id
        reason = dict(self._fields['replacement_reason'].selection).get(self.replacement_reason)
        
        if not patient:
            raise UserError("Cannot replace device: No patient is assigned to the current device.")
        
        if not old_device.is_glucose_pump:
            raise UserError("The current device is not a glucose pump device.")
        
        # Validate that old device is a primary device
        if old_device.assignment_type != 'primary':
            raise UserError(
                "Device replacement is only available for primary devices. "
                "Holiday pumps cannot be replaced through this workflow."
            )
        
        # Validate new device is RMA and available
        if not new_device.is_rma_device:
            raise UserError(
                "Only RMA replacement devices can be used for device replacement."
            )
        
        if new_device.pump_state != 'available':
            raise UserError(
                f"The replacement device '{new_device.name}' is not available."
            )
        
        # Get reason label for messages
        reason_label = reason or self.replacement_reason
        notes_text = f" Notes: {self.replacement_notes}" if self.replacement_notes else ""
        
        # 1. Set replacement date on old device assignment log
        old_log = self.env['glucose.assignment.log'].search([
            ('patient_id', '=', patient.id),
            ('equipment_id', '=', old_device.id),
            ('assignment_type', '=', 'primary'),
            ('replacement_date', '=', False),
        ], limit=1)
        if old_log:
            old_log.replacement_date = fields.Date.today()
        
        # 2. Unlink old device from patient and set state to 'available'
        old_device.with_context(skip_device_sync=True).write({
            'pump_state': 'available',
            'assigned_patient_id': False,
            'assignment_type': False,
        })
        
        # 3. Transfer old device to return location
        self._transfer_to_return_location(old_device)
        
        # 4. Clear patient's primary device (with context to prevent sync issues)
        patient.with_context(skip_device_sync=True).write({
            'primary_device_id': False,
        })
        
        # 5. Assign new RMA device to patient as primary
        # Use allow_rma_assignment context to bypass RMA constraint check
        new_device.with_context(skip_device_sync=True, allow_rma_assignment=True).write({
            'pump_state': 'assigned',
            'assigned_patient_id': patient.id,
            'assignment_type': 'primary',
            'installation_date': fields.Date.today(),
        })
        
        # 6. Update patient's primary device
        patient.with_context(skip_device_sync=True).write({
            'primary_device_id': new_device.id,
            'installation_date': fields.Date.today(),
        })
        
        # 7. Create new assignment log with current date as installation date
        self.env['glucose.assignment.log'].create({
            'patient_id': patient.id,
            'equipment_id': new_device.id,
            'assignment_type': 'primary',
            'installation_date': fields.Date.today(),
        })
        
        # 8. Leave notes in chatter
        # Patient chatter message
        patient_msg = (
            f"Primary device SN {old_device.name} replaced with RMA device SN {new_device.name}. "
            f"Reason: {reason_label}.{notes_text}"
        )
        patient.message_post(body=patient_msg, message_type='notification')
        
        # Old device chatter message
        old_device_msg = (
            f"Replaced for Patient ID {patient.patient_internal_id}. "
            f"Reason: {reason_label}.{notes_text}"
        )
        old_device.message_post(body=old_device_msg, message_type='notification')
        
        # New device chatter message
        new_device_msg = (
            f"Assigned to Patient ID {patient.patient_internal_id} as replacement "
            f"for SN {old_device.name}."
        )
        new_device.message_post(body=new_device_msg, message_type='notification')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Device Replaced Successfully',
                'message': f"Device {old_device.name} has been replaced with {new_device.name}.",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _transfer_to_return_location(self, device):
        """Transfer device to the configured return location.
        
        Creates a stock move to transfer the device to the return location
        if configured in settings.
        """
        # Get return location from settings
        return_location_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'glucose_pumps.return_location_id', default=0
        ))
        
        if not return_location_id:
            # No return location configured, skip transfer
            return
        
        return_location = self.env['stock.location'].browse(return_location_id)
        if not return_location.exists():
            return
        
        # Find current location of the device via stock.quant
        quant = self.env['stock.quant'].search([
            ('lot_id', '=', device.id),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
        ], limit=1)
        
        if quant and quant.location_id.id != return_location.id:
            # Create stock move to return location
            move_vals = {
                'name': f'Return: {device.name}',
                'product_id': device.product_id.id,
                'product_uom_qty': 1,
                'product_uom': device.product_id.uom_id.id,
                'location_id': quant.location_id.id,
                'location_dest_id': return_location.id,
                'lot_ids': [(4, device.id)],
                'state': 'draft',
            }
            
            move = self.env['stock.move'].create(move_vals)
            move._action_confirm()
            move._action_assign()
            
            # Force assign the lot to the move line
            for move_line in move.move_line_ids:
                move_line.lot_id = device.id
                move_line.quantity = 1
            
            move._action_done()
