# -*- coding: utf-8 -*-
{
    'name': "Customer Classification",

    'summary': """
        This Module allows us to categorized customer on contact form , sale order customer invoice and crm.""",

    'description': """
       
    """,

    'author': "Comstar USA",
    'website': "https://www.comstarusa.com/",
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','crm','sale_crm'],

    # always loaded
    'data': [
        'views/res_partner.xml',
        'views/saleorder.xml',
        'views/account_move.xml',
        'views/crm.xml',
    ],
}
