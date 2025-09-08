from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    """
    Extended Account Journal Model for NVE Activation Control

    This model extends account.journal to add NVE activation control.
    When activate_nve is True, related stock pickings will automatically
    generate NVE numbers upon validation.
    """
    _inherit = 'account.journal'

    # Boolean flag to control whether NVE generation is active for this journal
    # When True, stock pickings related to sales orders using this journal
    # will automatically generate NVE numbers during validation
    activate_nve = fields.Boolean(
        string='Activate NVE',
        help='Enable automatic NVE generation for stock pickings related to sales orders using this journal'
    )

    def unlink(self):
        """
        Overrides the unlink method to ensure that if an account journal is deleted,
        any associated custom sequence (based on the journal's code) is also deleted.

        This method performs the following steps:
        1. Finds the custom sequence related to the journal by its code.
        2. If such a sequence exists, it deletes the sequence.
        3. Then, it proceeds to delete the journal itself.
        """
        for rec in self:
            # Construct the sequence code based on the journal's code
            sequence_code = f'account.move.custom_code_{rec.code}'

            # Search for the related sequence object by the generated code
            related_sequence_object = rec.env['ir.sequence'].search([
                ('code', '=', sequence_code)
            ], limit=1)
            
            # If a related sequence is found, delete it
            if related_sequence_object:
                related_sequence_object.unlink()
                
        return super(AccountJournal, self).unlink()


class StockWarehouse(models.Model):
    """
    Extended Stock Warehouse Model for NVE (Nummer der Versandeinheit) Support
    
    This model extends the standard stock.warehouse to add support for NVE generation.
    NVE is a standardized shipping unit number used in logistics, particularly in Germany.
    It consists of:
    - NVE Prefix (1 digit): A single digit identifier (0-9)
    - GLN (Global Location Number): 7-9 digits identifying the location
    - Sequential Number: Auto-generated sequence padded to make total 16 digits
    - Check Digit: Calculated using standard barcode algorithm
    """
    _inherit = 'stock.warehouse'

    # GLN (Global Location Number) - A unique identifier for locations
    # Must be between 7-9 digits to get correct padding
    gln = fields.Char(string='GLN', help='Global Location Number (7-9 digits)')
    
    # NVE Prefix - Single digit prefix for the shipping unit number
    # Used as the first digit in the NVE number (0-9)
    nve_prefix = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
    ], string='NVE Prefix', help='Single digit prefix for NVE generation (0-9)')

    # Sequence reference used for generating sequential numbers in NVE
    sequence_id = fields.Many2one('ir.sequence', string='NVE Sequence', 
                                  help='Sequence used for generating sequential numbers in NVE')

    @api.constrains('gln')
    def check_gln(self):
        """
        Validation constraint for GLN field
        
        Validates that:
        1. GLN contains only digits (no letters or special characters)
        2. GLN length results in valid padding (7-9 digits)
        
        The padding is calculated as: 16 - len(gln)
        Valid padding range is 7-9, which means GLN should be 7-9 digits
        
        Raises:
            ValidationError: If GLN is not numeric or has invalid length
        """
        for record in self:
            if not record.gln:
                continue

            # Validate that GLN contains only numeric characters
            # GLN Must be Integer Value - no letters or special characters allowed
            if not record.gln.isdigit():
                raise ValidationError(_('GLN Must Be Numbers'))

            # Calculate padding needed to reach 16 digits total
            # Total NVE length is 17 digits (16 + check digit)
            # So we need padding to make the sequence part reach 16 digits total
            padding = 16 - len(record.gln)

            # Validate that padding is in the allowed range (7-9)
            # This ensures GLN is between 7-9 digits
            if not (7 <= padding <= 9):
                raise ValidationError(_("Check Your GLN Number Again it must be (7, 8 or 9) digits."))

    @api.model
    def create(self, vals):
        """
        Override create method to automatically create NVE sequence
        
        When a new warehouse is created with GLN and NVE prefix,
        automatically creates the associated sequence for NVE generation
        """
        warehouse = super(StockWarehouse, self).create(vals)
        warehouse._create_or_update_sequence()
        return warehouse

    def write(self, vals):
        """
        Override write method to update NVE sequence when GLN or prefix changes
        
        If GLN or NVE prefix is modified, updates the sequence padding
        to ensure correct NVE generation
        """
        res = super(StockWarehouse, self).write(vals)
        # If GLN or NVE prefix changed, update the sequence
        if 'gln' in vals or 'nve_prefix' in vals:
            self._create_or_update_sequence()
        return res

    def _create_or_update_sequence(self):
        """
        Create or update sequence for NVE generation
        
        This method:
        1. Checks if warehouse has both GLN and NVE prefix
        2. Calculates required padding based on GLN length
        3. Creates new sequence or updates existing one
        
        The sequence is used to generate the sequential part of the NVE number.
        Padding ensures the total length (prefix + GLN + sequence) equals 17 digits.
        """
        for record in self:
            # Check if both GLN and NVE prefix are present
            if record.gln and record.nve_prefix:
                padding = 16 - len(record.gln)

                if record.sequence_id:
                    # Update existing sequence with new padding value
                    record.sequence_id.write({
                        'padding': padding,
                    })
                else:
                    # Create new sequence specific to this warehouse
                    sequence = self.env['ir.sequence'].create({
                        'name': f'NVE Sequence - {record.name}',
                        'code': f'nve.sequence.{record.id}',
                        'padding': padding,
                        'number_next': 1,
                        'implementation': 'no_gap',
                    })
                    record.sequence_id = sequence


