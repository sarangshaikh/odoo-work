# -*- coding: utf-8 -*-
{
    'name': "Sale Extension",

    'summary': """
        This Module extends the functionality of sale order.""",

    'description': """
       
    """,

    'author': "Comstar USA",
    'website': "https://www.comstarusa.com/",
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','contact_extension'],

    # always loaded
    'data': [
        'views/saleorder.xml',
        'views/cron_job.xml',
    ],
}
