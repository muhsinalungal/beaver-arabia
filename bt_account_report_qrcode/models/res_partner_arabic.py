from odoo import models, fields, api, _
# from googletrans import Translator
# import googletrans

class PartnerArabic(models.Model):
    
    _inherit = "res.partner"
    
    arb_name = fields.Char(string="Arabic Name")
    arb_street = fields.Char(string="Arabic Street")
    arb_street2 = fields.Char(string="Arabic Street2")
    arb_city = fields.Char(string="Arabic City")
    arb_state_id = fields.Char(string="Arabic State")
    arb_zip = fields.Char(String="Zip")
    arb_country_id = fields.Char(string="Arabic Country")
    attention = fields.Char(string="Attention")
    
    
    
        
        
        