class StockPicking(models.Model):
    """
    Extended Stock Picking Model for NVE Support
    
    This model extends stock.picking to add NVE generation functionality.
    NVE is automatically calculated when:
    1. The picking is validated (button_validate)
    2. The related sale order's journal has activate_nve = True
    3. The warehouse has all required fields (GLN, NVE prefix, sequence)
    """
    _inherit = 'stock.picking'

    # NVE field - The shipping unit number
    # # Readonly to prevent manual modification, copy=False to avoid duplication
    # nve = fields.Char(string='NVE', readonly=True, copy=False,
    #                  help='Nummer der Versandeinheit - Shipping unit number')
    picking_type_code = fields.Selection(related='picking_type_id.code')
    
    account_journal_id = fields.Many2one('account.journal', string='Account Journal')
    
    # Related field to check NVE activation from the sale order's journal
    # This field automatically reflects the activate_nve value from the journal
    activate_nve = fields.Boolean(
        related='sale_id.journal_id.activate_nve',
        readonly=False,
        help='Automatically synced with journal NVE activation status'
    )
    def button_validate(self):
        """
        Override button_validate to generate NVE on picking validation.
        
        This method is triggered when the picking is validated for outgoing deliveries.
        It performs NVE generation if activate_nve is True and all requirements are met.

        Returns:
            The result of the parent button_validate method.
        """
        result = super(StockPicking, self).button_validate()
        
        # Only process outgoing pickings with NVE activation
        if (self.activate_nve and 
            self.picking_type_id.code == 'outgoing' and 
            self.state == 'done'):
            
            self._validate_nve_requirements()
            self._create_invoice_and_link_delivery()
            self._compute_nve()
            
        return result
    
    def _validate_nve_requirements(self):
        """Validate that warehouse has all required NVE configuration."""
        warehouse = self.picking_type_id.warehouse_id
        
        if not warehouse.nve_prefix:
            raise ValidationError(_('NVE prefix does not exist. Please configure it in the warehouse settings.'))
        if not warehouse.gln:
            raise ValidationError(_('GLN does not exist. Please configure it in the warehouse settings.'))
    
    def _create_invoice_and_link_delivery(self):
        """Create invoice for the sale order and link this delivery."""
        if self.sale_id:
            invoices = self.sale_id._create_invoices()
            if invoices:
                invoices.write({'picking_id': self.id})

    def _compute_nve(self):
        """
        Calculate and assign NVE for each package only for packages .
        
        NVE Structure (18 digits total):
        1. NVE Prefix (1 digit): From warehouse configuration
        2. GLN (7-9 digits): Global Location Number from warehouse
        3. Sequential Number (variable): Padded to make total 16 digits
        4. Check Digit (1 digit): Calculated using barcode algorithm
        
        Example: 0 + 1234567 + 000000001 + 3 = 012345670000000013
        """
        warehouse = self.picking_type_id.warehouse_id
        
        # Verify all required fields are present
        if not all([warehouse, warehouse.gln, warehouse.nve_prefix, warehouse.sequence_id]):
            return
        
        # Get all result packages from move lines
        result_packages = self.move_line_ids.mapped('result_package_id')
        result_packages = result_packages.filtered(lambda p: p)  # Remove empty records
        
        # Generate NVE for each result package
        for package in result_packages:
            if not package.nve:  # Only generate if NVE doesn't exist
                # Get next sequence number and build NVE
                reference = warehouse.sequence_id.next_by_id()
                sequence = warehouse.nve_prefix + warehouse.gln + reference
                check_digit = self._calculate_check_digit(sequence)
                package.nve = sequence + str(check_digit)

    def _calculate_check_digit(self, sequence):
        """
        Calculate check digit for barcode using Modulo 10 algorithm.
        
        This implements the standard GS1 check digit calculation:
        1. Starting from the rightmost digit
        2. Multiply every second digit by 3, others by 1
        3. Sum all results
        4. Check digit = (10 - (sum mod 10)) mod 10
        
        Args:
            sequence: The 16-digit sequence without check digit
            
        Returns:
            int: The calculated check digit (0-9)
        """
        total = sum(
            int(digit) * (3 if i % 2 == 0 else 1)
            for i, digit in enumerate(sequence)
        )
        
        return (10 - (total % 10)) % 10



