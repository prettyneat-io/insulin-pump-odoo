from odoo import api, fields, models


class ConsumablesAllocation(models.Model):
    """Track consumables allocated and used per patient per month."""
    _name = 'glucose.consumables.allocation'
    _description = 'Glucose Pump Consumables Allocation'
    _rec_name = 'display_name'
    _order = 'year desc, month desc'

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
    
    quantity_allocated = fields.Integer(
        string='Quantity Allocated',
        default=0
    )
    quantity_used = fields.Integer(
        string='Quantity Used',
        default=0
    )
    threshold = fields.Integer(
        string='Threshold',
        default=13,
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

    @api.depends('quantity_used', 'quantity_allocated')
    def _compute_threshold_status(self):
        """Compute threshold status based on usage.
        
        Green: 10 or less used
        Orange: 11 to 13 used
        Red: more than allocated
        """
        for record in self:
            if record.quantity_used <= 10:
                record.threshold_status = 'green'
            elif record.quantity_used <= 13:
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

    @api.constrains('threshold')
    def _check_threshold_positive(self):
        for record in self:
            if record.threshold <= 0:
                raise models.ValidationError("Threshold must be a positive integer.")

    @api.onchange('quantity_allocated')
    def _onchange_quantity_allocated(self):
        """Show warning if more than 13 consumables allocated."""
        if self.quantity_allocated > 13:
            return {
                'warning': {
                    'title': 'Charge for additional pumps',
                    'message': 'More than 13 consumables allocated. Additional charges may apply.',
                }
            }
