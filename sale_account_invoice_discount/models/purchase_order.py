# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrderLineExtended(models.Model):
    _inherit = 'purchase.order.line'

    actual_cost_compute = fields.Float(compute="_compute_actual_cost",copy=False)


    @api.depends('price_unit')
    def _compute_actual_cost(self):
        for rec in self:
            rec.actual_cost_compute = False
            if rec.order_id.state == 'purchase':
                if rec.order_id.origin != False:
                    origins = rec.order_id.origin.split(',')
                    filtered_origin = [rec for rec in origins if rec.startswith('S')]
                    if filtered_origin != False:
                        sale_order_lines = self.env["sale.order.line"].sudo().search([('order_id.name', 'in', filtered_origin), ('product_id', '=', rec.product_id.id)])
                        if sale_order_lines.ids:
                            for sale_line in sale_order_lines:
                                sale_line.actual_cost= rec.price_unit
                            rec.actual_cost_compute = True


