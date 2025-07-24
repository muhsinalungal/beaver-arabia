# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from collections import defaultdict
from datetime import datetime, date
from calendar import monthrange


class AccountMove(models.Model):
	_inherit = "account.move"

	name = fields.Char(string='Number', copy=False, readonly=False, index=True, tracking=True, default='/')
	line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items', copy=True, readonly=True,
							   states={'draft': [('readonly', False)]})

	site_id = fields.Many2one(
		comodel_name="site.site",
		string="Site", )
	analytic_account_id = fields.Many2one(
		comodel_name="account.analytic.account",
		string="Project Code", )
	employee_id = fields.Many2one(
		comodel_name="hr.employee",
		string="Employee", )
	invoice_type_id = fields.Many2one(
		comodel_name="invoice.type",
		string="Invoice Type", )
	receipt_date = fields.Date(string='Receipt Date')
	our_ref_no = fields.Char(
		string="Our Ref No", )
	your_ref_no = fields.Char(
		string="Your Ref No", )
	journal_code_id = fields.Many2one(
		comodel_name="journal.code",
		string="Journal Code", )
	petty_cash_account_id = fields.Many2one(
		comodel_name="account.account",
		string="Petty Cash Code", domain="[('is_petty_cash', '=', True), ('company_id', '=', company_id)]")
	petty_amnt = fields.Float(
		string="Petty Amount")
	petty_balance_amnt = fields.Float(
		string="Petty Balance Amount", compute="compute_petty_amount", store=True)

	sales_person = fields.Many2one('res.salesperson',string="Sales Person")

	# adv_doc = fields.Char(
	# 	string="Advance Docu.",)
	# adv_amt = fields.Float(
	# 	string="Advance Amt",)

	# adv_ded = fields.Float(
	# string="Advance Deduction %",)
	# retention_account_id = fields.Many2one('account.account',
	# 	string="Retention Account",)
	retention_perc = fields.Float(
		string="Retention %", size=5)
	total_adv_ded = fields.Float(
		string="Advance Deduction", compute="_compute_adv_ded", store=True)
	total_excl_vat = fields.Float(
		string="Total (Excl. VAT)", compute="_compute_total_excl_vat", store=True)
	# total_vat_amt = fields.Float(
	# 	string="Total VAT",compute="_compute_vat_amt",store=True)
	less_retention = fields.Float(
		string="Less Retention", compute="_compute_less_retention", store=True)
	amount_total_after_ret = fields.Float(
		string="Net Amount Incl. VAT", compute="_compute_total_ret", store=True)
	petty_cash_type = fields.Boolean(help="Technical field used for usability purposes")
	bank_cash_type = fields.Boolean(help="Technical field used for usability purposes")
	payment_method = fields.Selection([
		('cash', 'Cash'),
		('transfer', 'Transfer'),
		('cheque', 'Cheque'),
	], string='Payment Mode', )
	cheq_no = fields.Char(string='Cheque No', )
	gl_account_id = fields.Many2one(
		comodel_name="account.account",
		string="GL Account", )

	transfer_type = fields.Selection([
		('cash', 'Cash'),
		('bank', 'Bank'),
		('petty', 'Petty Cash'),
	], string='Transfer Type')
	partner_name = fields.Char(string='Pay To', )

	pt_total_amount = fields.Float(string='Net Amount(Incl.Vat)', compute="compute_amount_pt", store=True)
	pt_vat_amount = fields.Float(string='Total VAT', compute="compute_amount_pt", store=True)
	pt_taxable_amount = fields.Float(string='Total Taxable Amt', compute="compute_amount_pt", store=True)
	move_type = fields.Selection(selection=[
		('entry', 'Journal Entry'),
		('out_invoice', 'Customer Invoice'),
		('out_refund', 'Customer Credit Note'),
		('in_invoice', 'Vendor Bill'),
		('in_refund', 'Vendor Debit Note'),
		('out_receipt', 'Sales Receipt'),
		('in_receipt', 'Purchase Receipt'),
	], string='Type', required=True, store=True, index=True, readonly=True, tracking=True,
		default="entry", change_default=True)
	product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[]")
	suitable_partner_ids = fields.Many2many('res.partner', compute='_compute_suitable_partner_ids')
	partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
								 states={'draft': [('readonly', False)]},
								 check_company=True,
								 string='Partner', change_default=True, domain="[('id','in',suitable_partner_ids)]")

	reversed_entry_ids = fields.Many2many('account.move', 'src_model_rel', 'name', string="Reversal of", readonly=True,
										  copy=False,
										  check_company=True)

	@api.onchange('reversed_entry_ids', 'partner_id')
	def _get_move_reverse_domain(self):
		if self.partner_id:
			return {'domain': {'reversed_entry_ids': [('partner_id', '=', self.partner_id.id), ('state', '=', 'posted'),
													  ('payment_state', 'in', ['not_paid', 'in_payment', 'partial'])],
							   }}
		else:
			return {'domain': {'reversed_entry_ids': [('state', '=', 'posted'),
													  ('payment_state', 'in', ['not_paid', 'in_payment', 'partial'])],
							   }}

	@api.depends('line_ids.pt_taxable_amount', 'line_ids.pt_vat_amount', 'line_ids.pt_total_amount', )
	def compute_amount_pt(self):
		total_vat_amount = total_amount = total_taxable_amount = 0.00
		for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
			total_vat_amount += line.pt_vat_amount
			total_amount += line.pt_total_amount
			total_taxable_amount += line.pt_taxable_amount

		self.write({'pt_total_amount': total_amount, 'pt_vat_amount': total_vat_amount,
					'pt_taxable_amount': total_taxable_amount})

	@api.model
	def _get_tax_grouping_key_from_tax_line(self, tax_line):
		''' Create the dictionary based on a tax line that will be used as key to group taxes together.
		/!\ Must be consistent with '_get_tax_grouping_key_from_base_line'.
		:param tax_line:    An account.move.line being a tax line (with 'tax_repartition_line_id' set then).
		:return:            A dictionary containing all fields on which the tax will be grouped.
		'''
		return {
			'tax_repartition_line_id': tax_line.tax_repartition_line_id.id,
			'account_id': tax_line.account_id.id,
			'seq': tax_line.seq,
			'currency_id': tax_line.currency_id.id,
			'analytic_tag_ids': [(6, 0, tax_line.tax_line_id.analytic and tax_line.analytic_tag_ids.ids or [])],
			'analytic_account_id': tax_line.tax_line_id.analytic and tax_line.analytic_account_id.id,
			'tax_ids': [(6, 0, tax_line.tax_ids.ids)],
			'tax_tag_ids': [(6, 0, tax_line.tax_tag_ids.ids)],
		}

	@api.model
	def _get_tax_grouping_key_from_base_line(self, base_line, tax_vals):
		''' Create the dictionary based on a base line that will be used as key to group taxes together.
		/!\ Must be consistent with '_get_tax_grouping_key_from_tax_line'.
		:param base_line:   An account.move.line being a base line (that could contains something in 'tax_ids').
		:param tax_vals:    An element of compute_all(...)['taxes'].
		:return:            A dictionary containing all fields on which the tax will be grouped.
		'''
		tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
		account = base_line._get_default_tax_account(tax_repartition_line) or base_line.account_id
		if base_line.move_id.move_type == 'entry':
			return {
				'tax_repartition_line_id': tax_vals['tax_repartition_line_id'],
				'account_id': account.id,
				'seq': base_line.seq,
				'currency_id': base_line.currency_id.id,
				'analytic_tag_ids': [(6, 0, tax_vals['analytic'] and base_line.analytic_tag_ids.ids or [])],
				'analytic_account_id': tax_vals['analytic'] and base_line.analytic_account_id.id,
				'tax_ids': [(6, 0, tax_vals['tax_ids'])],
				'tax_tag_ids': [(6, 0, tax_vals['tag_ids'])],
			}
		else:

			return {
				'tax_repartition_line_id': tax_vals['tax_repartition_line_id'],
				'account_id': account.id,
				'currency_id': base_line.currency_id.id,
				'analytic_tag_ids': [(6, 0, tax_vals['analytic'] and base_line.analytic_tag_ids.ids or [])],
				'analytic_account_id': tax_vals['analytic'] and base_line.analytic_account_id.id,
				'tax_ids': [(6, 0, tax_vals['tax_ids'])],
				'tax_tag_ids': [(6, 0, tax_vals['tag_ids'])],
			}

	# def _recompute_tax_lines(self, recompute_tax_base_amount=False):
	# 	''' Compute the dynamic tax lines of the journal entry.

	# 	:param lines_map: The line_ids dispatched by type containing:
	# 		* base_lines: The lines having a tax_ids set.
	# 		* tax_lines: The lines having a tax_line_id set.
	# 		* terms_lines: The lines generated by the payment terms of the invoice.
	# 		* rounding_lines: The cash rounding lines of the invoice.
	# 	'''
	# 	self.ensure_one()
	# 	in_draft_mode = self != self._origin

	# 	def _serialize_tax_grouping_key(grouping_dict):
	# 		''' Serialize the dictionary values to be used in the taxes_map.
	# 		:param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
	# 		:return: A string representing the values.
	# 		'''
	# 		return '-'.join(str(v) for v in grouping_dict.values())

	# 	def _compute_base_line_taxes(base_line):
	# 		''' Compute taxes amounts both in company currency / foreign currency as the ratio between
	# 		amount_currency & balance could not be the same as the expected currency rate.
	# 		The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
	# 		:param base_line:   The account.move.line owning the taxes.
	# 		:return:            The result of the compute_all method.
	# 		'''
	# 		move = base_line.move_id

	# 		if move.is_invoice(include_receipts=True):
	# 			handle_price_include = True
	# 			sign = -1 if move.is_inbound() else 1
	# 			quantity = base_line.quantity
	# 			is_refund = move.move_type in ('out_refund', 'in_refund')
	# 			price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
	# 		else:
	# 			handle_price_include = False
	# 			quantity = 1.0
	# 			tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
	# 			is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
	# 			price_unit_wo_discount = base_line.amount_currency

	# 		balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
	# 			price_unit_wo_discount,
	# 			currency=base_line.currency_id,
	# 			quantity=quantity,
	# 			product=base_line.product_id,
	# 			partner=base_line.partner_id,
	# 			is_refund=is_refund,
	# 			handle_price_include=handle_price_include,
	# 		)

	# 		if move.move_type == 'entry':
	# 			repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
	# 			repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
	# 			tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
	# 			if tags_need_inversion:
	# 				balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
	# 				for tax_res in balance_taxes_res['taxes']:
	# 					tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

	# 		return balance_taxes_res

	# 	taxes_map = {}

	# 	# ==== Add tax lines ====
	# 	to_remove = self.env['account.move.line']
	# 	for line in self.line_ids.filtered('tax_repartition_line_id'):
	# 		grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
	# 		grouping_key = _serialize_tax_grouping_key(grouping_dict)
	# 		if grouping_key in taxes_map:
	# 			# A line with the same key does already exist, we only need one
	# 			# to modify it; we have to drop this one.
	# 			to_remove += line
	# 		else:
	# 			taxes_map[grouping_key] = {
	# 				'tax_line': line,
	# 				'amount': 0.0,
	# 				'tax_base_amount': 0.0,
	# 				'grouping_dict': False,
	# 			}

	# 	if not recompute_tax_base_amount:
	# 		self.line_ids -= to_remove

	# 	# ==== Mount base lines ====
	# 	for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):

	# 		# Don't call compute_all if there is no tax.
	# 		if not line.tax_ids:
	# 			if not recompute_tax_base_amount:
	# 				line.tax_tag_ids = [(5, 0, 0)]
	# 			continue

	# 		compute_all_vals = _compute_base_line_taxes(line)

	# 		# Assign tags on base line
	# 		if not recompute_tax_base_amount:
	# 			line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

	# 		tax_exigible = True
	# 		for tax_vals in compute_all_vals['taxes']:
	# 			grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
	# 			grouping_key = _serialize_tax_grouping_key(grouping_dict)

	# 			tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
	# 			tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

	# 			if tax.tax_exigibility == 'on_payment':
	# 				tax_exigible = False

	# 			taxes_map_entry = taxes_map.setdefault(grouping_key, {
	# 				'tax_line': None,
	# 				'amount': 0.0,
	# 				'tax_base_amount': 0.0,
	# 				'grouping_dict': False,
	# 			})
	# 			taxes_map_entry['amount'] += tax_vals['amount']
	# 			taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
	# 			taxes_map_entry['grouping_dict'] = grouping_dict
	# 			# taxes_map_entry['tax_line'] = line
	# 		if not recompute_tax_base_amount:
	# 			line.tax_exigible = tax_exigible

	# 	# ==== Pre-process taxes_map ====
	# 	taxes_map = self._preprocess_taxes_map(taxes_map)

	# 	# ==== Process taxes_map ====
	# 	for taxes_map_entry in taxes_map.values():
	# 		# The tax line is no longer used in any base lines, drop it.

	# 		if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
	# 			if not recompute_tax_base_amount:
	# 				self.line_ids -= taxes_map_entry['tax_line']
	# 			continue

	# 		currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

	# 		# Don't create tax lines with zero balance.
	# 		if currency.is_zero(taxes_map_entry['amount']):
	# 			if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
	# 				self.line_ids -= taxes_map_entry['tax_line']
	# 			continue

	# 		# tax_base_amount field is expressed using the company currency.
	# 		tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

	# 		# Recompute only the tax_base_amount.
	# 		if recompute_tax_base_amount:
	# 			if taxes_map_entry['tax_line']:
	# 				taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
	# 			continue

	# 		balance = currency._convert(
	# 			taxes_map_entry['amount'],
	# 			self.company_currency_id,
	# 			self.company_id,
	# 			self.date or fields.Date.context_today(self),
	# 		)
	# 		to_write_on_line = {
	# 			'amount_currency': taxes_map_entry['amount'],
	# 			'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
	# 			'debit': balance > 0.0 and balance or 0.0,
	# 			'credit': balance < 0.0 and -balance or 0.0,
	# 			'tax_base_amount': tax_base_amount,
	# 		}

	# 		if taxes_map_entry['tax_line']:
	# 			# Update an existing tax line.
	# 			taxes_map_entry['tax_line'].update(to_write_on_line)
	# 		else:
	# 			create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
	# 			tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
	# 			tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
	# 			tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
	# 			taxes_map_entry['tax_line'] = create_method({
	# 				**to_write_on_line,
	# 				'name': tax.name,
	# 				'move_id': self.id,
	# 				'partner_id': line.partner_id.id,
	# 				'company_id': line.company_id.id,
	# 				'company_currency_id': line.company_currency_id.id,
	# 				# 'seq':line.seq,
	# 				'tax_base_amount': tax_base_amount,
	# 				'exclude_from_invoice_tab': True,
	# 				'tax_exigible': tax.tax_exigibility == 'on_invoice',
	# 				**taxes_map_entry['grouping_dict'],
	# 			})

	# 		if in_draft_mode:
	# 			taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))

	@api.depends('state')
	def _compute_name(self):

		def journal_key(move):
			return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

		def date_key(move):
			return (move.date.year, move.date.month)

		grouped = defaultdict(  # key: journal_id, move_type
			lambda: defaultdict(  # key: first adjacent (date.year, date.month)
				lambda: {
					'records': self.env['account.move'],
					'format': False,
					'format_values': False,
					'reset': False
				}
			)
		)
		self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
		highest_name = self[0]._get_last_sequence() if self else False

		# Group the moves by journal and month
		for move in self:

			if not highest_name and move == self[0] and not move.posted_before and move.date:
				# In the form view, we need to compute a default sequence so that the user can edit
				# it. We only check the first move as an approximation (enough for new in form view)
				pass
			elif (move.name and move.name != '/') or move.state != 'posted':
				try:
					if not move.posted_before:
						move._constrains_date_sequence()
					# Has already a name or is not posted, we don't add to a batch
					continue
				except ValidationError:
					# Has never been posted and the name doesn't match the date: recompute it
					pass
			group = grouped[journal_key(move)][date_key(move)]

			if not group['records']:
				# Compute all the values needed to sequence this whole group
				move._set_next_sequence()
				group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
				group['reset'] = move._deduce_sequence_number_reset(move.name)
			group['records'] += move

		# Fusion the groups depending on the sequence reset and the format used because `seq` is
		# the same counter for multiple groups that might be spread in multiple months.
		final_batches = []
		for journal_group in grouped.values():

			journal_group_changed = True
			for date_group in journal_group.values():

				if (
						journal_group_changed
						or final_batches[-1]['format'] != date_group['format']
						or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
				):
					final_batches += [date_group]
					journal_group_changed = False

				elif date_group['reset'] == 'never':

					final_batches[-1]['records'] += date_group['records']
				elif (
						date_group['reset'] == 'year'
						and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
				):

					final_batches[-1]['records'] += date_group['records']

				else:
					final_batches += [date_group]

	# Give the name based on previously computed values
	# for batch in final_batches:
	# 	for move in batch['records']:

	# 		# move.name = batch['format'].format(**batch['format_values'])
	# 		# batch['format_values']['seq'] += 1
	# 		# if move.move_type == 'out_invoice' and move.journal_code_id:
	# 		# 	move.name = move.journal_code_id.code + '-' +(
	# 		# 			self.env["ir.sequence"].next_by_code("customer.invoice.seq") or move.name
	# 		# 		)
	# 		# if move.move_type == 'in_invoice' and move.journal_code_id:
	# 		# 	move.name = move.journal_code_id.code + '-' +(
	# 		# 			self.env["ir.sequence"].next_by_code("vendor.invoice.seq") or move.name
	# 		# 		)

	# 	batch['records']._compute_split_sequence()

	# self.filtered(lambda m: not m.name).name = '/'

	@api.onchange('site_id', 'analytic_account_id', 'employee_id')
	def set_values(self):
		for line in self.invoice_line_ids:
			line.site_id = self.site_id.id
			# line.analytic_account_id = self.analytic_account_id.id
			# line.employee_id = self.employee_id.id

	@api.onchange('petty_cash_type', 'journal_id')
	def set_petty_code(self):
		for rec in self:
			if rec.petty_cash_type == True and rec.journal_id.petty_cash_account_id:
				rec.petty_cash_account_id = rec.journal_id.petty_cash_account_id or False
			else:
				rec.petty_cash_account_id = False

	@api.onchange('petty_cash_type', 'journal_id', 'transfer_type')
	def set_gl_account_code(self):
		for rec in self:
			if rec.petty_cash_type == False and rec.journal_id.type in ('bank', 'cash'):
				rec.gl_account_id = rec.journal_id.default_account_id or False
			elif rec.petty_cash_type == False and rec.journal_id.is_petty_cash == True:
				rec.gl_account_id = rec.journal_id.petty_cash_account_id or False
			else:
				rec.gl_account_id = False

	@api.depends('petty_cash_account_id', 'employee_id', 'line_ids.credit', 'line_ids.debit')
	def compute_petty_amount(self):
		if self.petty_cash_account_id and self.employee_id:
			self._cr.execute('''
					SELECT sum(debit - credit)
					FROM account_move_line 
					WHERE account_id = %s
				
					AND employee_id = %s and move_id in (SELECT id FROM account_move WHERE state=%s)
				''', [self.petty_cash_account_id.id, self.employee_id.id, 'posted', ])
			res = self._cr.fetchone()[0]

			if res != None:
				self.petty_balance_amnt = res
			else:
				self.petty_balance_amnt = 0.0

	@api.onchange('petty_cash_account_id', 'employee_id')
	def onchange_petty_amount(self):
		if self.petty_cash_account_id and self.employee_id:
			self._cr.execute('''
					SELECT sum(debit - credit)
					FROM account_move_line 
					WHERE account_id = %s
				
					AND employee_id = %s and move_id in (SELECT id FROM account_move WHERE state=%s)
				''', [self.petty_cash_account_id.id, self.employee_id.id, 'posted', ])
			res = self._cr.fetchone()[0]

			if res != None:
				self.petty_balance_amnt = res
			else:
				self.petty_balance_amnt = 0.0

	@api.depends('invoice_line_ids.price_subtotal', 'partner_id')
	def _compute_total_excl_vat(self):
		total_excl_amount = 0.00
		for line in self.invoice_line_ids:

			if line.product_id and line.product_id.is_advance == False:
				total_excl_amount += line.price_subtotal
			elif not line.product_id:
				total_excl_amount += line.price_subtotal

		self.write({'total_excl_vat': total_excl_amount})

	@api.depends('invoice_line_ids.price_subtotal', 'partner_id')
	def _compute_adv_ded(self):
		total_adv_amount = 0.00
		for line in self.invoice_line_ids:

			if line.product_id and line.product_id.is_advance == True:
				total_adv_amount += line.price_subtotal
		self.write({'total_adv_ded': abs(total_adv_amount)})

	@api.onchange('petty_cash_type')
	def onchange_petty_cash_type(self):
		if self.petty_cash_type == True:

			journal_type = self.invoice_filter_type_domain or 'general'
			company_id = self.company_id.id or self.env.company.id
			domain = [('company_id', '=', company_id), ('is_petty_cash', '=', True)]
			journal_ids = self.env['account.journal'].search(domain)
			if journal_ids:
				self.journal_id = journal_ids[0]
				self.petty_cash_account_id = journal_ids[0].petty_cash_account_id.id

			else:
				self.journal_id = False
				self.petty_cash_account_id = False
			self.name = '/'

	@api.onchange('date', 'date_invoice')
	def onchange_date(self):
		if self.state == 'draft' and self.name == '/':
			self.name = '/'

	@api.onchange('bank_cash_type')
	def onchange_bank_cash_type(self):
		if self.bank_cash_type == True:

			journal_type = self.invoice_filter_type_domain or ('bank', 'cash')
			company_id = self.company_id.id or self.env.company.id
			domain = [('company_id', '=', company_id), '|', ('type', '=', journal_type), ('is_petty_cash', '=', True)]
			journal_ids = self.env['account.journal'].search(domain)
			if journal_ids:
				self.journal_id = journal_ids[0]
			# self.petty_cash_account_id = journal_ids[0].default_bank_id.id or journal_ids[0].petty_cash_account_id.id or False
			else:
				self.journal_id = False
				self.petty_cash_account_id = False
			self.name = '/'

	@api.onchange('transfer_type')
	def onchange_transfer_type(self):
		for m in self:

			if m.transfer_type == 'cash':
				journal_type = m.invoice_filter_type_domain or ('cash')
				company_id = m.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
				m.suitable_journal_ids = self.env['account.journal'].search(domain)
				m.journal_id = self.env['account.journal'].search(domain)[0]
				m.gl_account_id = self.env['account.journal'].search(domain)[0].default_account_id.id
			elif m.transfer_type == 'bank':
				journal_type = m.invoice_filter_type_domain or ('bank')
				company_id = m.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
				m.suitable_journal_ids = self.env['account.journal'].search(domain)
				m.journal_id = self.env['account.journal'].search(domain)[0]
				m.gl_account_id = self.env['account.journal'].search(domain)[0].default_account_id.id
			elif m.transfer_type == 'petty':
				journal_type = m.invoice_filter_type_domain or ('bank')
				company_id = m.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id), ('is_petty_cash', '=', True)]
				m.suitable_journal_ids = self.env['account.journal'].search(domain)
				m.journal_id = self.env['account.journal'].search(domain)[0]
				m.gl_account_id = self.env['account.journal'].search(domain)[0].petty_cash_account_id.id
			m.name = '/'

	@api.depends('move_type')
	def _compute_invoice_filter_type_domain(self):
		for move in self:
			if move.is_sale_document(include_receipts=True):
				move.invoice_filter_type_domain = 'sale'
			elif move.is_purchase_document(include_receipts=True):
				move.invoice_filter_type_domain = 'purchase'
			elif move.petty_cash_type == True:
				move.invoice_filter_type_domain = 'purchase'
			else:
				move.invoice_filter_type_domain = False

	@api.model
	def _search_default_journal(self, journal_types):
		company_id = self._context.get('default_company_id', self.env.company.id)
		if self._context.get('default_move_type') == 'entry' and not self._context.get(
				'default_bank_cash_type') and not self._context.get('default_petty_cash_type'):
			domain = [('company_id', '=', company_id), ('type', 'in', journal_types), ('is_petty_cash', '=', False)]
		else:
			domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]

		journal = None
		if self._context.get('default_currency_id'):
			currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
			journal = self.env['account.journal'].search(currency_domain, limit=1)

		if not journal:
			journal = self.env['account.journal'].search(domain, limit=1)

		if not journal:
			company = self.env['res.company'].browse(company_id)

			error_msg = _(
				"No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
				company_name=company.display_name,
				journal_types=', '.join(journal_types),
			)
			raise UserError(error_msg)

		return journal

	@api.depends('company_id', 'invoice_filter_type_domain', 'transfer_type')
	def _compute_suitable_journal_ids(self):
		for m in self:
			if m.petty_cash_type == True:
				journal_type = m.invoice_filter_type_domain or 'general'
				company_id = m.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id), ('is_petty_cash', '=', True)]
				m.suitable_journal_ids = self.env['account.journal'].search(domain)
			# m.journal_id = self.env['account.journal'].search(domain)
			elif m.bank_cash_type == True:
				if m.transfer_type == 'cash':
					journal_type = m.invoice_filter_type_domain or ('cash')
					company_id = m.company_id.id or self.env.company.id
					domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
					m.suitable_journal_ids = self.env['account.journal'].search(domain)
				# m.journal_id = self.env['account.journal'].search(domain)[0]
				# m.gl_account_id = self.env['account.journal'].search(domain)[0].default_account_id.id
				elif m.transfer_type == 'bank':
					journal_type = m.invoice_filter_type_domain or ('bank')
					company_id = m.company_id.id or self.env.company.id
					domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
					m.suitable_journal_ids = self.env['account.journal'].search(domain)
				# m.journal_id = self.env['account.journal'].search(domain)[0]
				# m.gl_account_id = self.env['account.journal'].search(domain)[0].default_account_id.id
				elif m.transfer_type == 'petty':
					journal_type = m.invoice_filter_type_domain or ('bank')
					company_id = m.company_id.id or self.env.company.id
					domain = [('company_id', '=', company_id), ('is_petty_cash', '=', True)]
					m.suitable_journal_ids = self.env['account.journal'].search(domain)
				# m.journal_id = self.env['account.journal'].search(domain)[0]
				# m.gl_account_id = self.env['account.journal'].search(domain)[0].petty_cash_account_id.id
				else:
					journal_type = m.invoice_filter_type_domain or ('bank', 'cash')
					company_id = m.company_id.id or self.env.company.id
					domain = [('company_id', '=', company_id), '|', ('type', '=', journal_type),
							  ('is_petty_cash', '=', True)]
					m.suitable_journal_ids = self.env['account.journal'].search(domain)
			else:
				journal_type = m.invoice_filter_type_domain or 'general'
				company_id = m.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id), ('type', '=', journal_type), ('is_petty_cash', '=', False)]
				m.suitable_journal_ids = self.env['account.journal'].search(domain)
			# m.journal_id = self.env['account.journal'].search(domain)[0]

	@api.depends('move_type')
	def _compute_suitable_partner_ids(self):
		for rec in self:
			if rec.move_type in ('out_invoice', 'out_refund'):
				company_id = rec.company_id.id or self.env.company.id
				domain = [('customer_rank', '>', 0)]
				rec.suitable_partner_ids = self.env['res.partner'].search(domain)
			elif rec.move_type in ('in_invoice', 'in_refund'):
				company_id = rec.company_id.id or self.env.company.id
				domain = [('supplier_rank', '>', 0)]
				rec.suitable_partner_ids = self.env['res.partner'].search(domain)
			else:

				company_id = rec.company_id.id or self.env.company.id
				domain = [('company_id', '=', company_id)]
				rec.suitable_partner_ids = self.env['res.partner'].search(domain)

	@api.depends('total_excl_vat', 'retention_perc')
	def _compute_less_retention(self):
		for rec in self:
			ret_amount = rec.total_excl_vat * (rec.retention_perc / 100)
			rec.write({'less_retention': ret_amount})

	@api.depends('amount_total', 'less_retention')
	def _compute_total_ret(self):
		for rec in self:
			total_amount = rec.amount_total - rec.less_retention
			rec.write({'amount_total_after_ret': total_amount})

	def _recompute_tax_lines(self, recompute_tax_base_amount=False):
		''' Compute the dynamic tax lines of the journal entry.

		:param lines_map: The line_ids dispatched by type containing:
			* base_lines: The lines having a tax_ids set.
			* tax_lines: The lines having a tax_line_id set.
			* terms_lines: The lines generated by the payment terms of the invoice.
			* rounding_lines: The cash rounding lines of the invoice.
		'''
		self.ensure_one()
		in_draft_mode = self != self._origin

		def _serialize_tax_grouping_key(grouping_dict):
			''' Serialize the dictionary values to be used in the taxes_map.
			:param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
			:return: A string representing the values.
			'''
			return '-'.join(str(v) for v in grouping_dict.values())

		def _compute_base_line_taxes(base_line):

			''' Compute taxes amounts both in company currency / foreign currency as the ratio between
			amount_currency & balance could not be the same as the expected currency rate.
			The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
			:param base_line:   The account.move.line owning the taxes.
			:return:            The result of the compute_all method.
			'''
			move = base_line.move_id

			if move.is_invoice(include_receipts=True):
				handle_price_include = True
				sign = -1 if move.is_inbound() else 1
				quantity = base_line.quantity
				is_refund = move.move_type in ('out_refund', 'in_refund')
				price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
				if base_line.product_uom_id.name in ("Days", "Monthly", "Weekly"):
					price_unit_wo_discount = sign * base_line.price_subtotal
					quantity = 1



			else:
				handle_price_include = False
				quantity = 1.0
				tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
				is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
				price_unit_wo_discount = base_line.amount_currency

			balance_taxes_res = base_line.tax_ids._origin.with_context(
				force_sign=move._get_tax_force_sign()).compute_all(
				price_unit_wo_discount,
				currency=base_line.currency_id,
				quantity=quantity,
				product=base_line.product_id,
				partner=base_line.partner_id,
				is_refund=is_refund,
				handle_price_include=handle_price_include,
			)

			if move.move_type == 'entry':
				repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
				repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(
					lambda x: x.repartition_type == 'base').tag_ids
				tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
				if tags_need_inversion:
					balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
					for tax_res in balance_taxes_res['taxes']:
						tax_res['tag_ids'] = base_line._revert_signed_tags(
							self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

			# tax_amount = 0
			# price_amount = 0

			# for line in self.invoice_line_ids:
			#     if line.tax_ids:
			#         for tax in line.tax_ids:
			#             # taxes = (line.price_subtotal * tax.amount / 100)
			#             taxes = tax.compute_all(line.price_subtotal, currency=line.currency_id, quantity=1, product=None, partner=None, is_refund=None)
			#             tax_amount += taxes['taxes'][0]['amount']
			#             price_amount += taxes['taxes'][0]['base']
			#     # if line.price_subtotal:
			#     #     price_value = line.price_subtotal
			# balance_taxes_res['taxes'][0]['base'] = -price_amount
			# balance_taxes_res['taxes'][0]['amount'] = -tax_amount

			return balance_taxes_res

		taxes_map = {}

		# ==== Add tax lines ====
		to_remove = self.env['account.move.line']
		for line in self.line_ids.filtered('tax_repartition_line_id'):
			grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
			grouping_key = _serialize_tax_grouping_key(grouping_dict)
			if grouping_key in taxes_map:
				# A line with the same key does already exist, we only need one
				# to modify it; we have to drop this one.
				to_remove += line
			else:
				taxes_map[grouping_key] = {
					'tax_line': line,
					'amount': 0.0,
					'tax_base_amount': 0.0,
					'grouping_dict': False,
				}
		if not recompute_tax_base_amount:
			self.line_ids -= to_remove

		# ==== Mount base lines ====
		for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
			# Don't call compute_all if there is no tax.
			if not line.tax_ids:
				if not recompute_tax_base_amount:
					line.tax_tag_ids = [(5, 0, 0)]
				continue

			compute_all_vals = _compute_base_line_taxes(line)

			# Assign tags on base line
			if not recompute_tax_base_amount:
				line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

			tax_exigible = True
			for tax_vals in compute_all_vals['taxes']:
				grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
				grouping_key = _serialize_tax_grouping_key(grouping_dict)

				tax_repartition_line = self.env['account.tax.repartition.line'].browse(
					tax_vals['tax_repartition_line_id'])
				tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

				if tax.tax_exigibility == 'on_payment':
					tax_exigible = False

				taxes_map_entry = taxes_map.setdefault(grouping_key, {
					'tax_line': None,
					'amount': 0.0,
					'tax_base_amount': 0.0,
					'grouping_dict': False,
				})
				taxes_map_entry['amount'] += tax_vals['amount']
				taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'],
																					   tax_repartition_line,
																					   tax_vals['group'])
				taxes_map_entry['grouping_dict'] = grouping_dict
			if not recompute_tax_base_amount:
				line.tax_exigible = tax_exigible

		# ==== Pre-process taxes_map ====
		taxes_map = self._preprocess_taxes_map(taxes_map)

		# ==== Process taxes_map ====
		for taxes_map_entry in taxes_map.values():
			# The tax line is no longer used in any base lines, drop it.
			if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
				if not recompute_tax_base_amount:
					self.line_ids -= taxes_map_entry['tax_line']
				continue

			currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

			# Don't create tax lines with zero balance.
			if currency.is_zero(taxes_map_entry['amount']):
				if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
					self.line_ids -= taxes_map_entry['tax_line']
				continue

			# tax_base_amount field is expressed using the company currency.
			tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id,
												self.company_id, self.date or fields.Date.context_today(self))

			# Recompute only the tax_base_amount.
			if recompute_tax_base_amount:
				if taxes_map_entry['tax_line']:
					taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
				continue

			balance = currency._convert(
				taxes_map_entry['amount'],
				self.company_currency_id,
				self.company_id,
				self.date or fields.Date.context_today(self),
			)
			to_write_on_line = {
				'amount_currency': taxes_map_entry['amount'],
				'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
				'debit': balance > 0.0 and balance or 0.0,
				'credit': balance < 0.0 and -balance or 0.0,
				'tax_base_amount': tax_base_amount,
			}

			if taxes_map_entry['tax_line']:
				# Update an existing tax line.
				taxes_map_entry['tax_line'].update(to_write_on_line)
			else:
				create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
					'account.move.line'].create
				tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
				tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
				tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
				taxes_map_entry['tax_line'] = create_method({
					**to_write_on_line,
					'name': tax.name,
					'move_id': self.id,
					'partner_id': line.partner_id.id,
					'company_id': line.company_id.id,
					'company_currency_id': line.company_currency_id.id,
					'tax_base_amount': tax_base_amount,
					'exclude_from_invoice_tab': True,
					'tax_exigible': tax.tax_exigibility == 'on_invoice',
					**taxes_map_entry['grouping_dict'],
				})

			if in_draft_mode:
				taxes_map_entry['tax_line'].update(
					taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	move_id = fields.Many2one('account.move', string='Journal Entry',
							  index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
							  check_company=True,
							  help="The move of this entry line.")
	price_value_new = fields.Float(string='new value')

	site_id = fields.Many2one(
		comodel_name="site.site",
		string="Site", )
	analytic_account_id = fields.Many2one(
		comodel_name="account.analytic.account",
		string="Project", )
	employee_id = fields.Many2one(
		comodel_name="hr.employee",
		string="Employee", )
	category = fields.Selection([
		('weekly', 'Weekly'),
		('monthly', 'Monthly'),
		('day', 'Day'),
		('lumpsum', 'Lumpsum'),
		('hourly', 'Hourly'),
		('each', 'Each'),
		('misc', 'Misc'),
	], string="Category",
	)

	unit = fields.Char(string='Unit')
	start_date = fields.Date(string='Start Date')
	end_date = fields.Date(string='End Date')
	days = fields.Integer(string='Days', compute="_get_days")
	hours = fields.Float(string="Hours")

	department_id = fields.Many2one(
		comodel_name="hr.department",
		string="Department", )
	# asset_id = fields.Many2one(
	# 	comodel_name="account.asset",
	# 	string="Asset",)
	accomadation_id = fields.Many2one(
		comodel_name="hr.accomadation",
		string="Accomadation", )

	taxed_amount = fields.Float(string="Tax Amount", compute="compute_taxamount")
	advance_line = fields.Boolean(string="Advance Line")
	acc_desc = fields.Char(
		string="Account Description", )
	# price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=False,
	# 	currency_field='currency_id')
	pt_total_amount = fields.Float(string='Net Amount(Incl.Vat)', compute="compute_amount_pt", store=True)
	pt_vat_amount = fields.Float(string='Total VAT', compute="compute_amount_pt", store=True)
	pt_taxable_amount = fields.Float(string='Total Taxable Amt', compute="compute_amount_pt", store=True)
	employee = fields.Boolean(string='Employee', related='account_id.employee')
	project = fields.Boolean(string='Project', related='account_id.project')
	asset = fields.Boolean(string='Asset', related='account_id.asset')
	cost_center = fields.Boolean(string='Department', related='account_id.cost_center')
	cost_center_new = fields.Boolean(string='Cost Center', related='account_id.cost_center_new')
	accomodation = fields.Boolean(string='Accomodation', related='account_id.accomodation')
	budgetry_position_id = fields.Many2one('account.budget.post', string='Cost Center')
	seq = fields.Integer(
		string="Sequence", )
	journal_code_id = fields.Many2one(
		comodel_name="journal.code",
		string="Journal Code", related='move_id.journal_code_id', store=True)
	invoice_type_id = fields.Many2one(
		comodel_name="invoice.type",
		string="Invoice Type", related='move_id.invoice_type_id', store=True)
	price_unit = fields.Float(string='Unit Price', digits='Product Price')

	@api.depends('start_date', 'end_date')
	def _get_days(self):
		for rec in self:
			if rec.start_date and rec.end_date:
				start = rec.start_date
				end = rec.end_date
				day = end - start
				rec.days = int(str(day.days)) + 1
			else:
				rec.days = 0

	#
	# @api.onchange('product_uom_id','price_unit', 'quantity')
	# def _onchange_product(self):
	#     for line in self:
	#         if line.price_unit:
	#             line.price_subtotal= line.quantity * line.price_unit

	@api.onchange('quantity', 'discount', 'product_uom_id', 'price_unit', 'tax_ids', 'start_date', 'end_date',
				  'product_id')
	def _onchange_price_subtotal(self):
		return super(AccountMoveLine, self)._onchange_price_subtotal()

	def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None,
									  partner=None, taxes=None, move_type=None):
		res = super(AccountMoveLine, self)._get_price_total_and_subtotal(price_unit=None, quantity=None, discount=None,
																		 currency=None, product=None, partner=None,
																		 taxes=None, move_type=None)

		
		if self.product_uom_id and not self.product_id:
			self.ensure_one()
			for line in self:
				amounts = 0.00
				if line.product_uom_id.name == "Days":
					amounts = line.days * (line.price_unit * line.quantity)
				if line.product_uom_id.name == "Weekly":
					amounts = (self.days / 7) * (line.price_unit * line.quantity)
				if line.product_uom_id.name == "Monthly":
					today = datetime.today()
					if line.start_date:
						month = line.start_date.month
						if month in [1, 3, 5, 7, 8, 10, 12]:
							amounts = (line.price_unit / 31) * (line.days * line.quantity)
						elif month == 2:
							month_count = monthrange(datetime.today().year, 2)
							amounts = (line.price_unit / month_count[1]) * (line.days * line.quantity)
						else:
							amounts = (line.days / 30) * (line.price_unit * line.quantity)
				if line.product_uom_id.name == "LS":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "LM":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "M":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "Misc":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "Nos.":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "Units":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "Each":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "%":
					amounts = line.quantity * line.price_unit
				if line.product_uom_id.name == "Dozens":
					amounts = (line.quantity * 12) * line.price_unit
				if line.product_uom_id.name == "Hours":
					amounts = (line.quantity * line.price_unit)
				res['price_subtotal'] = amounts
				taxes = 0
				for tax_line in line.tax_ids:
					taxes = taxes + (line.price_subtotal * tax_line.amount / 100)
				res['price_total'] = amounts + taxes
		return res

	@api.onchange('price_unit')
	def _onchange_price(self):
		for line in self:
			if line.price_unit:
				line.price_value_new = line.price_unit

	@api.model_create_multi
	def create(self, vals_list):
		res = super(AccountMoveLine, self).create(vals_list)
		for rec in res:
			rec['price_unit'] = rec.price_value_new
		return res

	def _prepare_analytic_line(self):
		""" Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
			an analytic account. This method is intended to be extended in other modules.
			:return list of values to create analytic.line
			:rtype list
		"""
		result = []
		for move_line in self:
			amount = (move_line.credit or 0.0) - (move_line.debit or 0.0)
			default_name = move_line.name or (
						move_line.ref or '/' + ' -- ' + (move_line.partner_id and move_line.partner_id.name or '/'))
			result.append({
				'name': default_name,
				'date': move_line.date,
				'account_id': move_line.analytic_account_id.id,
				'group_id': move_line.analytic_account_id.group_id.id,
				'tag_ids': [(6, 0, move_line._get_analytic_tag_ids())],
				'unit_amount': move_line.quantity,
				'product_id': move_line.product_id and move_line.product_id.id or False,
				'product_uom_id': move_line.product_uom_id and move_line.product_uom_id.id or False,
				'amount': amount,
				'general_account_id': move_line.account_id.id,
				'ref': move_line.ref,
				'move_id': move_line.id,
				'user_id': move_line.move_id.invoice_user_id.id or self._uid,
				'partner_id': move_line.partner_id.id,
				'budgetry_position_id': move_line.budgetry_position_id.id,
				'company_id': move_line.analytic_account_id.company_id.id or move_line.move_id.company_id.id,
			})
		return result

	@api.model
	def default_get(self, fields):
		res = super(AccountMoveLine, self).default_get(fields)
		if self._context:
			context_keys = self._context.keys()
			next_sequence = 1
			if 'line_ids' in context_keys:
				if len(self._context.get('line_ids')) > 0:
					next_sequence = len(self._context.get('line_ids')) + 1
		res.update({'seq': next_sequence})
		return res

	@api.onchange('product_id')
	def _onchange_product_id(self):
		for line in self:
			if not line.move_id.petty_cash_type == True:
				if not line.product_id or line.display_type in ('line_section', 'line_note'):
					continue

				line.name = line._get_computed_name()
				line.account_id = line._get_computed_account()
				taxes = line._get_computed_taxes()
				if taxes and line.move_id.fiscal_position_id:
					taxes = line.move_id.fiscal_position_id.map_tax(taxes, partner=line.partner_id)
				line.tax_ids = taxes
				line.product_uom_id = line._get_computed_uom()
				line.price_unit = line._get_computed_price_unit()

	# @api.model
	# def default_get(self, fields):
	#     result = super(AccountMoveLine, self).default_get(fields)
	#     if result.get('move_id'):
	#         move_id = result.get('move_id')
	#         move_obj = self.env['account.invoice'].browse(move_id)
	#         result.update(
	#             {'site_id': move_obj.site_id and move_obj.site_id.id or False,
	#             'employee_id': move_obj.employee_id and move_obj.employee_id.id or False})
	#     return result

	@api.depends('tax_ids', 'credit', 'debit')
	def compute_amount_pt(self):
		for line in self:
			amount = line.debit
			if line.tax_ids:

				taxes = line.tax_ids.compute_all(amount, line.move_id.currency_id, 1, product=False, partner=False)
				line.update({
					'pt_vat_amount': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
					'pt_total_amount': taxes['total_included'],
					'pt_taxable_amount': line.debit,
				})
			else:
				line.update({
					'pt_vat_amount': 0.00,
					'pt_total_amount': line.debit,
					'pt_taxable_amount': line.debit,
				})

	@api.depends('tax_ids')
	def compute_taxamount(self):
		for line in self:
			taxes = line.tax_ids.compute_all(line.price_unit, line.move_id.currency_id, line.quantity, product=False,
											 partner=line.move_id.partner_id)
			line.update({
				'taxed_amount': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
				# 'line_total': taxes['total_included'],
				# 'subtotal': taxes['total_excluded'],
			})

	@api.onchange('product_id')
	def set_default_qty(self):
		for line in self:
			if line.product_id.is_advance == True:
				line.quantity = -(line.quantity)
				line.price_unit = (line.price_unit)
				line.price_subtotal = -(line.price_subtotal)
				line.price_total = -(line.price_subtotal)

	def _create_exchange_difference_move(self):
		''' Create the exchange difference journal entry on the current journal items.
		:return: An account.move record.
		'''

		def _add_lines_to_exchange_difference_vals(lines, exchange_diff_move_vals):
			''' Generate the exchange difference values used to create the journal items
			in order to fix the residual amounts and add them into 'exchange_diff_move_vals'.

			1) When reconciled on the same foreign currency, the journal items are
			fully reconciled regarding this currency but it could be not the case
			of the balance that is expressed using the company's currency. In that
			case, we need to create exchange difference journal items to ensure this
			residual amount reaches zero.

			2) When reconciled on the company currency but having different foreign
			currencies, the journal items are fully reconciled regarding the company
			currency but it's not always the case for the foreign currencies. In that
			case, the exchange difference journal items are created to ensure this
			residual amount in foreign currency reaches zero.

			:param lines:                   The account.move.lines to which fix the residual amounts.
			:param exchange_diff_move_vals: The current vals of the exchange difference journal entry.
			:return:                        A list of pair <line, sequence> to perform the reconciliation
											at the creation of the exchange difference move where 'line'
											is the account.move.line to which the 'sequence'-th exchange
											difference line will be reconciled with.
			'''
			journal = self.env['account.journal'].browse(exchange_diff_move_vals['journal_id'])
			to_reconcile = []

			for line in lines:

				exchange_diff_move_vals['date'] = max(exchange_diff_move_vals['date'], line.date)

				if not line.company_currency_id.is_zero(line.amount_residual):
					# amount_residual_currency == 0 and amount_residual has to be fixed.

					if line.amount_residual > 0.0:
						exchange_line_account = journal.company_id.expense_currency_exchange_account_id
					else:
						exchange_line_account = journal.company_id.income_currency_exchange_account_id

				elif line.currency_id and not line.currency_id.is_zero(line.amount_residual_currency):
					# amount_residual == 0 and amount_residual_currency has to be fixed.

					if line.amount_residual_currency > 0.0:
						exchange_line_account = journal.company_id.expense_currency_exchange_account_id
					else:
						exchange_line_account = journal.company_id.income_currency_exchange_account_id
				else:
					continue

				sequence = len(exchange_diff_move_vals['line_ids'])
				exchange_diff_move_vals['line_ids'] += [
					(0, 0, {
						'name': _('Currency exchange rate difference'),
						'debit': -line.amount_residual if line.amount_residual < 0.0 else 0.0,
						'credit': line.amount_residual if line.amount_residual > 0.0 else 0.0,
						'amount_currency': -line.amount_residual_currency,
						'account_id': line.account_id.id,
						'currency_id': line.currency_id.id,
						'partner_id': line.partner_id.id,
						'sequence': sequence,
					}),
					(0, 0, {
						'name': _('Currency exchange rate difference'),
						'debit': line.amount_residual if line.amount_residual > 0.0 else 0.0,
						'credit': -line.amount_residual if line.amount_residual < 0.0 else 0.0,
						'amount_currency': line.amount_residual_currency,
						'account_id': exchange_line_account.id,
						'currency_id': line.currency_id.id,
						'partner_id': line.partner_id.id,
						'sequence': sequence + 1,
					}),
				]

				to_reconcile.append((line, sequence))

			return to_reconcile

		def _add_cash_basis_lines_to_exchange_difference_vals(lines, exchange_diff_move_vals):
			''' Generate the exchange difference values used to create the journal items
			in order to fix the cash basis lines using the transfer account in a multi-currencies
			environment when this account is not a reconcile one.

			When the tax cash basis journal entries are generated and all involved
			transfer account set on taxes are all reconcilable, the account balance
			will be reset to zero by the exchange difference journal items generated
			above. However, this mechanism will not work if there is any transfer
			accounts that are not reconcile and we are generating the cash basis
			journal items in a foreign currency. In that specific case, we need to
			generate extra journal items at the generation of the exchange difference
			journal entry to ensure this balance is reset to zero and then, will not
			appear on the tax report leading to erroneous tax base amount / tax amount.

			:param lines:                   The account.move.lines to which fix the residual amounts.
			:param exchange_diff_move_vals: The current vals of the exchange difference journal entry.
			'''
			for move in lines.move_id:
				account_vals_to_fix = {}

				move_values = move._collect_tax_cash_basis_values()

				# The cash basis doesn't need to be handle for this move because there is another payment term
				# line that is not yet fully paid.
				if not move_values or not move_values['is_fully_paid']:
					continue

				# ==========================================================================
				# Add the balance of all tax lines of the current move in order in order
				# to compute the residual amount for each of them.
				# ==========================================================================

				for line in move_values['to_process_lines']:

					vals = {
						'currency_id': line.currency_id.id,
						'partner_id': line.partner_id.id,
						'tax_ids': [(6, 0, line.tax_ids.ids)],
						'tax_tag_ids': [(6, 0, line._convert_tags_for_cash_basis(line.tax_tag_ids).ids)],
						'debit': line.debit,
						'credit': line.credit,
					}

					if line.tax_repartition_line_id:
						# Tax line.
						grouping_key = self.env[
							'account.partial.reconcile']._get_cash_basis_tax_line_grouping_key_from_record(line)
						if grouping_key in account_vals_to_fix:
							debit = account_vals_to_fix[grouping_key]['debit'] + vals['debit']
							credit = account_vals_to_fix[grouping_key]['credit'] + vals['credit']
							balance = debit - credit

							account_vals_to_fix[grouping_key].update({
								'debit': balance if balance > 0 else 0,
								'credit': -balance if balance < 0 else 0,
								'tax_base_amount': account_vals_to_fix[grouping_key][
													   'tax_base_amount'] + line.tax_base_amount,
							})
						else:
							account_vals_to_fix[grouping_key] = {
								**vals,
								'account_id': line.account_id.id,
								'tax_base_amount': line.tax_base_amount,
								'tax_repartition_line_id': line.tax_repartition_line_id.id,
							}
					elif line.tax_ids:
						# Base line.
						account_to_fix = line.company_id.account_cash_basis_base_account_id
						if not account_to_fix:
							continue

						grouping_key = self.env[
							'account.partial.reconcile']._get_cash_basis_base_line_grouping_key_from_record(line,
																											account=account_to_fix)

						if grouping_key not in account_vals_to_fix:
							account_vals_to_fix[grouping_key] = {
								**vals,
								'account_id': account_to_fix.id,
							}
						else:
							# Multiple base lines could share the same key, if the same
							# cash basis tax is used alone on several lines of the invoices
							account_vals_to_fix[grouping_key]['debit'] += vals['debit']
							account_vals_to_fix[grouping_key]['credit'] += vals['credit']

				# ==========================================================================
				# Subtract the balance of all previously generated cash basis journal entries
				# in order to retrieve the residual balance of each involved transfer account.
				# ==========================================================================

				cash_basis_moves = self.env['account.move'].search([('tax_cash_basis_move_id', '=', move.id)])
				for line in cash_basis_moves.line_ids:
					grouping_key = None
					if line.tax_repartition_line_id:
						# Tax line.
						grouping_key = self.env[
							'account.partial.reconcile']._get_cash_basis_tax_line_grouping_key_from_record(
							line,
							account=line.tax_line_id.cash_basis_transition_account_id,
						)
					elif line.tax_ids:
						# Base line.
						grouping_key = self.env[
							'account.partial.reconcile']._get_cash_basis_base_line_grouping_key_from_record(
							line,
							account=line.company_id.account_cash_basis_base_account_id,
						)

					if grouping_key not in account_vals_to_fix:
						continue

					account_vals_to_fix[grouping_key]['debit'] -= line.debit
					account_vals_to_fix[grouping_key]['credit'] -= line.credit

				# ==========================================================================
				# Generate the exchange difference journal items:
				# - to reset the balance of all transfer account to zero.
				# - fix rounding issues on the tax account/base tax account.
				# ==========================================================================

				for values in account_vals_to_fix.values():
					balance = values['debit'] - values['credit']

					if move.company_currency_id.is_zero(balance):
						continue

					if values.get('tax_repartition_line_id'):
						# Tax line.
						tax_repartition_line = self.env['account.tax.repartition.line'].browse(
							values['tax_repartition_line_id'])
						account = tax_repartition_line.account_id or self.env['account.account'].browse(
							values['account_id'])

						sequence = len(exchange_diff_move_vals['line_ids'])
						exchange_diff_move_vals['line_ids'] += [
							(0, 0, {
								**values,
								'name': _('Currency exchange rate difference (cash basis)'),
								'debit': balance if balance > 0.0 else 0.0,
								'credit': -balance if balance < 0.0 else 0.0,
								'account_id': account.id,
								'sequence': sequence,
							}),
							(0, 0, {
								**values,
								'name': _('Currency exchange rate difference (cash basis)'),
								'debit': -balance if balance < 0.0 else 0.0,
								'credit': balance if balance > 0.0 else 0.0,
								'account_id': values['account_id'],
								'tax_ids': [],
								'tax_tag_ids': [],
								'tax_repartition_line_id': False,
								'sequence': sequence + 1,
							}),
						]
					else:
						# Base line.
						sequence = len(exchange_diff_move_vals['line_ids'])
						exchange_diff_move_vals['line_ids'] += [
							(0, 0, {
								**values,
								'name': _('Currency exchange rate difference (cash basis)'),
								'debit': balance if balance > 0.0 else 0.0,
								'credit': -balance if balance < 0.0 else 0.0,
								'sequence': sequence,
							}),
							(0, 0, {
								**values,
								'name': _('Currency exchange rate difference (cash basis)'),
								'debit': -balance if balance < 0.0 else 0.0,
								'credit': balance if balance > 0.0 else 0.0,
								'tax_ids': [],
								'tax_tag_ids': [],
								'sequence': sequence + 1,
							}),
						]

		if not self:
			return self.env['account.move']

		company = self[0].company_id
		journal = company.currency_exchange_journal_id

		exchange_diff_move_vals = {
			'move_type': 'entry',
			'date': date.min,
			'journal_id': journal.id,
			'line_ids': [],
		}

		# Fix residual amounts.
		to_reconcile = _add_lines_to_exchange_difference_vals(self, exchange_diff_move_vals)

		# Fix cash basis entries.
		is_cash_basis_needed = self[0].account_internal_type in ('receivable', 'payable')
		if is_cash_basis_needed:
			_add_cash_basis_lines_to_exchange_difference_vals(self, exchange_diff_move_vals)

		# ==========================================================================
		# Create move and reconcile.
		# ==========================================================================

		# if exchange_diff_move_vals['line_ids']:
		#     # Check the configuration of the exchange difference journal.

		#     if not journal:
		#         raise UserError(_("You should configure the 'Exchange Gain or Loss Journal' in your company settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
		#     if not journal.company_id.expense_currency_exchange_account_id:
		#         raise UserError(_("You should configure the 'Loss Exchange Rate Account' in your company settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
		#     if not journal.company_id.income_currency_exchange_account_id.id:
		#         raise UserError(_("You should configure the 'Gain Exchange Rate Account' in your company settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))

		#     exchange_diff_move_vals['date'] = max(exchange_diff_move_vals['date'], company._get_user_fiscal_lock_date())

		#     exchange_move = self.env['account.move'].create(exchange_diff_move_vals)
		# else:
		#     return None
		return None

		# Reconcile lines to the newly created exchange difference journal entry by creating more partials.
		partials_vals_list = []
		for source_line, sequence in to_reconcile:
			exchange_diff_line = exchange_move.line_ids[sequence]

			if source_line.company_currency_id.is_zero(source_line.amount_residual):
				exchange_field = 'amount_residual_currency'
			else:
				exchange_field = 'amount_residual'

			if exchange_diff_line[exchange_field] > 0.0:
				debit_line = exchange_diff_line
				credit_line = source_line
			else:
				debit_line = source_line
				credit_line = exchange_diff_line

			partials_vals_list.append({
				'amount': abs(source_line.amount_residual),
				'debit_amount_currency': abs(debit_line.amount_residual_currency),
				'credit_amount_currency': abs(credit_line.amount_residual_currency),
				'debit_move_id': debit_line.id,
				'credit_move_id': credit_line.id,
			})

		self.env['account.partial.reconcile'].create(partials_vals_list)

		return exchange_move

