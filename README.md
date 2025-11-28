# NGR Customizations (Odoo 18)

Comprehensive marketplace and logistics enhancements for NGR Dynamic Solution GmbH. The module streamlines the order-to-ship process across multiple marketplaces, automates invoice creation/posting and emailing, and generates GS1-compliant NVE shipping labels.

## Overview

This module adds:
- Marketplace-aware sales processing (Shopify, Kaufland, OTTO, eBay, Amazon, MediaMarkt variants).
- Automatic invoice creation and posting from sales orders depending on marketplace rules.
- Journal-driven invoice/credit-note naming with per-journal sequences.
- Multilingual, branded invoice report (DE/EN)  and EAN column.
- NVE (Nummer der Versandeinheit) generation per package at delivery validation with Code128 barcode labels.

Author: TecSee GmbH  |  Website: https://tecsee.de/de/

## Dependencies

The module depends on core Odoo apps:
- `base`
- `account_accountant`
- `sale_management`
- `stock`
- `stock_delivery`

## Key Features

### 1) Marketplace processing on Sales Orders
- Adds two fields on `sale.order`:
  - `to_market_place` (Boolean): mark order as marketplace order.
  - `market_place` (Selection): marketplace code (Shopify/Kaufland/OTTO/eBay/Amazon/Mediamarkt Saturn Retail/Mediamarkt Marketplace).
- On confirm (`action_confirm`):
  - If `to_market_place` is enabled, the module locates a sales journal matching the marketplace name and uses it for invoicing.
  - Automatically creates and posts the invoice for all marketplaces except MediaMarkt (code `7`).
- Validation rule: `market_place` becomes required when `to_market_place` is enabled.

### 2) Journal-driven numbering & NVE activation
- Extends `account.journal` with:
  - `activate_nve` (Boolean) to control NVE generation on related deliveries.
  - `invoice_name` and `credit_note_name` prefixes used in invoice/credit note naming.
- When a journal is deleted, its custom sequence (if created by this module) is also removed.

### 3) Invoice numbering and emailing
- Extends `account.move` to:
  - Build per-journal sequences and dynamic names on creation for `out_invoice` / `out_refund`.
  - Compute a language-aware formatting for dates and amounts.
  - Send invoice email automatically when payment state becomes `paid`  and logs status on the chatter.

### 4) NVE generation at delivery validation
- Extends `stock.warehouse` with:
  - `gln` (7–9 digits) and `nve_prefix` (single digit 0–9).
  - Automatically creates/updates an `ir.sequence` to produce the sequential part of the NVE.
  - Validation ensures GLN is numeric and results in valid sequence padding.
- Extends `stock.picking` to:
  - Mirror `activate_nve` from the originating sale order’s journal.
  - Enforce package assignment before NVE generation (each move line must have a `result_package_id`).
  - On validating an outgoing picking in `done` state, it:
    - Creates an invoice (if applicable) and links the delivery to it.
    - Generates NVE per result package using warehouse GLN/prefix/sequence and a GS1 check digit.
  - Adds a "Print NVE" button to print Code128 barcode labels per package.

### 5) Package and quant enhancements
- Extends `stock.quant.package` with:
  - `nve` (readonly; set/reset on pack/unpack), `picking_id`, `tracking_ref` (unique), and editable quant list.
  - Weight helpers on related quants: `packaging_weight`, `net_weight`, `gross_weight` (auto-computed).
- Extends `stock.move.line` so assigning a `result_package_id` links that package to the picking.

## Reports

### Invoice (A4)
- Action: overrides `account.account_invoices` to use `ngr_addon.de_invoice_report`.
- Language-aware headers, totals, footer, and payment/credit texts (DE/EN/EN-GB) derived from customer language.
- Adds an EAN column when product barcode is present.
- Custom stylesheet: `static/src/css/invoice.css`.

### NVE Barcode Labels (Custom size)
- Action: `ngr_addon.nve_barcode_report` on `stock.picking`.
- Paper format: custom 105x148 (Portrait) with minimal margins.
- Prints one label per result package using Code128 and the computed NVE value.

## Installation

1. Copy `ngr_addon` into your Odoo custom addons path.
2. Update app list and install the module:
   - Apps → Update Apps List.
   - Search for "NGR Customizations" and install.

## Configuration

1) Create/prepare Sales Journals
- For each marketplace you use, create a Sales Journal named exactly as the marketplace label you’ll select on the order:
  - Shopify, Kaufland, OTTO, Ebay, Amazon, MediamarktSaturn Retail, Mediamarkt Marketplace.
- In each journal:
  - Optionally set `invoice_name` and `credit_note_name` prefixes.
  - Enable `activate_nve` if you want related deliveries to auto-generate NVE and allow label printing.

2) Warehouse NVE settings
- Inventory → Configuration → Warehouses:
  - Set `GLN` (7–9 digits) and `NVE Prefix` (0–9).
  - The module will create/update an internal sequence to complete the NVE.

## Usage

1) Marketplace Sales Order
- Create a quotation.
- Enable `To Marketplace` and choose `Marketplace`.
- Confirm the order:
  - If marketplace is not MediaMarkt (`7`), an invoice is created and posted automatically using the matching Sales Journal.

2) Delivery and NVE Generation
- On the related delivery (outgoing picking):
  - Assign result packages: each move line quantity must be assigned to a `result_package_id`.
  - Validate the picking (it must reach state `done`).
  - If the sales journal had `activate_nve` enabled and the warehouse NVE settings are complete, the system computes NVE per package.
  - Click "Print NVE" to generate barcode labels (one per package).

3) Invoice Email on Payment
- When an invoice is marked `Paid`, the module automatically sends the invoice by email and logs the result on the invoice chatter.

## Technical Details

- Models extended/added:
  - `sale.order`: marketplace fields, journal selection, invoice creation on confirm.
  - `account.journal`: `activate_nve`, `invoice_name`, `credit_note_name`, cleanup of custom sequences on delete.
  - `account.move`: language-aware formatting, automatic email on paid, custom per-journal naming/sequence.
  - `stock.warehouse`: `gln`, `nve_prefix`, `sequence_id` auto create/update, validation rules.
  - `stock.picking`: NVE generation on validate, "Print NVE" action, package checks, link delivery to invoice.
  - `stock.quant.package`: `nve`, `picking_id`, `tracking_ref` (unique), editable quant list.
  - `stock.quant`: weight helpers (`packaging_weight`, `net_weight`, `gross_weight`) and back-reference to sale line.
  - `stock.move.line`: ensures package is linked back to picking.

- Views updated:
  - `sale.order` form/tree: marketplace fields.
  - `account.journal` form: NVE activation and naming fields.
  - `stock.warehouse` form: GLN and NVE Prefix.
  - `stock.picking` form: "Print NVE" button (visible when outgoing, done, packages exist, and NVE is active).
  - `account.move` form: linked delivery (`picking_id`).
  - `stock.quant.package` form: NVE, tracking, weights, and editable lines.

- Reports:
  - Invoice: `ngr_addon.de_invoice_report` (A4) with multilingual content.
  - NVE Labels: `ngr_addon.nve_report_template` with Code128 barcodes per package.

## Notes & Limitations

- For automatic invoice posting at order confirmation, the Sales Journal name must match the marketplace label you select.
- MediaMarkt (`7`) is intentionally excluded from automatic invoice creation.
- NVE generation requires: warehouse `GLN` and `NVE Prefix`, and that every move line is assigned to a package.
- `tracking_ref` on packages is enforced unique.


## Support

For issues or enhancements, please contact TecSee GmbH.


