# -*- coding: utf-8 -*-
from odoo import fields, models,api
import datetime
import calendar
from odoo.fields import Date
from datetime import timedelta
class PurchaseOrderExt(models.Model):
    _inherit = 'purchase.order'

    vendor_code = fields.Char()
    fax = fields.Char(string="Fax")

    recurring_order = fields.Boolean(string='Recurring Order')
    recurring_period = fields.Selection([('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],string="Recurring Period")
    ship_via = fields.Char()
    buyer_code = fields.Char()
    ship_to = fields.Char()
    fob =  fields.Char()
    freight = fields.Char()
    confirm_to = fields.Char()
# Invisible Fields
    recurring_date = fields.Date(string="Next Order date")
    done_recurring = fields.Boolean(string="Done Recurring")
    remarks = fields.Text(string="Remarks:")
    comments = fields.Text()
    @api.onchange('partner_id')
    def onchange_purchase_partner_id(self):
        if self.partner_id:
            self.fax = self.partner_id.fax
            self.payment_term_id = False
            self.vendor_code = self.partner_id.code


    def add_months(self, sourcedate, months):
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)



    @api.onchange('recurring_order')
    def onchange_purchase_recurring_period(self):
        if self.recurring_order == False:
            self.recurring_period = False
            self.recurring_date = False


    def button_confirm(self):
        res = super(PurchaseOrderExt, self).button_confirm()
        for po in self:
            if po.recurring_date == False:
                if po.recurring_period   ==   'weekly':
                    po.recurring_date = Date.to_string(po.date_order + timedelta(days=7))

                elif po.recurring_period == 'monthly':
                    po.recurring_date =  po.add_months(po.date_order,1)

                elif po.recurring_period == 'yearly':
                    po.recurring_date =  po.add_months(po.date_order,12)
        return res




    @api.model
    def recurring_purchase_order(self):
        purchase_obj = self.env['purchase.order'].search([('recurring_order', '=', True), ('done_recurring', '=', False)])
        current_date = datetime.datetime.now().date()
        if purchase_obj.ids:
            for order in purchase_obj:
                if order.recurring_date:
                    if order.recurring_date == current_date:
                        order.copy({'recurring_date':False})
                        order.done_recurring = True


class PurchaseorderLineExt(models.Model):
    _inherit = 'purchase.order.line'

    memo = fields.Char()
    description_type = fields.Selection([('long', 'Long'), ('short', 'Short'), ('alternative', 'Alternative')],string="Description Type")
    ic_clearing_account = fields.Many2one('account.account', string="Accounts")

    @api.onchange('product_id','description_type')
    def onchange_purchase_product_id(self):
        if self.product_id:
            if self.description_type == 'long':
                self.name = self.product_id.long_description
            elif self.description_type == 'short':
                self.name = self.product_id.short_description
            elif self.description_type == 'alternative':
                self.name = self.product_id.alternative_description

            self.unit_cost = self.product_id.standard_price
            if self.product_id.categ_id.id:
                self.ic_clearing_account = self.product_id.categ_id.property_account_income_categ_id.id