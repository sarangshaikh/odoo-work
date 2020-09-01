# -*- coding: utf-8 -*-
from odoo import fields, models,api
import datetime
import calendar
from odoo.fields import Date
from datetime import timedelta
class StockPickingExt(models.Model):
    _inherit = 'stock.picking'

    # vendor_code = fields.Char()
    # customer_code = fields.Char()

    # @api.onchange('partner_id')
    # def onchange_inventory_partner_id(self):
    #     if self.partner_id:
    #         if  self.picking_type_id.code == 'incoming':
    #             self.vendor_code = self.partner_id.code
    #         elif  self.picking_type_id.code == 'outgoing':
    #             self.customer_code = self.partner_id.code




class StockMoveExt(models.Model):
    _inherit = 'stock.move'

    unit_cost = fields.Float()
    ic_clearing_account =  fields.Many2one('account.account',string="IC Clearing Account")

    @api.onchange('product_id')
    def onchange_stock_move_product_id(self):
        if self.product_id:
            self.unit_cost = self.product_id.standard_price
            if self.product_id.categ_id.id:
                self.ic_clearing_account = self.product_id.categ_id.property_account_income_categ_id.id

class StockMoveLineExt(models.Model):
    _inherit = 'stock.move.line'

    unit_cost = fields.Float()
    ic_clearing_account =  fields.Many2one('account.account',string="IC Clearing Account")

    @api.onchange('product_id')
    def onchange_stock_move_line_product_id(self):
        if self.product_id:
            self.unit_cost = self.product_id.standard_price
            if self.product_id.categ_id.id:
                self.ic_clearing_account = self.product_id.categ_id.property_account_income_categ_id.id

class StockQuantExt(models.Model):
    _inherit = 'stock.quant'

    reference = fields.Char()
    transaction_date = fields.Date(default=datetime.date.today())
    ic_clearing_account = fields.Many2one('account.account', string="IC Clearing Account")

    @api.onchange('product_id')
    def onchange_stock_quant_product_id(self):
        if self.product_id:
            if self.product_id.categ_id.id:
                self.ic_clearing_account = self.product_id.categ_id.property_account_income_categ_id.id


