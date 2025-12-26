from odoo import api, fields, models


class HolidayPumpRequest(models.Model):
    """Holiday pump requests submitted via public website form."""
    _name = 'glucose.holiday.pump.request'
    _description = 'Holiday Pump Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submitted_date desc'

    name = fields.Char(
        string='Request Reference',
        readonly=True,
        copy=False,
        default='New'
    )
    
    # Patient information
    patient_name = fields.Char(
        string='Patient Name',
        required=True
    )
    main_pump_serial = fields.Char(
        string='Main Pump Serial Number',
        required=True
    )
    contact_phone = fields.Char(
        string='Mobile Number',
        required=True
    )
    contact_email = fields.Char(
        string='Contact Email'
    )
    
    # Travel information
    travel_start_date = fields.Date(
        string='Travel Start Date',
        required=True
    )
    travel_end_date = fields.Date(
        string='Travel End Date',
        required=True
    )
    destination = fields.Char(
        string='Destination',
        required=True
    )
    
    # Additional info
    reason = fields.Text(
        string='Reason'
    )
    additional_notes = fields.Text(
        string='Additional Notes'
    )
    
    # Status tracking
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', tracking=True)
    
    submitted_date = fields.Datetime(
        string='Submitted Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    # Link to patient (if found)
    patient_id = fields.Many2one(
        'res.partner',
        string='Linked Patient',
        domain="[('is_patient', '=', True)]"
    )
    patient_internal_id = fields.Char(
        related='patient_id.patient_internal_id',
        string='Patient Internal ID',
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'glucose.holiday.pump.request'
                ) or 'New'
            
            # Try to link to existing patient by serial number
            if vals.get('main_pump_serial'):
                serial = vals['main_pump_serial'].strip()
                lot = self.env['stock.lot'].search([
                    ('name', '=ilike', serial),
                    ('is_glucose_pump', '=', True),
                ], limit=1)
                if lot and lot.assigned_patient_id:
                    vals['patient_id'] = lot.assigned_patient_id.id
        
        return super().create(vals_list)
