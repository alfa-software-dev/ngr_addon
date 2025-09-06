# -*- coding: utf-8 -*-
{
    'name': "NGR Customizations",

    'summary': "Comprehensive marketplace management and logistics system for NGR Dynamic Solution GmbH",

    'description': """
        NGR Invoice & Logistics Management System
        
        A complete solution for managing marketplace orders, invoice generation, and NVE shipping labels for NGR Dynamic Solution GmbH.
        
        Key Features:
        • Multi-Marketplace Support: Supports Shopify, Kaufland,and MediaMarkt integrations
        • Automatic Invoice Generation: Auto-creates and posts invoices when marketplace orders are confirmed
        • Journal-Based Processing: Automatically assigns appropriate accounting journals based on marketplace
        • Multi-Language Invoice Templates: German and English invoice layouts with professional formatting
        • NVE (Nummer der Versandeinheit) Generation: Automated shipping unit numbers for logistics compliance
        • Barcode Label Generation: Creates professional shipping labels with Code128 barcodes
        • GLN Integration: Supports Global Location Number for warehouse management
        • Custom Paper Formats: Optimized layouts for both invoices (A4) and shipping labels (custom size)
        • Professional Branding: Consistent NGR Dynamic Solution GmbH branding across all documents
        
        This module streamlines the complete order-to-ship process for e-commerce operations.
                       """,

    'author': "TecSee GmbH",
    'website': "https://tecsee.de/de/",
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_accountant', 'sale_management','stock','stock_delivery'],

    # always loaded

    'data': [
        'reports/invoice.xml',
        'reports/nve_barcode.xml',
        'views/sale_order_.xml',
        'views/stock_.xml',
        'views/account_journal_.xml',
        'views/account_move_.xml',
        'views/stock_quant_package_.xml',
    ],

}
