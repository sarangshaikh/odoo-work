# -*- coding: utf-8 -*-
from odoo import fields, models,api,_
import datetime
import calendar
from odoo.fields import Date
from datetime import timedelta
from odoo.exceptions import UserError
class SaleorderExt(models.Model):
    _inherit = 'sale.order'
    tax_exempt = fields.Boolean(string='Tax Exempt')
    # order_reference = fields.Char(string="Order Reference")
    po_no = fields.Char(string="PO #")
    po_date = fields.Date(string="PO Date")
    fax = fields.Char(string="Fax")
    customer_classification = fields.Selection([('diamond', 'Diamond'), ('regular', 'Regular'), ('basic', 'Basic')],
                                               string="Customer Classification")
    customer_type = fields.Selection([('c', 'C'), ('n', 'N'), ('p', 'P')], string="Customer Type ")
    customer_color = fields.Char(string="Customer Type")
    territory = fields.Char()
    shipping_address = fields.Char(string="Shipping Address")
    customer_code = fields.Char()
    recurring_order = fields.Boolean(string='Recurring Order')
    recurring_period = fields.Selection([('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],string="Recurring Period")

    shipper_no = fields.Many2one('stock.picking', string="Shipper Number")
    ship_via = fields.Selection([('by_sea', 'By Sea'), ('by_air', 'By Air')], string="Ship Via")
    fob = fields.Char(string="FOB")

    # Invisible Fields
    recurring_date = fields.Date(string="Next Order date")
    done_recurring = fields.Boolean(string="Done Recurring")


    @api.onchange('partner_id')
    def onchange_sale_partner_id(self):
        if self.partner_id:
            self.customer_classification = self.partner_id.customer_classification
            self.customer_code = self.partner_id.code
            self.customer_color = self.partner_id.customer_color
            self.customer_type = self.partner_id.customer_type
            self.fax = self.partner_id.fax
            self.payment_term_id = False
            self.tax_exempt = self.partner_id.tax_exempt
            self.territory= self.partner_id.territory


    @api.onchange('tax_exempt')
    def onchange_sale_tax_exempt(self):
        if self.tax_exempt == True:
            for line in self.order_line:
                line.tax_id = False


    def add_months(self, sourcedate, months):
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)



    @api.onchange('recurring_order')
    def onchange_sale_recurring_period(self):
        if self.recurring_order == False:
            self.recurring_period = False
            self.recurring_date = False


    def action_confirm(self):
        res = super(SaleorderExt, self).action_confirm()
        for so in self:
            if so.recurring_date == False:
                if so.recurring_period   ==   'weekly':
                    so.recurring_date = Date.to_string(so.date_order + timedelta(days=7))

                elif so.recurring_period == 'monthly':
                    so.recurring_date =  so.add_months(so.date_order,1)

                elif so.recurring_period == 'yearly':
                    so.recurring_date =  so.add_months(so.date_order,12)
        return res




    @api.model
    def recurring_sale_order(self):
        sale_obj = self.env['sale.order'].search([('recurring_order', '=', True), ('done_recurring', '=', False)])
        current_date = datetime.datetime.now().date()
        if sale_obj.ids:
            for order in sale_obj:
                if order.recurring_date:
                    if (order.recurring_date == current_date):
                        order.copy({'recurring_date':False})
                        order.done_recurring = True


class SaleorderLineExt(models.Model):
    _inherit = 'sale.order.line'

    # product_code = fields.Char(string='Product Code')
    freight = fields.Char(string='Freight')
    ic_clearing_account = fields.Many2one('account.account', string="Accounts")
    memo = fields.Char(string="Memo")

    @api.onchange('product_template_id','product_id')
    def onchange_sale_order_line_product_id(self):
        if self.product_id:
            self.unit_cost = self.product_id.standard_price
            if self.product_id.categ_id.id:
                self.ic_clearing_account = self.product_id.categ_id.property_account_income_categ_id.id

            if self.product_id.type == 'product' and self.product_uom_qty > self.product_id.qty_available and (self.product_id.item1 or self.product_id.item2):
                raise UserError(_("%s is Out Of Stock ! Here are the alternative Products: \n\n     %s \n     %s") % (self.product_id.name,self.product_id.item1.name,self.product_id.item2.name))


class ProductTemplateExt(models.Model):
    _inherit = 'product.template'

    item1 = fields.Many2one('product.template', string="Item 1")
    item2 = fields.Many2one('product.template', string="Item 2")

