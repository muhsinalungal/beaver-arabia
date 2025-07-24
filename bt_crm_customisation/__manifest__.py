# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Crm Customisation',
    'version': '14.1.3',
    'category': 'Account',
    # 'sequence': 225,
    'summary': 'Crm Customisation',
    'description': """
    """,
    'depends': ['crm','bt_job_cost_estimation','bt_account_customisation'],
    'data': [
        'security/estimate_security.xml',
    	'data/crm_data.xml',
       	'views/crm_lead_view.xml',
        
    ],
    'qweb': [],
    'application': True,
}

