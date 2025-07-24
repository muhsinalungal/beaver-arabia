from odoo import models, fields, api, _


class ResCompanyInheritBank(models.Model):
    _inherit = 'res.company'
    
    acc_name = fields.Char(string="Acc. Name")
    iban_no = fields.Char(string="Iban No.")
    acc_no = fields.Char(string="Acc No.")
    bank_name = fields.Char(string="Bank")
    branch_name = fields.Char(string="Branch")
    contact_person = fields.Char(string="Contact Person")


class AccountMove(models.Model):
    _inherit = "account.move"

    def  source_move_out_refund(self):
        moves = [move.name for move in self.reversed_entry_ids]
        label = " / ".join(moves) if len(moves) > 1 else " ".join(moves)
        return label



    def source_move_in_refund(self):
        moves = [move.name for move in self.reversed_entry_ids]
        label = " / ".join(moves) if len(moves) > 1 else " ".join(moves)
        return label
