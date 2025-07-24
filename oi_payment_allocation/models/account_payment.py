'''

'''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description ='Payment'
    
   
    invoice_line_ids = fields.One2many('account.payment.alloc.line', 'payment_id', domain = [('type', '=', 'invoice')])
    exchange_amount_diff = fields.Float(string="Exchange Difference",compute="_compute_diff_amt",store=True)
    foriegn_curr_amt = fields.Float(string="Foreign Currency Amt")
    foriegn_curr_id = fields.Many2one('res.currency',string="Foreign Currency Amt")
    total_amt = fields.Float(string="Converted Amt")
    allocated_amt = fields.Float(string="Allocated Amt",compute="_compute_allocated_amt",store=True)
    foreign_currency = fields.Boolean(string="Foreign Exchange",default=False)

    foriegn_curr_rate = fields.Float(string="Foreign Currency Rate",compute="_compute_rate",store=True)
    exchange_account_id = fields.Many2one('account.account',string="Exchange Account",)


    @api.onchange('foriegn_curr_amt','foriegn_curr_rate')
    def onchange_amt(self):
        if self.foriegn_curr_amt and self.foriegn_curr_rate:
            self.total_amt = self.foriegn_curr_id._convert(
                            self.foriegn_curr_amt,
                            self.destination_account_id.company_id.currency_id,
                            self.destination_account_id.company_id,
                            self.date,
                        )

    @api.depends('invoice_line_ids','amount','total_amt')
    def _compute_diff_amt(self):
        
        if self.total_amt != self.amount:
            self.exchange_amount_diff = self.amount - self.allocated_amt
        else:
            self.exchange_amount_diff = 0.00
        return True

    @api.depends('foriegn_curr_amt','foriegn_curr_id')
    def _compute_rate(self):
        self.foriegn_curr_rate = self.foriegn_curr_id.rate
        return True

    @api.depends('invoice_line_ids','foriegn_curr_id')
    def _compute_allocated_amt(self):
        self.allocated_amt = sum(self.invoice_line_ids.mapped('allocate_amount'))

        return True



    @api.onchange('partner_id','partner_type','destination_account_id')
    def onchange_partner_id(self):
        if self.partner_id:
            for line_type in ['invoice']:
                fname = '%s_line_ids' % line_type
                self[fname] = False  
                domain = [('account_id', '=', self.destination_account_id.id), ('reconciled', '=', False), ('company_id', '=', self.company_id.id)]
                
                domain.append(('partner_id', '=', self.partner_id.id))            
                if line_type == 'invoice':                        
                    domain.extend([('move_id.move_type', 'in', ['out_invoice', 'in_invoice', 'in_refund'])])
                elif line_type == 'credit':                        
                    domain.extend([('move_id.move_type', 'in', ['out_refund'])])
                elif line_type == 'payment':
                    domain.append(('payment_id', '!=', False))     
                elif line_type == 'other':
                    domain.extend([('move_id.move_type', 'not in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']), ('payment_id', '=', False)])                
                else:
                    domain=([('account_id.user_type_id.type', 'in',['other']),('account_id.user_type_id.internal_group', 'in',['liability']),('partner_id', '=', self.partner_id.id),('company_id', '=', self.company_id.id),('reconciled', '=', False),('move_id.move_type', 'in', ['entry']), ('payment_id', '=', False)])
                
                for move_line in self.env['account.move.line'].search(domain):
                    if line_type != 'payment' and move_line.move_id.state != 'posted':
                        continue
                    allocate = move_line.payment_id
                              
                    self[fname] += self[fname].new({
                        'move_line_id' : move_line.id,
                        'allocate' : allocate,
                        'type' : line_type
                        })

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        self.validate()
        for line in self.invoice_line_ids:
            if not line.allocate:
                line.unlink() 

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'journal_id','exchange_amount_diff','foriegn_curr_id','foriegn_curr_amt','allocated_amt','invoice_line_ids','foreign_currency'
        )):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.

            if liquidity_lines and counterpart_lines and writeoff_lines:

                counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                # To be consistent with the payment_difference made in account.payment.register,
                # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                # Since the write is already done at this point, we need to base the computation on accounting values.
                if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                    sign = -1
                else:
                    sign = 1
                writeoff_amount = abs(writeoff_amount) * sign

                write_off_line_vals = {
                    'name': writeoff_lines[0].name,
                    'amount': writeoff_amount,
                    'account_id': writeoff_lines[0].account_id.id,
                }
            else:
                write_off_line_vals = {}

            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

            line_ids_commands = []
            if liquidity_lines:
                line_ids_commands.append((1, liquidity_lines.id, line_vals_list[0]))
            else:
                line_ids_commands.append((0, 0, line_vals_list[0]))
            if counterpart_lines:
                line_ids_commands.append((1, counterpart_lines.id, line_vals_list[1]))
            else:
                line_ids_commands.append((0, 0, line_vals_list[1]))

            for line in writeoff_lines:
                line_ids_commands.append((2, line.id))

            for extra_line_vals in line_vals_list[2:]:
                line_ids_commands.append((0, 0, extra_line_vals))

            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.

            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            })

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1 or len(counterpart_lines) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal entry must always contains:\n"
                        "- one journal item involving the outstanding payment/receipts account.\n"
                        "- one journal item involving a receivable/payable account.\n"
                        "- optional journal items, all sharing the same account.\n\n"
                    ) % move.display_name)

                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, all the write-off journal items must share the same account."
                    ) % move.display_name)

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same currency."
                    ) % move.display_name)

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same partner."
                    ) % move.display_name)

                if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))


    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set on the %s journal.",
                self.journal_id.display_name))

        # Compute amounts.
        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)
        write_off_account = write_off_line_vals.get('account_id')
        # if self.exchange_amount_diff != 0.00:
        #     write_off_amount_currency = self.exchange_amount_diff
        #     write_off_account = self.exchange_account_id.id

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0

        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        
        currency_id = self.currency_id.id
        if self.exchange_amount_diff != 0.00 and self.foreign_currency == True:
            write_off_amount_currency = self.exchange_amount_diff
            write_off_amount_currency = float_round(write_off_amount_currency,precision_rounding=0.01)
            write_off_account = self.exchange_account_id.id
            liquidity_amount_currency = -self.amount
            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
                )
            write_off_balance = float_round(write_off_balance,precision_rounding=0.01)
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            counterpart_amount_currency = self.allocated_amt
            counterpart_balance = self.currency_id._convert(
                counterpart_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date)
        else:
            counterpart_amount_currency = -liquidity_amount_currency
            counterpart_balance = -liquidity_balance

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.journal_id.payment_credit_account_id.id if liquidity_balance < 0.0 else self.journal_id.payment_debit_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if not self.currency_id.is_zero(write_off_amount_currency) and self.foreign_currency == True:
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_amount_currency if write_off_amount_currency > 0.0 else 0.0,
                'credit': -write_off_amount_currency if write_off_amount_currency < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_account,
            })
        return line_vals_list


    def validate(self):         
        
        
        if self.partner_type == 'customer':
            debit_line_ids = self.invoice_line_ids.filtered(lambda line : line.allocate and line.allocate_amount and line.move_line_id.debit)
            # credit_line_ids = self.move_id.filtered(lambda line : line.allocate and line.allocate_amount and line.move_line_id.credit)
            
            # if not debit_line_ids or not credit_line_ids:
            #     #raise Warning('Select at least one payment & one invoice')
            #     raise ValidationError(_("Please allocate at least one payment & one invoice"))
            
            if debit_line_ids:
                tot_invoice_amount = sum(debit_line_ids.mapped('allocate_amount'))
            else:
                tot_invoice_amount=0
            if self.amount:
                tot_payment_amount = self.amount
            else:
                tot_payment_amount=0
            # if tot_payment_amount != tot_invoice_amount or tot_payment_amount == tot_invoice_amount==0:
            #     #raise Warning('Select at least one payment & one invoice')
            #     raise ValidationError(_("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))    
            
            move_line_ids = (debit_line_ids).mapped('move_line_id')
            credit_move_line_ids = self.env['account.move.line'].search([('account_id', '=', self.destination_account_id.id),('move_id', '=', self.move_id.id), ('reconciled', '=', False), ('company_id', '=', self.company_id.id)])
            move_line_ids += credit_move_line_ids  
                              
            partner_ids = move_line_ids.mapped('partner_id')
            partner_balance = False
            if len(partner_ids) > 1:
                partner_balance = dict.fromkeys(partner_ids.ids, 0)
            
            partial_reconcile_ids = self.env["account.partial.reconcile"]
            
            for debit_line in debit_line_ids:
                # for credit_line in credit_line_ids:
                    amount = min (abs(debit_line.allocate_amount), abs(self.amount))
                    if not amount:
                        continue
                    vals = {
                        'debit_move_id' : debit_line.move_line_id.id,
                        'credit_move_id' : credit_move_line_ids.id,
                        'amount' : amount,                                        
                        }
                    if debit_line.move_line_id.amount_currency and credit_move_line_ids.amount_currency and debit_line.move_line_id.currency_id== credit_move_line_ids.currency_id:
                        max_date = max(debit_line.move_line_id.date, credit_move_line_ids.date)
                        company_id = debit_line.move_line_id.company_id
    #                     vals.update({
    #                         'currency_id' : debit_line.move_line_id.currency_id.id,
    #                         'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
    #                         })
                        min_debit_amount_residual_currency = credit_move_line_ids.company_currency_id._convert(
                        amount,
                        debit_line.move_line_id.currency_id,
                        credit_move_line_ids.company_id,
                        credit_move_line_ids.date,
                        )
                        min_credit_amount_residual_currency = debit_line.move_line_id.company_currency_id._convert(
                            amount,
                            credit_move_line_ids.currency_id,
                            debit_line.move_line_id.company_id,
                            debit_line.move_line_id.date,
                        )
                        
                        
                        
                        vals.update({
                            #'currency_id' : debit_line.move_line_id.currency_id.id,
                            #'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
                            
                            'debit_amount_currency': min_debit_amount_residual_currency,
                            'credit_amount_currency': min_credit_amount_residual_currency,
                            
                            
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
                    
                    # debit_line.allocate_amount -= amount * (debit_line.allocate_amount < 0 and -1 or 1)
                    # credit_line.allocate_amount -= amount * (credit_line.allocate_amount < 0 and -1 or 1)  
                            
            reconciled_move_line_ids = move_line_ids.filtered('reconciled')
            if reconciled_move_line_ids:            
                partial_reconcile_ids = partial_reconcile_ids.filtered(lambda record : record.debit_move_id in reconciled_move_line_ids or record.credit_move_id in reconciled_move_line_ids)
                self.env["account.full.reconcile"].create({
                    'partial_reconcile_ids' : [(6,0, partial_reconcile_ids.ids)],
                    'reconciled_line_ids' : [(6,0, reconciled_move_line_ids.ids)],
                    }) 

        if self.partner_type == 'supplier':
            # debit_line_ids = self.invoice_line_ids.filtered(lambda line : line.allocate and line.allocate_amount and line.move_line_id.debit)
            credit_line_ids = self.invoice_line_ids.filtered(lambda line : line.allocate and line.allocate_amount and line.move_line_id.credit)
            
            # if not debit_line_ids or not credit_line_ids:
            #     #raise Warning('Select at least one payment & one invoice')
            #     raise ValidationError(_("Please allocate at least one payment & one invoice"))
            
            if credit_line_ids:
                tot_invoice_amount = sum(credit_line_ids.mapped('allocate_amount'))
            else:
                tot_invoice_amount=0
            if self.amount:
                tot_payment_amount = self.amount
            else:
                tot_payment_amount=0
            tot_invoice_amount = round(tot_invoice_amount,2)
            # if self.total_amt != self.allocated_amt and self.exchange_amount_diff !=0.00:
            #     #raise Warning('Select at least one payment & one invoice')
            #     raise ValidationError(_("Total Payment Allocate Amount and Total Invoice Allocate Amount should be equal."))    
            
            move_line_ids = (credit_line_ids).mapped('move_line_id')
            credit_move_line_ids = self.env['account.move.line'].search([('account_id', '=', self.destination_account_id.id),('move_id', '=', self.move_id.id), ('reconciled', '=', False), ('company_id', '=', self.company_id.id)])
            move_line_ids += credit_move_line_ids  
            partner_ids = move_line_ids.mapped('partner_id')
            partner_balance = False
            if len(partner_ids) > 1:
                partner_balance = dict.fromkeys(partner_ids.ids, 0)
            
            partial_reconcile_ids = self.env["account.partial.reconcile"]
            
            for credit_line in credit_line_ids:
                # for credit_line in credit_line_ids:
                    if self.foreign_currency:
                       amount = credit_line.allocate_amount
                    else:

                        amount = min (abs(credit_line.allocate_amount), abs(self.amount))
                    if not amount:
                        continue
                    vals = {
                        'debit_move_id' : credit_move_line_ids.id,
                        'credit_move_id' : credit_line.move_line_id.id,
                        'amount' : amount,                                        
                        }
                    if credit_line.move_line_id.amount_currency and credit_move_line_ids.amount_currency and credit_line.move_line_id.currency_id== credit_move_line_ids.currency_id:
                        max_date = max(credit_line.move_line_id.date, credit_move_line_ids.date)
                        company_id = credit_line.move_line_id.company_id
    #                     vals.update({
    #                         'currency_id' : debit_line.move_line_id.currency_id.id,
    #                         'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
    #                         })
                        min_debit_amount_residual_currency = credit_move_line_ids.company_currency_id._convert(
                        amount,
                        credit_line.move_line_id.currency_id,
                        credit_move_line_ids.company_id,
                        credit_move_line_ids.date,
                        )
                        min_credit_amount_residual_currency = credit_line.move_line_id.company_currency_id._convert(
                            amount,
                            credit_move_line_ids.currency_id,
                            credit_line.move_line_id.company_id,
                            credit_line.move_line_id.date,
                        )
                        
                        
                        
                        vals.update({
                            #'currency_id' : debit_line.move_line_id.currency_id.id,
                            #'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
                            
                            'debit_amount_currency': min_debit_amount_residual_currency,
                            'credit_amount_currency': min_credit_amount_residual_currency,
                            
                            
                            })
                    elif credit_line.move_line_id.amount_currency and credit_move_line_ids.amount_currency and credit_line.move_line_id.currency_id!= credit_move_line_ids.currency_id:
                        amount = credit_line.allocate_amount
                        forr_amt = credit_line.allocate_amount_curr
                        max_date = max(credit_line.move_line_id.date, credit_move_line_ids.date)
                        company_id = credit_move_line_ids.company_id
    #                     vals.update({
    #                         'currency_id' : debit_line.move_line_id.currency_id.id,
    #                         'amount_currency' : company_id.currency_id._convert(amount, debit_line.move_line_id.currency_id, company_id, max_date)
    #                         })
                        min_debit_amount_residual_currency = amount
                        min_credit_amount_residual_currency = credit_line.move_line_id.company_currency_id._convert(
                            amount,
                            credit_line.move_line_id.currency_id,
                            credit_move_line_ids.company_id,
                            credit_move_line_ids.date,
                        )
                        # min_credit_amount_residual_currency = float_round(min_credit_amount_residual_currency, precision_rounding=0., rounding_method='UP')
              
                        min_credit_amount_residual_currency = forr_amt
                        vals.update({
                                   
                            'debit_amount_currency': min_debit_amount_residual_currency,
                            'credit_amount_currency': min_credit_amount_residual_currency,
                            # 'debit_move_id': debit_line.id,
                            # 'credit_move_id': credit_line.id,
                            
                            
                            })
                    
                    partial_reconcile_ids += self.env["account.partial.reconcile"].create(vals)
                    if partner_balance:
                        partner_balance[credit_line.move_line_id.partner_id.id] += amount
                        partner_balance[credit_line.move_line_id.partner_id.id] -= amount
                    
                    # credit_line.allocate_amount -= amount * (credit_line.allocate_amount < 0 and -1 or 1)
                    # credit_line.allocate_amount -= amount * (credit_line.allocate_amount < 0 and -1 or 1)  
                            
            reconciled_move_line_ids = move_line_ids.filtered('reconciled')
            if reconciled_move_line_ids:            
                partial_reconcile_ids = partial_reconcile_ids.filtered(lambda record : record.debit_move_id in reconciled_move_line_ids or record.credit_move_id in reconciled_move_line_ids)
                self.env["account.full.reconcile"].create({
                    'partial_reconcile_ids' : [(6,0, partial_reconcile_ids.ids)],
                    'reconciled_line_ids' : [(6,0, reconciled_move_line_ids.ids)],
                    })
            # for lines in self.invoice_line_ids.filtered(lambda line : line.allocate):

            #     if lines.invoice_id.amount_residual_signed == 0.00:
            #         # lines.amount_residual = 0.00
            #         lines.invoice_id.amount_residual = 0.00
            #         lines.invoice_id.payment_state = 'paid'
                    
            # if partner_balance:
            #     move_vals= {
            #         'journal_id' : self.entry_journal_id.id,
            #         'ref': self.entry_name or 'Payment Allocation',
            #         'date' : max(move_line_ids.mapped('date')),
            #         'line_ids' : []
            #         }
            #     for partner_id, balance in partner_balance.items():
            #         if not balance:
            #             continue
            #         move_vals['line_ids'].append((0,0, {
            #             'account_id': self.account_id.id,
            #             'name' : '',
            #             'partner_id' : partner_id,
            #             'credit' : balance > 0 and balance or 0,
            #             'debit' : balance < 0 and -balance or 0
            #             }))
            #     move_id=self.env['account.move'].create(move_vals)
            #     move_id.post()
            #     move_id.line_ids.reconcile()
            #     move_line_ids +=  move_id.line_ids
   

class PaymentAllocLines(models.Model):
    _name = "account.payment.alloc.line"
    _description ='Payment Allocation Line'
    
    # allocation_id = fields.Many2one('account.payment.allocation', required = False, ondelete='cascade')
    type = fields.Selection([('invoice', 'Invoice'),('credit', 'Credit Invoice'),('debit', 'Debit Invoice'), ('payment', 'Payment'), ('other', 'Other'),('advance', 'Advance')])
    
    move_line_id = fields.Many2one('account.move.line', required = True, ondelete = 'cascade')
   
    company_currency_id = fields.Many2one(related='move_line_id.company_currency_id')
    currency_id = fields.Many2one(related='move_line_id.company_currency_id')
    invoice_currency_id = fields.Many2one(related='payment_id.foriegn_curr_id',store=True)
    amount_residual = fields.Monetary(related='move_line_id.amount_residual')
    partner_id = fields.Many2one(related='move_line_id.partner_id')
    ref = fields.Char(related='move_line_id.ref', readonly = True)
    name = fields.Char(related='move_line_id.name', readonly = True)
    date_maturity = fields.Date(related='move_line_id.date_maturity', readonly = True)
    date = fields.Date(related='move_line_id.date', readonly = True)
        
    allocate = fields.Boolean()
    allocate_amount = fields.Monetary()
    allocate_amount_curr = fields.Monetary(currency_field='invoice_currency_id')
    
    invoice_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
    payment_id = fields.Many2one(related='move_line_id.payment_id', readonly = True, string='Payment')
    move_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
    balance = balance = fields.Monetary(related='move_line_id.balance', readonly = True)
    
    payment_date = fields.Date(related='payment_id.date', readonly = True)
    payment_amount = fields.Monetary(compute = '_calc_payment_amount')
    communication = fields.Char(related='payment_id.ref', readonly = True)
    
    date_invoice = fields.Date(related='invoice_id.invoice_date', readonly = True)
    invoice_amount = fields.Monetary(compute = "_calc_invoice_amount")
    amount_balance = fields.Monetary(related='move_line_id.move_id.amount_residual', readonly = True,currency_field='invoice_currency_id')
    amount_total = fields.Monetary(related='move_line_id.move_id.amount_total', readonly = True,currency_field='invoice_currency_id')
    
    amount_residual_display = fields.Monetary(compute = '_calc_amount_residual_display', string='Unallocated Amount')
    
    sign = fields.Integer(compute = "_calc_sign")
    payment_id = fields.Many2one('account.payment',)
    
    @api.depends('type')
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

    @api.depends('sign','balance','payment_id.foriegn_curr_rate')
    def _calc_amount_balance(self):
        for record in self:
            record.amount_balance = (record.balance * record.sign) * record.payment_id.foriegn_curr_rate
            
    
    @api.depends('amount_residual','sign')
    def _calc_amount_residual_display(self):
        for record in self:
            record.amount_residual_display = record.amount_residual * record.sign
    
    @api.onchange('allocate','amount_residual_display')
    def _calc_allocate_amount(self):
        if self.payment_id and self.payment_id.foreign_currency ==False:
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

        if self.payment_id and self.payment_id.foreign_currency ==True:
            total = self.payment_id.total_amt
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

    @api.onchange('allocate','amount_residual_display',"allocate_amount")
    def _calc_allocate_curr_amount(self):

        if self.payment_id and self.payment_id.foreign_currency ==True:
            foriegn_curr_amt = self.payment_id.foriegn_curr_amt
            
            if self.allocate_amount == self.amount_residual_display:
                self.allocate_amount_curr = self.move_line_id.move_id.amount_residual

            else:
                self.allocate_amount_curr = self.move_line_id.company_currency_id._convert(
                            self.allocate_amount,
                            self.move_line_id.currency_id,
                            self.move_line_id.company_id,
                            self.payment_id.date,
                        )
        # else:
        #     line_ids = self.allocation_id.invoice_line_ids + self.allocation_id.payment_line_ids + self.allocation_id.other_line_ids + self.allocation_id.advance_line_ids
        #     other_lines = line_ids.filtered(lambda line : line !=self and line.allocate)
        #     total = 0
        #     for line in other_lines:
        #         total += line.allocate_amount * line.sign 
            
        #     total = total * self.sign
            
        #     if total < 0:
        #         total = abs(total)
        #     else:
        #         total = 0

        #     if not self.allocate:
        #         self.allocate_amount = 0
        #     elif total:
        #         self.allocate_amount = abs(min(self.amount_residual_display, total))
        #     elif total==0.00:
        #         self.allocate_amount = abs(self.amount_residual_display)
        #     else:
        #         self.allocate_amount = abs(self.amount_residual_display)
                        
    # @api.onchange('allocate_amount')
    # def _onchange_allocate_amount(self):
    #     self.allocation_id._calc_balance()
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    avoid_line = fields.Boolean(default=False)
    advance_move_line = fields.Many2one('account.move.line',string="Advance move line")

class AccountMoveAdvance(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        # OVERRIDE  button_draft to reset amount_residual of advance move lines
        res = super(AccountMoveAdvance, self).button_draft()
        for move in self:
            move_line = move.mapped('line_ids').filtered(lambda line: line.advance_move_line)
            if move_line:
                if move_line.credit != 0.0:
                    move_line.advance_move_line.amount_residual += move_line.credit
                    move_line.advance_move_line.amount_residual_currency += move_line.credit
                    move_line.advance_move_line = False

                if move_line.debit != 0.0:
                    move_line.advance_move_line.amount_residual -= move_line.debit
                    move_line.advance_move_line.amount_residual_currency -= move_line.debit
                    move_line.advance_move_line = False

        return res



