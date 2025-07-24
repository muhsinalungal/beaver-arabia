# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError





class AssetGroup(models.Model):
	_name = "asset.group"

	name = fields.Char("Description")
	code = fields.Char("Code")
	


	@api.model
	@api.depends('name')
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

class AccountAssetCategory(models.Model):
	_inherit = "account.asset.category"

	code = fields.Char("Code")
	asset_group_id = fields.Many2one(
		comodel_name="asset.group",)
	sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence',
								   copy=False)


	def create_sequence(self, res):
		
		self = res
		prefix = self.asset_group_id.code + "-" + self.code + "-"
		seq_name = self.code+ "-" + self.name
		seq = {
			'name': _('%s Sequence') % seq_name,
			'implementation': 'no_gap',
			'prefix': prefix,
			'padding': 4,
			'number_increment': 1,
			'use_date_range': False,
		}
		# if self.company_id:
		# 	seq['company_id'] = self.company_id.id
		seq = self.env['ir.sequence'].create(seq)
		# seq_date_range = seq._get_current_sequence()
		# seq_date_range.number_next = refund and (self.refund_sequence_number_next or 1) or \
		# 							 (self.sequence_number_next or 1)
		return seq



	@api.model
	def create(self, vals):
		
		
		res = super(AccountAssetCategory, self.with_context(mail_create_nolog=True)).create(vals)
		if not vals.get('sequence_id'):
			res.sequence_id = self.sudo().create_sequence(res).id
			# vals.update({'sequence_id': self.sudo().create_sequence(res).id})
		return res


class AccountAssetAsset(models.Model):
	_inherit = "account.asset.asset"

	ref = fields.Char("Reference")


	@api.model
	def create(self, vals):
		
		
		res = super(AccountAssetAsset, self.with_context(mail_create_nolog=True)).create(vals)
		res.code = res.category_id.sequence_id.next_by_id()
		return res