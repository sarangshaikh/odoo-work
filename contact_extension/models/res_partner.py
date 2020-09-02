# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'
    code = fields.Char(string='Code', required=False,
                       copy=False, readonly=False, index=True,
                       default=lambda self: _(''))

    is_customer = fields.Boolean(string="Customer")
    is_supplier = fields.Boolean("Supplier")


    customer_classification = fields.Selection([('diamond', 'Diamond'), ('regular', 'Regular'), ('basic', 'Basic')],
                                               string="Customer Classification")
    tax_exempt = fields.Boolean(string='Tax Exempt')
    customer_color = fields.Char(string="Customer Color")
    customer_type = fields.Selection([('c','C'),('n','N'),('p','P')],string="Customer Type")
    fax = fields.Char(string="Fax")
    phone = fields.Char(string="Primary Phone")
    phone2 = fields.Char(string='Secondary Phone')
    territory = fields.Char()

    @api.onchange('is_customer','is_supplier')
    def onchange_contact_selection(self):
        if self.is_customer:
            self.is_supplier = False
        else:
            self.is_customer = False

    @api.model
    def create(self, vals):
        print("&&**", vals,)
        print("&self**", self,)
        print("context&&**",self.env.context)
        print("contextnext**", self._context)
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        if not search_partner_mode:
            if 'is_customer' in vals and vals['is_customer'] == True:
                self.with_context({'res_partner_search_mode': 'customer'})

            elif 'is_supplier' in vals and vals['is_supplier'] == True:
                self.with_context({'res_partner_search_mode': 'supplier'})

        else:
            vals['is_customer'] = search_partner_mode == 'customer'
            vals['is_supplier'] = search_partner_mode == 'supplier'

        if 'is_customer' in vals and vals['is_customer'] and 'customer_rank' not in vals:
            vals['customer_rank'] = 1
            vals['code'] = self.env['ir.sequence'].next_by_code(
                                                    'res.partner.customer.code') or 'New'
        elif 'is_supplier' in vals and vals['is_supplier'] and 'supplier_rank' not in vals:
            vals['supplier_rank'] = 1
            vals['code'] = self.env['ir.sequence'].next_by_code(
                                                        'res.partner.supplier.code') or 'New'
        partner = super().create(vals)

        return partner



    def action_generate_sequence(self):
        print("self",self)
        for partner in self:
            print("partner",partner)
            print("partner.code",partner.code)
            if not partner.code:
                if partner.is_customer == False and partner.is_supplier == False:
                    raise UserError(_("Please select Customer or Supplier in %s Contact!" %(partner.name)))
                elif partner.is_customer == True:
                    partner.customer_rank = 1
                    partner.code = self.env['ir.sequence'].next_by_code(
                                                    'res.partner.customer.code') or 'New'
                elif partner.is_supplier == True:
                    partner.supplier_rank = 1
                    partner.code = self.env['ir.sequence'].next_by_code(
                        'res.partner.supplier.code') or 'New'







    @api.onchange('customer_type')
    def onchange_customer_color_type(self):
        if self.customer_type == 'c':
            self.customer_color = '#008000'
        elif self.customer_type == 'n':
            self.customer_color = '#FF0000'
        elif self.customer_type == 'p':
            self.customer_color = '#000000'

