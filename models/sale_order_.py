from email.policy import default

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    MARKETPLACE_CHOICES = [
        ('1', 'Shopify'),
        ('2', 'Kaufland'),
        ('4', 'OTTO'),
        ('5', 'Ebay'),
        ('6', 'Amazon'),
        ('7', 'MediamarktSaturn Retail'),
        ('8', 'Mediamarkt Marketplace'),
    ]

    to_market_place = fields.Boolean(
        help='Activate this field to associate the order with a marketplace. If not activated, the order will remain a standard Odoo order.',default=True)

    market_place = fields.Selection(MARKETPLACE_CHOICES, string='Marketplace')

    journal_id = fields.Many2one(comodel_name='account.journal')

    def action_confirm(self):
        """Override action_confirm to auto-create and post invoices for marketplace orders."""
        result = super(SaleOrder, self).action_confirm()

        for order in self:
                order._process_marketplace_order()
                
        return result
    
    def _process_marketplace_order(self):
        """Process marketplace order by creating invoice with appropriate journal."""
        marketplace_name = dict(self.MARKETPLACE_CHOICES).get(self.market_place)
        journal = self._find_marketplace_journal(marketplace_name)

        
        if not journal and  self.to_market_place:
            raise UserError(_(
                "Failed to create invoice. "
                f"Please create a sales journal with name '{marketplace_name}' in Accounting."
            ))

        self.journal_id = journal if self.to_market_place else False
        
        # MediaMarkt (marketplace '7') doesn't auto-create invoices
        if self.market_place != '7':
            invoices = self._create_invoices()
            # only Post Marketplaces Invoices
            if self.to_market_place :
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



    @api.constrains('state')
    def check_market_place(self):
        for rec in self :
            if not rec.market_place and rec.state == 'sale' and rec.to_market_place:
                raise ValidationError(
                    _('Marketplace field is required.'))


    @api.onchange('to_market_place')
    def reset_marketplace(self):

        for rec in self :
            if not rec.to_market_place:
                rec.market_place = False



