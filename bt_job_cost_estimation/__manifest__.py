# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Job Cost Estimation',
    'version': '1.1.8',
    'category': 'Sales',
    'author': "BroadTech IT Solutions Pvt Ltd",
    'summary':'Cost Estimation',
    'description': """
Cost Estimation.
===============================

Cost Estimation
    """,
    'depends': ['sale_management','bt_account_customisation'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_estimate_line_view.xml',
        'views/sale_estimate_view.xml',
        'views/sale_estimate_sheet_view.xml',
        'views/sale_menu_view.xml',
        'views/product_view.xml',
        'views/sale_template_view.xml',
        'views/menu_view.xml',
        'views/sale_order_view.xml',
        'data/estimate_mail.xml',
        'data/estimate_sequence.xml',
    ],
}
