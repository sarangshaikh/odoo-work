# -*- coding: utf-8 -*-
from odoo import fields, models,api

class ProductTemplateExt(models.Model):
    _inherit = 'product.template'

    long_description = fields.Text()
    short_description = fields.Text()
    alternative_description = fields.Text()

    


# class ProductExt(models.Model):
#     _inherit = 'product.product'
#
#     long_description = fields.Text()
#     short_description = fields.Text()
#     alternative_description = fields.Text()







