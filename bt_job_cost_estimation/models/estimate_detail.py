from odoo import api, fields, models, _

class estimate_detail(models.Model):
    _name = "estimate.detail"
    
    name = fields.Char('Description',)
    
    project_id = fields.Many2one('sale.project',string='Project',)