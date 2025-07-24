# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError





class AccountJournal(models.Model):
	_inherit = "account.journal"

	is_petty_cash = fields.Boolean(string='Is Petty Cash',default=False)
	petty_cash_account_id = fields.Many2one(
		comodel_name="account.account",
		string="Petty Cash Code",domain="[('is_petty_cash', '=', True), ('company_id', '=', company_id)]")
	

class AccountAccount(models.Model):
	_inherit = "account.account"

	is_petty_cash = fields.Boolean(string='Is Petty Cash',default=False)
	employee = fields.Boolean(string='Employee',default=False)
	project = fields.Boolean(string='Project',default=False)
	asset = fields.Boolean(string='Asset',default=False)
	cost_center = fields.Boolean(string='Department',default=False)
	cost_center_new = fields.Boolean(string='Cost Center',default=False)
	accomodation = fields.Boolean(string='Accomodation',default=False)
	show_in_ageing = fields.Boolean(string='Show in Ageing',default=False)
	account_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')])

class AccountAnalyticAccount(models.Model):
	_inherit = "account.analytic.account"

	partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, check_company=True,domain="[('id','in',suitable_partner_ids)]")
	suitable_partner_ids = fields.Many2many('res.partner', compute='_compute_suitable_partner_ids')


	@api.depends('name')
	def _compute_suitable_partner_ids(self):
		for rec in self:
			
			# company_id = rec.company_id.id or self.env.company.id
			domain = [('customer_rank', '>', 0)]
			rec.suitable_partner_ids = self.env['res.partner'].search(domain)
			
				



   
