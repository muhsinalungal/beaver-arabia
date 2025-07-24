# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError





class SiteSite(models.Model):
    _name = "site.site"

    name = fields.Char("Title")
    code = fields.Char("Code")
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    @api.depends('name', 'code')
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        result = []

        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        csm = self.search(domain + args, limit=limit)
        
        for site in csm:
            name = site.code + ' ' + site.name
            result.append((site.id, name))
        return result

class HrAccomodation(models.Model):
    _name = "hr.accomadation"

    name = fields.Char("Title")
    code = fields.Char("Code")
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    @api.depends('name', 'code')
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        result = []

        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        csm = self.search(domain + args, limit=limit)
        if csm:
            for site in csm:
                name = site.code + ' ' + site.name
                result.append((site.id, name))
        return result


class JournalCode(models.Model):
    _name = "journal.code"

    name = fields.Char("Title")
    code = fields.Char("Code")
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    @api.depends('name', 'code')
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        result = []

        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        csm = self.search(domain + args, limit=limit)
        
        for site in csm:
            name = site.code + ' ' + site.name
            result.append((site.id, name))
        return result


