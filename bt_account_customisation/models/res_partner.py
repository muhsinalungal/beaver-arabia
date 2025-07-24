# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError





class ResPartner(models.Model):
	_inherit = "res.partner"

	customer_ref = fields.Char("Customer ID")
	# supplier_ref = fields.Char("Supplier ID")
	advance_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Advance Payment Account",domain="[('user_type_id.internal_group', 'in', ['asset'])]")

	_sql_constraints = [
		('customer_ref_uniq', 'unique (customer_ref)', "Customer ID already exists !"),
	]


	
	@api.model
	@api.depends('name','supplier_ref','customer_ref')
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		result = []

		if name:
			domain = ['|',('name', operator, name),('customer_ref', operator, name)]
		partners = self.search(domain + args, limit=limit)
		
		for partner in partners:
			if partner.customer_ref:
				name = partner.customer_ref + ' ' + partner.name
			else:
				name = partner.name
			result.append((partner.id, name))
		return result

