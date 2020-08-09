# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'

    customer_class = fields.Selection([('e_com', 'E-Commerce'),('retail', 'Retail'),('trade', 'Trade')],string="Customer Classification")
    is_customer = fields.Boolean(string="Customer")
    # is_supplier  = fields.Boolean(string="Supplier")
    #
    # @api.onchange('customer_rank')
    # def onchange_customer_rank(self):
    #     if self.customer_rank > 0:
    #         self.is_customer = True
    #     else:
    #         self.is_customer = False
    #
    #     if self.supplier_rank > 0:
    #         self.is_supplier = True
    #     else:
    #         self.is_supplier = False


