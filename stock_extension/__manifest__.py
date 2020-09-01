# -*- coding: utf-8 -*-
{
    'name': "Inventory Extension",

    'summary': """
        This Module extends the functionality of Inventory.""",

    'description': """
       
    """,

    'author': "Comstar USA",
    'website': "https://www.comstarusa.com/",
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','contact_extension'],

    # always loaded
    'data': [
        'views/stock_picking.xml',
        'views/stock_quant.xml',
    ],
}
