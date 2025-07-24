


{
    'name': 'Print Journal Entries',
    'version': '1.1',
    'category': 'account',
    'summary': 'Print Journal Entry',
    'description': """
    this module use for print journal Entries in PDF report"
    """,
    'author': "HAK Solutions",
    'website': "http://haksolutions.com",
    'depends': ['account','saudi_einvoice_knk'],
    'license': 'AGPL-3',
    'data': [
            'report/report_menu.xml',
            'report/voucher_report.xml'
            ],

    'demo': [],
    "images": [
        'static/description/icon.png'
    ],
    'price': 00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
