# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(string='Number', required=True, readonly=False, copy=False, default='/')
    internal_type  = fields.Selection([ 
        ('receipt', 'Receipt'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
    ], string='Type')
    transfer_type  = fields.Selection([ 
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('petty', 'Petty Cash'),
    ], string='Transfer Type')
    number = fields.Char(string='Number', required=True, readonly=False, copy=False, default='/')
    number_genrated = fields.Boolean(default=False,copy=False,)


    def _get_sequence(self):
        self.ensure_one()
        journal = self.journal_id
        if self.move_type in ('entry',  'out_receipt', 'in_receipt') or not journal.refund_sequence:
            return journal.sequence_id
        if not journal.refund_sequence_id:
            return
        return journal.refund_sequence_id

    def action_post(self):
        for rec in self:

            res = super(AccountMove, rec).action_post()
            if rec.number_genrated == False:
                rec.create_sequence()

        return res

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals) 
        # res.create_sequence()
        
        return res   

    def create_sequence(self):
        for move in self:
            if move.name == '/' or move.number_genrated==False:
                if move.move_type in ('entry', 'out_receipt', 'in_receipt'):
                    if move.transfer_type and move.bank_cash_type == True:
                        journal = self.journal_id

                        if journal.type == 'bank':
                            code = "BT" +journal.seq_code
                            sequence = self.env["ir.sequence"].search([("code",'=',"pay.receipt.transfer.bank")])
                        elif journal.type == 'cash':
                            code = 'CT'
                            sequence = self.env["ir.sequence"].search([("code",'=',"pay.receipt.transfer")])
                        elif journal.is_petty_cash:
                            code = "PT" +journal.seq_code
                            sequence = self.env["ir.sequence"].search([("code",'=',"pay.receipt.transfer.petty")])
                        number_seq = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                        move.name = code + '-' + number_seq
                        move.number = code + '-' + number_seq
                        move.number_genrated = True

  
                    elif move.petty_cash_type == True:
                        journal = self.journal_id

                        if journal.type == 'bank':
                            code = "BP" +journal.seq_code
                            sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.bank")])
                        elif journal.type == 'cash':
                            code = 'CP'
                            sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer.cash")])
                        elif journal.is_petty_cash:
                            code = "PC" +journal.seq_code
                            sequence = self.env["ir.sequence"].search([('code','=',"payments.sequencer")])
                        number_seq = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                        move.name = code + '-' + number_seq
                        move.number = code + '-' + number_seq
                        move.number_genrated = True

                    else:
                        sequence = self.env["ir.sequence"].search([('code','=',"journal.entry.sequence")])
                        number_seq = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                        move.name =  number_seq
                        move.number = number_seq
                        move.number_genrated = True
                            

                elif move.move_type in ('out_invoice', 'in_invoice','in_refund','out_refund'):
                    if move.invoice_date:
                        date=move.invoice_date
                    else:
                        date = fields.Date.today()
                    if move.move_type == 'out_invoice' and move.journal_code_id:
                        sequence = self.env["ir.sequence"].search([('code','=',"customer.invoice.seq")])
                        number_seq = sequence.with_context(ir_sequence_date=date).next_by_id()
                        move.name = move.journal_code_id.code + '-' + number_seq
                        move.number = move.journal_code_id.code + '-' + number_seq
                        move.number_genrated = True

                            
                    if move.move_type == 'in_invoice' and move.journal_code_id:
                        sequence = self.env["ir.sequence"].search([('code','=',"vendor.invoice.seq")])
                        number_seq = sequence.with_context(ir_sequence_date=date).next_by_id()
                        move.name = move.journal_code_id.code + '-' + number_seq
                        move.number = move.journal_code_id.code + '-' + number_seq
                        move.number_genrated = True
                            
                    if move.move_type == 'in_refund':
                        sequence = self.env["ir.sequence"].search([('code','=',"debit.invoice.seq")])
                        number_seq = sequence.with_context(ir_sequence_date=date).next_by_id()
                        move.name = number_seq
                        move.number = number_seq
                        move.number_genrated = True
                            
                    if move.move_type == 'out_refund':
                        sequence = self.env["ir.sequence"].search([('code','=',"customer.credit.invoice.seq")])
                        number_seq = sequence.with_context(ir_sequence_date=date).next_by_id()
                        move.name =  number_seq
                        move.number = number_seq
                        move.number_genrated = True
                            


                    
        return True

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.name = '/'

    def _constrains_date_sequence(self):
        return
