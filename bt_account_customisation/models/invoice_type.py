# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError





class InvoiceType(models.Model):
    _name = "invoice.type"

    name = fields.Char("Type Code")
    description = fields.Char("Description")
    category = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    ], string="Type",)



    @api.model
    @api.depends('name')
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        result = []

        if name:
            domain = [('name', operator, name)]
        csm = self.search(domain + args, limit=limit)
        
        for site in csm:
            name = site.name
            result.append((site.id, name))
        return result


