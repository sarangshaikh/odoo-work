from odoo import models, fields,tools,api,_
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class LeadExt(models.Model):
    _inherit = 'crm.lead'

    customer_class = fields.Selection([
        ('e_com', 'E-Commerce'),('retail', 'Retail'),('trade', 'Trade')],
        related='partner_id.customer_class',
        string="Customer Classification",
        readonly="1",
        store=True
    )



    def action_new_quotation(self):
        action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]
        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_customer_class': self.customer_class,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': self.tag_ids.ids,
        }
        return action