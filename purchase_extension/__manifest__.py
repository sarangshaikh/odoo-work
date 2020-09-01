# -*- coding: utf-8 -*-
{
    'name': "Purchase Extension",

    'summary': """
        This Module extends the functionality of Purchase order.""",

    'description': """
       
    """,

    'author': "Comstar USA",
    'website': "https://www.comstarusa.com/",
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','contact_extension'],

    # always loaded
    'data': [
        'views/product.xml',
        'views/purchase_order.xml',
        'views/cron_job.xml',
    ],
}
