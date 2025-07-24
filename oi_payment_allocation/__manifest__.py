# -*- coding: utf-8 -*-
##############################################################################

{
    'name': 'Advance Payment Allocation',
    'summary': 'Payment Allocation, Partial Payment Allocation, Payment Distribution, Payment Reconciliation, Partial Payment Distribution, Sales Allocation, Purchase Allocation',
    'version': '14.0.2.1',
    'author': 'Openinside',
    'website': "https://www.open-inside.com",
    'category': 'Accounting',
    'description': """
        
    """,
    
    'depends' : ['account','base_accounting_kit','bt_account_payment'],
    'data': [  
        'security/ir.model.access.csv',      
        'views/account_payment_allocation.xml',
        'views/account_payment_view.xml',
        'views/action.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    "license": "OPL-1",
    "price" : 69.99,
    "currency": 'EUR',
    'odoo-apps' : True,
    'images':[
            'static/description/cover.png'
        ],                  
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
