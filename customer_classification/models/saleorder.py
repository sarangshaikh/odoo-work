from odoo import models, fields,tools,api,_
from odoo.addons import decimal_precision as dp

class SaleOrderExt(models.Model):
    _inherit = 'sale.order'
    customer_class = fields.Selection([
    	('e_com', 'E-Commerce'),
    	('retail', 'Retail'),
    	('trade', 'Trade')],
        string="Customer Classification",
    )



    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id.id:
            self.customer_class = self.partner_id.customer_class


class SaleReportExt(models.Model):
    _inherit = "sale.report"


    customer_class = fields.Selection([
    	('e_com', 'E-Commerce'),
    	('retail', 'Retail'),
    	('trade', 'Trade')],
        string="Customer Classification",
        readonly = True
        ,store=True)


    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sale_report')
        self.env.cr.execute("""
             CREATE OR REPLACE VIEW public.sale_report AS 
             SELECT min(l.id) AS id,
                l.product_id,
                t.uom_id AS product_uom,
                sum(l.product_uom_qty / u.factor * u2.factor) AS product_uom_qty,
                sum(l.qty_delivered / u.factor * u2.factor) AS qty_delivered,
                sum(l.qty_invoiced / u.factor * u2.factor) AS qty_invoiced,
                sum(l.qty_to_invoice / u.factor * u2.factor) AS qty_to_invoice,
                sum(l.price_total /
                    CASE COALESCE(s.currency_rate, 0::numeric)
                        WHEN 0 THEN 1.0
                        ELSE s.currency_rate
                    END) AS price_total,
                sum(l.price_subtotal /
                    CASE COALESCE(s.currency_rate, 0::numeric)
                        WHEN 0 THEN 1.0
                        ELSE s.currency_rate
                    END) AS price_subtotal,
                sum(l.untaxed_amount_to_invoice /
                    CASE COALESCE(s.currency_rate, 0::numeric)
                        WHEN 0 THEN 1.0
                        ELSE s.currency_rate
                    END) AS untaxed_amount_to_invoice,
                sum(l.untaxed_amount_invoiced /
                    CASE COALESCE(s.currency_rate, 0::numeric)
                        WHEN 0 THEN 1.0
                        ELSE s.currency_rate
                    END) AS untaxed_amount_invoiced,
                count(*) AS nbr,
                s.name,
                s.date_order AS date,
                s.state,
                s.partner_id,
                s.customer_class,
                s.user_id,
                s.company_id,
                s.campaign_id,
                s.medium_id,
                s.source_id,
                date_part('epoch'::text, avg(date_trunc('day'::text, s.date_order) - date_trunc('day'::text, s.create_date))) / (24 * 60 * 60)::numeric(16,2)::double precision AS delay,
                t.categ_id,
                s.pricelist_id,
                s.analytic_account_id,
                s.team_id,
                p.product_tmpl_id,
                partner.country_id,
                partner.industry_id,
                partner.commercial_partner_id,
                sum(p.weight * l.product_uom_qty / u.factor * u2.factor) AS weight,
                sum(p.volume * l.product_uom_qty / u.factor * u2.factor) AS volume,
                l.discount,
                sum(l.price_unit * l.product_uom_qty * l.discount / 100.0 /
                    CASE COALESCE(s.currency_rate, 0::numeric)
                        WHEN 0 THEN 1.0
                        ELSE s.currency_rate
                    END) AS discount_amount,
                s.id AS order_id,
                s.date_order <= (timezone('utc'::text, now()) - ((COALESCE(w.cart_abandoned_delay, '1'::double precision) || ' hour'::text)::interval)) AND s.website_id <> NULL::integer AND s.state::text = 'draft'::text AND s.partner_id <> 5 AS is_abandoned_cart,
                s.invoice_status,
                sum(l.margin /
                    CASE COALESCE(s.currency_rate, 0::numeric)
                        WHEN 0 THEN 1.0
                        ELSE s.currency_rate
                    END) AS margin,
                s.website_id,
                s.warehouse_id,
                date_part('day'::text, s.date_order - s.create_date) AS days_to_confirm
               FROM sale_order_line l
                 JOIN sale_order s ON l.order_id = s.id
                 JOIN res_partner partner ON s.partner_id = partner.id
                 LEFT JOIN product_product p ON l.product_id = p.id
                 LEFT JOIN product_template t ON p.product_tmpl_id = t.id
                 LEFT JOIN uom_uom u ON u.id = l.product_uom
                 LEFT JOIN uom_uom u2 ON u2.id = t.uom_id
                 LEFT JOIN product_pricelist pp ON s.pricelist_id = pp.id
                 LEFT JOIN crm_team team ON team.id = s.team_id
                 LEFT JOIN website w ON w.id = s.website_id
              WHERE l.product_id IS NOT NULL
              GROUP BY l.product_id,s.customer_class, l.order_id, t.uom_id, t.categ_id, s.name, s.date_order, s.partner_id, s.user_id, s.state, s.company_id, s.campaign_id, s.medium_id, s.source_id, s.pricelist_id, s.analytic_account_id, s.team_id, p.product_tmpl_id, partner.country_id, partner.industry_id, partner.commercial_partner_id, l.discount, s.id, w.cart_abandoned_delay, s.invoice_status, s.website_id, s.warehouse_id;

            """)
