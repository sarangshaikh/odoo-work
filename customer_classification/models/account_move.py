from odoo import models, fields, api, tools


class AccountInvoiceExt(models.Model):
    _inherit = 'account.move'

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





class AccountReportExt(models.Model):
    _inherit = "account.invoice.report"

    customer_class = fields.Selection([
    	('e_com', 'E-Commerce'),
    	('retail', 'Retail'),
    	('trade', 'Trade')],
        string="Customer Classification",
        readonly = True
        ,store=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'account_invoice_report')
        self.env.cr.execute("""
             CREATE OR REPLACE VIEW public.account_invoice_report AS 
             SELECT line.id,
                line.move_id,
                line.product_id,
                line.account_id,
                line.analytic_account_id,
                line.journal_id,
                line.company_id,
                line.company_currency_id AS currency_id,
                line.partner_id AS commercial_partner_id,
                move.name,
                move.state,
                move.type,
                move.partner_id,
                move.customer_class,
                move.invoice_user_id,
                move.fiscal_position_id,
                move.invoice_payment_state,
                move.invoice_date,
                move.invoice_date_due,
                move.invoice_payment_term_id,
                move.invoice_partner_bank_id,
                (- line.balance) * (move.amount_residual_signed / NULLIF(move.amount_total_signed, 0.0)) * (line.price_total / NULLIF(line.price_subtotal, 0.0)) AS residual,
                (- line.balance) * (line.price_total / NULLIF(line.price_subtotal, 0.0)) AS amount_total,
                uom_template.id AS product_uom_id,
                template.categ_id AS product_categ_id,
                line.quantity / NULLIF(COALESCE(uom_line.factor, 1::numeric) / COALESCE(uom_template.factor, 1::numeric), 0.0) *
                    CASE
                        WHEN move.type::text = ANY (ARRAY['in_invoice'::character varying::text, 'out_refund'::character varying::text, 'in_receipt'::character varying::text]) THEN '-1'::integer
                        ELSE 1
                    END::numeric AS quantity,
                - line.balance AS price_subtotal,
                (- line.balance) / NULLIF(COALESCE(uom_line.factor, 1::numeric) / COALESCE(uom_template.factor, 1::numeric), 0.0) AS price_average,
                COALESCE(partner.country_id, commercial_partner.country_id) AS country_id,
                1 AS nbr_lines,
                move.team_id
               FROM account_move_line line
                 LEFT JOIN res_partner partner ON partner.id = line.partner_id
                 LEFT JOIN product_product product ON product.id = line.product_id
                 LEFT JOIN account_account account ON account.id = line.account_id
                 LEFT JOIN account_account_type user_type ON user_type.id = account.user_type_id
                 LEFT JOIN product_template template ON template.id = product.product_tmpl_id
                 LEFT JOIN uom_uom uom_line ON uom_line.id = line.product_uom_id
                 LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                 JOIN account_move move ON move.id = line.move_id
                 LEFT JOIN res_partner commercial_partner ON commercial_partner.id = move.commercial_partner_id
              WHERE (move.type::text = ANY (ARRAY['out_invoice'::character varying::text, 'out_refund'::character varying::text, 'in_invoice'::character varying::text, 'in_refund'::character varying::text, 'out_receipt'::character varying::text, 'in_receipt'::character varying::text])) AND line.account_id IS NOT NULL AND NOT line.exclude_from_invoice_tab
              GROUP BY line.id, line.move_id, line.product_id, line.account_id, line.analytic_account_id, line.journal_id, line.company_id, line.currency_id, line.partner_id, move.name, move.state, move.type, move.amount_residual_signed, move.amount_total_signed, move.partner_id,move.customer_class, move.invoice_user_id, move.fiscal_position_id, move.invoice_payment_state, move.invoice_date, move.invoice_date_due, move.invoice_payment_term_id, move.invoice_partner_bank_id, uom_template.id, uom_line.factor, template.categ_id, (COALESCE(partner.country_id, commercial_partner.country_id)), move.team_id;

        
        
        """)

        #         create OR REPLACE VIEW public.account_invoice_report AS
        #          WITH currency_rate AS (
        #                  SELECT r.currency_id,
        #                     COALESCE(r.company_id, c.id) AS company_id,
        #                     r.rate,
        #                     r.name AS date_start,
        #                     ( SELECT r2.name
        #                            FROM res_currency_rate r2
        #                           WHERE r2.name > r.name AND r2.currency_id = r.currency_id AND (r2.company_id IS NULL OR r2.company_id = c.id)
        #                           ORDER BY r2.name
        #                          LIMIT 1) AS date_end
        #                    FROM res_currency_rate r
        #                      JOIN res_company c ON r.company_id IS NULL OR r.company_id = c.id
        #                 )
        #          SELECT sub.id,
        #             sub.date,
        #             sub.product_id,
        #             sub.partner_id,
        #             sub.country_id,
        #             sub.account_analytic_id,
        #             sub.payment_term_id,
        #             sub.uom_name,
        #             sub.currency_id,
        #             sub.journal_id,
        #             sub.fiscal_position_id,
        #             sub.user_id,
        #             sub.company_id,
        #             sub.nbr,
        #             sub.type,
        #             sub.state,
        #             sub.categ_id,
        #             sub.date_due,
        #             sub.account_id,
        #             sub.account_line_id,
        #             sub.partner_bank_id,
        #             sub.product_qty,
        #             sub.price_total,
        #             sub.price_average,
        #
        #             COALESCE(cr.rate, 1::numeric) AS currency_rate,
        #             sub.residual,
        #             sub.commercial_partner_id,
        #             sub.team_id,
        #             sub.customer_class
        #            FROM ( SELECT ail.id,
        #                     ai.date_invoice AS date,
        #                     ail.product_id,
        #                     ai.partner_id,
        #                     ai.customer_class,
        #                     ai.payment_term_id,
        #                     ail.account_analytic_id,
        #                     u2.name AS uom_name,
        #                     ai.currency_id,
        #                     ai.journal_id,
        #                     ai.fiscal_position_id,
        #                     ai.user_id,
        #                     ai.company_id,
        #                     1 AS nbr,
        #                     ai.type,
        #                     ai.state,
        #                     pt.categ_id,
        #                     ai.date_due,
        #                     ai.account_id,
        #                     ail.account_id AS account_line_id,
        #                     ai.partner_bank_id,
        #                     sum(invoice_type.sign_qty::numeric * ail.quantity / u.factor * u2.factor) AS product_qty,
        #                     sum(ail.price_subtotal_signed * invoice_type.sign::numeric) AS price_total,
        #                     sum(abs(ail.price_subtotal_signed)) /
        #                         CASE
        #                             WHEN sum(ail.quantity / u.factor * u2.factor) <> 0::numeric THEN sum(ail.quantity / u.factor * u2.factor)
        #                             ELSE 1::numeric
        #                         END AS price_average,
        #                     ai.residual_company_signed / (( SELECT count(*) AS count
        #                            FROM account_invoice_line l
        #                           WHERE l.invoice_id = ai.id))::numeric * count(*)::numeric * invoice_type.sign::numeric AS residual,
        #                     ai.commercial_partner_id,
        #                     COALESCE(partner.country_id, partner_ai.country_id) AS country_id,
        #                     ai.team_id
        #                    FROM account_invoice_line ail
        #                      JOIN account_invoice ai ON ai.id = ail.invoice_id
        #                      JOIN res_partner partner ON ai.commercial_partner_id = partner.id
        #                      JOIN res_partner partner_ai ON ai.partner_id = partner_ai.id
        #                      LEFT JOIN product_product pr ON pr.id = ail.product_id
        #                      LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
        #                      LEFT JOIN product_uom u ON u.id = ail.uom_id
        #                      LEFT JOIN product_uom u2 ON u2.id = pt.uom_id
        #                      JOIN ( SELECT ai_1.id,
        #                                 CASE
        #                                     WHEN ai_1.type::text = ANY (ARRAY['in_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN '-1'::integer
        #                                     ELSE 1
        #                                 END AS sign,
        #                                 CASE
        #                                     WHEN ai_1.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN '-1'::integer
        #                                     ELSE 1
        #                                 END AS sign_qty
        #                            FROM account_invoice ai_1) invoice_type ON invoice_type.id = ai.id
        #                   GROUP BY ail.id, ail.product_id, ail.account_analytic_id, ai.date_invoice, ai.id, ai.partner_id, ai.payment_term_id, u2.name, u2.id, ai.currency_id, ai.journal_id, ai.fiscal_position_id, ai.user_id, ai.company_id, ai.type, invoice_type.sign, ai.state, pt.categ_id, ai.date_due, ai.account_id, ail.account_id, ai.partner_bank_id, ai.residual_company_signed, ai.amount_total_company_signed, ai.commercial_partner_id, (COALESCE(partner.country_id, partner_ai.country_id)), ai.team_id) sub
        #              LEFT JOIN currency_rate cr ON cr.currency_id = sub.currency_id AND cr.company_id = sub.company_id AND cr.date_start <= COALESCE(sub.date::timestamp with time zone, now()) AND (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date::timestamp with time zone, now()));

