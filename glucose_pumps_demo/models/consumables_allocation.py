from odoo import api, fields, models


class ConsumablesAllocation(models.Model):
    """Track consumables allocated and used per patient per month."""
    _name = 'glucose.consumables.allocation'
    _description = 'Glucose Pump Consumables Allocation'
    _rec_name = 'display_name'
    _order = 'year desc, month desc'

    _sql_constraints = [
        ('patient_month_year_unique', 'unique(patient_id, month, year)', 
         'An allocation record already exists for this patient in the selected month and year.')
    ]

    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        required=True,
        domain="[('is_patient', '=', True)]",
        ondelete='cascade'
    )
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', required=True)
    year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: fields.Date.today().year
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if 'quantity_allocated' in fields_list:
            res['quantity_allocated'] = int(get_param('glucose_pumps.default_allocated_quantity', 10))
        if 'threshold' in fields_list:
            res['threshold'] = int(get_param('glucose_pumps.default_critical_threshold', 13))
        return res

    quantity_allocated = fields.Integer(
        string='Quantity Allocated'
    )
    quantity_used = fields.Integer(
        string='Quantity Used',
        default=0
    )
    threshold = fields.Integer(
        string='Threshold',
        help='Maximum number of consumables before warning'
    )
    
    threshold_status = fields.Selection([
        ('green', 'Normal'),
        ('orange', 'Warning'),
        ('red', 'Exceeded'),
    ], string='Threshold Status', compute='_compute_threshold_status', store=True)
    
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    # Related fields
    patient_internal_id = fields.Char(
        related='patient_id.patient_internal_id',
        string='Patient Internal ID',
        store=True
    )

    @api.depends('quantity_used', 'quantity_allocated', 'threshold')
    def _compute_threshold_status(self):
        """Compute threshold status based on usage.
        
        Normal (green): quantity_used <= quantity_allocated
        Warning (orange): quantity_allocated < quantity_used <= threshold
        Exceeded (red): quantity_used > threshold
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        default_allocated = int(get_param('glucose_pumps.default_allocated_quantity', 10))
        default_threshold = int(get_param('glucose_pumps.default_critical_threshold', 13))
        
        for record in self:
            allocated = record.quantity_allocated or default_allocated
            threshold = record.threshold or default_threshold
            
            if record.quantity_used <= allocated:
                record.threshold_status = 'green'
            elif record.quantity_used <= threshold:
                record.threshold_status = 'orange'
            else:
                record.threshold_status = 'red'

    @api.depends('patient_id', 'month', 'year')
    def _compute_display_name(self):
        month_names = dict(self._fields['month'].selection)
        for record in self:
            patient_name = record.patient_id.name or 'Unknown'
            month_name = month_names.get(record.month, '')
            record.display_name = f"{patient_name} - {month_name} {record.year}"

    @api.constrains('threshold', 'quantity_allocated')
    def _check_threshold_values(self):
        for record in self:
            if record.threshold <= 0:
                raise models.ValidationError("Threshold must be a positive integer.")
            if record.threshold <= record.quantity_allocated:
                raise models.ValidationError("The Critical Threshold must always be greater than the Allocated Quantity.")

    @api.onchange('quantity_allocated')
    def _onchange_quantity_allocated(self):
        """Show warning if more than threshold consumables allocated."""
        if self.quantity_allocated > self.threshold:
            return {
                'warning': {
                    'title': 'Charge for additional pumps',
                    'message': f'More than {self.threshold} consumables allocated. Additional charges may apply.',
                }
            }
