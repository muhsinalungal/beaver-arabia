import time
from odoo import fields, models, api, _

import io
import json
from datetime import datetime
from odoo.exceptions import AccessError, UserError, AccessDenied

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PartnerView(models.TransientModel):
    _inherit = "account.common.report"
    _name = 'account.partner.ledger'

    journal_ids = fields.Many2many('account.journal',
                                   string='Journals', required=True,
                                   default=[])
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts", check_company=True,
    )

    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')

    partner_ids = fields.Many2many('res.partner', string='Partner')
    partner_category_ids = fields.Many2many('res.partner.category',
                                            string='Partner tags')
    journal_code_ids = fields.Many2many('journal.code', string='Journal Code')
    invoice_type_ids = fields.Many2many('invoice.type', string='Invoice Type')
    reconciled = fields.Selection([
        ('unreconciled', 'Unreconciled Only')],
        string='Reconcile Type', default='unreconciled')

    account_type_ids = fields.Many2many('account.account.type',string='Account Type',
                                        domain=[('type', 'in', ('receivable', 'payable'))])
    suitable_partner_ids = fields.Many2many('res.partner', compute='_compute_suitable_partner_ids')

    @api.depends('account_type_ids')
    def _compute_suitable_partner_ids(self):
        for rec in self:
            for type in rec.account_type_ids.ids:
                type_obj = self.env['account.account.type'].browse(type)


                if rec.type_obj.type == 'receivable':
                    # company_id = rec.company_id.id or self.env.company.id
                    domain = [('customer_rank', '>', 0)]
                    rec.suitable_partner_ids = self.env['res.partner'].search(domain)
                if rec.type_obj.type == 'payable':
                    # company_id = rec.company_id.id or self.env.company.id
                    domain = [('supplier_rank', '>', 0)]
                    rec.suitable_partner_ids = self.env['res.partner'].search(domain)
                else:

                    # company_id = rec.company_id.id or self.env.company.id
                    domain = []
                    rec.suitable_partner_ids = self.env['res.partner'].search(domain)
    @api.onchange('account_type_ids')
    def _onchage_suitable_partner_ids(self):
        for rec in self:
            for type in rec.account_type_ids.ids:
                type_obj = self.env['account.account.type'].browse(type)


                if rec.type_obj.type == 'receivable':
                    # company_id = rec.company_id.id or self.env.company.id
                    domain = [('customer_rank', '>', 0)]
                    rec.suitable_partner_ids = self.env['res.partner'].search(domain)
                if rec.type_obj.type == 'payable':
                    # company_id = rec.company_id.id or self.env.company.id
                    domain = [('supplier_rank', '>', 0)]
                    rec.suitable_partner_ids = self.env['res.partner'].search(domain)
                else:

                    # company_id = rec.company_id.id or self.env.company.id
                    domain = []
                    rec.suitable_partner_ids = self.env['res.partner'].search(domain)

    @api.model
    def view_report(self, option):
        r = self.env['account.partner.ledger'].search([('id', '=', option[0])])
        data = {
            'display_account': r.display_account,
            'model': self,
            'journals': r.journal_ids,
            'journal_code': r.journal_code_ids,
            'invoice_type': r.invoice_type_ids,
            'accounts': r.account_ids,
            'target_move': r.target_move,
            'partners': r.partner_ids,
            'reconciled': r.reconciled,
            'account_type': r.account_type_ids,
            'partner_tags': r.partner_category_ids,
        }

        if r.date_from:
            data.update({
                'date_from':r.date_from,
            })
        if r.date_to:
            data.update({
                'date_to':r.date_to,
            })

        filters = self.get_filter(option)
        records = self._get_report_values(data)
        currency = self._get_currency()

        return {
            'name': "partner Ledger",
            'type': 'ir.actions.client',
            'tag': 'p_l',
            'filters': filters,
            'report_lines': records['Partners'],
            'debit_total': records['debit_total'],
            'credit_total': records['credit_total'],
            'debit_balance': records['debit_balance'],
            'currency': currency,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)

        filters = {}
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('journal_code_ids'):
            filters['journal_code'] = self.env['journal.code'].browse(data.get('journal_code_ids')).mapped('code')
        else:
            filters['journal_code'] = ['All']
        if data.get('invoice_type_ids'):
            filters['invoice_type'] = self.env['journal.code'].browse(data.get('invoice_type_ids')).mapped('code')
        else:
            filters['invoice_type'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All Payable and Receivable']
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move').capitalize()
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')

        filters['company_id'] = ''
        filters['accounts_list'] = data.get('accounts_list')
        filters['journals_list'] = data.get('journals_list')
        filters['journal_code_list'] = data.get('journal_code_list')
        filters['invoice_type_list'] = data.get('invoice_type_list')

        filters['company_name'] = data.get('company_name')

        if data.get('partners'):
            
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partners')).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('reconciled') == 'unreconciled':
            filters['reconciled'] = 'Unreconciled'

        if data.get('account_type', []):
            filters['account_type'] = self.env['account.account.type'].browse(data.get('account_type', [])).mapped('name')
        else:
            filters['account_type'] = ['Receivable and Payable']

        if data.get('partner_tags', []):
            filters['partner_tags'] = self.env['res.partner.category'].browse(
                data.get('partner_tags', [])).mapped('name')
        else:
            filters['partner_tags'] = ['All']

        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['account_type_list'] = data.get('account_type_list')
        filters['target_move'] = data.get('target_move').capitalize()
        return filters

    def get_filter_data(self, option):
        r = self.env['account.partner.ledger'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = self.env.company
        company_domain = [('company_id', '=', company_id.id)]
        journals = r.journal_ids if r.journal_ids else self.env['account.journal'].search(company_domain)
        journals_code = r.journal_code_ids if r.journal_code_ids else self.env['journal.code'].search([])
        invoice_type = r.invoice_type_ids if r.invoice_type_ids else self.env['invoice.type'].search([])
        accounts = self.account_ids if self.account_ids else self.env['account.account'].search(company_domain)
       
        partner = r.partner_ids if r.partner_ids else self.env[
                'res.partner'].search([])

        categories = self.partner_category_ids if self.partner_category_ids \
            else self.env['res.partner.category'].search([])
        account_types = r.account_type_ids if r.account_type_ids \
            else self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
       

        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'journal_code_ids': r.journal_code_ids.ids,
            'invoice_type_ids': r.invoice_type_ids.ids,
            'account_ids': r.account_ids.ids,
            'company_id': company_id.id,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': r.target_move,
            'journals_list': [(j.id, j.name, j.code) for j in journals],
            'journal_code_list': [(jc.id, jc.name, jc.code) for jc in journals_code],
            'invoice_type_list': [(it.id, it.name) for it in invoice_type],
            'accounts_list': [(a.id, a.name) for a in accounts],
            'company_name': company_id and company_id.name,
            'partners': r.partner_ids.ids,
            'reconciled': r.reconciled,
            'account_type': r.account_type_ids.ids,
            'partner_tags': r.partner_category_ids.ids,
            'partners_list': [(p.id, p.name) for p in partner],
            'category_list': [(c.id, c.name) for c in categories],
            'account_type_list': [(t.id, t.name) for t in account_types],

        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_values(self, data):
        docs = data['model']
        display_account = data['display_account']
        init_balance = True
        accounts = self.env['account.account'].search([('user_type_id.type', 'in', ('receivable', 'payable')),
                                                       ('company_id', '=', self.env.company.id)])
        if data['account_type']:
            accounts = self.env['account.account'].search(
                [('user_type_id.id', 'in', data['account_type'].ids),('company_id', '=', self.env.company.id)])

        partners = self.env['res.partner'].search([])
        journals_code = self.env['journal.code'].search([])
        invoice_type = self.env['invoice.type'].search([])

        if data['partner_tags']:
            partners = self.env['res.partner'].search(
                [('category_id', 'in', data['partner_tags'].ids)])
        if not accounts:
            raise UserError(_("No Accounts Found! Please Add One"))
        partner_res = self._get_partners(partners,accounts, init_balance, display_account, data)

        debit_total = 0
        debit_total = sum(x['debit'] for x in partner_res)
        credit_total = sum(x['credit'] for x in partner_res)
        debit_balance = round(debit_total,2) - round(credit_total,2)
        return {
            'doc_ids': self.ids,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'debit_balance':debit_balance,
            'docs': docs,
            'time': time,
            'Partners': partner_res,
        }

    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        res = super(PartnerView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if not vals.get('journal_ids'):
            vals.update({'journal_ids': [(5,)]})
        if vals.get('journal_code_ids'):
            vals.update({'journal_code_ids': [(6, 0, vals.get('journal_code_ids'))]})
        if not vals.get('journal_code_ids'):
            vals.update({'journal_code_ids': [(5,)]})
        if vals.get('invoice_type_ids'):
            vals.update({'invoice_type_ids': [(6, 0, vals.get('invoice_type_ids'))]})
        if not vals.get('invoice_type_ids'):
            vals.update({'invoice_type_ids': [(5,)]})
        if vals.get('account_ids'):
            vals.update({'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if not vals.get('account_ids'):
            vals.update({'account_ids': [(5,)]})
        if vals.get('partner_ids'):
            vals.update(
                {'partner_ids': [(4, j) for j in vals.get('partner_ids')]})
        if not vals.get('partner_ids'):
            vals.update({'partner_ids': [(5,)]})
        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(4, j) for j in vals.get(
                'partner_category_ids')]})
        if not vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(5,)]})

        if vals.get('account_type-ids'):
            vals.update(
                {'account_type_ids': [(4, j) for j in vals.get('account_type_ids')]})
        if not vals.get('account_type_ids'):
            vals.update({'account_type_ids': [(5,)]})

        res = super(PartnerView, self).write(vals)
        return res

    def _get_partners(self, partners, accounts, init_balance, display_account, data):

        cr = self.env.cr
        move_line = self.env['account.move.line']
        move_lines = {x: [] for x in partners.ids}
        currency_id = self.env.company.currency_id

        tables, where_clause, where_params = move_line._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        final_filters = " AND ".join(wheres)
        final_filters = final_filters.replace('account_move_line__move_id', 'm').replace(
            'account_move_line', 'l')
        new_final_filter = final_filters
        if data['target_move'] == 'posted':
            new_final_filter += " AND m.state = 'posted'"
        else:
            new_final_filter += " AND m.state in ('draft','posted')"
        if data.get('date_from'):
            new_final_filter += " AND l.date >= '%s'" % data.get('date_from')
        if data.get('date_to'):
            new_final_filter += " AND l.date <= '%s'" % data.get('date_to')

        if data['journals']:
            new_final_filter += ' AND j.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
       
        if data.get('accounts'):
            WHERE = "WHERE l.account_id IN %s" % str(tuple(data.get('accounts').ids) + tuple([0]))
        else:
            WHERE = "WHERE l.account_id IN %s"
        if data['journal_code']:
            WHERE  += ' AND l.journal_code_id IN %s' % str(tuple(data['journal_code'].ids) + tuple([0]))
        
        if data['invoice_type']:
            WHERE +=  ' AND l.invoice_type_id IN %s' % str(tuple(data['invoice_type'].ids) + tuple([0]))
        


        if data.get('partners'):
            WHERE += ' AND p.id IN %s' % str(
                tuple(data.get('partners').ids) + tuple([0]))

        # if data.get('reconciled') == 'unreconciled':
        #     WHERE += ' AND l.full_reconcile_id is null AND' \
        #              ' l.balance != 0 AND a.reconcile is true'
        
        sql = ('''SELECT l.id AS lid,l.partner_id AS partner_id,m.id AS move_id, 
                    l.account_id AS account_id, l.date AS ldate, j.code AS lcode,jc.code AS ljournal_code,
                    it.name AS linv_type, l.currency_id, 
                    l.amount_currency, l.ref AS lref, l.name AS lname, 
                    COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, 
                    COALESCE(SUM(l.balance),0) AS balance,\
                    m.name AS move_name, c.symbol AS currency_code,c.position AS currency_position, p.name AS partner_name\
                    FROM account_move_line l\
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    JOIN account_journal j ON (l.journal_id=j.id)\
                    LEFT JOIN journal_code jc ON (l.journal_code_id=jc.id)\
                    LEFT JOIN invoice_type it ON (l.invoice_type_id=it.id)\
                    JOIN account_account acc ON (l.account_id = acc.id) '''
                    + WHERE + new_final_filter + ''' GROUP BY l.id, m.id,  l.account_id, l.date, j.code,jc.code, it.name,l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, c.position, p.name
                    ORDER BY l.date asc''' )
        if data.get('accounts'):
            params = tuple(where_params)
        else:
            params = (tuple(accounts.ids),) + tuple(where_params)
        s = cr.execute(sql, params)

        account_list = { x.id : {'name' : x.name, 'code': x.code} for x in accounts}

        for row in cr.dictfetchall():
            balance = 0
            if row['partner_id'] in move_lines:
                for line in move_lines.get(row['partner_id']):
                    balance += round(line['debit'],2) - round(line['credit'],2)
                row['balance'] += (round(balance, 2))
                row['m_id'] = row['account_id']
                row['account_name'] = account_list[row['account_id']]['name'] + "(" +account_list[row['account_id']]['code'] + ")"
                move_lines[row.pop('partner_id')].append(row)

        partner_res = []
        for partner in partners:
            company_id = self.env.company
            currency = company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['name'] = partner.name
            res['customer_ref'] = partner.customer_ref
            res['id'] = partner.id
            res['move_lines'] = move_lines[partner.id]
            for line in res.get('move_lines'):
                res['debit'] += round(line['debit'], 2)
                res['credit'] += round(line['credit'], 2)
                res['balance'] = round(line['balance'], 2)
            if display_account == 'all':
                partner_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                partner_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(
                    res['balance']):
                partner_res.append(res)
        return partner_res

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(
            self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        lang = self.env.user.lang
        if not lang:
            lang = 'en_US'
        lang = lang.replace("_", '-')
        currency_array = [self.env.company.currency_id.symbol,
                          self.env.company.currency_id.position, lang]
        return currency_array

    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data):
        report_data = json.loads(report_data)
        filters = json.loads(data)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        cell_format = workbook.add_format(
            {'align': 'center', 'bold': True,
             'border': 0
             })
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        pos_neg_fmt = workbook.add_format({'font_size': '10px', 'border': 1,'num_format': '#,##0;(#,##0)'})
        txt_date = workbook.add_format({'font_size': '10px', 'border': 1,'num_format': 'mm/dd/yy'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        sub_heading_sub = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        sub_heading_sub_total = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black','num_format': '#,##0;(#,##0)'})
        sheet.merge_range('A1:H2',
                          filters.get('company_name') + ':' + 'Partner Ledger',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})

        sheet.merge_range('A4:B4',
                          'Target Moves: ' + filters.get('target_move'),
                          date_head)

        sheet.merge_range('C4:D4', 'Account Type: ' + ', ' .join(
            [lt or '' for lt in
             filters['account_type']]),
                          date_head)
        sheet.merge_range('E3:F3', ' Partners: ' + ', '.join(
            [lt or '' for lt in
             filters['partners']]), date_head)
        sheet.merge_range('G3:H3', ' Partner Tags: ' + ', '.join(
            [lt or '' for lt in
             filters['partner_tags']]),
                          date_head)
        sheet.merge_range('A3:B3', ' Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]),
                          date_head)
        sheet.merge_range('C3:D3', ' Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]),
                          date_head)

        if filters.get('date_from') and filters.get('date_to'):
            sheet.merge_range('E4:F4', 'From: ' + filters.get('date_from'),
                              date_head)

            sheet.merge_range('G4:H4', 'To: ' + filters.get('date_to'),
                              date_head)
        elif filters.get('date_from'):
            sheet.merge_range('E4:F4', 'From: ' + filters.get('date_from'),
                              date_head)
        elif filters.get('date_to'):
            sheet.merge_range('E4:F4', 'To: ' + filters.get('date_to'),
                              date_head)

        sheet.merge_range('A5:E5', 'Partner', cell_format)
        # sheet.write('F5', 'Debit', cell_format)
        # sheet.write('G5', 'Credit', cell_format)
        # sheet.write('H5', 'Balance', cell_format)

        row = 4
        col = 0

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 36)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)

        for report in report_data:

            row += 1
            
            sheet.merge_range(row, col + 0, row, col + 5, report['name'],
                              sub_heading_sub)
            
            row += 1
            sheet.write(row, col + 0, 'Date', cell_format)
            sheet.write(row, col + 1, 'JRNL', cell_format)
            sheet.write(row, col + 2, 'JRNL Code', cell_format)
            sheet.write(row, col + 3, 'Inv.Type', cell_format)
            sheet.write(row, col + 4, 'Invoice No', cell_format)
            sheet.write(row, col + 5, 'Entry Label', cell_format)
            sheet.write(row, col + 6, 'Debit', cell_format)
            sheet.write(row, col + 7, 'Credit', cell_format)
            sheet.write(row, col + 8, 'Balance', cell_format)
            for r_rec in report['move_lines']:
                row += 1
                date1=datetime.strptime(r_rec['ldate'], "%Y-%m-%d").date()
                date = date1.strftime("%m/%d/%Y")
                sheet.write(row, col + 0, date, txt_date)
                sheet.write(row, col + 1, r_rec['lcode'], txt)
                sheet.write(row, col + 2, r_rec['ljournal_code'], txt)
                sheet.write(row, col + 3, r_rec['linv_type'], txt)
                sheet.write(row, col + 4, r_rec['move_name'], txt)
                sheet.write(row, col + 5, r_rec['lname'], txt)
                sheet.write(row, col + 6, r_rec['debit'], pos_neg_fmt)
                sheet.write(row, col + 7, r_rec['credit'], pos_neg_fmt)
                sheet.write(row, col + 8, r_rec['balance'], pos_neg_fmt)
            row += 1
            sheet.merge_range(row, col + 0, row, col + 5, 'Total',
                              sub_heading_sub)
            sheet.write(row, col + 6, report['debit'], sub_heading_sub_total)
            sheet.write(row, col + 7, report['credit'], sub_heading_sub_total)
            sheet.write(row, col + 8, report['balance'], sub_heading_sub_total)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
