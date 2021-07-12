# -*- coding: utf-8 -*-
from odoo import fields, models,api


class SaleOrderExtension(models.Model):
    _inherit = "sale.order"

    business = fields.Selection([('new', 'New Bussiness'),('renewal', 'Renewal Bussiness')],string="Bussiness")

class SaleOrderLineExtension(models.Model):
    _inherit = "sale.order.line"

    duration  = fields.Integer(string="Duration (Years)")
    acv = fields.Float(compute="_compute_duration",store=True,readonly=True)
    tcv = fields.Float()

    @api.depends('duration','price_unit')
    def _compute_duration(self):
        for line in self:
            line.acv =0.0
            line.tcv = line.price_unit
            if line.price_unit > 0 and  line.duration > 0:
                line.acv = (line.price_unit / line.duration)


class SaleReportExtd(models.Model):

    _inherit = "sale.report"

    business = fields.Selection([('new', 'New Bussiness'),('renewal', 'Renewal Bussiness')],string="Bussiness")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['business'] = ", s.business as business"
        groupby += ', s.business'
        return super(SaleReportExtd, self)._query(with_clause, fields, groupby, from_clause)
