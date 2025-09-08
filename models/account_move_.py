from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    picking_id = fields.Many2one('stock.picking',readonly=True)

