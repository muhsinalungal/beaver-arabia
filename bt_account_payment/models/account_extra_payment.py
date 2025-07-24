# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError

class account_extra_payment(models.Model):
    _name = "account.extra.payment"
    _description = "Extra Payments"
    _check_company_auto = True
    
    
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'),
    ], string='Payment Type', default='inbound', required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,domain="[('id', 'in', suitable_journal_ids)]")
    suitable_journal_ids = fields.Many2many('account.journal', compute='_compute_suitable_journal_ids')
    name = fields.Char(string='Reference',copy=False,default=False)
    partner_name = fields.Char(string='Receipt from',)
    line_ids = fields.One2many('account.extra.payment.line', 'extra_payment_id', string='Payment lines', copy=True)
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
    amount = fields.Float(string='Amount',compute="compute_amount",store=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency", default=lambda self: self.env.company.currency_id)
    total_amount = fields.Float(string='Net Amount(Incl.Vat)',compute="compute_amount",store=True)
    vat_amount = fields.Float(string='Total VAT',compute="compute_amount",store=True)
    taxable_amount = fields.Float(string='Total Taxable Amt',compute="compute_amount",store=True)
    ref = fields.Char(string='Reference',)
    gl_account_id = fields.Many2one(
        comodel_name="account.account",
        string="GL Account",)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer/Vendor",domain="[('id','in',suitable_partner_ids)]")
    suitable_partner_ids = fields.Many2many('res.partner', compute='_compute_suitable_partner_ids')
    is_advance = fields.Boolean(string='Is Advance',)

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

    @api.onchange('petty_cash_type','journal_id')
    def set_gl_account_code(self):
        for rec in self:
            if rec.journal_id.type in ('bank','cash'):
                rec.gl_account_id = rec.journal_id.default_account_id 
            elif rec.journal_id.is_petty_cash == True:
                rec.gl_account_id = rec.journal_id.petty_cash_account_id
            else:
                rec.gl_account_id = False

    @api.depends('company_id', 'payment_type')
    def _compute_suitable_journal_ids(self):
        for m in self:
            if m.payment_type == 'outbound':
                journal_type = ('bank','cash')
                company_id = m.company_id.id or self.env.company.id
                domain = [('company_id', '=', company_id),'|', ('type', 'in', journal_type),('is_petty_cash', '=', True)]
                m.suitable_journal_ids = self.env['account.journal'].search(domain)
                # m.journal_id = self.env['account.journal'].search(domain)
            else:
                journal_type = ('bank','cash')
                company_id = m.company_id.id or self.env.company.id
                domain = [('company_id', '=', company_id),('type', 'in', journal_type)]
                m.suitable_journal_ids = self.env['account.journal'].search(domain)
            

    @api.depends('line_ids.taxed_amount','line_ids.total_amount','line_ids.amount',)
    def compute_amount(self):
        total_vat_amount = total_amount = total_taxable_amount = 0.00
        for line in self.line_ids:

            
            total_vat_amount += line.taxed_amount
            total_amount += line.total_amount
            total_taxable_amount += line.amount

        self.write({'total_amount': total_amount,'vat_amount':total_vat_amount,'taxable_amount':total_taxable_amount,'amount':total_taxable_amount})


    

    
    def _prepare_move_line_offsetting_account(
        self, amount_company_currency, amount_payment_currency, payment):
        vals = {}
        if payment.payment_type == "outbound":
            name = payment.ref
        else:
            name = payment.ref
        
        vals.update({"date": payment.date_done})
        account_id = payment.journal_id.default_account_id.id
        vals.update(
            {
                "name": name,
                "partner_id": payment.partner_id.id or False,
                "account_id": account_id,
                "extra_payment_id": payment.id,
                "credit": (
                    payment.payment_type == "outbound" and amount_company_currency or 0.0
                ),
                "debit": (
                    payment.payment_type == "inbound" and amount_company_currency or 0.0
                ),
                "site_id": payment.site_id.id or False,
                # "budgetry_position_id": payment.budgetry_position_id.id or False,
                "analytic_account_id": payment.analytic_account_id.id or False,
                "cost_center_id": payment.cost_center_id.id or False,
                "employee_id": payment.employee_id.id or False,
                # "asset_id": line.asset_id.id or False,
                # "accomadation_id": line.accomadation_id.id or False,
                

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

    def _prepare_move_line_partner_account(self, line):
        
        if line.extra_payment_id.payment_type == "outbound":
            name = _("%s") % line.name
        else:
            name = _("%s") % line.name
        vals = {
            "name": line.name,
            "extra_payment_id": line.extra_payment_id.id,
            "extra_payment_line_id": line.id,
            "account_id": line.destination_account_id.id,
            "partner_id": line.extra_payment_id.partner_id.id or False,
            "credit": (
                line.extra_payment_id.payment_type == "inbound"
                and line.amount
                or 0.0
            ),
            "debit": (
                line.extra_payment_id.payment_type == "outbound"
                and line.amount
                or 0.0
            ),
            "site_id": line.site_id.id or False,
            "analytic_account_id": line.analytic_account_id.id or False,
            "budgetry_position_id": line.budgetry_position_id.id or False,
            "cost_center_id": line.cost_center_id.id or False,
            "employee_id": line.employee_id.id or False,
             "asset_id": line.asset_id.id or False,
            "accomadation_id": line.accomadation_id.id or False,
            'tax_ids' : [(6, 0, line.tax_ids.ids)],
        }
        
        sign = line.extra_payment_id.payment_type == "inbound" and -1 or 1
        vals.update(
            {
                "currency_id": line.extra_payment_id.company_id.currency_id.id,
                "amount_currency": line.amount * sign,
            }
        )
        if line.amount < 0:
            if vals['debit'] < 0:
                vals.update(
                    {
                      "credit": vals['credit'] - vals['debit'],
                      "debit": 0,
                    }
                )
            else:
                vals.update(
                    {
                        "debit": vals['debit'] - vals['credit'],
                        "credit": 0,
                    }
                )
        return vals

    def _prepare_move_line_tax_account(self, line):
        
        if line.extra_payment_id.payment_type == "outbound":
            name = _("%s") % line.name
        else:
            name = _("%s") % line.name
        
        if line.tax_ids:
            for tax in line.tax_ids:
                for tax_line in tax.invoice_repartition_line_ids.filtered(lambda line: line.repartition_type == 'tax'):
                    account_id = tax_line.account_id.id
                if account_id:

                    vals = {
                            "name": line.name,
                            "extra_payment_id": line.extra_payment_id.id,
                            "extra_payment_line_id": line.id,
                            "account_id": account_id,
                            "partner_id": line.extra_payment_id.partner_id.id or False,
                            "credit": (
                                line.extra_payment_id.payment_type == "inbound"
                                and line.taxed_amount
                                or 0.0
                            ),
                            "debit": (
                                line.extra_payment_id.payment_type == "outbound"
                                and line.taxed_amount
                                or 0.0
                            ),
                            # "site_id": line.site_id.id or False,
                            # "analytic_account_id": line.analytic_account_id.id or False,
                            # "cost_center_id": line.cost_center_id.id or False,
                            # "employee_id": line.employee_id.id or False,
                            #  "asset_id": line.asset_id.id or False,
                            # "accomadation_id": line.accomadation_id.id or False,
                            
                        }

        sign = line.extra_payment_id.payment_type == "inbound" and -1 or 1
        vals.update(
            {
                "currency_id": line.extra_payment_id.company_id.currency_id.id,
                "amount_currency": line.taxed_amount * sign,
            }
        )
        return vals

    
    def _prepare_move(self, payment=None):
        
        if payment.payment_type == "outbound":
            ref = payment.ref
        else:
            ref =  payment.ref
        vals = {
            "name": payment.name,
            "journal_id": payment.journal_id.id,
            "ref": ref,
            "extra_payment_id": payment.id,
            "site_id": payment.site_id.id or False,
            "analytic_account_id": payment.analytic_account_id.id or False,
            "cost_center_id": payment.cost_center_id.id or False,
            "employee_id": payment.employee_id.id or False,
            "journal_code_id": payment.journal_code_id.id or False,
            "line_ids": [],
        }
        
        vals.update({"date": payment.date_done})
        total_company_currency = total_payment_currency = 0
        for line in payment.line_ids:
            total_company_currency += line.total_amount
            total_payment_currency += line.total_amount
            
            partner_ml_vals = self._prepare_move_line_partner_account(line)

            vals["line_ids"].append((0, 0, partner_ml_vals))
            if line.tax_ids:
                tax_ml_vals = self._prepare_move_line_tax_account(line)
                vals["line_ids"].append((0, 0, tax_ml_vals))
        trf_ml_vals = self._prepare_move_line_offsetting_account(
            total_company_currency, total_payment_currency, payment
        )
        vals["line_ids"].append((0, 0, trf_ml_vals))
        return vals
    
    def button_post(self):
        for payment in self:
            am_obj = self.env["account.move"]
            mvals = self._prepare_move(payment)
            move = am_obj.create(mvals)
            move.number_genrated = True
            move.action_post()
            payment.state='post'
            
            
    def button_journal_entry(self):
        action={}
        for payment in self:
            move_id = self.env['account.move'].search([
                            ('extra_payment_id', '=', payment.id),
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
            
    # @api.model
    # def create(self, vals):
        
    #     vals["name"] = (
    #             self.env["ir.sequence"].next_by_code("account.extra.payment") or "New"
    #         )
    #     return super(account_extra_payment, self).create(vals)    


class account_extra_payment_line(models.Model):
    _name = "account.extra.payment.line"
    _description = "Extra Payment Line"
    _check_company_auto = True
 
    extra_payment_id = fields.Many2one(
        comodel_name='account.extra.payment',
        string='Payment id', index=True, required=True, ondelete='cascade',)
    amount = fields.Monetary(currency_field='currency_id')
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        help="The payment's currency.")
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account ID',
        store=True, readonly=False,
        )
    name = fields.Char(string='Label', required=True)
    site_id = fields.Many2one(
        comodel_name="site.site",
        string="Site")
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Project")
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee")
    cost_center_id = fields.Many2one(
        comodel_name="cost.center",
        string="Cost Center",)
    project = fields.Boolean(string='Project',related='destination_account_id.project')
    asset = fields.Boolean(string='Asset',related='destination_account_id.asset')
    budgetry_position = fields.Boolean(string='Cost Center', related='destination_account_id.cost_center_new')
    cost_center = fields.Boolean(string='Cost Center',related='destination_account_id.cost_center')
    accomodation = fields.Boolean(string='Accomodation',related='destination_account_id.accomodation')
    employee = fields.Boolean(string='Employee',related='destination_account_id.employee')
    budgetry_position_id = fields.Many2one('account.budget.post', string='Cost Center')




    
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",)
    asset_id = fields.Many2one(
        comodel_name="account.asset",
        string="Asset",)
    accomadation_id = fields.Many2one(
        comodel_name="hr.accomadation",
        string="Accomadation",)
    
    taxed_amount = fields.Float(string="Tax Amount", compute="compute_taxamount")
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        context={'active_test': False},
        check_company=True,
        help="Taxes that apply on the base amount")
    total_amount = fields.Monetary(currency_field='currency_id')

    @api.depends('tax_ids','amount')
    def compute_taxamount(self):
        for line in self:
              taxes = line.tax_ids.compute_all(line.amount, line.extra_payment_id.currency_id, 1, product=False, partner=False)
              line.update({
                           'taxed_amount': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                           'total_amount': taxes['total_included'],
                           # 'subtotal': taxes['total_excluded'],
                       })


    @api.onchange('name','destination_account_id')
    def _compute_values(self):
        for record in self:
            record.site_id = record.extra_payment_id.site_id.id or False
            record.analytic_account_id = record.extra_payment_id.analytic_account_id.id or False
            record.employee_id = record.extra_payment_id.employee_id.id or False
            record.cost_center_id = record.extra_payment_id.cost_center_id.id or False

 
    # @api.constrains('amount')
    # def _check_amount(self):
    #   for line in self:
    #       if line.amount <= 0:
    #           raise ValidationError(_('Amount should be greater than zero.'))
class AccountMove(models.Model):
    _inherit = "account.move"

    extra_payment_id = fields.Many2one(
        comodel_name="account.extra.payment",
        string="Extra Payment",)
    advance_payment_id = fields.Many2one(
        comodel_name="account.advance.payment",
        string="Extra Payment",)
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    extra_payment_id = fields.Many2one(
        comodel_name="account.extra.payment",
        string="Extra Payment",)
    extra_payment_line_id = fields.Many2one(
        comodel_name="account.extra.payment.line",
    )  
    advance_payment_id = fields.Many2one(
        comodel_name="account.advance.payment",
        string="Extra Payment",)
