from odoo import models, fields, api


class SaleTemplate(models.Model):
    _name = "sale.template"

    name = fields.Char("Name")
    template_line_ids = fields.One2many('sale.template.line','sale_template_id')
    fixed_cost_line_ids = fields.One2many('fixed.cost.line', 'sale_template_id')

    @api.model
    def create(self, vals):
        res = super(SaleTemplate, self).create(vals)
        self.env['product.template'].create({'name': vals['name'], 'type': 'service',})
        return res
