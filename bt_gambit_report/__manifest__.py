#bbbn
{
    'name': "BT Account Report",
    'category': 'Invoicing',
    'version': '2.0',
    'depends': ['account', 'bt_account_customisation', 'bt_account_report_qrcode','saudi_einvoice_knk' ],
    'data': [
        'data/paperformat.xml',
        'views/asset.xml',
        'views/report_invoice.xml',
        'views/account_report.xml',
        'views/res_company.xml',
    ],
}
