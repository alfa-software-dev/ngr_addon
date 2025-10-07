from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'
    # NVE field - The shipping unit number
    # Readonly to prevent manual modification, copy=False to avoid duplication
    nve = fields.Char(string='NVE', readonly=True, copy=False,
                      help='Nummer der Versandeinheit - Shipping unit number')
    quant_ids = fields.One2many('stock.quant', 'package_id', 'Bulk Content', readonly=False,
                                domain=['|', ('quantity', '!=', 0), ('reserved_quantity', '!=', 0)])
    picking_id = fields.Many2one(comodel_name='stock.picking' , string='Delivery Ref',readonly=True)
    picking_type_code  = fields.Char(related='package_type_id.barcode' , store=True)
    tracking_ref = fields.Char(copy=False,index=True)
    _sql_constraints = [
        ('name_tracking_ref', 'unique (tracking_ref)', "Tracking number should not be repeated."),
    ]

    def unpack(self):
        rtn = super(StockQuantPackage,self).unpack()
        self.nve = False
        self.picking_id = False
        return  rtn


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    gross_weight = fields.Float(digits='Product Unit of Measure', compute='_compute_gross_weight',store=True)
    packaging_weight = fields.Float(digits='Product Unit of Measure', readonly=False)
    net_weight = fields.Float(digits='Product Unit of Measure', readonly=True,compute='_compute_net_weight' ,store=True)
    sale_order_line_id = fields.Many2one(comodel_name='sale.order.line')

    @api.depends('packaging_weight')
    def _compute_gross_weight(self):
        for rec in self:
            rec.gross_weight = rec.packaging_weight + float(rec.product_id.weight * rec.quantity)

    @api.depends('packaging_weight')
    def _compute_net_weight (self):
        for rec in self :
            rec.net_weight = rec.product_id.weight * rec.quantity


    def create(self, vals_list):
        rtn = super(StockQuant,self).create(vals_list)
        # Only run this logic when package_id is being updated, and avoid recursion
        if rtn.package_id.picking_id:
            moves_ids = rtn.package_id.picking_id.move_ids
            matched_moves = moves_ids.filtered(lambda move: move.product_id == rtn.product_id and move.sale_line_id)
            rtn.sale_order_line_id = matched_moves[0].sale_line_id
        return rtn






