# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError

class account_advance_payment(models.Model):
    _name = "account.advance.payment"
    _description = "Advance Payments"
    _check_company_auto = True
    
    
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'),
    ], string='Payment Type', default='inbound', required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    name = fields.Char(string='Reference',copy=False,default=False)
    # line_ids = fields.One2many('account.extra.payment.line', 'extra_payment_id', string='Payment lines', copy=True)
    date_done = fields.Date(string="Accounting Date")
    state = fields.Selection([
            ("draft", "Draft"),
            ("post", "Posted"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    site_id = fields.Many2one(
        comodel_name="site.site",
        string="Site")
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Project",)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Pay To",)
    cost_center_id = fields.Many2one(
        comodel_name="cost.center",
        string="Cost Center",)
    journal_code_id = fields.Many2one(
        comodel_name='journal.code',
        string="Journal Code",)
    payment_method  = fields.Selection([ 
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('cheque', 'Cheque'),
    ], string='Payment Mode', )
    cheq_no = fields.Char(string='Cheque No',)
    amount = fields.Float(string='Amount')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency", default=lambda self: self.env.company.currency_id)
    # total_amount = fields.Float(string='Net Amount(Incl.Vat)',compute="compute_amount",store=True)
    # vat_amount = fields.Float(string='Total VAT',compute="compute_amount",store=True)
    # taxable_amount = fields.Float(string='Total Taxable Amt',compute="compute_amount",store=True)
    ref = fields.Char(string='Reference',)
    gl_account_id = fields.Many2one(
        comodel_name="account.account",
        string="GL Account",)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer/Vendor",domain="[('id','in',suitable_partner_ids)]")
    is_advance = fields.Boolean(string='Is Advance',)
    destination_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Destination Account",compute="_compute_destination_account_id")
    total_amount = fields.Monetary(compute="compute_local_amt")
    partner_bank_id = fields.Many2one('res.partner.bank', string="Recipient Bank Account",
        readonly=False, store=True,
        compute='_compute_partner_bank_id',
        domain="[('partner_id', '=', partner_id)]",
        check_company=True)
    suitable_partner_ids = fields.Many2many('res.partner', compute='_compute_suitable_partner_ids')

    exchange_amount_diff = fields.Float(string="Exchange Difference", compute="_compute_diff_amt", store=True)
    foriegn_curr_amt = fields.Float(string="Foreign Currency Amt")
    foriegn_curr_id = fields.Many2one('res.currency', string="Foreign Currency Amt")
    total_amt = fields.Float(string="Converted Amt")
    allocated_amt = fields.Float(string="Allocated Amt", store=True)
    foreign_currency = fields.Boolean(string="Foreign Exchange", default=False)

    foriegn_curr_rate = fields.Float(string="Foreign Currency Rate", compute="_compute_rate", store=True)
    exchange_account_id = fields.Many2one('account.account', string="Exchange Account", )
    amount_to_pay = fields.Float(String="Amount")

    @api.onchange('foriegn_curr_amt', 'foriegn_curr_rate')
    def onchange_amt(self):
        import datetime
        for rec in self:
            if rec.foriegn_curr_amt and rec.foriegn_curr_rate and rec.gl_account_id:
                rec.total_amt = rec.foriegn_curr_id._convert(
                    rec.foriegn_curr_amt,
                    rec.gl_account_id.company_id.currency_id,
                    rec.gl_account_id.company_id,
                    datetime.date.today(),
                )

    @api.depends('amount', 'allocated_amt')
    def _compute_diff_amt(self):
        for rec in self:
            if rec.amount != (rec.allocated_amt):
                rec.exchange_amount_diff = (rec.amount) - rec.allocated_amt
            else:
                rec.exchange_amount_diff = 0.00
        return True

    @api.depends('foriegn_curr_amt', 'foriegn_curr_id')
    def _compute_rate(self):
        for rec in self:
            rec.foriegn_curr_rate = rec.foriegn_curr_id.rate
        return True

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



    @api.depends('partner_id')
    def _compute_partner_bank_id(self):
        ''' The default partner_bank_id will be the first available on the partner. '''
        for pay in self:
            available_partner_bank_accounts = pay.partner_id.bank_ids.filtered(lambda x: x.company_id in (False, pay.company_id))
            if available_partner_bank_accounts:
                if pay.partner_bank_id not in available_partner_bank_accounts:
                    pay.partner_bank_id = available_partner_bank_accounts[0]._origin
            else:
                pay.partner_bank_id = False


    @api.onchange('petty_cash_type','journal_id')
    def set_gl_account_code(self):
        for rec in self:
            if rec.journal_id.type in ('bank','cash'):
                rec.gl_account_id = rec.journal_id.default_account_id or False
            else:
                rec.gl_account_id = False
    @api.depends('currency_id','amount')
    def compute_local_amt(self):
    	self.total_amount = self.currency_id._convert(self.amount, self.company_id.currency_id, self.company_id, self.date_done)


    @api.depends('payment_type','partner_id')
    def _compute_destination_account_id(self):
        self.destination_account_id = False
        for pay in self:
            
            if pay.payment_type == 'inbound':
                # Receive money from invoice or send money to refund it.
                
                pay.destination_account_id = self.env['account.account'].search([
                    ('company_id', '=', pay.company_id.id),
                    ('name', '=', 'Advance from Customers'),
                    ('deprecated', '=', False),
                ], limit=1)
            elif pay.payment_type == 'outbound':
                # Send money to pay a bill or receive money to refund it.
                
                
                pay.destination_account_id = pay.partner_id.advance_account_id

    def button_post(self):
        for payment in self:
            if self.foreign_currency and self.exchange_amount_diff != 0.0 and not self.exchange_account_id:
                raise ValidationError(_('Please Select Exchange Difference Account.'))
            am_obj = self.env["account.move"]
            mvals = self._prepare_move(payment)
            move = am_obj.create(mvals)
            move.number_genrated = True
            move.action_post()
            payment.state='post'


    def _prepare_move(self, payment=None):
        
        if payment.payment_type == "outbound":
            ref = _("%s") % payment.ref
        else:
            ref = _("%s") % payment.ref
        vals = {
            "name": payment.name,
            "journal_id": payment.journal_id.id,
            "ref": ref,
            "advance_payment_id": payment.id,
            # "site_id": payment.site_id.id or False,
            # "analytic_account_id": payment.analytic_account_id.id or False,
            # "cost_center_id": payment.cost_center_id.id or False,
            # "employee_id": payment.employee_id.id or False,
            "journal_code_id": payment.journal_code_id.id or False,
            "line_ids": [],
        }

        vals.update({"date": payment.date_done})
        total_company_currency = total_payment_currency = payment.total_amount
        # for line in payment.line_ids:
        #     total_company_currency += line.total_amount
        #     total_payment_currency += line.total_amount
            
        #     partner_ml_vals = self._prepare_move_line_partner_account(line)

        #     vals["line_ids"].append((0, 0, partner_ml_vals))
        #     if line.tax_ids:
        #         tax_ml_vals = self._prepare_move_line_tax_account(line)
        #         vals["line_ids"].append((0, 0, tax_ml_vals))
        # partner_ml_vals = self._prepare_move_line_partner_account(total_company_currency, total_payment_currency, payment)
        trf_ml_vals = self._prepare_move_line_offsetting_account(
            total_company_currency, total_payment_currency, payment
        )
        vals["line_ids"].append((0, 0, trf_ml_vals))
        trf_adv_vals = self._prepare_move_line_offsetting_adv_account(
            total_company_currency, total_payment_currency, payment
        )
        vals["line_ids"].append((0, 0, trf_adv_vals))

        if payment.payment_type in  ['outbound','inbound']  and payment.foreign_currency and payment.exchange_amount_diff != 0.0:
            for_exc_vals = self._prepare_move_line_for_exch_adv_account(
                total_company_currency, total_payment_currency, payment
            )
            vals["line_ids"].append((0, 0, for_exc_vals))

        return vals


    def _prepare_move_line_offsetting_account(
        self, amount_company_currency, amount_payment_currency, payment):
        vals = {}
        if payment.payment_type == "outbound":
            name = _("%s") % payment.ref
        else:
            name = _("%s") % payment.ref

        vals.update({"date": payment.date_done})
        account_id = payment.journal_id.default_account_id.id
        vals.update(
            {
                "name": name,
                "partner_id": payment.partner_id.id or False,
                "account_id": account_id,
                "advance_payment_id": payment.id,
                "credit": (
                    payment.payment_type == "outbound" and amount_company_currency or 0.0
                ),
                "debit": (
                    payment.payment_type == "inbound" and amount_company_currency or 0.0
                ),
                # "site_id": payment.site_id.id or False,
                "analytic_account_id": payment.analytic_account_id.id or False,
                "cost_center_id": payment.cost_center_id.id or False,
                # "employee_id": payment.employee_id.id or False,
                

            }
        )
        sign = payment.payment_type == "outbound" and -1 or 1
        vals.update(
                {
                    "currency_id": payment.company_id.currency_id.id,
                    "amount_currency": amount_payment_currency * sign,
                }
            )
        return vals

    def _prepare_move_line_offsetting_adv_account(
        self, amount_company_currency, amount_payment_currency, payment):
        vals = {}
        if payment.payment_type == "outbound":
            name = _("%s") % payment.ref
        else:
            name = _("%s") % payment.ref
        
        vals.update({"date": payment.date_done})
        account_id = payment.journal_id.default_account_id.id

        if payment.payment_type == 'outbound' and payment.foreign_currency and payment.exchange_amount_diff != 0.0:
            debit =  payment.allocated_amt
        else:
            debit = (payment.payment_type == "outbound" and amount_company_currency or 0.0 )

        if payment.payment_type == 'inbound' and payment.foreign_currency and payment.exchange_amount_diff != 0.0:
            credit =  payment.allocated_amt
        else:
            credit = (payment.payment_type == "inbound" and amount_company_currency or 0.0)

        vals.update(
            {
                "name": name,
                "partner_id": payment.partner_id.id or False,
                "account_id": payment.destination_account_id.id,
                "advance_payment_id": payment.id,
                "credit": credit,
                "debit":debit,
                "analytic_account_id": payment.analytic_account_id.id or False,
                "cost_center_id": payment.cost_center_id.id or False,
                

            }
        )
        sign = payment.payment_type == "outbound" and -1 or 1
        vals.update(
                {
                    "currency_id": payment.company_id.currency_id.id,
                    "amount_currency": amount_payment_currency * sign,
                }
            )
        return vals

    def _prepare_move_line_for_exch_adv_account(
            self, amount_company_currency, amount_payment_currency, payment):
        vals = {}
        if payment.payment_type == "outbound":
            name = _("%s") % payment.ref
        else:
            name = _("%s") % payment.ref

        vals.update({"date": payment.date_done})
        account_id = payment.exchange_account_id.id

        if payment.payment_type == 'outbound':
            if payment.exchange_amount_diff > 0.0:
                debit = payment.exchange_amount_diff
                credit = 0.0
            else:
                debit = 0.0
                credit = -payment.exchange_amount_diff

        else:
            if payment.exchange_amount_diff > 0.0:
                debit = 0.0
                credit = payment.exchange_amount_diff
            else:
                debit = -payment.exchange_amount_diff
                credit = 0.0


        vals.update(
            {
                "name": name,
                "partner_id": payment.partner_id.id or False,
                "account_id": account_id,
                "advance_payment_id": payment.id,
                "credit": credit,
                "debit": debit,
                "analytic_account_id": payment.analytic_account_id.id or False,
                "cost_center_id": payment.cost_center_id.id or False,

            }
        )
        sign = payment.payment_type == "outbound" and -1 or 1
        vals.update(
            {
                "currency_id": payment.company_id.currency_id.id,
                "amount_currency": amount_payment_currency * sign,
            }
        )
        return vals

    
    def button_journal_entry(self):
        action={}
        for payment in self:
            move_id = self.env['account.move'].search([
                            ('advance_payment_id', '=', payment.id),
                        ], limit=1)
            if move_id:
                action = {
                    'name': _("Journal Entry"),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'context': {'create': False},
                     'view_mode': 'form',
                    'res_id': move_id.id,
                }
        return action   




    
    
