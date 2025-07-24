'''
Created on Oct 20, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError

class PaymentAllocationLines(models.TransientModel):
    _name = "account.payment.allocation.line"
    _description ='Payment Allocation Line'

    allocation_id = fields.Many2one('account.payment.allocation', required = False, ondelete='cascade')
    type = fields.Selection([('invoice', 'Invoice'),('credit', 'Credit Invoice'),('debit', 'Debit Invoice'), ('payment', 'Payment'), ('other', 'Other'),('advance', 'Advance')])
    
    move_line_id = fields.Many2one('account.move.line', required = True, ondelete = 'cascade')
   
    company_currency_id = fields.Many2one(related='move_line_id.company_currency_id')
    currency_id = fields.Many2one(related='move_line_id.company_currency_id')
    amount_residual = fields.Monetary(related='move_line_id.amount_residual')
    partner_id = fields.Many2one(related='move_line_id.partner_id')
    ref = fields.Char(related='move_line_id.ref', readonly = True)
    name = fields.Char(related='move_line_id.name', readonly = True)
    date_maturity = fields.Date(related='move_line_id.date_maturity', readonly = True)
    date = fields.Date(related='move_line_id.date', readonly = False)
    edit_date = fields.Date(String="Update date")
        
    allocate = fields.Boolean()
    allocate_amount = fields.Monetary()
    
    invoice_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
    payment_id = fields.Many2one(related='move_line_id.payment_id', readonly = True, string='Payment')
    move_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
    balance = balance = fields.Monetary(related='move_line_id.balance', readonly = True)

    payment_date = fields.Date(related='payment_id.date', readonly = True)
    payment_amount = fields.Monetary(compute = '_calc_payment_amount')
    communication = fields.Char(related='payment_id.ref', readonly = True)
    
    date_invoice = fields.Date(related='invoice_id.invoice_date', readonly = True)
    invoice_amount = fields.Monetary(compute = "_calc_invoice_amount")
    
    amount_residual_display = fields.Monetary(compute = '_calc_amount_residual_display', string='Unallocated Amount')
    
    sign = fields.Integer(compute = "_calc_sign")
    payment_id = fields.Many2one('account.payment',)

    @api.depends('type','allocation_id')
    def _calc_sign(self):
        for record in self:
            record.sign = (record.type in ['invoice', 'other'] and -1 or 1) * (record.move_line_id.account_id.user_type_id.type == 'payable' and 1 or -1)
            
    @api.depends('sign','balance')
    def _calc_payment_amount(self):
        for record in self:
            record.payment_amount = record.balance * record.sign
            
    @api.depends('sign','balance')
    def _calc_invoice_amount(self):
        for record in self:
            record.invoice_amount = record.balance * record.sign


    @api.depends('amount_residual','sign')
    def _calc_amount_residual_display(self):
        for record in self:
            record.amount_residual_display = record.amount_residual * record.sign

    @api.onchange('allocate','amount_residual_display')
    def _calc_allocate_amount(self):
        if self.payment_id:
            total = self.payment_id.amount
            line_amount = 0.00
            for line in self.payment_id.invoice_line_ids:
                if line.allocate == True:
                    line_amount += line.allocate_amount
            if not self.allocate:
                self.allocate_amount = 0
            elif (total - line_amount) <= self.amount_residual_display:
                self.allocate_amount = total - line_amount
            else:
                self.allocate_amount = self.amount_residual_display
        else:
            line_ids = self.allocation_id.invoice_line_ids + self.allocation_id.payment_line_ids + self.allocation_id.other_line_ids + self.allocation_id.advance_line_ids + self.allocation_id.credit_line_ids + self.allocation_id.debit_line_ids
            other_lines = line_ids.filtered(lambda line : line !=self and line.allocate)
            total = 0
            for line in other_lines:
                total += line.allocate_amount * line.sign 
            
            total = total * self.sign
            
            if total < 0:
                total = abs(total)
            else:
                total = 0

            if not self.allocate:
                self.allocate_amount = 0
            elif total:
                self.allocate_amount = abs(min(self.amount_residual_display, total))
            elif total==0.00:
                self.allocate_amount = abs(self.amount_residual_display)
            else:
                self.allocate_amount = abs(self.amount_residual_display)
                        
    @api.onchange('allocate_amount')
    def _onchange_allocate_amount(self):
        self.allocation_id._calc_balance()
        
    # @api.constrains('allocate', 'amount_residual_display','allocate_amount')
    # def _validate_allocate_amount(self):
    #     for record in self:
    #         if record.allocate == True and record.amount_residual_display < record.allocate_amount:
    #             raise ValidationError(_("Allocate amount should not be greater than Unallocated Amount"))
    
                 
            