from odoo import models, fields


class SaleTemplateLine(models.Model):
    _name = "sale.template.line"

    name = fields.Char("Activities")
    contractor = fields.Char("Contractor")
    gambit = fields.Char("Gambit")
    sequence = fields.Integer("Sequence")
    sale_template_id = fields.Many2one('sale.template', string="Sale Template")