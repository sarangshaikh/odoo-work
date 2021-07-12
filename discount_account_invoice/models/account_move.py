# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"


    margin =  fields.Monetary(string="Margin", compute="_compute_margin")



    compute_apply_tax = fields.Boolean()
    tax_ids = fields.Many2many('account.tax', string='Taxes', ondelete='restrict')
    # compute = '_tax_amount',
    taxes_amount = fields.Monetary( string="Tax")
    global_untaxed_amount = fields.Monetary(compute='_global_untaxed_amount', string="Subtotal")

    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.actual_cost')
    def _compute_margin(self):
        total_unit_price = 0.0
        total_actual_cost = 0.0
        for rec in self:
            for line in self.invoice_line_ids.filtered(lambda x: not x.is_global_tax_line):
                total_unit_price += line.quantity * line.price_unit
                total_actual_cost += line.quantity * line.actual_cost

            rec.margin = total_unit_price - total_actual_cost

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if res.compute_apply_tax == True:
            res.calculate_tax_amount()
        return res



    @api.depends('invoice_line_ids.price_subtotal')
    def _global_untaxed_amount(self):
        for rec in self:
            rec.global_untaxed_amount = 0.0
            subtotal = 0.0
            discount = 0.0
            if rec.discount_selection == 'global':
                for line in self.invoice_line_ids.filtered(lambda x: not x.is_global_tax_line):
                    print(line.account_id.name)
                    subtotal+= line.price_subtotal

                if rec.global_discount_type == 'fixed':
                    discount = rec.global_order_discount
                elif rec.global_discount_type == 'percent':
                    discount = subtotal * (rec.global_order_discount / 100)

                rec.global_untaxed_amount = subtotal - discount

            else:
                rec.global_untaxed_amount = 0.0

    # @api.depends('tax_ids','global_discount_type', 'global_order_discount','discount_selection','global_untaxed_amount')
    # def _tax_amount(self):
    #     for rec in self:
    #         rec.taxes_amount = 0.0
    #         print("rec",rec)

    # @api.depends('tax_ids','global_discount_type', 'global_order_discount','discount_selection','global_untaxed_amount')
    def calculate_tax_amount(self):
        for rec in self:
            rec.taxes_amount = 0.0
            if rec.discount_selection == 'global':
                if not rec._origin.id or not isinstance(rec._origin.id, int):
                    raise UserError(_("You Need To Save First Before Changing To Global!!"))

                if rec.tax_ids.ids:
                    for tax in rec.tax_ids:
                        rec.taxes_amount += (tax.amount * rec.global_untaxed_amount) / 100

                    print("rec.invoice_line_ids.mapped('is_global_tax_line')",rec.invoice_line_ids.mapped('is_global_tax_line'))
                    if not  True in rec.invoice_line_ids.mapped('is_global_tax_line'):
                        global_tax_vals = {
                            'name':"Global Tax",
                            'move_id': rec.id,
                            'account_id': int(rec.tax_ids[0].mapped('invoice_repartition_line_ids.account_id')[0].id),
                            'price_unit': rec.taxes_amount,
                            'quantity': 1,
                            'is_global_tax_line': True
                        }

                        invoice_line= rec.env['account.move.line'].with_context(check_move_validity=False).create(global_tax_vals)
                        rec.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True, recompute_tax_base_amount=True)
                    else:
                        rec.invoice_line_ids.with_context(check_move_validity=False).filtered(lambda  x:x.is_global_tax_line == True)[0].update({'price_unit': rec.taxes_amount})
                        rec.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True, recompute_tax_base_amount=True)

                else:
                    rec.taxes_amount = 0.0
                    global_tax_line = rec.invoice_line_ids.with_context(check_move_validity=False).filtered(lambda x: x.is_global_tax_line == True)
                    if global_tax_line:
                        global_tax_line.unlink()
                        rec.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True, recompute_tax_base_amount=True)
            else:
                rec.taxes_amount = 0.0
                global_tax_line = rec.invoice_line_ids.with_context(check_move_validity=False).filtered(lambda x: x.is_global_tax_line == True)
                if global_tax_line:
                        global_tax_line.unlink()
                        rec.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True,
                                                                                         recompute_tax_base_amount=True)


    @api.onchange('discount_selection')
    def onchange_sale_discount_selection(self):
        print("chal raha hai")
        if self.discount_selection == 'global':

            for line in self.invoice_line_ids:
                line.discount = 0.0
                line.fixed_amount = 0.0
                line.discount_type = False
                line.tax_ids= False
            self.amount_by_group = False

            self._recompute_tax_lines()
            self.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True,
                                                                             recompute_tax_base_amount=True)

        else:
            self.global_discount_type = 'fixed'
            self.global_order_discount = 0.0
            self.tax_ids = False
            self.taxes_amount = 0.0
            self.calculate_tax_amount()

            # self.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True,
            #                                                                       recompute_tax_base_amount=True)


            # global_tax_line = self._origin.invoice_line_ids.with_context(check_move_validity=False).filtered(lambda x: x.is_global_tax_line == True)
            # print("self._origin.invoice_line_ids.with_context(check_move_validity=False).filtered(lambda x: x.is_global_tax_line == True)",self._origin.invoice_line_ids.with_context(check_move_validity=False).filtered(lambda x: x.is_global_tax_line == True))
            # if global_tax_line:
            #     print("global_tax_line",global_tax_line)
            #     global_tax_line[0].unlink()
                # self._recompute_tax_lines()
                # self.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True,
                #                                                                  recompute_tax_base_amount=True)

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        ''' Compute the dynamic tax lines of the journal entry.

        :param lines_map: The line_ids dispatched by type containing:
            * base_lines: The lines having a tax_ids set.
            * tax_lines: The lines having a tax_line_id set.
            * terms_lines: The lines generated by the payment terms of the invoice.
            * rounding_lines: The cash rounding lines of the invoice.
        '''
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                if base_line.currency_id:
                    if base_line.discount_type and base_line.discount_type == 'fixed':
                        price_unit_foreign_curr = sign * (base_line.price_unit - (base_line.discount / (base_line.quantity or 1.0)))
                    else:
                        price_unit_foreign_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                    price_unit_comp_curr = base_line.currency_id._convert(price_unit_foreign_curr, move.company_id.currency_id, move.company_id, move.date)
                else:
                    price_unit_foreign_curr = 0.0
                    if base_line.discount_type and base_line.discount_type == 'fixed':
                        price_unit_comp_curr = sign * (base_line.price_unit - (base_line.discount / (base_line.quantity or 1.0)))
                    else:
                        price_unit_comp_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            else:
                quantity = 1.0
                price_unit_foreign_curr = base_line.amount_currency
                price_unit_comp_curr = base_line.balance

            balance_taxes_res = base_line.tax_ids._origin.compute_all(
                price_unit_comp_curr,
                currency=base_line.company_currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=self.type in ('out_refund', 'in_refund'),
            )

            if base_line.currency_id:
                # Multi-currencies mode: Taxes are computed both in company's currency / foreign currency.
                amount_currency_taxes_res = base_line.tax_ids._origin.compute_all(
                    price_unit_foreign_curr,
                    currency=base_line.currency_id,
                    quantity=quantity,
                    product=base_line.product_id,
                    partner=base_line.partner_id,
                    is_refund=self.type in ('out_refund', 'in_refund'),
                )
                for b_tax_res, ac_tax_res in zip(balance_taxes_res['taxes'], amount_currency_taxes_res['taxes']):
                    tax = self.env['account.tax'].browse(b_tax_res['id'])
                    b_tax_res['amount_currency'] = ac_tax_res['amount']

                    # A tax having a fixed amount must be converted into the company currency when dealing with a
                    # foreign currency.
                    if tax.amount_type == 'fixed':
                        b_tax_res['amount'] = base_line.currency_id._convert(b_tax_res['amount'], move.company_id.currency_id, move.company_id, move.date)

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'balance': 0.0,
                    'amount_currency': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                line.tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            line.tag_ids = compute_all_vals['base_tags']

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'balance': 0.0,
                    'amount_currency': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['balance'] += tax_vals['amount']
                taxes_map_entry['amount_currency'] += tax_vals.get('amount_currency', 0.0)
                taxes_map_entry['tax_base_amount'] += tax_vals['base']
                taxes_map_entry['grouping_dict'] = grouping_dict
            line.tax_exigible = tax_exigible

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # Don't create tax lines with zero balance.
            if self.currency_id.is_zero(taxes_map_entry['balance']) and self.currency_id.is_zero(taxes_map_entry['amount_currency']):
                taxes_map_entry['grouping_dict'] = False

            tax_line = taxes_map_entry['tax_line']
            tax_base_amount = -taxes_map_entry['tax_base_amount'] if self.is_inbound() else taxes_map_entry['tax_base_amount']

            if not tax_line and not taxes_map_entry['grouping_dict']:
                continue
            elif tax_line and recompute_tax_base_amount:
                tax_line.tax_base_amount = tax_base_amount
            elif tax_line and not taxes_map_entry['grouping_dict']:
                # The tax line is no longer used, drop it.
                self.line_ids -= tax_line
            elif tax_line:
                tax_line.update({
                    'amount_currency': taxes_map_entry['amount_currency'],
                    'debit': taxes_map_entry['balance'] > 0.0 and taxes_map_entry['balance'] or 0.0,
                    'credit': taxes_map_entry['balance'] < 0.0 and -taxes_map_entry['balance'] or 0.0,
                    'tax_base_amount': tax_base_amount,
                })
            else:
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                tax_line = create_method({
                    'name': tax.name,
                    'move_id': self.id,
                    'partner_id': line.partner_id.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'quantity': 1.0,
                    'date_maturity': False,
                    'amount_currency': taxes_map_entry['amount_currency'],
                    'debit': taxes_map_entry['balance'] > 0.0 and taxes_map_entry['balance'] or 0.0,
                    'credit': taxes_map_entry['balance'] < 0.0 and -taxes_map_entry['balance'] or 0.0,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                tax_line._onchange_amount_currency()
                tax_line._onchange_balance()





    #
    # @api.depends('line_ids.debit', 'line_ids.credit', 'line_ids.currency_id',
    #              'line_ids.amount_currency', 'line_ids.amount_residual',
    #              'line_ids.amount_residual_currency',
    #              'line_ids.payment_id.state', 'global_discount_type',
    #              'global_order_discount')
    # def _compute_amount(self):
    #     invoice_ids = [
    #         move.id for move in self
    #         if move.id and move.is_invoice(include_receipts=True)
    #     ]
    #     self.env['account.payment'].flush(['state'])
    #     if invoice_ids:
    #         self._cr.execute(
    #             '''
    #                 SELECT move.id
    #                 FROM account_move move
    #                 JOIN account_move_line line ON line.move_id = move.id
    #                 JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
    #                 JOIN account_move_line rec_line ON
    #                     (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
    #                     OR
    #                     (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
    #                 JOIN account_payment payment ON payment.id = rec_line.payment_id
    #                 JOIN account_journal journal ON journal.id = rec_line.journal_id
    #                 WHERE payment.state IN ('posted', 'sent')
    #                 AND journal.post_at = 'bank_rec'
    #                 AND move.id IN %s
    #             ''', [tuple(invoice_ids)])
    #         in_payment_set = set(res[0] for res in self._cr.fetchall())
    #     else:
    #         in_payment_set = {}
    #
    #     for move in self:
    #         total_untaxed = 0.0
    #         total_untaxed_currency = 0.0
    #         total_tax = 0.0
    #         total_tax_currency = 0.0
    #         total_residual = 0.0
    #         total_residual_currency = 0.0
    #         total = 0.0
    #         total_currency = 0.0
    #         total_discount = 0.0
    #         global_discount = 0.0
    #         global_discount_currency = 0.0
    #         currencies = set()
    #
    #         for line in move.line_ids:
    #             if line.currency_id:
    #                 currencies.add(line.currency_id)
    #
    #             if move.is_invoice(include_receipts=True):
    #                 # === Invoices ===
    #
    #                 if not line.exclude_from_invoice_tab:
    #                     # Untaxed amount.
    #                     total_untaxed += line.balance
    #                     total_untaxed_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                     total_discount += line.discount if line.discount_type == 'fixed' else line.quantity * line.price_unit - line.price_subtotal
    #                 elif line.tax_line_id:
    #                     # Tax amount.
    #                     total_tax += line.balance
    #                     total_tax_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.is_global_line:
    #                     # Discount amount.
    #                     global_discount = line.balance
    #                     global_discount_currency = line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.account_id.user_type_id.type in ('receivable', 'payable'):
    #                     # Residual amount.
    #                     total_residual += line.amount_residual
    #                     total_residual_currency += line.amount_residual_currency
    #             else:
    #                 # === Miscellaneous journal entry ===
    #                 if line.debit:
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #
    #         if move.type == 'entry' or move.is_outbound():
    #             sign = 1
    #         else:
    #             sign = -1
    #
    #         total_discount += -1 * sign * (global_discount_currency if len(
    #             currencies) == 1 else global_discount)
    #         move.total_discount = total_discount
    #         move.amount_untaxed = sign * (total_untaxed_currency if len(
    #             currencies) == 1 else total_untaxed)
    #         move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
    #         move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
    #         move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
    #         move.amount_untaxed_signed = -total_untaxed
    #         move.amount_tax_signed = -total_tax
    #         move.amount_total_signed = abs(total) if move.type == 'entry' else -total
    #         move.amount_residual_signed = total_residual
    #
    #         currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
    #         is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual
    #
    #         # Compute 'invoice_payment_state'.
    #         if move.type == 'entry':
    #             move.invoice_payment_state = False
    #         elif move.state == 'posted' and is_paid:
    #             if move.id in in_payment_set:
    #                 move.invoice_payment_state = 'in_payment'
    #             else:
    #                 move.invoice_payment_state = 'paid'
    #         else:
    #             move.invoice_payment_state = 'not_paid'

    @api.depends('global_order_discount','discount_selection','global_discount_type')
    def _calculate_discount(self):
        res = 0.0
        discount = 0.0
        for self_obj in self:
            if self_obj.discount_selection == 'global':
                for line in self.invoice_line_ids:
                    line.discount_type =False
                    line.discount = 0.0
                    line.fixed_amount = 0.0
                if self_obj.global_discount_type == 'fixed':
                    discount = self_obj.global_order_discount
                    res = discount
                elif self_obj.global_discount_type == 'percent':
                    subtotal = 0.0
                    for rec in self.invoice_line_ids.filtered(lambda x: not x.is_global_tax_line):
                        subtotal +=rec.price_subtotal
                    discount = subtotal * (self_obj.global_order_discount / 100)
                    res = discount
                else:
                    res = discount
            else:
                total_discount = 0.0
                for line in self.invoice_line_ids:
                    total_discount += (line.price_unit * line.discount * line.quantity) / 100 if line.discount_type == 'percent' else line.discount
                res = total_discount

        return res


    # @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.estimated_cost')
    # def _compute_margin(self):
    #     res = super(AccountMove,self)._compute_margin()
    #     print("res",res)
    #     for rec in self:
    #         rec.margin = rec.margin - rec.total_discount
    #     return res


    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state','global_discount_type',
                 'global_order_discount','tax_ids')
    def _compute_amount(self):
        invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
        self.env['account.payment'].flush(['state'])
        if invoice_ids:
            self._cr.execute(
                '''
                    SELECT move.id
                    FROM account_move move
                    JOIN account_move_line line ON line.move_id = move.id
                    JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                    JOIN account_move_line rec_line ON
                        (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
                        OR
                        (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
                    JOIN account_payment payment ON payment.id = rec_line.payment_id
                    JOIN account_journal journal ON journal.id = rec_line.journal_id
                    WHERE payment.state IN ('posted', 'sent')
                    AND journal.post_at = 'bank_rec'
                    AND move.id IN %s
                ''', [tuple(invoice_ids)]
            )
            in_payment_set = set(res[0] for res in self._cr.fetchall())
        else:
            in_payment_set = {}

        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.type == 'entry' else -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

            # Compute 'invoice_payment_state'.
            if move.type == 'entry':
                move.invoice_payment_state = False
            elif move.state == 'posted' and is_paid:
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            else:
                move.invoice_payment_state = 'not_paid'

            #Calculate Discount
            move.amount_untaxed = sum(line.price_subtotal for line in move.invoice_line_ids)
            res = move._calculate_discount()
            sum_of_price_subtotal = 0.0
            for line in move.invoice_line_ids:
                sum_of_price_subtotal += line.price_subtotal
            untaxed_discount_amount =  move.global_untaxed_amount if move.discount_selection == 'global' else sum_of_price_subtotal
            move.total_discount = res
            move.update({'amount_untaxed': untaxed_discount_amount})
            # move.amount_untaxed = untaxed_discount_amount
           # global pe tax ki line create karni hai tax amount plus nahn karna total main
            # + move.taxes_amount
            move.amount_total = untaxed_discount_amount + move.amount_tax if move.discount_selection == 'line' else untaxed_discount_amount+ move.taxes_amount
            amount_total_company_signed = move.amount_total
            amount_untaxed_signed = move.amount_untaxed
            if move.currency_id and move.currency_id != move.company_id.currency_id:
                amount_total_company_signed = move.currency_id.compute(move.amount_total, move.company_id.currency_id)
                amount_untaxed_signed = move.currency_id.compute(move.amount_untaxed, move.company_id.currency_id)
            sign = move.type in ['in_refund', 'out_refund'] and -1 or 1
            move.amount_total_company_signed = amount_total_company_signed * sign
            move.amount_total_signed = move.amount_total * sign
            move.amount_untaxed_signed = amount_untaxed_signed * sign

    total_discount = fields.Monetary(string='Discount', store=True,
        readonly=True, default=0, compute='_compute_amount', tracking=True)

    global_discount_type = fields.Selection([('fixed', 'Fixed'),
                                             ('percent', 'Percent')],
                                            string="Discount Type", default="percent", tracking=True)
    global_order_discount = fields.Float(string='Global Discount', tracking=True,store = True)







    @api.onchange('global_discount_type', 'global_order_discount','discount_selection')
    def _onchange_global_order_discount(self):

        if not self.global_order_discount:

            global_discount_line = self.line_ids.filtered(lambda line: line.is_global_line)
            self.line_ids -= global_discount_line
        self._recompute_dynamic_lines()

    def _recompute_global_discount_lines(self):
        ''' Compute the dynamic global discount lines of the journal entry.'''
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)

        def _compute_payment_terms(self):
            sign = 1 if self.is_inbound() else -1

            IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
            discTax = IrConfigPrmtrSudo.get_param('account.global_discount_tax')
            if not discTax:
                discTax = 'untax'

            discount_balance = 0.0
            if self.discount_selection == 'line':
                total = self.amount_untaxed + self.amount_tax
            else:
                price_subtotal = 0.0
                for line in self.invoice_line_ids.filtered(lambda x: not x.is_global_tax_line):
                   price_subtotal += line.price_subtotal
                total =  price_subtotal + self.taxes_amount

            if discTax != 'taxed':

                if self.discount_selection == 'line':
                    total = self.amount_untaxed
                else:
                    taxed_price_subtotal = 0.0
                    for line in self.invoice_line_ids.filtered(lambda x: not x.is_global_tax_line):
                        taxed_price_subtotal += line.price_subtotal
                    total = taxed_price_subtotal
                    # total = self.global_untaxed_amount



            if self.global_discount_type == 'fixed':
                discount_balance = sign * (self.global_order_discount or 0.0)
            else:
                discount_balance = sign * (total * (self.global_order_discount or 0.0) / 100)

            if self.currency_id == self.company_id.currency_id:
                discount_amount_currency = 0.0
            else:
                discount_amount_currency = discount_balance
                discount_balance = self.currency_id._convert(
                    discount_amount_currency, self.company_id.currency_id, self.company_id, self.date)

            if self.invoice_payment_term_id:
                date_maturity = self.invoice_date or today
            else:
                date_maturity = self.invoice_date_due or self.invoice_date or today
            return [(date_maturity, discount_balance, discount_amount_currency)]

        def _compute_diff_global_discount_lines(self, existing_global_lines, account, to_compute):
            new_global_discount_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency in to_compute:
                if existing_global_lines:
                    candidate = existing_global_lines[0]
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                    candidate = create_method({
                        'name': 'Global Discount',
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                        'is_global_line': True,
                    })
                new_global_discount_lines += candidate
                if in_draft_mode:
                    candidate._onchange_amount_currency()
                    candidate._onchange_balance()
            return new_global_discount_lines

        existing_global_lines = self.line_ids.filtered(lambda line: line.is_global_line)
        others_lines = self.line_ids.filtered(lambda line: not line.is_global_line)

        if not others_lines:
            self.line_ids -= existing_global_lines
            return

        if existing_global_lines:
            account = existing_global_lines[0].account_id
        else:
            IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
            if self.type in ['out_invoice', 'out_refund', 'out_receipt']:
                account = self.env.company.discount_account_invoice
            else:
                account = self.env.company.discount_account_bill
            if not account:
                raise UserError(
                    _("Global Discount!\nPlease first set account for global discount in account setting."))

        to_compute = _compute_payment_terms(self)

        new_terms_lines = _compute_diff_global_discount_lines(self, existing_global_lines, account, to_compute)

        self.line_ids -= existing_global_lines - new_terms_lines

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        ''' Recompute all lines that depend of others.

        For example, tax lines depends of base lines (lines having tax_ids set). This is also the case of cash rounding
        lines that depend of base lines or tax lines depending the cash rounding strategy. When a payment term is set,
        this method will auto-balance the move with payment term lines.

        :param recompute_all_taxes: Force the computation of taxes. If set to False, the computation will be done
                                    or not depending of the field 'recompute_tax_line' in lines.
        '''
        for invoice in self:
            if invoice.global_order_discount:
                # Dispatch lines and pre-compute some aggregated values like taxes.
                for line in invoice.line_ids:
                    if line.recompute_tax_line:
                        recompute_all_taxes = True
                        line.recompute_tax_line = False

                # Compute taxes.
                if recompute_all_taxes:
                    invoice._recompute_tax_lines()
                if recompute_tax_base_amount:
                    invoice._recompute_tax_lines(recompute_tax_base_amount=True)

                if invoice.is_invoice(include_receipts=True):

                    # Compute cash rounding.
                    invoice._recompute_cash_rounding_lines()

                    # Compute global discount line.
                    invoice._recompute_global_discount_lines()

                    # Compute payment terms.
                    invoice._recompute_payment_terms_lines()

                    # Only synchronize one2many in onchange.
                    if invoice != invoice._origin:
                        invoice.invoice_line_ids = invoice.line_ids.filtered(
                            lambda line: not line.exclude_from_invoice_tab)
            else:
                super(AccountMove, invoice)._recompute_dynamic_lines(recompute_all_taxes=False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_type = fields.Selection([('fixed', 'Fixed'),
                                      ('percent', 'Percent')],
                                     string="Discount Type", default="percent")
    is_global_line = fields.Boolean(string='Global Discount Line',
        help="This field is used to separate global discount line.")


    is_global_tax_line = fields.Boolean(string='Global tax Line')

    @api.onchange('discount_type', 'fixed_amount','discount_selection')
    def onchange_percent_discount(self):
            if self.discount_type == 'fixed':
                self.discount = 0.0
                if self.fixed_amount != 0.0:
                    self.discount = self.fixed_amount

            if self.discount_type == 'percent':
                self.fixed_amount = 0.0
                self.discount = 0.0

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        discount_type = ''
        if self._context and self._context.get('wk_vals_list', []):
            for vals in self._context.get('wk_vals_list', []):
                if price_unit == vals.get('price_unit', 0.0) and quantity == vals.get('quantity', 0.0) and discount == vals.get('discount', 0.0) and product.id == vals.get('product_id', False) and partner.id == vals.get('partner_id', False):
                    discount_type = vals.get('discount_type', '')
        discount_type = self.discount_type or discount_type or ''
        if discount_type == 'fixed':
            price_unit_wo_discount = price_unit * quantity - discount
            quantity = 1.0
        else:
            price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, balance, move_type, currency, taxes, price_subtotal):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param balance:         The new balance.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        balance_form = 'credit' if balance > 0 else 'debit'
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        balance *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if currency.is_zero(balance - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            taxes_res = taxes._origin.compute_all(balance, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    balance += tax_res['amount']

        discount_type = ''
        if self._context and self._context.get('wk_vals_list', []):
            for vals in self._context.get('wk_vals_list', []):
                if quantity == vals.get('quantity', 0.0) and discount == vals.get('discount', 0.0) and balance == vals.get(balance_form, 0.0):
                    discount_type = vals.get('discount_type', '')
        discount_type = self.discount_type or discount_type or ''
        if discount_type == 'fixed':
            if balance:
                vals = {
                    'quantity': quantity or 1.0,
                    'price_unit': (balance + discount) / (quantity or 1.0),
                }
            else:
                vals = {}
        else:
            discount_factor = 1 - (discount / 100.0)
            if balance and discount_factor:
                # discount != 100%
                vals = {
                    'quantity': quantity or 1.0,
                    'price_unit': balance / discount_factor / (quantity or 1.0),
                }
            elif balance and not discount_factor:
                # discount == 100%
                vals = {
                    'quantity': quantity or 1.0,
                    'discount': 0.0,
                    'price_unit': balance / (quantity or 1.0),
                }
            else:
                vals = {}
        return vals

    @api.onchange('quantity', 'discount', 'discount_type', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        return super(AccountMoveLine, self)._onchange_price_subtotal()

    @api.model_create_multi
    def create(self, vals_list):
        context = self._context.copy()
        context.update({'wk_vals_list': vals_list})
        res = super(AccountMoveLine, self.with_context(context)).create(vals_list)
        return res