# @api.onchange('quantity')
# def set_default_value(self):
# 	for line in self:
# 		if line.move_id.site_id:
# 			line.site_id = line.move_id.site_id.id
# 		if line.move_id.analytic_account_id:
# 			line.analytic_account_id = line.move_id.analytic_account_id.id
# 		if line.move_id.employee_id:
# 			line.employee_id = line.move_id.employee_id.id


class AccountAnalyticLine(models.Model):
	_inherit = 'account.analytic.line'

	budgetry_position_id = fields.Many2one('account.budget.post', string='Cost Center')


class ProductTemplate(models.Model):
	_inherit = "product.template"

	is_advance = fields.Boolean('Is Advance')
	gl_account_id = fields.Many2one(
		comodel_name="account.account",
		string="GL Account", )


class SequenceMixin(models.AbstractModel):
	"""Mechanism used to have an editable sequence number.

	Be careful of how you use this regarding the prefixes. More info in the
	docstring of _get_last_sequence.
	"""

	_inherit = 'sequence.mixin'

	def _constrains_date_sequence(self):
		# Make it possible to bypass the constraint to allow edition of already messed up documents.
		# /!\ Do not use this to completely disable the constraint as it will make this mixin unreliable.
		constraint_date = fields.Date.to_date(self.env['ir.config_parameter'].sudo().get_param(
			'sequence.mixin.constraint_start_date',
			'1970-01-01'
		))
		for record in self:
			date = fields.Date.to_date(record[record._sequence_date_field])
			sequence = record[record._sequence_field]
			if sequence and date and date > constraint_date:
				format_values = record._get_sequence_format_param(sequence)[1]
			# if (
			#     format_values['year'] and format_values['year'] != date.year % 10**len(str(format_values['year']))
			#     or format_values['month'] and format_values['month'] != date.month
			# ):
			#     raise ValidationError(_(
			#         "The %(date_field)s (%(date)s) doesn't match the %(sequence_field)s (%(sequence)s).\n"
			#         "You might want to clear the field %(sequence_field)s before proceeding with the change of the date.",
			#         date=format_date(self.env, date),
			#         sequence=sequence,
			#         date_field=record._fields[record._sequence_date_field]._description_string(self.env),
			#         sequence_field=record._fields[record._sequence_field]._description_string(self.env),
			#     ))


