from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    picking_id = fields.Many2one('stock.picking')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    MARKETPLACE_CHOICES = [
        ('1', 'Shopify'),
        ('2', 'Kaufland'),
        ('4', 'OTTO'),
        ('5', 'Ebay'),
        ('6', 'Amazon'),
        ('7', 'MediaMarkt'),
    ]
    
    market_place = fields.Selection(MARKETPLACE_CHOICES, string='Marketplace')

    journal_id = fields.Many2one(comodel_name='account.journal')

    def action_confirm(self):
        """Override action_confirm to auto-create and post invoices for marketplace orders."""
        result = super(SaleOrder, self).action_confirm()

        for order in self:
            if order.market_place:
                order._process_marketplace_order()
                
        return result
    
    def _process_marketplace_order(self):
        """Process marketplace order by creating invoice with appropriate journal."""
        marketplace_name = dict(self.MARKETPLACE_CHOICES).get(self.market_place)
        journal = self._find_marketplace_journal(marketplace_name)
        
        if not journal:
            raise UserError(_(
                "Failed to create invoice. "
                f"Please create a sales journal with name '{marketplace_name}' in Accounting."
            ))
            
        self.journal_id = journal
        
        # MediaMarkt (marketplace '7') doesn't auto-create invoices
        if self.market_place != '7':
            invoices = self._create_invoices()
            invoices.action_post()
    
    def _find_marketplace_journal(self, marketplace_name):
        """Find the appropriate journal for the marketplace.
        
        Args:
            marketplace_name: Name of the marketplace
            
        Returns:
            account.journal: The matching journal record or None
        """
        return self.env['account.journal'].search([
            ('name', '=', marketplace_name),
            ('type', '=', 'sale')
        ], limit=1)

    def _prepare_invoice(self):
        """Override to set the marketplace journal when creating invoice."""
        invoice_vals = super()._prepare_invoice()
        
        # Use journal from context or sale order
        if self.env.context.get('default_journal_id'):
            invoice_vals['journal_id'] = self.env.context.get('default_journal_id')
        elif self.journal_id:
            invoice_vals['journal_id'] = self.journal_id.id
            
        return invoice_vals