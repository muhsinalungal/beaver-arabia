# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2017 Akretion - Alexis de Lattre
# Copyright 2018 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils


class TrialBalanceReportWizard(models.TransientModel):
    """Trial balance report wizard."""

    _name = "trial.balance.report.wizard"
    _description = "Trial Balance Report Wizard"
    _inherit = "account_financial_report_abstract_wizard"

    date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    fy_start_date = fields.Date(compute="_compute_fy_start_date")
    target_move = fields.Selection(
        [("posted", "All Posted Entries"), ("all", "All Entries")],
        string="Target Moves",
        required=True,
        default="posted",
    )
    hierarchy_on = fields.Selection(
        [
            ("computed", "Computed Accounts"),
            ("relation", "Child Accounts"),
            ("none", "No hierarchy"),
        ],
        string="Hierarchy On",
        required=True,
        default="none",
        help="""Computed Accounts: Use when the account group have codes
        that represent prefixes of the actual accounts.\n
        Child Accounts: Use when your account groups are hierarchical.\n
        No hierarchy: Use to display just the accounts, without any grouping.
        """,
    )
    limit_hierarchy_level = fields.Boolean("Limit hierarchy levels")
    show_hierarchy_level = fields.Integer("Hierarchy Levels to display", default=1)
    hide_parent_hierarchy_level = fields.Boolean(
        "Do not display parent levels", default=False
    )
    account_ids = fields.Many2many(
        comodel_name="account.account", string="Filter accounts"
    )
    hide_account_at_0 = fields.Boolean(
        string="Hide accounts at 0",
        default=True,
        help="When this option is enabled, the trial balance will "
        "not display accounts that have initial balance = "
        "debit = credit = end balance = 0",
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    show_partner_details = fields.Boolean()
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Filter partners")
    journal_ids = fields.Many2many(comodel_name="account.journal")

    not_only_one_unaffected_earnings_account = fields.Boolean(
        readonly=True, string="Not only one unaffected earnings account"
    )

    foreign_currency = fields.Boolean(
        string="Show foreign currency",
        help="Display foreign currency for move lines, unless "
        "account currency is not setup through chart of accounts "
        "will display initial and final balance in that currency.",
    )
    account_code_from = fields.Many2one(
        comodel_name="account.account",
        string="Account Code From",
        help="Starting account in a range",
    )
    account_code_to = fields.Many2one(
        comodel_name="account.account",
        string="Account Code To",
        help="Ending account in a range",
    )

    @api.onchange("account_code_from", "account_code_to")
    def on_change_account_range(self):
        if (
            self.account_code_from
            and self.account_code_from.code.isdigit()
            and self.account_code_to
            and self.account_code_to.code.isdigit()
        ):
            start_range = int(self.account_code_from.code)
            end_range = int(self.account_code_to.code)
            self.account_ids = self.env["account.account"].search(
                [("code", "in", [x for x in range(start_range, end_range + 1)])]
            )
            if self.company_id:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id
                )

    @api.constrains("hierarchy_on", "show_hierarchy_level")
    def _check_show_hierarchy_level(self):
        for rec in self:
            if rec.hierarchy_on != "none" and rec.show_hierarchy_level <= 0:
                raise UserError(
                    _("The hierarchy level to filter on must be " "greater than 0.")
                )

    @api.depends("date_from")
    def _compute_fy_start_date(self):
        for wiz in self:
            if wiz.date_from:
                date_from, date_to = date_utils.get_fiscal_year(
                    wiz.date_from,
                    day=self.company_id.fiscalyear_last_day,
                    month=int(self.company_id.fiscalyear_last_month),
                )
                wiz.fy_start_date = date_from
            else:
                wiz.fy_start_date = False

    @api.onchange("company_id")
    def onchange_company_id(self):
        """Handle company change."""
        account_type = self.env.ref("account.data_unaffected_earnings")
        count = self.env["account.account"].search_count(
            [
                ("user_type_id", "=", account_type.id),
                ("company_id", "=", self.company_id.id),
            ]
        )
        self.not_only_one_unaffected_earnings_account = count != 1
        if (
            self.company_id
            and self.date_range_id.company_id
            and self.date_range_id.company_id != self.company_id
        ):
            self.date_range_id = False
        if self.company_id and self.partner_ids:
            self.partner_ids = self.partner_ids.filtered(
                lambda p: p.company_id == self.company_id or not p.company_id
            )
        if self.company_id and self.journal_ids:
            self.journal_ids = self.journal_ids.filtered(
                lambda a: a.company_id == self.company_id
            )
        if self.company_id and self.account_ids:
            if self.receivable_accounts_only or self.payable_accounts_only:
                self.onchange_type_accounts_only()
            else:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id
                )
        res = {
            "domain": {
                "account_ids": [],
                "partner_ids": [],
                "date_range_id": [],
                "journal_ids": [],
            }
        }
        if not self.company_id:
            return res
        else:
            res["domain"]["account_ids"] += [("company_id", "=", self.company_id.id)]
            res["domain"]["partner_ids"] += self._get_partner_ids_domain()
            res["domain"]["date_range_id"] += [
                "|",
                ("company_id", "=", self.company_id.id),
                ("company_id", "=", False),
            ]
            res["domain"]["journal_ids"] += [("company_id", "=", self.company_id.id)]
        return res

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.constrains("company_id", "date_range_id")
    def _check_company_id_date_range_id(self):
        for rec in self.sudo():
            if (
                rec.company_id
                and rec.date_range_id.company_id
                and rec.company_id != rec.date_range_id.company_id
            ):
                raise ValidationError(
                    _(
                        "The Company in the Trial Balance Report Wizard and in "
                        "Date Range must be the same."
                    )
                )

    @api.onchange("receivable_accounts_only", "payable_accounts_only")
    def onchange_type_accounts_only(self):
        """Handle receivable/payable accounts only change."""
        if self.receivable_accounts_only or self.payable_accounts_only:
            domain = [("company_id", "=", self.company_id.id)]
            if self.receivable_accounts_only and self.payable_accounts_only:
                domain += [("internal_type", "in", ("receivable", "payable"))]
            elif self.receivable_accounts_only:
                domain += [("internal_type", "=", "receivable")]
            elif self.payable_accounts_only:
                domain += [("internal_type", "=", "payable")]
            self.account_ids = self.env["account.account"].search(domain)
            res = {"domain": {"account_ids": [], "partner_ids": []}}
            partner_domain = []
            if self.receivable_accounts_only and self.payable_accounts_only:
               
                partner_domain = [('customer_rank', '>', 0),('supplier_rank', '>', 0)]
            elif self.receivable_accounts_only:
               
                partner_domain = [('customer_rank', '>', 0)]
            elif self.payable_accounts_only:
                
                partner_domain = [('supplier_rank', '>', 0)]
            elif self.account_code_from.internal_type == 'receivable':
                partner_domain = [('customer_rank', '>', 0)]
            elif self.account_code_from.internal_type == 'payable':
                partner_domain = [('supplier_rank', '>', 0)]
            res["domain"]["partner_ids"] += partner_domain
            return res
        else:
            self.account_ids = None

    @api.onchange("show_partner_details")
    def onchange_show_partner_details(self):
        """Handle partners change."""
        if self.show_partner_details:
            self.receivable_accounts_only = self.payable_accounts_only = True
        else:
            self.receivable_accounts_only = self.payable_accounts_only = False

    @api.depends("company_id")
    def _compute_unaffected_earnings_account(self):
        account_type = self.env.ref("account.data_unaffected_earnings")
        for record in self:
            record.unaffected_earnings_account = self.env["account.account"].search(
                [
                    ("user_type_id", "=", account_type.id),
                    ("company_id", "=", record.company_id.id),
                ]
            )

    unaffected_earnings_account = fields.Many2one(
        comodel_name="account.account",
        compute="_compute_unaffected_earnings_account",
        store=True,
    )

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_report_trial_balance()
        if report_type == "xlsx":
            report_name = "a_f_r.report_trial_balance_xlsx"
        else:
            report_name = "account_financial_report.trial_balance"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, data=data)
        )

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            "wizard_id": self.id,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "only_posted_moves": self.target_move == "posted",
            "hide_account_at_0": self.hide_account_at_0,
            "foreign_currency": self.foreign_currency,
            "company_id": self.company_id.id,
            "account_ids": self.account_ids.ids or [],
            "partner_ids": self.partner_ids.ids or [],
            "journal_ids": self.journal_ids.ids or [],
            "fy_start_date": self.fy_start_date,
            "hierarchy_on": self.hierarchy_on,
            "limit_hierarchy_level": self.limit_hierarchy_level,
            "show_hierarchy_level": self.show_hierarchy_level,
            "hide_parent_hierarchy_level": self.hide_parent_hierarchy_level,
            "show_partner_details": self.show_partner_details,
            "unaffected_earnings_account": self.unaffected_earnings_account.id,
            "account_financial_report_lang": self.env.lang,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)
