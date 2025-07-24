# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Multiple Payments',
    'version': '14.3.2',
    'category': 'Account',
    'sequence': 225,
    'summary': 'For Multiple Payments',
    'description': """
    """,
    'depends': ['account','jt_cost_centers','bt_account_customisation','saudi_einvoice_knk'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_seq.xml',
        'report/payment_report.xml',
        'report/receipts_report.xml',
        'report/advance_payment_report.xml',
        'report/account_payment_report.xml',

        'views/account_extra_payment_view.xml',
        'views/account_advance_payment.xml',

        
    ],
    'qweb': [],
    'application': True,
}
