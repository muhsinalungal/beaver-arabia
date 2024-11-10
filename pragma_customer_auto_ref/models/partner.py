# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = _inherit

    @api.model
    def create(self, vals):
        partner_type = self._context.get('res_partner_search_mode')

        if partner_type == 'customer':
            vals['customer_ref'] = self.env['ir.sequence'].next_by_code('customer.number')
        elif partner_type == 'supplier':
            vals['customer_ref'] = self.env['ir.sequence'].next_by_code('vendor.number')

        return super(ResPartner, self).create(vals)
