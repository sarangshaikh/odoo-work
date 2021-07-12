# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _


class sale_order(models.Model):
    _inherit = 'sale.order'

    tax_ids = fields.Many2many('account.tax', string='Taxes', computondelete='restrict')
    taxes_amount = fields.Monetary(compute='_calculate_tax', string="Taxes")

    margin =  fields.Monetary(string="Margin", compute="_compute_margin")
    conversion_rate_enable = fields.Boolean()
    conversion_rate = fields.Float(string="Conversion Rate (PKR)")
    discount_selection = fields.Selection([('line','Line'),('global','Global')],default="line",string="Discount Selection")
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    discount_amount = fields.Float('Discount Amount')
    discount_amt = fields.Monetary(compute='_amount_all', string='- Discount', digits_compute=dp.get_precision('Account'),readonly=True)

    total_conversion_rate = fields.Monetary(compute="_compute_total_conversion_rate", digits_compute=dp.get_precision('Account'),string="Total Conversion Rate (PKR)")


    @api.depends('amount_total','conversion_rate')
    def _compute_total_conversion_rate(self):
        for rec in self:
            rec.total_conversion_rate = 0.0
            if rec.conversion_rate > 0.0 and  rec.amount_total > 0.0:
                rec.total_conversion_rate = rec.amount_total * rec.conversion_rate
            else:
                rec.total_conversion_rate = 0.0


    @api.depends('discount_selection','tax_ids')
    def _calculate_tax(self):
        for rec in self:
            rec.taxes_amount = 0.0
            if rec.discount_selection == 'global':
                if rec.tax_ids.ids:
                    for tax in rec.tax_ids:
                        rec.taxes_amount += (tax.amount * rec.amount_untaxed) / 100

            else:
                rec.taxes_amount = 0.0




    # store = True,

    @api.onchange('discount_selection')
    def onchange_sale_discount_selection(self):
        if self.discount_selection == 'global':
            for line in self.order_line:
                line.discount = 0.0
                line.fixed_amount = 0.0
                line.tax_id = False
        else:
            self.discount_method = False
            self.discount_amount =0.0




    # @api.depends('order_line.actual_cost')
    # def _compute_actual_cost(self):
    #     total_unit_price = 0.0
    #     total_actual_cost = 0.0
    #     for rec in self:
    #         for line in rec.order_line:
    #             total_unit_price += line.product_uom_qty * line.price_unit
    #             total_actual_cost += line.product_uom_qty * line.actual_cost
    #
    #         rec.margin = total_unit_price - total_actual_cost


    @api.depends('order_line.price_unit','order_line.actual_cost')
    def _compute_margin(self):
        total_unit_price = 0.0
        total_actual_cost = 0.0
        for rec in self:
            for line in rec.order_line:

                total_unit_price += line.product_uom_qty * line.price_unit
                total_actual_cost += line.product_uom_qty * line.actual_cost

            rec.margin = total_unit_price - total_actual_cost - rec.discount_amt


    @api.depends('discount_selection','discount_method','discount_amount')
    def _calculate_discount(self):
        res=0.0
        discount = 0.0
        for self_obj in self:
            if self_obj.discount_selection == 'global':
                if self_obj.discount_method == 'fix':
                    discount = self_obj.discount_amount
                    res = discount
                elif self_obj.discount_method == 'per':
                    total_untaxed_amount = 0.0
                    for rec in self_obj.order_line:
                        total_untaxed_amount += rec.price_subtotal
                    print("total_untaxed_amount**",total_untaxed_amount)
                    discount = total_untaxed_amount * (self_obj.discount_amount/ 100)
                    res = discount
                else:
                    res = discount
            else:
                total_discount = 0.0
                for line in self_obj.order_line:
                    total_discount += (line.price_unit * line.discount * line.product_uom_qty)/100 + line.fixed_amount
                res = total_discount

        return res


    @api.depends('order_line.price_total','discount_amount','discount_selection','discount_method',)
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        cur_obj = self.env['res.currency']
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal

                amount_tax += line.price_tax

            res = self._calculate_discount()
            untaxed_discount_amount =  amount_untaxed - res if order.discount_selection == 'global' else amount_untaxed
            order.update({'discount_amt' : res,
                  'amount_untaxed': untaxed_discount_amount,
                  'amount_tax': amount_tax,
                  'amount_total': untaxed_discount_amount + amount_tax if order.discount_selection == 'line' else untaxed_discount_amount + order.taxes_amount,
                  })



    def _prepare_invoice(self):
        res = super(sale_order,self)._prepare_invoice()

        discount_type = False
        if self.discount_method == 'per':
            discount_type = 'percent'
        elif self.discount_method == 'fix':
            discount_type = 'fixed'


        res.update({
            'discount_selection': self.discount_selection,
            'global_discount_type': discount_type,
            'global_order_discount': self.discount_amount,
            'total_discount': self.discount_amt,
            'conversion_rate_enable': self.conversion_rate_enable,
            'conversion_rate': self.conversion_rate,
            'total_conversion_rate': self.total_conversion_rate,
            'margin': self.margin,
            'tax_ids':[(6, 0, self.tax_ids.ids)],
            'taxes_amount':self.taxes_amount,
            'global_untaxed_amount':self.amount_untaxed,
            'compute_apply_tax': True,
        })
        return res
        
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    is_apply_on_discount_amount =  fields.Boolean("Tax Apply After Discount")
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    fixed_amount = fields.Monetary(string="Fixed Amount")
    estimated_cost =  fields.Monetary(string="Estimated Cost")

    actual_cost = fields.Float(compute="_compute_actual_cost")



    # @api.depends('price_unit')
    def _compute_actual_cost(self):
        for rec in self:
            rec.actual_cost = 0.0
            purchase_order_line_ids = self.env['purchase.order.line'].search(
                [('product_id', '=', rec.product_id.id), ('order_id.state', '=', 'purchase')])
            if purchase_order_line_ids:
                for order_line in purchase_order_line_ids:
                    if order_line.order_id.origin != False:
                        if rec.order_id.name in order_line.order_id.origin.split(','):
                            rec.actual_cost = order_line.price_unit
                        else:
                            rec.actual_cost = rec.product_id.standard_price
                    else:
                        rec.actual_cost = rec.product_id.standard_price
            else:
                rec.actual_cost = rec.product_id.standard_price


            # order_line_ids= purchase_order_line.filtered(lambda order_line: order_line.order_id.state == 'purchase' and (rec.order_id.name in (order_line.order_id.origin.split(',')) ))
            # rec.actual_cost = order_line_ids[0].price_unit
            #

            # if rec.order_id.origin != False:
                # origins = rec.order_id.origin.split(',')
                # filtered_origin = [rec for rec in origins if rec.startswith('S')]
                # if filtered_origin != False:
                #     sale_order_lines = self.env["sale.order.line"].sudo().search(
                #         [('order_id.name', 'in', filtered_origin), ('product_id', '=', rec.product_id.id)])
                #     if sale_order_lines.ids:
                #         for sale_line in sale_order_lines:
                #             sale_line.actual_cost = order_line_ids.price_unit
                #         rec.actual_cost_compute = True

    @api.onchange('discount_method')
    def onchange_percent_discount(self):

        if self.discount_method == 'fix':
            self.discount = 0.0

        if self.discount_method == 'per':
            self.fixed_amount = 0.0

    def _prepare_invoice_line(self):
        prep_vals = super(sale_order_line, self)._prepare_invoice_line()

        discount_type = False
        if self.discount_method == 'per':
            discount_type = 'percent'
        elif self.discount_method == 'fix':
            discount_type = 'fixed'

        prep_vals['fixed_amount'] = self.fixed_amount
        prep_vals['discount_type'] = discount_type
        prep_vals['estimated_cost'] = self.estimated_cost
        prep_vals['actual_cost'] = self.actual_cost
        return prep_vals




    @api.depends('product_uom_qty', 'discount','fixed_amount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:

            price = (line.price_unit - line.fixed_amount) * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                # - line.fixed_amount
                'price_total': taxes['total_included'] ,
                # - line.fixed_amount
                'price_subtotal': taxes['total_excluded'] ,
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
