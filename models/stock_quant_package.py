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




class StockQuant(models.Model):
    _inherit = 'stock.quant'
    gross_weight = fields.Float(digits='Product Unit of Measure', compute='_compute_gross_weight',store=True)
    packaging_weight = fields.Float(digits='Product Unit of Measure', readonly=False)
    net_weight = fields.Float(digits='Product Unit of Measure', readonly=True,compute='_compute_net_weight' ,store=True)

    @api.depends('packaging_weight')
    def _compute_gross_weight(self):
        for rec in self:
            rec.gross_weight = rec.packaging_weight + float(rec.product_id.weight * rec.quantity)

    @api.depends('packaging_weight')
    def _compute_net_weight (self):
        for rec in self :
            rec.net_weight = rec.product_id.weight * rec.quantity

