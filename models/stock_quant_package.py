from odoo import fields , models , api
from odoo.exceptions import  ValidationError , UserError



class StockQuantPackage(models.Model) :
    _inherit = 'stock.quant.package'
    # NVE field - The shipping unit number
    # Readonly to prevent manual modification, copy=False to avoid duplication
    nve = fields.Char(string='NVE', readonly=True, copy=False,
                      help='Nummer der Versandeinheit - Shipping unit number')

