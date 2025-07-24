from odoo import fields,models, api, _

import xlwt
import io
import base64
from xlwt import easyxf
from PIL import Image
import tempfile, os
from io import BytesIO
import xlrd
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class PartnerLedger(models.TransientModel):

    _name = 'partner.ledger'
    
    name = fields.Char(default='Partner Ledger')
    start_date = fields.Date(string='From Date', required=True, default=fields.Date.today().replace(day=1))
    end_date = fields.Date(string='To Date', required=True, default=fields.Date.today())
    partner_ids = fields.Many2many('res.partner', string='Partner', required=True, compute="_get_partner_domain", help='Select Partner for movement', invisible=True)
    partner_id = fields.Many2one('res.partner', string='Partner', domain="[('id', 'in', partner_ids)]", required=True, help='Select Partner for movement')
    patner_type = fields.Selection([('customer', 'Customer'),
                                    ('supplier', 'Supplier')], string="Partner Type")
    entry_type = fields.Selection([('all_entry', 'All Entry'),('posted_entry', 'Posted Entry')], default='all_entry', string="Entry Type")
    
        
    def print_report(self):
        data = {'partner_id': self.partner_id.id,'start_date': self.start_date, 'end_date': self.end_date, 'entry_type': self.entry_type}
        return self.env.ref('hak_partner_ledger.partner_ledger_pdf').report_action(self,data)
    
    
    
    def print_report_xls(self, data=None):
        data = {'partner_id': self.partner_id.id,'start_date': self.start_date, 'end_date': self.end_date, 'entry_type': self.entry_type}
        return self.env.ref('hak_partner_ledger.partner_ledger_xlsx').report_action(self, data)
        
    @api.depends('patner_type')
    def _get_partner_domain(self):
        for rec in self:
            if rec.patner_type:
                if rec.patner_type == 'customer':
                    domain = [('customer_rank', '>', 0)]
                    rec.partner_ids = self.env['res.partner'].search(domain)
                if rec.patner_type == 'supplier':
                    domain = [('supplier_rank', '>', 0)]
                    rec.partner_ids = self.env['res.partner'].search(domain)
            else:
                rec.partner_ids = self.env['res.partner'].search([])

