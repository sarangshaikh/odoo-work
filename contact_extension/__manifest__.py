# -*- coding: utf-8 -*-
{
    'name': "Contact Extension",

    'summary': """
        This Module extends the functionality of Contact.""",

    'description': """
       
    """,

    'author': "Comstar USA",
    'website': "https://www.comstarusa.com/",
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts','sms','account'],

    # always loaded
    'data': [
        'views/res_partner.xml',
    ],
}
