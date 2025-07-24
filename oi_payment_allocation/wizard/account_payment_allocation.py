'''
Created on Oct 20, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime

class PaymentAllocation(models.TransientModel):
    _name = "account.payment.allocation"
    _description ='Payment Allocation'

    @api.model
    def _get_payment(self):
        if self._context.get('active_model') == 'account.payment':
            return [(6, 0, self._context.get('active_ids'))]

    @api.model
    def _get_invoice(self):
        if self._context.get('active_model') == 'account.move':
            return [(6, 0, self._context.get('active_ids'))]

    @api.model
    def _get_statement(self):
        if self._context.get('active_model') == 'account.bank.statement':
            return [(6, 0, self._context.get('active_ids'))]

    @api.model
    def _get_adv_payment(self):
        if self._context.get('active_model') == 'account.advance.payment':
            return [(0, 0, self._context.get('active_ids'))]

    partner_id = fields.Many2one('res.partner', required=True)
    account_id = fields.Many2one('account.account', required=True)
    show_child = fields.Boolean('Show parent/children')

    line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id')
    invoice_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id',
                                       domain=[('type', '=', 'invoice')])
    payment_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id',
                                       domain=[('type', '=', 'payment')])
    other_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id',
                                     domain=[('type', '=', 'other')])
    advance_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id',
                                       domain=[('type', '=', 'advance')])
    credit_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id',
                                      domain=[('type', '=', 'credit')])
    debit_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id',
                                     domain=[('type', '=', 'debit')])

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(related='company_id.currency_id')

    balance = fields.Monetary(compute='_calc_balance')

    payment_ids = fields.Many2many('account.payment', default=_get_payment)
    invoice_ids = fields.Many2many('account.move', default=_get_invoice)
    statement_ids = fields.Many2many('account.bank.statement', default=_get_statement)

    writeoff_acc_id = fields.Many2one('account.account', string='Write off Account')
    writeoff_journal_id = fields.Many2one('account.journal', string='Write off Journal')
    writeoff_ref = fields.Char('Write off Reference')

    create_entry = fields.Boolean('Create Account/Partner Entry')
    entry_journal_id = fields.Many2one('account.journal', string='Account/Partner Entry Journal')
    entry_name = fields.Char('Entry Reference')
    adv_payments_ids = fields.Many2many('account.advance.payment')
    adv_payments_id = fields.Many2one('account.advance.payment')

    exchange_amount_diff = fields.Float(string="Exchange Difference", compute="_compute_diff_amt", store=True)
    foriegn_curr_amt = fields.Float(string="Foreign Currency Amt")
    foriegn_curr_id = fields.Many2one('res.currency', string="Foreign Currency Amt")
    total_amt = fields.Float(string="Converted Amt")
    allocated_amt = fields.Float(string="Allocated Amt", compute="_compute_allocated_amt", store=True)
    foreign_currency = fields.Boolean(string="Foreign Exchange", default=False)

    foriegn_curr_rate = fields.Float(string="Foreign Currency Rate", compute="_compute_rate", store=True)
    exchange_account_id = fields.Many2one('account.account', string="Exchange Account", )
    amount_to_pay = fields.Float(String="Amount")

    @api.onchange('foriegn_curr_amt', 'foriegn_curr_rate')
    def onchange_amt(self):
        for rec in self:
            if rec.foriegn_curr_amt and rec.foriegn_curr_rate:
                rec.total_amt = rec.foriegn_curr_id._convert(
                    rec.foriegn_curr_amt,
                    rec.account_id.company_id.currency_id,
                    rec.account_id.company_id,
                    datetime.date.today(),
                )

    @api.depends('invoice_line_ids', 'amount_to_pay', 'balance', 'total_amt')
    def _compute_diff_amt(self):
        for rec in self:
            if rec.total_amt != (rec.amount_to_pay):
                rec.exchange_amount_diff = (rec.amount_to_pay) - rec.allocated_amt
            else:
                rec.exchange_amount_diff = 0.00
        return True

    @api.depends('foriegn_curr_amt', 'foriegn_curr_id')
    def _compute_rate(self):
        for rec in self:
            rec.foriegn_curr_rate = rec.foriegn_curr_id.rate
        return True

    @api.depends('invoice_line_ids', 'foriegn_curr_id')
    def _compute_allocated_amt(self):
        for rec in self:
            rec.allocated_amt = sum(rec.invoice_line_ids.mapped('allocate_amount'))
        return True

    @api.onchange('adv_payments_id')
    def _onchange_adv_payment_ids(self):
        if self.adv_payments_id:

            self.partner_id = self.adv_payments_id.partner_id
            if self.adv_payments_id.payment_type == 'inbound':
                self.account_id = self.adv_payments_id.partner_id.property_account_receivable_id
            elif self.adv_payments_id.payment_type == 'outbound':
                self.account_id = self.adv_payments_id.partner_id.property_account_payable_id
            self._reset_lines()

    @api.onchange('account_id', 'partner_id', 'show_child', 'company_id')
    def _reset_lines(self):
        if self.account_id and self.partner_id:
            for line_type in ['invoice', 'payment', 'other', 'advance', 'credit', 'debit']:
                fname = '%s_line_ids' % line_type
                self[fname] = False
                domain = [('account_id', '=', self.account_id.id), ('reconciled', '=', False),
                          ('company_id', '=', self.company_id.id)]
                if self.show_child:
                    partner_id = self.partner_id
                    while partner_id.parent_id:
                        partner_id = partner_id.parent_id
                    domain.append(('partner_id', 'child_of', partner_id.ids))
                else:
                    domain.append(('partner_id', '=', self.partner_id.id))
                if line_type == 'invoice':
                    domain.extend([('move_id.move_type', 'in', ['out_invoice', 'in_invoice'])])
                elif line_type == 'credit':
                    domain.extend([('move_id.move_type', 'in', ['out_refund'])])
                elif line_type == 'debit':
                    domain.extend([('move_id.move_type', 'in', ['in_refund'])])
                elif line_type == 'payment':
                    domain.append(('payment_id', '!=', False))
                elif line_type == 'other':
                    domain.extend(
                        [('move_id.move_type', 'not in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
                         ('payment_id', '=', False)])
                else:
                    domain = ([('account_id.user_type_id.type', 'in', ['other']),
                               ('account_id.user_type_id.internal_group', 'in', ['liability', 'asset']),
                               ('partner_id', '=', self.partner_id.id), ('company_id', '=', self.company_id.id),
                               ('reconciled', '=', False), ('move_id.move_type', 'in', ['entry']),
                               ('payment_id', '=', False), ('avoid_line', '=', False)])

                for move_line in self.env['account.move.line'].search(domain):
                    if line_type != 'payment' and move_line.move_id.state != 'posted':
                        continue
                    # print(move_line.move_id,self.adv_payments_id,"payments")

                    if self.adv_payments_id and line_type == 'advance':
                        current_move_id = self.env['account.move'].search([
                            ('advance_payment_id', '=', self.adv_payments_id.id),
                        ], limit=1)
                        if current_move_id != move_line.move_id:
                            continue
                    allocate = move_line.payment_id in self.payment_ids or move_line.move_id in self.invoice_ids

                    self[fname] += self[fname].new({
                        'move_line_id': move_line.id,
                        'allocate': allocate,
                        'type': line_type
                    })

    @api.onchange('payment_ids')
    def _onchange_payment_ids(self):
        if self.payment_ids:
            self.account_id = self.payment_ids[0].destination_account_id
            self.partner_id = self.payment_ids[0].partner_id
            self._reset_lines()

    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        if self.invoice_ids:
            self.account_id = self.invoice_ids.mapped('line_ids.account_id').filtered(
                lambda account: account.user_type_id.type in ['receivable', 'payable'])[:1]
            self.partner_id = self.invoice_ids[0].partner_id
            self._reset_lines()

    @api.depends('invoice_line_ids.allocate_amount', 'payment_line_ids.allocate_amount',
                 'other_line_ids.allocate_amount')
    def _calc_balance(self):
        for record in self:
            balance = 0
            for line in record.invoice_line_ids + record.payment_line_ids + record.other_line_ids:
                if line.allocate:
                    balance += line.allocate_amount * line.sign
            record.balance = balance

    def validate(self):
        if self.balance and self.writeoff_acc_id and self.writeoff_journal_id:
            move_vals = {
                'journal_id': self.writeoff_journal_id.id,
                'ref': self.writeoff_ref or _('Write-Off'),
                'date': max(self.line_ids.mapped('move_line_id.date')),
                'line_ids': [
                    (0, 0, {
                        'account_id': self.account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': -self.balance if self.balance < 0 else 0,
                        'credit': self.balance if self.balance > 0 else 0,

                    }),
                    (0, 0, {
                        'account_id': self.writeoff_acc_id.id,
                        'partner_id': self.partner_id.id,
                        'credit': -self.balance if self.balance < 0 else 0,
                        'debit': self.balance if self.balance > 0 else 0,
                    })
                ]
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            move_line_id = move_id.line_ids.filtered(lambda line: line.account_id == self.account_id)
            self.env["account.payment.allocation.line"].create({
                'allocation_id': self.id,
                'type': 'other',
                'move_line_id': move_line_id.id,
                'allocate': True,
                'allocate_amount': abs(move_line_id.balance)
            })
        # if sum(self.advance_line_ids.mapped('allocate_amount')) > 0.00:

        #     for inv in self.invoice_line_ids:
        #         if inv.allocate_amount > 0.00: 
        #             inv.invoice_id.advnc_deduction += inv.allocate_amount


        debit_line_ids = self.line_ids.filtered(
            lambda line: line.allocate and line.allocate_amount and line.move_line_id.debit)
        credit_line_ids = self.line_ids.filtered(
            lambda line: line.allocate and line.allocate_amount and line.move_line_id.credit)

        # for credit_line_id in credit_line_ids:
        #     if credit_line_id.type == 'advance':
        #         date_field = credit_line_id.edit_date
        #         move_id_advance = credit_line_id.move_id
        #         if move_id_advance and date_field:
        #             move_id_advance.date = date_field
        #             move_id_advance_lines = move_id_advance.line_ids
        #             for move_id_advance_line in move_id_advance_lines:
        #                 move_id_advance_line.date = date_field

        # for debit_lines_id in debit_line_ids:
        #     if debit_lines_id.type == 'advance':
        #         date_field = debit_lines_id.edit_date
        #         move_id_advance = debit_lines_id.move_id
        #         if move_id_advance and date_field:
        #             move_id_advance.date = date_field
        #             move_id_advance_lines = move_id_advance.line_ids
        #             for move_id_advance_line in move_id_advance_lines:
        #                 move_id_advance_line.date = date_field

        if any(adv_line.allocate == True for adv_line in self.advance_line_ids):
            """customer  invoice ++"""
            for credit_line in credit_line_ids:
                if credit_line.move_line_id.account_id.id == 225:
                    # print(" in credit payments")
                    adjusted_date = fields.date.today()
                    if credit_line.type == 'advance' and credit_line.edit_date:
                        adjusted_date = credit_line.edit_date
                    default_journal_misc = self.env['account.journal'].search([
                        ('type', '=', 'general'),('code','=','MISC')], limit=1)
                    if credit_line.amount_residual_display == 0.0:
                        raise ValidationError(_("Insufficient Unallocated Amount in Advance"))

                    if self.foreign_currency:
                        allocated_line_ids = []
                    #
                    #     if not self.exchange_account_id:
                    #         raise ValidationError(_("Exchange Difference Account not configured"))
                    #     if self.exchange_amount_diff < 0:
                    #         if (self.amount_to_pay + -(self.exchange_amount_diff)) != abs(self.balance):
                    #             raise ValidationError(
                    #                 _("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))
                    #     elif self.exchange_amount_diff > 0:
                    #         if (self.amount_to_pay - (self.exchange_amount_diff)) != abs(self.balance):
                    #             raise ValidationError(
                    #                 _("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))
                    #     if self.exchange_amount_diff != 0.0 and self.exchange_amount_diff < 0:
                    #         allocated_line_ids.append((0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit':0.0,
                    #             'debit': -(self.exchange_amount_diff),
                    #             'name': 'Foreign Curr. Exch. Rate-Loss on ' + credit_line.move_line_id.move_id.name
                    #         }))
                    #
                    #         """ exchange difference entry between exchange difference account and advance account"""
                    #
                    #         exchange_difference_lines = [(0, 0, {
                    #             'account_id': credit_line.move_line_id.account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit':0.0,
                    #             'debit': -(self.exchange_amount_diff),
                    #             'avoid_line': True,
                    #         }), (0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit': -(self.exchange_amount_diff),
                    #             'debit':0.0 ,
                    #             'avoid_line': True,
                    #         })]
                    #         # print(exchange_difference_lines,allocated_line_ids)
                    #         exchange_difference_moves = {
                    #             'journal_id': default_journal_misc.id,
                    #             'ref': "exchange difference : " + credit_line.move_line_id.move_id.name,
                    #             'date': adjusted_date,
                    #             'journal_code_id': credit_line.move_line_id.move_id.journal_code_id.id,
                    #             'line_ids': exchange_difference_lines
                    #         }
                    #         print("exchange_difference_lines",exchange_difference_lines)
                    #         move_id_exc = self.env['account.move'].create(exchange_difference_moves)
                    #         move_id_exc.post()
                    #
                    #
                    #     elif self.exchange_amount_diff > 0:
                    #
                    #         allocated_line_ids.append((0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit': (self.exchange_amount_diff),
                    #             'debit':0.0 ,
                    #             'name': 'Foreign Curr. Exch. Rate-Loss on ' + credit_line.move_line_id.move_id.name
                    #         }))
                    #
                    #         """ exchange difference entry between exchange difference account and advance account"""
                    #
                    #         exchange_difference_lines = [(0, 0, {
                    #             'account_id': credit_line.move_line_id.account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'debit':0.0 ,
                    #             'credit': (self.exchange_amount_diff),
                    #             'avoid_line': True,
                    #         }), (0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'debit':(self.exchange_amount_diff),
                    #             'credit':0.0,
                    #             'avoid_line': True,
                    #         })]
                    #
                    #         exchange_difference_moves = {
                    #             'journal_id': default_journal_misc.id,
                    #             'ref': "exchange difference : " + credit_line.move_line_id.move_id.name ,
                    #             'date': adjusted_date,
                    #             'journal_code_id': credit_line.move_line_id.move_id.journal_code_id.id,
                    #             'line_ids': exchange_difference_lines
                    #         }
                    #         move_id_exc = self.env['account.move'].create(exchange_difference_moves)
                    #         move_id_exc.post()


                    else:
                        """ no foreighn exchange """
                        allocated_line_ids = []



                    allocated_invoice_name = ""
                    for allocated_debit_line in debit_line_ids:
                        allocated_line_ids.append((0, 0, {
                            'account_id': self.account_id.id,
                            'partner_id': self.partner_id.id,
                            'credit': allocated_debit_line.allocate_amount,
                            'debit': 0.00,
                            'name': allocated_debit_line.invoice_id.name
                        }))
                        allocated_invoice_name = allocated_invoice_name + allocated_debit_line.invoice_id.name + " /"

                    ref_str = "Matched : " + credit_line.move_line_id.move_id.name + " - " + allocated_invoice_name
                    allocated_line_ids.append((0, 0, {
                        'account_id': credit_line.move_line_id.account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': credit_line.allocate_amount,
                        'credit': 0.00,
                        'avoid_line': True,
                        'name': ref_str,
                        'advance_move_line': credit_line.move_line_id.id
                    }))
                    # print("allocated line ids",allocated_line_ids)
                    move_vals = {
                        'journal_id': default_journal_misc.id,
                        'ref': "Matched : " + credit_line.move_line_id.move_id.name + " - " + allocated_invoice_name,
                        'date': adjusted_date,
                        'journal_code_id': credit_line.move_line_id.move_id.journal_code_id.id,
                        'line_ids': allocated_line_ids
                    }
                    move_id = self.env['account.move'].create(move_vals)
                    move_id.post()
                    move_line_id = move_id.line_ids.filtered(lambda line: line.account_id == self.account_id)
                    for move_line_id_split in move_line_id:
                        self.env["account.payment.allocation.line"].create({
                            'allocation_id': self.id,
                            'type': 'other',
                            'move_line_id': move_line_id_split.id,
                            'allocate': True,
                            'allocate_amount': abs(move_line_id_split.balance)
                        })
                    credit_line.move_line_id.amount_residual += credit_line.allocate_amount
                    credit_line.move_line_id.amount_residual_currency += credit_line.allocate_amount
                    credit_line.allocate = False
            credit_line_ids = self.line_ids.filtered(
                lambda line: line.allocate and line.allocate_amount and line.move_line_id.credit)

            """customer  invoice ++"""

            """vendor bill """

            for debit_line in debit_line_ids:
                if debit_line.move_line_id.account_id.id in (191, 192, 193):
                    # print(" in debit payments", debit_line_ids, debit_line.move_line_id,
                    #       debit_line.move_line_id.move_id)
                    adjusted_date = fields.date.today()
                    if debit_line.type == 'advance' and debit_line.edit_date:
                        adjusted_date = debit_line.edit_date
                    # for allocated_credit_line in credit_line_ids:
                    default_journal_misc = self.env['account.journal'].search([
                        ('type', '=', 'general'),('code','=','MISC')], limit=1)
                    if debit_line.amount_residual_display == 0.0:
                        raise ValidationError(_("Insufficient Unallocated Amount in Advance"))

                    if self.foreign_currency:
                        allocated_line_ids = []
                    #
                    #     if not self.exchange_account_id:
                    #         raise ValidationError(_("Exchange Difference Account not configured"))
                    #     if self.exchange_amount_diff < 0:
                    #         if (self.amount_to_pay + -(self.exchange_amount_diff)) != abs(self.balance):
                    #             raise ValidationError(
                    #                 _("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))
                    #     elif self.exchange_amount_diff > 0:
                    #         if (self.amount_to_pay - (self.exchange_amount_diff)) != abs(self.balance):
                    #             raise ValidationError(
                    #                 _("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))
                    #     if self.exchange_amount_diff != 0.0 and self.exchange_amount_diff < 0:
                    #         allocated_line_ids.append((0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit': -(self.exchange_amount_diff),
                    #             'debit': 0.0,
                    #             'name': 'Foreign Curr. Exch. Rate-Loss on ' + debit_line.move_line_id.move_id.name
                    #         }))
                    #
                    #         """ exchange difference entry between exchange difference account and advance account"""
                    #
                    #         exchange_difference_lines = [(0, 0, {
                    #             'account_id': debit_line.move_line_id.account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit': -(self.exchange_amount_diff),
                    #             'debit': 0.0,
                    #             'avoid_line': True,
                    #         }), (0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit': 0.00,
                    #             'debit': -(self.exchange_amount_diff),
                    #             'avoid_line': True,
                    #         })]
                    #
                    #         exchange_difference_moves = {
                    #             'journal_id': default_journal_misc.id,
                    #             'ref': "exchange difference : " + debit_line.move_line_id.move_id.name,
                    #             'date': adjusted_date,
                    #             'journal_code_id': debit_line.move_line_id.move_id.journal_code_id.id,
                    #             'line_ids': exchange_difference_lines
                    #         }
                    #         print(exchange_difference_lines,"exchange_difference_lines")
                    #         move_id_exc = self.env['account.move'].create(exchange_difference_moves)
                    #         move_id_exc.post()
                    #
                    #
                    #     elif self.exchange_amount_diff > 0:
                    #
                    #         allocated_line_ids.append((0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'credit': 0.00,
                    #             'debit': (self.exchange_amount_diff),
                    #             'name': 'Foreign Curr. Exch. Rate-Loss on ' + debit_line.move_line_id.move_id.name
                    #         }))
                    #
                    #         """ exchange difference entry between exchange difference account and advance account"""
                    #
                    #         exchange_difference_lines = [(0, 0, {
                    #             'account_id': debit_line.move_line_id.account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'debit': (self.exchange_amount_diff),
                    #             'credit': 0.0,
                    #             'avoid_line': True,
                    #         }), (0, 0, {
                    #             'account_id': self.exchange_account_id.id,
                    #             'partner_id': self.partner_id.id,
                    #             'debit': 0.00,
                    #             'credit': (self.exchange_amount_diff),
                    #             'avoid_line': True,
                    #         })]
                    #
                    #         exchange_difference_moves = {
                    #             'journal_id': default_journal_misc.id,
                    #             'ref': "exchange difference : " + debit_line.move_line_id.move_id.name ,
                    #             'date': adjusted_date,
                    #             'journal_code_id': debit_line.move_line_id.move_id.journal_code_id.id,
                    #             'line_ids': exchange_difference_lines
                    #         }
                    #         move_id_exc = self.env['account.move'].create(exchange_difference_moves)
                    #         move_id_exc.post()
                    #

                    else:
                        """ no foreighn exchange """
                        allocated_line_ids = []

                    allocated_invoice_name = ""
                    for allocated_credit_line in credit_line_ids:
                        allocated_line_ids.append((0, 0, {
                            'account_id': self.account_id.id,
                            'partner_id': self.partner_id.id,
                            'credit': 0.00,
                            'debit': allocated_credit_line.allocate_amount,
                            'name': allocated_credit_line.invoice_id.name
                        }))
                        allocated_invoice_name = allocated_invoice_name + allocated_credit_line.invoice_id.name + " /"
                    ref_str = "Matched : " + debit_line.move_line_id.move_id.name + " - " + allocated_invoice_name

                    allocated_line_ids.append((0, 0, {
                        'account_id': debit_line.move_line_id.account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': 0.00,
                        'credit': debit_line.allocate_amount,
                        'avoid_line': True,
                        'name':ref_str,
                        'advance_move_line':debit_line.move_line_id.id
                    }))

                    # print(allocated_line_ids,"allocated_line_ids",ref_str)
                    move_vals = {
                        'journal_id': default_journal_misc.id,
                        'ref': "Matched : " + debit_line.move_line_id.move_id.name + " - " + allocated_invoice_name,
                        'date': adjusted_date,
                        'journal_code_id': debit_line.move_line_id.move_id.journal_code_id.id,
                        'line_ids': allocated_line_ids,
                    }
                    move_id = self.env['account.move'].create(move_vals)
                    move_id.post()
                    move_line_id = move_id.line_ids.filtered(lambda line: line.account_id == self.account_id)
                    # print(allocated_line_ids)
                    for move_line_id_split in move_line_id:
                        self.env["account.payment.allocation.line"].create({
                            'allocation_id': self.id,
                            'type': 'other',
                            'move_line_id': move_line_id_split.id,
                            'allocate': True,
                            'allocate_amount': abs(move_line_id_split.balance)
                        })
                    debit_line.move_line_id.amount_residual -= debit_line.allocate_amount
                    debit_line.move_line_id.amount_residual_currency -= debit_line.allocate_amount
                    # print(debit_line.move_line_id,debit_line.move_line_id.name,debit_line.allocate_amount)
                    debit_line.allocate = False

            debit_line_ids = self.line_ids.filtered(
                lambda line: line.allocate and line.allocate_amount and line.move_line_id.debit)
        """vendor bill  """
        if not debit_line_ids or not credit_line_ids:
            # raise Warning('Select at least one payment & one invoice')
            raise ValidationError(_("Please allocate at least one payment & one invoice"))
        # raise ValidationError(_("Please allocate at least one payment & one invoice"))
        if debit_line_ids:
            tot_payment_amount = sum(debit_line_ids.mapped('allocate_amount'))
        else:
            tot_payment_amount = 0
        if credit_line_ids:
            tot_invoice_amount = sum(credit_line_ids.mapped('allocate_amount'))
        else:
            tot_invoice_amount = 0
        tot_invoice_amount = round(tot_invoice_amount, 2)
        if tot_payment_amount != tot_invoice_amount or tot_payment_amount == tot_invoice_amount == 0:
            # raise Warning('Select at least one payment & one invoice')
            raise ValidationError(_("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))
        move_line_ids = (debit_line_ids + credit_line_ids).mapped('move_line_id')

        partner_ids = move_line_ids.mapped('partner_id')
        partner_balance = False
        if len(partner_ids) > 1 and self.create_entry:
            partner_balance = dict.fromkeys(partner_ids.ids, 0)

        partial_reconcile_ids = self.env["account.partial.reconcile"]

        for debit_line in debit_line_ids:
            for credit_line in credit_line_ids:
                amount = min(abs(debit_line.allocate_amount), abs(credit_line.allocate_amount))

                if not amount:
                    continue
                vals = {
                    'debit_move_id': debit_line.move_line_id.id,
                    'credit_move_id': credit_line.move_line_id.id,
                    'amount': amount,
                }
                if debit_line.move_line_id.amount_currency and credit_line.move_line_id.amount_currency and debit_line.move_line_id.currency_id == credit_line.move_line_id.currency_id:
                    max_date = max(debit_line.move_line_id.date, credit_line.move_line_id.date)
                    company_id = debit_line.move_line_id.company_id
                    #                     vals.update({
                    #                         'currency_id' : debit_line.move_line_id.currency_id.id,
                    #                         'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
                    #                         })
                    min_debit_amount_residual_currency = credit_line.move_line_id.company_currency_id._convert(
                        amount,
                        debit_line.move_line_id.currency_id,
                        credit_line.move_line_id.company_id,
                        credit_line.move_line_id.date,
                    )
                    min_credit_amount_residual_currency = debit_line.move_line_id.company_currency_id._convert(
                        amount,
                        credit_line.move_line_id.currency_id,
                        debit_line.move_line_id.company_id,
                        debit_line.move_line_id.date,
                    )

                    vals.update({

                        'debit_amount_currency': min_debit_amount_residual_currency,
                        'credit_amount_currency': min_credit_amount_residual_currency,
                        # 'debit_move_id': debit_line.id,
                        # 'credit_move_id': credit_line.id,

                    })
                elif debit_line.move_line_id.amount_currency and credit_line.move_line_id.amount_currency and debit_line.move_line_id.currency_id != credit_line.move_line_id.currency_id:
                    max_date = max(debit_line.move_line_id.date, credit_line.move_line_id.date)
                    company_id = debit_line.move_line_id.company_id
                    #                     vals.update({
                    #                         'currency_id' : debit_line.move_line_id.currency_id.id,
                    #                         'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
                    #                         })
                    min_debit_amount_residual_currency = amount
                    min_credit_amount_residual_currency = credit_line.move_line_id.company_currency_id._convert(
                        amount,
                        credit_line.move_line_id.currency_id,
                        debit_line.move_line_id.company_id,
                        debit_line.move_line_id.date,
                    )

                    vals.update({

                        'debit_amount_currency': min_debit_amount_residual_currency,
                        'credit_amount_currency': min_credit_amount_residual_currency,
                        # 'debit_move_id': debit_line.id,
                        # 'credit_move_id': credit_line.id,

                    })

                partial_reconcile_ids += self.env["account.partial.reconcile"].create(vals)

                if partner_balance:
                    partner_balance[debit_line.move_line_id.partner_id.id] += amount
                    partner_balance[credit_line.move_line_id.partner_id.id] -= amount

                debit_line.allocate_amount -= amount * (debit_line.allocate_amount < 0 and -1 or 1)
                credit_line.allocate_amount -= amount * (credit_line.allocate_amount < 0 and -1 or 1)

        reconciled_move_line_ids = move_line_ids.filtered('reconciled')

        if reconciled_move_line_ids:
            partial_reconcile_ids = partial_reconcile_ids.filtered(lambda
                                                                       record: record.debit_move_id in reconciled_move_line_ids or record.credit_move_id in reconciled_move_line_ids)
            self.env["account.full.reconcile"].create({
                'partial_reconcile_ids': [(6, 0, partial_reconcile_ids.ids)],
                'reconciled_line_ids': [(6, 0, reconciled_move_line_ids.ids)],
            })

        if partner_balance:
            move_vals = {
                'journal_id': self.entry_journal_id.id,
                'ref': self.entry_name or 'Payment Allocation',
                'date': max(move_line_ids.mapped('date')),
                'line_ids': []
            }
            for partner_id, balance in partner_balance.items():
                if not balance:
                    continue
                move_vals['line_ids'].append((0, 0, {
                    'account_id': self.account_id.id,
                    'name': '',
                    'partner_id': partner_id,
                    'credit': balance > 0 and balance or 0,
                    'debit': balance < 0 and -balance or 0
                }))
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            move_id.line_ids.reconcile()
            move_line_ids += move_id.line_ids


        return {
            'type': 'ir.actions.act_window_close'
        }
