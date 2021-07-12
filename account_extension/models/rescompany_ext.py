# -*- coding: utf-8 -*-
from odoo import fields, models,api


class CompanyExtension(models.Model):
    _inherit = "res.company"
    strn = fields.Char(string="STRN")

    vat = fields.Char(related='partner_id.vat', string="NTN", readonly=False)


class RespartnerExtension(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(string='NTN',
                      help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")

    strn = fields.Char(string="STRN")
