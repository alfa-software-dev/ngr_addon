from odoo import fields , models , api
from odoo.exceptions import  ValidationError , UserError



class StockQuantPackage(models.Model) :
    _inherit = 'stock.quant.package'
    # NVE field - The shipping unit number
    # Readonly to prevent manual modification, copy=False to avoid duplication
    nve = fields.Char(string='NVE', readonly=True, copy=False,
                      help='Nummer der Versandeinheit - Shipping unit number')


    def action_nve_report(self):
        """Generate NVE barcode report for this picking."""
        return self.env.ref('ngr_addon.nve_barcode_report').report_action(self)

    # def label_template(self):
    #     """
    #     Get label template based on partner language.
    #
    #     Returns:
    #         dict: Template data for shipping labels
    #     """
    #     templates = {
    #         'de_DE': {
    #             'addresses': {'sender': "Absender", 'recipient': 'Empfänger'},
    #         },
    #         'en_US': {
    #             'addresses': {'sender': "Sender", 'recipient': 'Recipient'},
    #         }
    #     }
    #
    #     user_lang = 'de_DE' if self.partner_id.lang == 'de_DE' else 'en_US'
    #     return templates[user_lang]



class StockQuant(models.Model) :
    _inherit = 'stock.quant'
    gross_weight  = fields.Float(digits='Product Unit of Measure',compute='_compute_gross_weight')
    packaging_weight = fields.Float(digits='Product Unit of Measure',readonly=False)

    @api.depends('gross_weight')
    def _compute_gross_weight (self) :
         for rec in self :
             rec.gross_weight = rec.packaging_weight + float(rec.product_id.weight * rec.quantity)





