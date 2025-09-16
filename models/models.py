# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import format_datetime, format_date, formatLang
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_formatted_amount(self, value):
        """
        Returns the formatted amount based on the customer's language.

        Args:
            value (float): The amount to be formatted.

        Returns:
            str: The formatted amount, including currency symbol and in the appropriate language format.
        """
        lang_code = self.partner_id.lang or 'en_US'
        return formatLang(
            self.with_context(lang=lang_code).env,
            value=value,
            digits=2,
            currency_obj=self.currency_id
        )
    
    def get_move_sequence(self):
        """
        Extract sequence number from move name for display in reports.
        Removes static prefixes (RE_/GS_) from the sequence.
        
        Returns:
            str: Clean sequence number (e.g., 'O2025-00001')
        """
        move_type_prefixes = {
            'out_invoice': 'RE_',
            'out_refund': 'GS_'
        }
        
        prefix = move_type_prefixes.get(self.move_type)
        if prefix and prefix in self.name:
            return self.name.split(prefix)[1]
        
        return ""
    
    def get_invoice_paid_date(self):
        """
        Returns the formatted payment date for the invoice.
        
        Returns:
            str: The formatted payment date in the partner's language.
        """
        if not self.matched_payment_ids:
            return format_date(self.env, self.invoice_date, lang_code=self.partner_id.lang or 'en_US')
            
        latest_payment = max(self.matched_payment_ids, key=lambda payment: payment.date)
        return format_date(self.env, latest_payment.date, lang_code=self.partner_id.lang or 'en_US')

    def get_invoice_template_based_on_lang(self):
        """
        Returns the invoice template based on the customer's language.
        
        Returns:
            dict: Template data including titles, headers, footer, and payment text.
        """
        payment_date = (self.get_invoice_paid_date() 
                       if self.matched_payment_ids 
                       else self.get_invoice_date())
        invoice_date = self.get_invoice_date()
        
        templates = {
            'de_DE': {
                'title' : ['Rechnung','Gutschrift','Steuer-Nr. 44/663/70421','Ust-IdNr. DE452204311'],
                'invoice_details' : ['Rechnungsdatum','Gutschriftsdatum' , 'Bestellungs-Nr' , 'Bestelldatum'],
                'headers': ['Pos.', 'Anzahl', 'Einheit', 'Bezeichnung', 'Einzelpreis', 'Gesamtpreis'],
                'totals': ['Gesamt Netto', 'Zzgl.MwSt.', 'Gesamt Brutto:'],
                'footer_company': {
                    'left': 'Sitz der Gesellschaft: Nackenheim\nGeschäftsführer: Ouyang Shi',
                    'center': 'Amtsgericht Mainz, HRB 53400\nUst-IdNr DE452204311\nSteuer-Nr. 44/663/70421',
                    'right': 'Bankverbindung: Commerzbank\nIBAN: DE26 5084 0005 0604 5702 00\nBIC: COBADEFFXXX'
                },
                'payment_text': f'Die Rechnung wurde am {payment_date} bezahlt.',
                'credit_text': f'Die Gutschrift wurde am {invoice_date} gebucht.'
            },
            'en_US': {
                'title': ['Invoice', 'Credit Note','Tax Number: 44/663/70421','VAT ID No.: DE452204311'],
                'invoice_details': ['Invoice Date', 'Credit Note Date', 'Order Number', 'Order Date'],
                'headers': ['No.', 'Quantity', 'Unit', 'Description', 'Unit Price', 'Total Price'],
                'totals': ['Total net', 'Plus VAT', 'Total gross:'],
                'footer_company': {
                    'left': 'Registered Office: Nackenheim\nManaging Director: Ouyang Shi',
                    'center': 'Commercial Register: Mainz, HRB 53400\nVAT ID No.: DE452204311\nTax Number: 44/663/70421',
                    'right': 'Bank Details: Commerzbank\nIBAN: DE26 5084 0005 0604 5702 00\nBIC: COBADEFFXXX'
                },
                'payment_text': f'The invoice was paid on {payment_date}.',
                'credit_text': f'The credit note was posted on {invoice_date}.'
            },

             'en_GB': {
                'title': ['Invoice', 'Credit Note','Tax Number: 44/663/70421','VAT ID No.: DE452204311'],
                'invoice_details': ['Invoice Date', 'Credit Note Date', 'Order Number', 'Order Date'],
                'headers': ['No.', 'Quantity', 'Unit', 'Description', 'Unit Price', 'Total Price'],
                'totals': ['Total net', 'Plus VAT', 'Total gross:'],
                'footer_company': {
                    'left': 'Registered Office: Nackenheim\nManaging Director: Ouyang Shi',
                    'center': 'Commercial Register: Mainz, HRB 53400\nVAT ID No.: DE452204311\nTax Number: 44/663/70421',
                    'right': 'Bank Details: Commerzbank\nIBAN: DE26 5084 0005 0604 5702 00\nBIC: COBADEFFXXX'
                },
                'payment_text': f'The invoice was paid on {payment_date}.',
                'credit_text': f'The credit note was posted on {invoice_date}.'
            }
        }

        lang = self.partner_id.lang or 'en_US'
        return templates.get(lang, templates['en_US'])

    def get_invoice_date(self):
        """
               Returns the formatted invoice date according to the partner's language.

               Returns:
                   str: The formatted invoice date.
        """
        
        return format_date(self.env, self.invoice_date, lang_code=self.partner_id.lang or 'en_US')

    def get_order_date(self, order_obj):
        """
        Returns the formatted order date for the given order object.
        
        Args:
            order_obj: The order record containing the date_order field.
            
        Returns:
            str: The formatted order date in the appropriate language and timezone.
        """
        user_lang = self.partner_id.lang or 'en_US'
        dt_format = "MM/dd/yyyy HH:mm:ss" if user_lang != 'de_DE' else None
        
        return format_datetime(
            self.env,
            order_obj.date_order,
            tz=self.partner_id.tz or 'UTC',
            lang_code=user_lang,
            dt_format=dt_format
        )

    def item_price_with_tax(self, line):
        """
        Returns the price of an item including tax, formatted appropriately.
        
        Args:
            line: The invoice line record containing price and tax details.
            
        Returns:
            str: The formatted price of the item including tax.
        """
        if not line.tax_ids:
            return self.get_formatted_amount(line.price_unit)
            
        tax_rate = line.tax_ids[0].amount
        tax_amount = round(tax_rate * line.price_unit / 100, 2)
        price_with_tax = round(line.price_unit + tax_amount, 2)
        
        return self.get_formatted_amount(price_with_tax)

    check_if_email_is_send = fields.Boolean(copy=False)
    @api.constrains('payment_state')
    def _check_payment_and_send_email(self):
        """Send invoice email when payment state changes to paid"""
        for invoice in self:
            if (invoice.payment_state == 'paid'
                and invoice.move_type in ('out_invoice', 'out_refund')
                and not invoice.check_if_email_is_send):
                try:
                    # Mark as sent first to prevent duplicates
                    invoice.check_if_email_is_send = True

                    # Create wizard instance for this specific invoice
                    wizard = self.env['account.move.send.wizard'].create({
                        'move_id': invoice.id,
                    })

                    # Send the invoice
                    wizard.action_send_and_print()

                    # Log success
                    invoice.message_post(body="Invoice email sent automatically after payment")

                except Exception as e:
                    # Reset flag on error
                    invoice.check_if_email_is_send = False
                    # Log error but don't stop process
                    invoice.message_post(body=f"Failed to send invoice email: {str(e)}")

    # Override This Method To Add more Logic about Intializing First Invoice / Credit Note For Specific Journal
    @api.depends('date', 'journal_id', 'move_type', 'name', 'posted_before', 'sequence_number', 'sequence_prefix',
                 'state')
    def _compute_name_placeholder(self):
        """
        This method is responsible for setting the placeholder name for invoices and credit notes.
        It uses the journal and move type to generate a custom name.

        First, the normal behavior of the method is applied, but it will be modified in one case only:
        - If an invoice or credit note is created for a specific journal and it is the first invoice or credit note in that journal,
          the sequence will be modified to apply a custom format.
        """

        # Calling the default behavior of the parent method to ensure other computations are executed
        super()._compute_name_placeholder()

        for move in self:
            # Search for existing invoices or credit notes in the same journal, excluding the current move
            moves = self.env['account.move'].search([('move_type', 'in', ['out_refund', 'out_invoice']),
                                                     ('journal_id', '=', move.journal_id.id),
                                                     ('id', '!=', move.id)])

            # Check if the move is an invoice or credit note, if no name exists, and if there are no previous invoices/credit notes in the journal
            if move.move_type in ["out_invoice", "out_refund"] and move.journal_id and (
                    not move.name or move.name == '/') and not moves:

                # Generate a custom sequence code based on the journal code
                sequence_code = f'account.move.custom_code_{move.journal_id.code}'

                # Fetch the sequence object based on the generated code
                sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], limit=1)

                # Call a custom method to create a new sequence if it doesn't exist
                if not sequence :
                    sequence=move.create_new_sequence(move.journal_id.name, sequence_code)


                # Get the next number in the sequence using the sequence object's method
                next_number = sequence.get_next_char(sequence.number_next)

                # Depending on whether the move is an invoice or credit note, set the placeholder name
                if move.move_type == "out_invoice":
                    move.name_placeholder = 'RE_ ' + move.journal_id.code + next_number
                elif move.move_type == "out_refund":
                    move.name_placeholder = 'GS_ ' + move.journal_id.code + next_number

    @api.model
    def create(self, vals):
        """
        Creates a new account move (invoice or credit note) and assigns it a custom sequence number
        based on the journal configuration. If no sequence exists for the journal, a new sequence
        is created. If this is the first invoice or credit note in the journal, the sequence is reset to 1.

        Args:
            vals (dict): The values used to create the new account move.

        Returns:
            AccountMove: The created account move record.
        """

        # Create the account move (invoice/credit note)
        result = super(AccountMove, self).create(vals)

        # Check if the move is an invoice or credit note
        if result.move_type in ["out_invoice", "out_refund"]:
            # Define the custom sequence code based on the journal code
            sequence_code = f'account.move.custom_code_{result.journal_id.code}'

            # Check if the sequence already exists, if not, create a new one
            sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], limit=1)
            if not sequence:
                sequence = self.create_new_sequence(result.journal_id.name, sequence_code)



            # Check if there are any previous invoices/credit notes in the same journal
            existing_moves = self.env['account.move'].search([
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('journal_id', '=', result.journal_id.id),
                ('id', '!=', result.id)  # Exclude the current invoice/credit note
            ])

            if not existing_moves:
                # Reset the sequence number to 1 if there are no previous invoices/credit notes
                sequence.number_next = 1

            # Set the name of the invoice/credit note using the sequence
            if result.move_type == "out_invoice":
                result.name = 'RE_' + result.journal_id.code + sequence.next_by_id()
            elif result.move_type == "out_refund":
                result.name = 'GS_ ' + result.journal_id.code + sequence.next_by_id()

        return result

    def create_new_sequence(self, name, sequence_code):
        """
        Create a new sequence for invoice numbering.
        
        Args:
            name: The name for the sequence
            sequence_code: The unique code for the sequence
            
        Returns:
            ir.sequence: The created sequence record
        """
        return self.env['ir.sequence'].create({
            'name': f'Custom Sequence for {name}',
            'code': sequence_code,
            'prefix': '%(year)s-',
            'padding': 6,
            'number_next': 1,
        })



