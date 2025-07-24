# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class ProductTemplate(models.Model):
    _inherit = "product.template"

    estimate_type = fields.Selection([
        ('work', 'Works'),
        ('wages', 'Wages'),
        ('equipments', 'Equipments'),
        ('material', 'Materials'),
        ('general', 'General'),
       ],
        
        track_visibility='onchange',
        copy='True',
    )





class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    flag =fields.Boolean('Flag',_default=False)


    def get_activate(self):
        for rec in self:
            rec.write({'flag':True})

    def get_deactivate(self):
        for rec in self:
            rec.write({'flag':False})