class AccountPaymentRegister(models.TransientModel):
	_inherit = 'account.payment.register'

	def _create_payments(self):
		self.ensure_one()
		batches = self._get_batches()
		edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

		to_reconcile = []
		if edit_mode:
			payment_vals = self._create_payment_vals_from_wizard()
			payment_vals_list = [payment_vals]
			to_reconcile.append(batches[0]['lines'])
		else:
			# Don't group payments: Create one batch per move.
			if not self.group_payment:
				new_batches = []
				for batch_result in batches:
					for line in batch_result['lines']:
						new_batches.append({
							**batch_result,
							'lines': line,
						})
				batches = new_batches

			payment_vals_list = []
			for batch_result in batches:
				payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
				to_reconcile.append(batch_result['lines'])

		payments = self.env['account.payment'].create(payment_vals_list)

		# If payments are made using a currency different than the source one, ensure the balance match exactly in
		# order to fully paid the source journal items.
		# For example, suppose a new currency B having a rate 100:1 regarding the company currency A.
		# If you try to pay 12.15A using 0.12B, the computed balance will be 12.00A for the payment instead of 12.15A.
		if edit_mode:
			for payment, lines in zip(payments, to_reconcile):
				# Batches are made using the same currency so making 'lines.currency_id' is ok.
				if payment.currency_id != lines.currency_id:
					liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
					source_balance = abs(sum(lines.mapped('amount_residual')))
					payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
					source_balance_converted = abs(source_balance) * payment_rate

					# Translate the balance into the payment currency is order to be able to compare them.
					# In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
					# attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
					# match.
					payment_balance = abs(sum(counterpart_lines.mapped('balance')))
					payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
					if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
						continue

					delta_balance = source_balance - payment_balance

					# Balance are already the same.
					if self.company_currency_id.is_zero(delta_balance):
						continue

					# Fix the balance but make sure to peek the liquidity and counterpart lines first.
					debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
					credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

					payment.move_id.write({'line_ids': [
						(1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
						(1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
					]})

		payments.action_post()

		domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
		for payment, lines in zip(payments, to_reconcile):

			# When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
			# and then, we can't perform the reconciliation.
			if payment.state != 'posted':
				continue

			payment_lines = payment.line_ids.filtered_domain(domain)
			for account in payment_lines.account_id:
				(payment_lines + lines) \
					.filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
					.reconcile()
				amt = self.amount
				for line in lines:
					if line.move_id.amount_residual <= amt:
						line.amount_residual = 0.00
						line.move_id.amount_residual = 0.00
						line.move_id.payment_state = 'paid'
						amt = amt - line.move_id.amount_residual

		return payments
