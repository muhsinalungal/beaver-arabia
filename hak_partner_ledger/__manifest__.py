
{
    'name': 'Partner Ledger Report',
    'version': '14.9',
    'summary': 'Partner Ledger Report',
    'description': 'Partner Ledger Report',
    'author': 'HAK Solutions',
    'maintainer': 'Haksolutions',
    'company': 'Haksolutions',
    'website': 'https://www.Haksolutions.com',
    'depends': [
		'base', 'account',
		],
    'category': 'Accounting',
    'demo': [],
    'data': [
        
            'security/ir.model.access.csv',
            'data/paperformat.xml',
            'views/template_layout.xml',
            'views/partner_ledger_views.xml',
            ],
    'installable': True,
    'images': ['static/description/banner.png'],
    'qweb': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
