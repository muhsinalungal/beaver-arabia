# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Invoice Report QR Code',
    'version': '14.2.6',
    'category': 'Account',
    'sequence': 225,
    'description': """
    """,
    'depends': ['base','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/report_invoice_qrcode_view.xml',
        'views/account_move_report_view.xml',
        'views/res_partner_arb_view.xml',
        'views/layout.xml', 
        'views/report_layout.xml',
        'reports/account_invoice_report.xml',
        'reports/invoice_report.xml',
    ],
    'qweb': [],
    'application': True,
}
