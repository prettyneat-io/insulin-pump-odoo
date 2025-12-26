from odoo import api, fields, models


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
