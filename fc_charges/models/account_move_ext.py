# -*- coding: utf-8 -*-
from odoo import api,fields,models,_
import odoo.addons.decimal_precision as dp
from datetime import date
from odoo import models, fields, api, _




#inherit AccountInvoice class. 
class AccountInvoice(models.Model):
    _inherit = "account.move"

    fc_invoice = fields.Many2one('account.move','FC Reference Invoice',copy=False)
    penalty = fields.Selection([('fixed', 'Amount'), ('penalty_percentage', 'Percentage'),],string='Late Fee Method')
    percentage_of_penalty = fields.Float("Late Fee Percentage",digits=dp.get_precision('Account'), default=0.0)
    fixed_amount = fields.Float("Late Fee Amount",default=0.0)
    is_fc_invoice = fields.Boolean(string="FC invoice",copy=False)
    # fc_line_saved = fields.Char()
    # late_fee_line_created = fields.Boolean()
    # statement_charges_line_created = fields.Boolean()



    def late_payment_penalty(self):
        invoice_ids = self.env['account.move'].search([('state', '=', 'posted'), ('type', '=', 'out_invoice'),('invoice_payment_state', '=', 'not_paid')])
        today_date = date.today()
        current_date = str(today_date)
        # current_date = datetime.date.today()
        product_late_fee = self.env.ref('fc_charges.penalty_product')
        unit_price = 0.0
        if invoice_ids:
            for invoice_id in invoice_ids:
                if invoice_id:
                    if invoice_id.invoice_date_due == False:
                        continue
                    elif str(invoice_id.invoice_date_due) < str(current_date):
                        if invoice_id.penalty != False and invoice_id.is_fc_invoice == False:

                            if invoice_id.penalty == 'fixed':
                                unit_price = invoice_id.fixed_amount

                            elif invoice_id.penalty == 'penalty_percentage':
                                unit_price = (invoice_id.amount_residual * invoice_id.percentage_of_penalty) / 100

                            if  invoice_id.fc_invoice.id == False :
                                invoice_vals = {
                                    'name': self.env['ir.sequence'].next_by_code('account.move.fc'),
                                    'partner_id': invoice_id.partner_id.id,
                                    'invoice_date': today_date,
                                    'invoice_origin': invoice_id.name,
                                    'type': 'out_invoice',
                                    'is_fc_invoice': True,
                                    'journal_id':self.env['account.journal'].search([('name','=','Customer Invoices')],limit=1).id,
                                    'invoice_line_ids': [(0, 0, {
                                        'product_id': product_late_fee.id,
                                        'price_unit': unit_price,
                                        'quantity': 1.0,
                                        'name': 'Late Fee Charges',
                                    })]
                                }

                                if invoice_vals:
                                    penality_invoice = self.env['account.move'].create(invoice_vals)
                                    invoice_id.fc_invoice = penality_invoice.id