class CustomReportXLSX(models.AbstractModel):
    _name = "report.hak_partner_ledger.hak_partner_ledger_xlsx_report"
    _description = 'Partner Ledger'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        bold = workbook.add_format({'bold': True, 'align' : 'center'})
        center = workbook.add_format({'align' : 'center'})
        right_bl = workbook.add_format({'align' : 'right','num_format': '#,##0.00;#,##0.00'})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'align' : 'left', 'bold': True})
        right = workbook.add_format({'align' : 'right', 'bold': True})
        top = workbook.add_format({'top': 1})
        pos_neg_fmt = workbook.add_format({'num_format': '#,##0.00;#,##0.00','align' : 'right', 'bold': True})
        report_format = workbook.add_format({'font_size': 24, 'bold': True,'align' : 'center'})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        
        def get_date_format(date):
            if date:
                date = date.strftime(date_format)
            return date
        
        cr = self._cr
        if data['entry_type'] == 'posted_entry':
            query = """select sum(l.debit - l.credit) as opening_bal
                        from account_move_line l
                        join account_move m on l.move_id = m.id
                        join account_account a on l.account_id = a.id
                        where a.reconcile = True
                        and l.partner_id = %s and l.date < %s and m.state = 'posted'
                        """
            cr.execute(query, [data['partner_id'], data['start_date']])
            openbal = cr.dictfetchall()
            cr = self._cr
            query = """
            select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name, 
            l.ref as line_desc, a.name as gl_account, m.currency_id, l.debit, l.credit,
            m.invoice_type_id as invoice_type, m.journal_code_id as journal_code
            
            from account_move_line l
            join account_move m on l.move_id = m.id
            join res_partner p on l.partner_id = p.id
            join account_account a on l.account_id = a.id
            join account_journal j on m.journal_id = j.id
            where a.reconcile = True
            and l.partner_id = %s and (m.date between %s and %s) and m.state = 'posted'
            order by m.date
            """
            cr.execute(query, [data['partner_id'], data['start_date'], data['end_date']])
        else:
            query = """select sum(l.debit - l.credit) as opening_bal
                        from account_move_line l
                        join account_move m on l.move_id = m.id
                        join account_account a on l.account_id = a.id
                        where a.reconcile = True
                        and l.partner_id = %s and l.date < %s
                        """
            cr.execute(query, [data['partner_id'], data['start_date']])
            openbal = cr.dictfetchall()
            cr = self._cr
            query = """
            select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name, 
            l.ref as line_desc, a.name as gl_account, m.currency_id, l.debit, l.credit,
            m.invoice_type_id as invoice_type, m.journal_code_id as journal_code
            
            from account_move_line l
            join account_move m on l.move_id = m.id
            join res_partner p on l.partner_id = p.id
            join account_account a on l.account_id = a.id
            join account_journal j on m.journal_id = j.id
            where a.reconcile = True
            and l.partner_id = %s and (m.date between %s and %s)
            order by m.date
            """
            cr.execute(query, [data['partner_id'], data['start_date'], data['end_date']])
        dat = cr.dictfetchall()
        report = 'Partner Ledger'
        sheet = workbook.add_worksheet(report)
        sheet.merge_range(0, 0, 2, 9, 'GAMBIT GULF CONTRACTING COMPANY LTD.', report_format)
        sheet.merge_range(3, 3, 4, 6, report, report_format)
        sheet.write(6, 0, _('Partner :'), left)
        sheet.write(6, 1, wizard.partner_id.name, left)
        sheet.write(6, 2, _('Print on :'), left)
        
        sheet.merge_range(7, 2, 7, 3, _('Start Date : %s ') % wizard.start_date if wizard.start_date else '', left)
        sheet.merge_range(8, 2, 8, 3, _('End Date : %s ') % wizard.end_date if wizard.end_date else '', left)
        sheet.write(7, 4, _('Entry Type :'), left)
        if wizard.entry_type == 'all_entry':
            sheet.write(8, 4, _('All Entry'), left)
        if wizard.entry_type == 'posted_entry':
            sheet.write(8, 4, _('Posted Entry'), left)
        sheet.write(10, 0, 'Date', bold)
        sheet.write(10, 1, 'Invoice Type', bold)
        sheet.write(10, 2, 'Journal', bold)
        sheet.write(10, 3, 'Journal Code', bold)
        sheet.write(10, 4, 'Voucher#', bold)
        sheet.write(10, 5, 'Account', bold)
        sheet.write(10, 6, 'Description', bold)
        sheet.write(10, 7, 'Debit', right)
        sheet.write(10, 8, 'Credit', right)
        sheet.write(10, 9, 'Balance', right)
        
        sheet.set_column(9, 0, 20)
        sheet.set_column(9, 1, 20)
        sheet.set_column(9, 2, 20)
        sheet.set_column(9, 3, 20)
        sheet.set_column(9, 4, 20)
        sheet.set_column(9, 5, 20)
        sheet.set_column(9, 6, 20)
        sheet.set_column(9, 7, 20)
        sheet.set_column(9, 8, 20)
        sheet.set_column(9, 9, 20)
        rb = 0.00
        deb = 0.00
        cre = 0.00
        if openbal:
            for open in openbal:
                if open.get('opening_bal'):
                    rb = rb + open.get('opening_bal')
                    sheet.merge_range(11, 0, 11, 8, 'Opening Balance', left)
                    sheet.write(11, 9, open.get('opening_bal'), pos_neg_fmt)
                else:
                    rb = rb + 0
                    sheet.merge_range(11, 0, 11, 8, 'Opening Balance', left)
                    sheet.write(11, 9, '0', pos_neg_fmt)
        else:
            sheet.merge_range(11, 0, 11, 8, 'Opening Balance', left)
            sheet.write(11, 9, '0.00', pos_neg_fmt)
        row = 11
        row += 1
        if dat:
            start_row = row
            for i, line in enumerate(dat):
                rb = rb + line.get('debit') - line.get('credit')
                deb = deb + line.get('debit')
                cre = cre + line.get('credit')
                type = self.env['invoice.type'].search([('id', '=', line['invoice_type'])], limit=1)
                code = self.env['journal.code'].search([('id', '=', line['journal_code'])], limit=1)
                i += row
                sheet.write(i, 0, get_date_format(line.get('date', '')), center)
                if type:
                    sheet.write(i, 1, type.name, center)
                else:
                    sheet.write(i, 1, '', center)
                sheet.write(i, 2, line.get('journal', ''),center)
                if code:
                    sheet.write(i, 3, code.name, center)
                else:
                    sheet.write(i, 3, '', center)
                sheet.write(i, 4, line.get('doc_no', ''), center)
                sheet.write(i, 5, line.get('gl_account', ''), center)
                sheet.write(i, 6, line.get('line_desc', ''), center)
                sheet.write(i, 7, line.get('debit', ''), right_bl)
                sheet.write(i, 8, line.get('credit', ''), right_bl)
                sheet.write(i, 9, rb, right_bl)
            row = i
        sheet.merge_range(row+1, 0, row+1, 6, 'Closing Balance', left)
        sheet.write(row+1, 7, deb, pos_neg_fmt)
        sheet.write(row+1, 8, cre, pos_neg_fmt)
        sheet.write(row+1, 9, rb, pos_neg_fmt)


