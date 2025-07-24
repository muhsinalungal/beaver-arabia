# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import copy
from collections import OrderedDict

from odoo import api, fields, models
import datetime
import calendar
from dateutil.relativedelta import relativedelta


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    allow_horizontal = fields.Boolean(compute="_compute_allow_horizontal")
    horizontal = fields.Boolean()
    dept_wise = fields.Boolean()
    month_wise = fields.Boolean()
    dept_ids = fields.Many2many(
        comodel_name="cost.center", string="Filter Dept"
    )
    quarter_wise = fields.Selection([
        ('current_year', 'Current Year'),
        ('prev_year', 'Previous Year'),
        ('first', '1st Quarter'),
        ('second', '2nd Quarter'),
        ('third', '3rd Quarter'),
        ('fourth', '4th Quarter'),
    ], string="Quarter Wise",
        
        )
    year = fields.Char('Year')
    year_wise = fields.Selection([
        ('current_year', 'Current Year'),
        ('prev_year', 'Previous Year'),
    ], string="Year Wise",
        
        )

    note = fields.Char('Note',compute="_compute_note",store=True)
    compare_year = fields.Char('Compare Year',)
    head_name = fields.Selection([
        ('dept_wise', 'Income Statement - Dept Wise'),
        ('month_wise', 'Income Statement - Monthly'),
        ('summary', 'Income Statement - Summary'),
        ('comparitive', 'Income Statement - Comparitive'),
    ],string='Name')

    project_ids = fields.Many2many(
        comodel_name="account.analytic.account", string="Filter Project"
    )


    @api.onchange("head_name")
    def on_change_head_name(self):
        if self.head_name == 'dept_wise':
                       
            self.dept_wise = True
            self.month_wise = False
            self.comparison_mode = True
            self.compare_year = ''
        elif self.head_name == 'month_wise':
                       
            self.month_wise = True
            self.comparison_mode = True
            self.dept_wise = False
            self.compare_year = ''
        elif self.head_name == 'summary':
                       
            self.comparison_mode = False
            self.dept_wise = False
            self.month_wise = False
            self.quarter_wise = ''
            self.compare_year = ''
        elif self.head_name == 'comparitive':
                       
            self.comparison_mode = True
            self.dept_wise = False
            self.month_wise = False
            self.quarter_wise = ''
        else:
           self.comparison_mode = False
           self.dept_wise = False
           self.month_wise = False

    @api.depends("date_from")
    def _compute_comparison_mode(self):
        for instance in self:
            instance.comparison_mode = True

    @api.depends("date_from","date_to","report_id","comparison_mode","year_wise","quarter_wise",
        "year","dept_wise","month_wise","compare_year","head_name")
    def _compute_note(self):
        for instance in self:
            if instance.quarter_wise:
                if instance.head_name == 'comparitive' and instance.compare_year:
                    if instance.quarter_wise in ('current_year','prev_year'):
                        year = instance.date_to.year
                        last_date = datetime.datetime(int(year), 12, 31)
                        if last_date.date()==instance.date_to:
                            instance.note = "For The Year Ended %s 31, %s & %s" % (last_date.strftime('%B'),last_date.strftime('%Y'),instance.compare_year)
                    elif instance.quarter_wise in ('first','second','third','fourth'):

                        st_date = instance.date_from
                        end_date =instance.date_to
                        if st_date and end_date:
                            months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                            if months == 0:
                                instance.note = "For The Month of %s, %s & %s" % (end_date.strftime('%b'),end_date.strftime('%Y'),instance.compare_year)
                            else:
                                instance.note = "For The Month from %s to %s, %s & %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'),instance.compare_year)

                else:

                    if not instance.month_wise:
                        if instance.quarter_wise == 'current_year':
                            year = fields.Datetime.now().strftime('%Y')
                            last_date = datetime.datetime(int(year), 12, 31)
                            instance.note = "For The Year Ended %s 31, %s" % (last_date.strftime('%B'),last_date.strftime('%Y'))
                        elif instance.quarter_wise == 'prev_year':
                            year = fields.Datetime.now().strftime('%Y')
                            last_date = datetime.datetime((int(year)-1), 12, 31)
                            instance.note = "For The Year Ended %s 31, %s" % (last_date.strftime('%B'),last_date.strftime('%Y'))
                        elif instance.quarter_wise in ('first','second','third','fourth'):
                            st_date = instance.date_from
                            end_date =instance.date_to
                            if st_date and end_date:
                                months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                                if months == 0:
                                    instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                                else:
                                    instance.note = "For The Month from %s to %s %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'))
                    elif instance.month_wise:
                        if instance.quarter_wise in ('current_year','prev_year'):
                            st_date = instance.date_from
                            end_date =instance.date_to
                            if st_date and end_date:
                                months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                                if months == 0:
                                    instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                                else:
                                    instance.note = "For The Month from %s to %s %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'))
                        elif instance.quarter_wise in ('first','second','third','fourth'):
                            st_date = instance.date_from
                            end_date =instance.date_to
                            if st_date and end_date:
                                months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                                if months == 0:
                                    instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                                else:
                                    instance.note = "For The Month from %s to %s %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'))


                    elif instance.quarter_wise in ('first','second','third','fourth'):
                        st_date = instance.date_from
                        end_date =instance.date_to
                        if st_date and end_date:
                            months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                            if months == 0:
                                instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                            else:
                                instance.note = "For The Month from %s to %s %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'))

            elif instance.month_wise:
                st_date = instance.date_from
                end_date =instance.date_to
                if st_date and end_date:
                    months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                    if months == 0:
                        instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                    else:
                        instance.note = "For The Month from %s to %s %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'))
            elif instance.compare_year:
                if instance.date_to:
                    st_date = instance.date_from
                    end_date =instance.date_to
                    if st_date and end_date:
                        months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                        if months == 0:
                            instance.note = "For The Month of %s, %s & %s" % (end_date.strftime('%b'),end_date.strftime('%Y'),instance.compare_year)
                            # instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                        elif months == 11:
                            year = instance.date_to.year
                            last_date = datetime.datetime(int(year), 12, 31)
                            if last_date.date()==instance.date_to:
                                instance.note = "For The Year Ended %s 31, %s & %s" % (last_date.strftime('%B'),last_date.strftime('%Y'),instance.compare_year)

                        else:
                            instance.note = "For The Month from %s to %s, %s & %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'),instance.compare_year)
                    
                # year = instance.date_to.year
                # last_date = datetime.datetime(int(year), 12, 31)
                # if last_date.date()==instance.date_to:
                #     instance.note = "For The Year Ended %s 31, %s & %s" % (last_date.strftime('%B'),last_date.strftime('%Y'),instance.compare_year)

            else:
                if instance.date_to:
                    st_date = instance.date_from
                    end_date =instance.date_to
                    if st_date and end_date:
                        months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
                        if months == 0:
                            instance.note = "For The Month of %s %s" % (end_date.strftime('%b'),end_date.strftime('%Y'))
                        elif months == 11:
                            year = instance.date_to.year
                            last_date = datetime.datetime(int(year), 12, 31)
                            if last_date.date()==instance.date_to:
                                instance.note = "For The Year Ended %s 31, %s" % (last_date.strftime('%B'),last_date.strftime('%Y'))

                        else:
                            instance.note = "For The Month from %s to %s %s" % (st_date.strftime('%b'),end_date.strftime('%b'),end_date.strftime('%Y'))
                    


    def _inverse_comparison_mode(self):
        for record in self:
            if not record.comparison_mode:
                if not record.date_from:
                    record.date_from = fields.Date.context_today(self)
                if not record.date_to:
                    record.date_to = fields.Date.context_today(self)
                record.period_ids.unlink()
                record.write({"period_ids": [(0, 0, {"name": "Default"})]})
            # else:
            #     record.date_from = None
            #     record.date_to = None

    @api.onchange("dept_wise")
    def on_change_dept_wise(self):
        if self.dept_wise:
            
            self.dept_ids = self.env["cost.center"].search(
                [])
            self.comparison_mode = True
        else:
           self.dept_ids = False 
           self.comparison_mode = False

    @api.onchange("month_wise")
    def on_change_month_wise(self):
        if self.month_wise:
                       
            self.comparison_mode = True
        else:
           self.comparison_mode = False

    @api.onchange("compare_year")
    def on_change_compare_year(self):
        if self.compare_year:
                       
            self.comparison_mode = True
        else:
           self.comparison_mode = False

    @api.onchange("year_wise")
    def on_change_current_year(self):
        if self.year_wise == 'current_year':
            year = fields.Datetime.now().strftime('%Y')
            first_date = datetime.datetime(int(year), 1, 1)
            last_date = datetime.datetime(int(year), 12, 31)
            
            self.date_from = first_date
            self.date_to = last_date
        elif self.year_wise == 'prev_year':
            year = fields.Datetime.now().strftime('%Y')
            first_date = datetime.datetime((int(year)-1), 1, 1)
            last_date = datetime.datetime((int(year)-1), 12, 31)
            
            self.date_from = first_date
            self.date_to = last_date
        else:
            self.date_from = ''
            self.date_to = ''



    @api.onchange("quarter_wise","year")
    def on_change_quarter_wise(self):
        if self.quarter_wise == 'first' and self.year:
            first_date = datetime.datetime(int(self.year), 1, 1)
            next_last_date = first_date + relativedelta(days=-1,months=3)
            
            self.date_from = first_date
            self.date_to = next_last_date
        elif self.quarter_wise == 'second' and self.year:
            first_date = datetime.datetime(int(self.year), 1, 1)
            qtr_first_date = first_date + relativedelta(months=3)
            next_last_date = qtr_first_date + relativedelta(days=-1,months=3)
            
            self.date_from = qtr_first_date
            self.date_to = next_last_date
        elif self.quarter_wise == 'third' and self.year:
            first_date = datetime.datetime(int(self.year), 1, 1)
            qtr_first_date = first_date + relativedelta(months=6)
            next_last_date = qtr_first_date + relativedelta(days=-1,months=3)
            
            self.date_from = qtr_first_date
            self.date_to = next_last_date
        elif self.quarter_wise == 'fourth' and self.year:
            first_date = datetime.datetime(int(self.year), 1, 1)
            qtr_first_date = first_date + relativedelta(months=9)
            next_last_date = qtr_first_date + relativedelta(days=-1,months=3)
            
            self.date_from = qtr_first_date
            self.date_to = next_last_date
        elif self.quarter_wise == 'current_year':
            year = fields.Datetime.now().strftime('%Y')
            first_date = datetime.datetime(int(year), 1, 1)
            last_date = datetime.datetime(int(year), 12, 31)
            
            self.date_from = first_date
            self.date_to = last_date
        elif self.quarter_wise == 'prev_year':
            year = fields.Datetime.now().strftime('%Y')
            first_date = datetime.datetime((int(year)-1), 1, 1)
            last_date = datetime.datetime((int(year)-1), 12, 31)
            
            self.date_from = first_date
            self.date_to = last_date
        elif self.year and not self.quarter_wise:
            first_date = datetime.datetime(int(self.year), 1, 1)
            last_date = datetime.datetime(int(self.year), 12, 31)
            
            self.date_from = first_date
            self.date_to = last_date
        else:
            self.date_from = ''
            self.date_to = ''
            


    def update_lines(self):
        self.period_ids.source_sumcol_ids.unlink()
        self.period_ids.unlink()
        if self.dept_wise == True:
            self.period_ids.source_sumcol_ids.unlink()
            self.period_ids.unlink()
            for dept in self.dept_ids.sorted(key=lambda r: r.code):
                vals = {
                    'name' : dept.short_code or dept.name,
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    'department_id' : dept.id,
                    'report_instance_id' : self.id,

                }
                self.env["mis.report.instance.period"].create(
                vals)
            vals_total = {
                    'name' : 'Total',
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    'dept_ids' : tuple(self.dept_ids.ids),
                    'report_instance_id' : self.id,

                }
            self.env["mis.report.instance.period"].create(
            vals_total)
        elif self.month_wise == True:
            self.period_ids.unlink()
            st_date = self.date_from
            end_date =self.date_to
            months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
            srt_date = self.date_from
            for month in range(months+1):
                days_in_month = calendar.monthrange(srt_date.year, srt_date.month)[1]
                next_last_date = srt_date + relativedelta(day=days_in_month)
                month_name = srt_date.strftime('%B'),
                vals = {
                    'name' : month_name[0][:3],
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : srt_date,
                    'manual_date_to' : next_last_date,
                    # 'department_id' : dept.id,
                    'report_instance_id' : self.id,

                }
                self.env["mis.report.instance.period"].create(
                vals)
                srt_date = srt_date + relativedelta(months=1)
            vals_total = {
                    'name' : 'Total',
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    # 'dept_ids' : tuple(self.dept_ids.ids),
                    'report_instance_id' : self.id,

                }
            self.env["mis.report.instance.period"].create(
            vals_total)
        elif self.compare_year:
            self.period_ids.unlink()

            compare_val1 = {
                    'name' : self.date_from.year,
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    # 'dept_ids' : tuple(self.dept_ids.ids),
                    'report_instance_id' : self.id,

                }
            instance1 = self.env["mis.report.instance.period"].create(
            compare_val1)

            first_date = datetime.datetime(int(self.compare_year), int(self.date_from.strftime('%m')), int(self.date_from.strftime('%d')))
            last_date = datetime.datetime((int(self.compare_year)), int(self.date_to.strftime('%m')), int(self.date_to.strftime('%d')))

            compare_val2 = {
                    'name' : self.compare_year,
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : first_date,
                    'manual_date_to' : last_date,
                    # 'dept_ids' : tuple(self.dept_ids.ids),
                    'report_instance_id' : self.id,

                }
            instance2 = self.env["mis.report.instance.period"].create(
            compare_val2)

            change = {
                    'name' : 'Change',
                    'source' : 'sumcol',
                    'mode' : 'none',
                    'source_sumcol_accdet' : True,
                    'report_instance_id' : self.id,

                }
            change = self.env["mis.report.instance.period"].create(
            change)

            change_det1 = {
                    'period_id' : change.id,
                    'period_to_sum_id' : instance1.id,
                    'sign' : '+',

                }
            self.env["mis.report.instance.period.sum"].create(
            change_det1)
            change_det2 = {
                    'period_id' : change.id,
                    'period_to_sum_id' : instance2.id,
                    'sign' : '-',

                }
            self.env["mis.report.instance.period.sum"].create(
            change_det2)

            change_perc = {
                    'name' : '% Change',
                    'source' : 'cmpcol',
                    'mode' : 'none',
                    'source_cmpcol_to_id' : instance1.id,
                    'source_cmpcol_from_id' : instance2.id,
                    'report_instance_id' : self.id,

                }
            change_perc_id = self.env["mis.report.instance.period"].create(
            change_perc)
        elif self.head_name == 'summary':
            self.period_ids.unlink()
            vals_total = {
                    'name' : 'Total',
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    'report_instance_id' : self.id,

                }
            self.env["mis.report.instance.period"].create(
            vals_total)
        elif self.project_ids:
            self.period_ids.unlink()
            for project in self.project_ids:
                vals = {
                    'name' : project.name,
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    'analytic_account_id' : project.id,
                    'report_instance_id' : self.id,

                }
                self.env["mis.report.instance.period"].create(
                vals)
            vals_total = {
                    'name' : 'Total',
                    'source' : 'actuals',
                    'mode' : 'fix',
                    'manual_date_from' : self.date_from,
                    'manual_date_to' : self.date_to,
                    'analytic_account_ids' : tuple(self.project_ids.ids),
                    'report_instance_id' : self.id,

                }
            self.env["mis.report.instance.period"].create(
            vals_total)



    @api.depends("report_id")
    def _compute_allow_horizontal(self):
        """Indicate that the instance supports horizontal rendering."""
        for instance in self:
            instance.allow_horizontal = set(
                instance.report_id.get_external_id().values()
            ) & {
                "mis_template_financial_report.report_bs",
                "mis_template_financial_report.report_pl",
            }

    def compute(self):
        if not self.horizontal:
            return super().compute()

        full_matrix = self._compute_matrix()

        matrices = self._compute_horizontal_matrices(full_matrix)

        result = full_matrix.as_dict()
        result["horizontal_matrices"] = [
            extra_matrix.as_dict() for extra_matrix in matrices
        ]

        return result

    def _compute_horizontal_matrices(self, matrix=None):
        """Compute the matrix (if not passed) and return the split versions"""
        return self._split_matrix(
            matrix or self._compute_matrix(),
            [
                (
                    self.env.ref("mis_template_financial_report.kpi_profit"),
                    self.env.ref("mis_template_financial_report.kpi_pl_to_report"),
                    self.env.ref("mis_template_financial_report.kpi_assets"),
                )
            ],
        )

    def _split_matrix(self, original_matrix, kpi_defs=None, keep_remaining=True):
        """Split a matrix by duplicating it as shallowly as possible and removing
        rows according to kpi_defs

        KPIs not listed there will end up together in the last matrix if
        `keep_remaining` is set.

        :param kpi_defs: [(kpi_first_matrix1, ...), (kpi_second_matrix1, ...)]
        :return: list of KpiMatrix
        """
        result = []
        remaining_rows = original_matrix._kpi_rows.copy()

        for kpis in kpi_defs:
            matrix = copy.copy(original_matrix)
            matrix._kpi_rows = OrderedDict(
                [
                    (kpi, remaining_rows.pop(kpi))
                    for kpi in kpis
                    if kpi in remaining_rows
                ]
            )
            result.append(matrix)

        if remaining_rows and keep_remaining:
            matrix = copy.copy(original_matrix)
            matrix._kpi_rows = remaining_rows
            result.append(matrix)

        return result
