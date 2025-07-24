from odoo import models, fields, api, _


class InsuranceCompany(models.Model):
    _name = 'insurance.company'
    _description = 'Insurance Company'
    
    name = fields.Char(string="Company Name")