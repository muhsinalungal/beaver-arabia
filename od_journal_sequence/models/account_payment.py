# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
	_inherit = 'account.payment'

	name = fields.Char(readonly=False, copy=False, default='/')
	gl_account_id = fields.Many2one(
		comodel_name="account.account",
		string="GL Account",)
	payment_method  = fields.Selection([ 
		('cash', 'Cash'),
		('transfer', 'Transfer'),
		('cheque', 'Cheque'),
	], string='Payment Mode', )
	journal_code_id = fields.Many2one(
		comodel_name="journal.code",
		string="Journal Code",)
	partner_id = fields.Many2one(
		comodel_name='res.partner',
		string="Customer/Vendor",
		store=True, readonly=False, ondelete='restrict',
		compute='_compute_partner_id',
		domain="[('id','in',suitable_partner_ids)]",
		check_company=True)
	suitable_partner_ids = fields.Many2many('res.partner', compute='_compute_suitable_partner_ids')
	number = fields.Char(string='Number', required=True, readonly=False, copy=False, default='/')
	number_genrated = fields.Boolean(default=False, copy=False)


	@api.depends('payment_type')
	def _compute_suitable_partner_ids(self):
		for rec in self:
			if rec.payment_type in ('inbound'):
				company_id = rec.company_id.id or self.env.company.id
				domain = [('customer_rank', '>', 0)]
				rec.suitable_partner_ids = self.env['res.partner'].search(domain)
			elif rec.payment_type in ('outbound'):
				company_id = rec.company_id.id or self.env.company.id
				domain = [('supplier_rank', '>', 0)]
				rec.suitable_partner_ids = self.env['res.partner'].search(domain)
			else:

				company_id = rec.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id)]
				rec.suitable_partner_ids = self.env['res.partner'].search(domain)

	@api.onchange('journal_id')
	def set_gl_account_code(self):
		for rec in self:
			if rec.petty_cash_type==False and rec.journal_id.type in ('bank','cash'):
				rec.gl_account_id = rec.journal_id.default_account_id or False
			
			else:
				rec.gl_account_id = False

	@api.onchange('posted_before', 'state', 'journal_id', 'date')
	def _onchange_journal_date(self):
		return

	@api.model
	def create(self, vals):
		res = super(AccountPayment, self).create(vals) 
		res.move_id.number_genrated = True
		
		return res  

	def create_sequence(self):
		for rec in self:
			if rec.name == '/' or rec.number_genrated == False:
				if rec.payment_type == 'inbound':
					journal = rec.journal_id

					if journal.type == 'bank':
							code = "BR" +journal.seq_code
							sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.bank")])
					elif journal.type == 'cash':
						code = 'CR'
						sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.transfer")])
					elif journal.is_petty_cash:
						code = "PR" +journal.seq_code
						sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.petty")])
					number_seq = sequence.with_context(ir_sequence_date=rec.date).next_by_id()
					rec.name = code + '-' + number_seq
					rec.number = code + '-' + number_seq
					rec.number_genrated = True
				elif rec.payment_type == 'outbound':
					journal = rec.journal_id
					if journal.type == 'bank':
							code = "BP" +journal.seq_code
							sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.bank")])
					elif journal.type == 'cash':
						code = 'CP'
						sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.cash")])
					elif journal.is_petty_cash:
						code = "PC" +journal.seq_code
						sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer")])
					number_seq = sequence.with_context(ir_sequence_date=rec.date).next_by_id()
					rec.name = code + '-' + number_seq
					rec.number = code + '-' + number_seq
					rec.number_genrated = True
				rec.move_id.name = rec.name



	def action_post(self):
		for rec in self:
			if rec.state != 'draft':
				raise UserError(_("Only a draft payment can be posted."))
			if any(inv.state != 'posted' for inv in rec.reconciled_invoice_ids):
				raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
			res = super(AccountPayment, rec).action_post()
			if rec.number_genrated == False:
				rec.create_sequence()

		return res

