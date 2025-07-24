
from odoo import models, fields, api, _
from odoo.http import request
from num2words import num2words
from googletrans import Translator
from odoo.exceptions import AccessError
import base64

class AccountMove(models.Model):
    
    _inherit = "account.move"
    
    qr_code = fields.Binary(string="QR Code")
    qr_in_report = fields.Boolean('Show QR in Report')
    advnc_deduction = fields.Float(string="Advanced Deduction")
    total_tax_amt = fields.Float(string="Total Tax Amount",)
    total_vat = fields.Float(string="VAT", )
    retension = fields.Float(string="Retension")
    net_amt_incl = fields.Float(string="Net Amount Incl", )
    total_in_word = fields.Char(string="Total In Words", compute="amount_to_text")
    total_in_arab = fields.Char(string="Total In Arab", compute="amount_to_arb")

    def  source_move_out_refund_bt_qr(self):
        moves = [move.name for move in self.reversed_entry_ids]
        label = " / ".join(moves) if len(moves) > 1 else " ".join(moves)
        return label



    def source_move_in_refund_bt_qr(self):
        moves = [move.name for move in self.reversed_entry_ids]
        label = " / ".join(moves) if len(moves) > 1 else " ".join(moves)
        return label

    
    
    def generate_qr_code(self):
        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array
        for record in self:
            qr_code_str = ''
            seller_name_enc = get_qr_encoding(1, record.company_id.display_name)
            company_vat_enc = get_qr_encoding(2, record.company_id.vat or '')
            # date_order = fields.Datetime.from_string(record.create_date)
            if record.invoice_date:
                time_sa =  record.invoice_date
            else:
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.create_date)
            timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
            invoice_total_enc = get_qr_encoding(4, str(format(record.amount_total, ".2f")))
            total_vat_enc = get_qr_encoding(5, str(format(record.currency_id.round(record.amount_total - record.amount_untaxed), ".2f")))

            str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc +  total_vat_enc
            qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            return qr_code_str

        
        
    def amount_to_text(self,amount):
        # amt = self.amount_total_after_ret
        amount = '%.2f' % amount
        
        list = str(amount).split('.')
        listout = list[0], 'SAR', list[1]
        lst_var = float(list[0])
        lst_var_f = float(list[1])
        a_amount = num2words(lst_var, lang='en')
        a_amount = a_amount.replace(' and','')
        b_amount = num2words(lst_var_f, lang='en')
        
        variable = a_amount + ' ' + 'Saudi Riyals'+ ' '+ 'and' + ' ' + b_amount + ' ' + 'Halalas'
        return variable
    
        
    def amount_to_arb(self,amount):
        
        amount = '%.2f' % amount
        
        list = str(amount).split('.')
        listout = list[0], 'SAR', list[1]
        lst_var = float(list[0])
        lst_var_f = float(list[1])
        a_amount = num2words(lst_var, lang='ar')
        b_amount = num2words(lst_var_f, lang='ar')
        variable = a_amount + ' ' + 'ريالا'+ ' '+ 'و' + ' ' + b_amount + ' ' + 'هللة'
        
        return variable
   
    # @api.depends('amount_total')
    # def compute_prices_total(self):
    #     #self.advnc_deduction = self.amount_untaxed * 0.15
    #     self.total_tax_amt = self.amount_untaxed - self.advnc_deduction
    #     self.total_vat = self.total_tax_amt * 0.15
    #     #self.retension = self.retention_amount_currency
    #     self.net_amt_incl = self.total_tax_amt + self.total_vat - self.retention_amount_currency
    # @api.model
    # def create(self, vals):
    #     res = super(AccountMove, self).create(vals)
    #     if res.move_type == 'out_invoice':
    #         res.generate_qr_code()
    #     return res
    
    
class AccountInvoiceLine(models.Model):
    
    _inherit = "account.move.line"
    
    
    arb_name = fields.Char(string="Arabic Name")
    
        
    
        
        
        

    