class CustomReport(models.AbstractModel):
    _name = "report.hak_partner_ledger.hak_partner_ledger_pdf_report"

    def _get_report_values(self, docids, data=None):
        cr = self._cr
        if data['entry_type'] == 'all_entry':
            query = """select sum(l.debit - l.credit) as opening_bal
                        from account_move_line l
                        join account_move m on l.move_id = m.id
                        join account_account a on l.account_id = a.id
                        where a.reconcile = True
                        and l.partner_id = %s and l.date < %s
                        """
            cr.execute(query, [data['partner_id'], data['start_date']])
            openbal = cr.dictfetchall()
            cr = self._cr
            query = """
            select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name, 
            l.ref as line_desc, a.name as gl_account, m.currency_id, l.debit, l.credit,
            m.invoice_type_id as invoice_type, m.journal_code_id as journal_code
            
            from account_move_line l
            join account_move m on l.move_id = m.id
            join res_partner p on l.partner_id = p.id
            join account_account a on l.account_id = a.id
            join account_journal j on m.journal_id = j.id
            where a.reconcile = True
            and l.partner_id = %s and (m.date between %s and %s)
            order by m.date
            """
            cr.execute(query, [data['partner_id'], data['start_date'], data['end_date']])
            dat = cr.dictfetchall()
        if data['entry_type'] == 'posted_entry':
            query = """select sum(l.debit - l.credit) as opening_bal
                        from account_move_line l
                        join account_move m on l.move_id = m.id
                        join account_account a on l.account_id = a.id
                        where a.reconcile = True
                        and l.partner_id = %s and l.date < %s and m.state = 'posted'
                        """
            cr.execute(query, [data['partner_id'], data['start_date']])
            openbal = cr.dictfetchall()
            cr = self._cr
            query = """
            select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name, 
            l.ref as line_desc, a.name as gl_account, m.currency_id, l.debit, l.credit,
            m.invoice_type_id as invoice_type, m.journal_code_id as journal_code
            
            from account_move_line l
            join account_move m on l.move_id = m.id
            join res_partner p on l.partner_id = p.id
            join account_account a on l.account_id = a.id
            join account_journal j on m.journal_id = j.id
            where a.reconcile = True
            and l.partner_id = %s and (m.date between %s and %s) and m.state = 'posted'
            order by m.date
            """
            cr.execute(query, [data['partner_id'], data['start_date'], data['end_date']])
            dat = cr.dictfetchall()
            
        return {
            'doc_ids': self.ids,
            'doc_model': 'partner.ledger',
            'openbal': openbal,
            'dat': dat,
            'data': data,
        }