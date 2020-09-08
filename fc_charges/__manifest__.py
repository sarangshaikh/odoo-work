# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'FC Charges',
    'version': '0.1',
    'category': 'Accounting',
    'summary': 'This module allows to create penalty invoice if invoices not paid on time',
    'license':'AGPL-3',
    'description': """
    Invoice Summary Report
""",
    'author' : 'Comstar USA',
    'website' : 'http://www.constarusa.com',
    'depends': ['account'],
    'images': ['static/description/banner.jpg'],
    'data': [
        'data/fc_sequence.xml',
        'data/product_demo_view.xml',
        'views/account_invoice_view.xml',
        'views/cronjob.xml',


    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

# vim:expandtab:smartindent:tabstop=2:softtabstop=2:shiftwidth=2:
