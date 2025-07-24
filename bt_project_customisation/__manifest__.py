# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Customisation',
    'version': '14.2.4',
    'category': 'Account',
    # 'sequence': 225,
    'summary': 'Project Customisation',
    'description': """
    """,
    'depends': ['hr_timesheet','sale_timesheet','sale_management',
    'hr_timesheet_sheet','project','sale','stock'],
    'data': [
       'security/security.xml',
       'security/ir.model.access.csv',

       'wizard/budget_line_view.xml',
       'wizard/stoc_return_view.xml',
       'views/project_task_view.xml',
       'views/sale_view.xml',
       'views/budget_view.xml',
       'views/hr_timesheet_view.xml',
       'views/action.xml',
        
    ],
    'qweb': [],
    'application': True,
}

