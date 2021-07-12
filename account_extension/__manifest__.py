# -*- coding: utf-8 -*-


{
    'name': "Account Extension",

    'summary': """
        NTN and STRN fields are added on Company form view and Contact Form view.""",

    'description': """
       
    """,

    'author': "Comstar ISA",
    'website': "https://www.comstar.com.pk/",
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale'],

    # always loaded
    'data': [

        'views/rescompany.xml',
        'views/sale_order.xml',

    ],
}