class AccountExtraPayment(models.Model):
	_inherit = 'account.extra.payment'

	number = fields.Char(string='Number', required=True, readonly=False, copy=False, default='/')
	number_genrated = fields.Boolean(default=False, copy=False)

	def create_sequence(self):
		for rec in self:
			
			if rec.name == False or rec.number_genrated == False:
				if rec.payment_type == 'inbound':
					journal = rec.journal_id

					if journal.type == 'bank':
							code = "BR" +journal.seq_code
							sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.bank")])
					elif journal.type == 'cash':
						code = 'CR'
						sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.transfer")])
					elif journal.is_petty_cash:
						code = "PR" +journal.seq_code
						sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.petty")])
					number_seq = sequence.with_context(ir_sequence_date=rec.date_done).next_by_id()
					rec.name = code + '-' + number_seq
					rec.number = code + '-' + number_seq
					rec.number_genrated = True
				elif rec.payment_type == 'outbound':
					journal = rec.journal_id
					if journal.type == 'bank':
							code = "BP" +journal.seq_code
							sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.bank")])
					elif journal.type == 'cash':
						code = 'CP'
						sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.cash")])
					elif journal.is_petty_cash:
						code = "PC" +journal.seq_code
						sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer")])
					number_seq = sequence.with_context(ir_sequence_date=rec.date_done).next_by_id()
					rec.name = code + '-' + number_seq
					rec.number = code + '-' + number_seq
					rec.number_genrated = True



	def button_post(self):
		for rec in self:
			if rec.number_genrated == False:
				rec.create_sequence()
			res = super(AccountExtraPayment, rec).button_post()

		return res
	

	@api.model
	def create(self, vals):
		res = super(AccountExtraPayment, self).create(vals) 

		
		return res   

class AccountAdvancePayment(models.Model):
	_inherit = 'account.advance.payment'

	number = fields.Char(string='Number', required=True, readonly=False, copy=False, default='/')
	number_genrated = fields.Boolean(default=False, copy=False)

	def create_sequence(self):
		for rec in self:
			
			if rec.name == False or rec.number_genrated == False:
				if rec.payment_type == 'inbound':
					journal = rec.journal_id

					if journal.type == 'bank':
							code = "BR" +journal.seq_code
							sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.bank")])
					elif journal.type == 'cash':
						code = 'CR'
						sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.transfer")])
					elif journal.is_petty_cash:
						code = "PR" +journal.seq_code
						sequence = self.env["ir.sequence"].search([("code",'=',"account.receipt.petty")])
					number_seq = sequence.with_context(ir_sequence_date=rec.date_done).next_by_id()
					rec.name = code + '-' + number_seq
					rec.number = code + '-' + number_seq
					rec.number_genrated = True
				elif rec.payment_type == 'outbound':
					journal = rec.journal_id

					if journal.type == 'bank':
							code = "BP" +journal.seq_code
							sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.bank")])
					elif journal.type == 'cash':
						code = 'CP'
						sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.cash")])
					elif journal.is_petty_cash:
						code = "PC" +journal.seq_code
						sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer")])
					number_seq = sequence.with_context(ir_sequence_date=rec.date_done).next_by_id()
					rec.name = code + '-' + number_seq
					rec.number = code + '-' + number_seq
					rec.number_genrated = True

	def button_post(self):
		for rec in self:
			if rec.number_genrated == False:
				rec.create_sequence()
			res = super(AccountAdvancePayment, rec).button_post()

		return res


	@api.model
	def create(self, vals):
		res = super(AccountAdvancePayment, self).create(vals) 
		# res.create_sequence()
		
		return res  


class ResPartner(models.Model):
	_inherit = 'res.partner' 

	@api.model
	def create(self, vals):
		res = super(ResPartner, self).create(vals) 
		
		if res.customer_rank >0:
			res.customer_ref = self.env["ir.sequence"].next_by_code("customer.sequence") or False
			
		elif res.supplier_rank >0:
			res.customer_ref = self.env["ir.sequence"].next_by_code("vendor.sequence") or False
		return res  
