from odoo import  fields , models , api



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def write(self, vals):
        rtn = super(StockMoveLine,self).write(vals)
        if 'result_package_id' in vals :
            self.result_package_id.picking_id = self.picking_id

        return rtn
