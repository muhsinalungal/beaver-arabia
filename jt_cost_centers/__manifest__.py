# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Cost Centers',
    'summary': """Manage expenses/income through different cost center""",
    'description': """
This is the module to manage the cost center in sale, purchase, account and employee and Employee expense.
=========================================================================================================
    """,
    'version': '14.0.0.1.6',
    'category': 'expense',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'contributors':['Anil Kesariya <anil.r.kesariya@gmail.com>'],
    'website': 'http://www.jupical.com',
    'depends': ['sale_expense', 'purchase', 'stock','hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/cost_center_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/account_invoice_view.xml',
        'views/employee_view.xml',
        'views/hr_expenses_view.xml',
        'report/hr_expense_report.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'images': ['static/description/poster_image.png'],
    'price': 25.00,
    'currency': 'USD'
}
