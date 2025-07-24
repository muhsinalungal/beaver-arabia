# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting Customisation',
    'version': '14.6.6',
    'category': 'Account',
    # 'sequence': 225,
    'summary': 'Accounting Customisation',
    'description': """
    """,
    'depends': ['account','jt_cost_centers','bt_account_report_qrcode','purchase',
                'base_accounting_kit','base_account_budget','hr',
                'analytic','account_asset_management','bt_project_customisation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        # 'reports/report_project_cost.xml',
        # 'reports/project_cost.xml',
        'views/templates.xml',
        'views/account_move_view.xml',
        'views/site_view.xml',
        'views/invoice_type_view.xml',
        'views/res_partner_view.xml',
        'views/account_journal_view.xml',
        'views/asset_view.xml',
        'views/account_analytic_account_view.xml',
        'views/res_salesperson_views.xml'
        
    ],
    'qweb': [],
    'application': True,
}
