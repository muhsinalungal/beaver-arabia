# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import operator
from datetime import date, datetime, timedelta

from odoo import api, models,fields
from odoo.tools import float_is_zero


class AgedPartnerBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.aged_partner_balance"
    _description = "Aged Partner Balance Report"
    _inherit = "report.account_financial_report.abstract_report"

    @api.model
    def _initialize_account(self, ag_pb_data, acc_id):
        ag_pb_data[acc_id] = {}
        ag_pb_data[acc_id]["id"] = acc_id
        ag_pb_data[acc_id]["residual"] = 0.0
        ag_pb_data[acc_id]["current"] = 0.0
        ag_pb_data[acc_id]["30_days"] = 0.0
        ag_pb_data[acc_id]["60_days"] = 0.0
        ag_pb_data[acc_id]["90_days"] = 0.0
        ag_pb_data[acc_id]["120_days"] = 0.0
        ag_pb_data[acc_id]["older"] = 0.0
        ag_pb_data[acc_id]["total"] = 0.0
        return ag_pb_data

    @api.model
    def _initialize_partner(self, ag_pb_data, acc_id, prt_id):
        ag_pb_data[acc_id][prt_id] = {}
        ag_pb_data[acc_id][prt_id]["id"] = acc_id
        ag_pb_data[acc_id][prt_id]["residual"] = 0.0
        ag_pb_data[acc_id][prt_id]["current"] = 0.0
        ag_pb_data[acc_id][prt_id]["30_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["60_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["90_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["120_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["older"] = 0.0
        ag_pb_data[acc_id][prt_id]["move_lines"] = []
        ag_pb_data[acc_id][prt_id]["total"] = 0.0
        return ag_pb_data

    @api.model
    def _calculate_amounts(
        self, ag_pb_data, acc_id, prt_id, residual,amount_total, due_date,date, date_at_object,wiz_obj
    ):
        ag_pb_data[acc_id]["residual"] += residual
        ag_pb_data[acc_id][prt_id]["residual"] += residual
        ag_pb_data[acc_id]["total"] += amount_total
        ag_pb_data[acc_id][prt_id]["total"] += amount_total
        today = date_at_object
        
        due_date = date

        
        if today <= due_date + timedelta(days=15):
            ag_pb_data[acc_id]["current"] += residual
            ag_pb_data[acc_id][prt_id]["current"] += residual
        elif today <= due_date + timedelta(days=30):
            ag_pb_data[acc_id]["30_days"] += residual
            ag_pb_data[acc_id][prt_id]["30_days"] += residual
        elif today <= due_date + timedelta(days=60):
            ag_pb_data[acc_id]["60_days"] += residual
            ag_pb_data[acc_id][prt_id]["60_days"] += residual
        elif today <= due_date + timedelta(days=90):
            ag_pb_data[acc_id]["90_days"] += residual
            ag_pb_data[acc_id][prt_id]["90_days"] += residual
        elif today <= due_date + timedelta(days=120000):
            ag_pb_data[acc_id]["120_days"] += residual
            ag_pb_data[acc_id][prt_id]["120_days"] += residual
        else:
            ag_pb_data[acc_id]["older"] += residual
            ag_pb_data[acc_id][prt_id]["older"] += residual
        return ag_pb_data

    def _get_account_partial_reconciled(self, company_id, date_at_object):
        domain = [("max_date", ">", date_at_object), ("company_id", "=", company_id)]
        fields = ["debit_move_id", "credit_move_id", "amount"]
        accounts_partial_reconcile = self.env["account.partial.reconcile"].search_read(
            domain=domain, fields=fields
        )
        debit_amount = {}
        credit_amount = {}
        for account_partial_reconcile_data in accounts_partial_reconcile:
            debit_move_id = account_partial_reconcile_data["debit_move_id"][0]
            credit_move_id = account_partial_reconcile_data["credit_move_id"][0]
            if debit_move_id not in debit_amount.keys():
                debit_amount[debit_move_id] = 0.0
            debit_amount[debit_move_id] += account_partial_reconcile_data["amount"]
            if credit_move_id not in credit_amount.keys():
                credit_amount[credit_move_id] = 0.0
            credit_amount[credit_move_id] += account_partial_reconcile_data["amount"]
            account_partial_reconcile_data.update(
                {"debit_move_id": debit_move_id, "credit_move_id": credit_move_id}
            )
        return accounts_partial_reconcile, debit_amount, credit_amount

    def _get_move_lines_data(
        self,
        company_id,
        account_ids,
        partner_ids,
        journal_code_ids,
        invoice_type_ids,
        date_at_object,
        date_from,
        only_posted_moves,
        show_move_line_details,
        wiz_obj
    ):
        domain = self._get_move_lines_domain_not_reconciled(
            company_id, account_ids, partner_ids,journal_code_ids,invoice_type_ids, only_posted_moves, date_from, wiz_obj
        )
        date_today= fields.Date.today()
        
        if wiz_obj.z_to_fifteen == True:
            today = date_today - timedelta(days=15)
            if wiz_obj.f_to_thirty == True or wiz_obj.tone_to_sixty == True or  wiz_obj.sone_to_ninety == True or wiz_obj.ninety_plus == True:
                domain += ['|', ("date", ">=", today)]
            else:
                domain += [("date", ">=", today)]
            
        if wiz_obj.f_to_thirty == True:
            today = date_today - timedelta(days=30)
            today_ls = date_today - timedelta(days=16)
            if wiz_obj.tone_to_sixty == True or  wiz_obj.sone_to_ninety == True or wiz_obj.ninety_plus == True:
                domain += ['|', '&', ("date", ">=", today),("date", "<=", today_ls)]
            else:
                domain += ['&', ("date", ">=", today),("date", "<=", today_ls)]

        if wiz_obj.tone_to_sixty == True:
            today = date_today - timedelta(days=60)
            today_ls = date_today - timedelta(days=31)
            if wiz_obj.sone_to_ninety == True or wiz_obj.ninety_plus == True:
                domain += ['|', '&', ("date", ">=", today), ("date", "<=", today_ls)]
            else:
                domain += ['&', ("date", ">=", today), ("date", "<=", today_ls)]
        
        if wiz_obj.sone_to_ninety == True:
            today = date_today - timedelta(days=90)
            today_ls = date_today - timedelta(days=61)
            if wiz_obj.ninety_plus == True:
                domain += ['|', '&', ("date", ">=", today),("date", "<=", today_ls)]
            else:
                domain += ['&', ("date", ">=", today),("date", "<=", today_ls)]
        
        if wiz_obj.ninety_plus == True:
            today_ls = date_today - timedelta(days=91)
            domain += [("date", "<=", today_ls)]
        

        
        ml_fields = [
            "id",
            "name",
            "date",
            "move_id",
            "journal_id",
            "account_id",
            "partner_id",
            "amount_residual",
            "date_maturity",
            "ref",
            "reconciled",
        ]
        line_model = self.env["account.move.line"]
        move_model = self.env["account.move"]
        partner_model = self.env["res.partner"]
        domain += [('advance_move_line', '=', False)]
        move_lines = line_model.search_read(domain=domain, fields=ml_fields)
        journals_ids = set()
        partners_ids = set()
        partners_data = {}
        ag_pb_data = {}
        if date_at_object < date.today():
            (
                acc_partial_rec,
                debit_amount,
                credit_amount,
            ) = self._get_account_partial_reconciled(company_id, date_at_object)
            if acc_partial_rec:
                ml_ids = list(map(operator.itemgetter("id"), move_lines))
                debit_ids = list(
                    map(operator.itemgetter("debit_move_id"), acc_partial_rec)
                )
                credit_ids = list(
                    map(operator.itemgetter("credit_move_id"), acc_partial_rec)
                )
                move_lines = self._recalculate_move_lines(
                    move_lines,
                    debit_ids,
                    credit_ids,
                    debit_amount,
                    credit_amount,
                    ml_ids,
                    account_ids,
                    company_id,
                    partner_ids,
                    journal_code_ids,
                    invoice_type_ids,
                    only_posted_moves,
                )
        move_lines = [
            move_line
            for move_line in move_lines
            if move_line["date"] <= date_at_object
            and not float_is_zero(move_line["amount_residual"], precision_digits=2)
        ]
        
        for move_line in move_lines:
            journals_ids.add(move_line["journal_id"][0])
            acc_id = move_line["account_id"][0]
            if move_line["partner_id"]:
                prt_code = partner_model.browse(move_line["partner_id"][0]).customer_ref
                prt_id = move_line["partner_id"][0]
                prt_name = move_line["partner_id"][1]
            else:
                prt_id = 0
                prt_name = ""
                prt_code = ""
            if prt_id not in partners_ids:
                partners_data.update({prt_id: {"id": prt_id, "name": prt_name,"code": prt_code}})

                sorted_data = dict(sorted(partners_data.items(), key=lambda x: x[1]['code']))
                partners_data = sorted_data
                partners_ids.add(prt_id)
                sorted(set(sorted(partners_ids)))

            if acc_id not in ag_pb_data.keys():
                ag_pb_data = self._initialize_account(ag_pb_data, acc_id)
            if prt_id not in ag_pb_data[acc_id]:
                ag_pb_data = self._initialize_partner(ag_pb_data, acc_id, prt_id)
            move_line_data = {}
            if show_move_line_details:
                if move_line["ref"] == move_line["name"]:
                    if move_line["ref"]:
                        ref_label = move_line["ref"]
                    else:
                        ref_label = ""
                elif not move_line["ref"]:
                    ref_label = move_line["name"]
                elif not move_line["name"]:
                    ref_label = move_line["ref"]
                else:
                    ref_label = move_line["ref"] + str(" - ") + move_line["name"]
                d1 = datetime.strptime(str(move_line["date"]), "%Y-%m-%d")
                d2 = datetime.strptime(str(fields.date.today()), "%Y-%m-%d")
                due_days = (d2 - d1).days
                if move_model.browse(move_line["move_id"][0]).move_type == 'out_refund':
                    total = -(move_model.browse(move_line["move_id"][0]).amount_total)
                else:
                    total = move_model.browse(move_line["move_id"][0]).amount_total
                move_line_data.update(
                    {
                        "line_rec": line_model.browse(move_line["id"]),
                        "date": move_line["date"],
                        "inv_type":move_model.browse(move_line["move_id"][0]).invoice_type_id.name,
                        "journal_code":move_model.browse(move_line["move_id"][0]).journal_code_id.code,
                        "entry": move_model.browse(move_line["move_id"][0]).name,
                        "jnl_id": move_line["journal_id"][0],
                        "acc_id": acc_id,
                        "partner": prt_name,
                        "ref_label": ref_label,
                        "due_date": move_line["date_maturity"],
                        "due_days": due_days,
                        "residual": move_line["amount_residual"],
                        # "total": move_line["amount_residual"],
                        "total":total
                    }
                )
                ag_pb_data[acc_id][prt_id]["move_lines"].append(move_line_data)
            if move_model.browse(move_line["move_id"][0]).move_type == 'out_refund':
                    total = -(move_model.browse(move_line["move_id"][0]).amount_total)
            else:
                total = move_model.browse(move_line["move_id"][0]).amount_total
            ag_pb_data = self._calculate_amounts(
                ag_pb_data,
                acc_id,
                prt_id,
                move_line["amount_residual"],
                total,
                move_line["date_maturity"],
                move_line["date"],
                date_at_object,
                wiz_obj
            )
        journals_data = self._get_journals_data(list(journals_ids))
        accounts_data = self._get_accounts_data(ag_pb_data.keys())
        return ag_pb_data, accounts_data, partners_data, journals_data

    @api.model
    def _compute_maturity_date(self, ml, date_at_object,wiz_obj):
        ml.update(
            {
                "current": 0.0,
                "30_days": 0.0,
                "60_days": 0.0,
                "90_days": 0.0,
                "120_days": 0.0,
                "older": 0.0,
            }
        )
        due_date = ml["due_date"]
        amount = ml["residual"]
        today = date_at_object
        date = ml["date"]
        
        due_date = date
        if today <= due_date + timedelta(days=15):
            ml["current"] += amount
        elif today <= due_date + timedelta(days=30):
            ml["30_days"] += amount
        elif today <= due_date + timedelta(days=60):
            ml["60_days"] += amount
        elif today <= due_date + timedelta(days=90):
            ml["90_days"] += amount
        elif today <= due_date + timedelta(days=120000):
            ml["120_days"] += amount
        else:
            ml["older"] += amount

    def _create_account_list(
        self,
        ag_pb_data,
        accounts_data,
        partners_data,
        journals_data,
        show_move_line_details,
        date_at_oject,
        wiz_obj
    ):
        aged_partner_data = []
        for account in accounts_data.values():
            acc_id = account["id"]
            account.update(
                {
                    "residual": ag_pb_data[acc_id]["residual"],
                    "current": ag_pb_data[acc_id]["current"],
                    "30_days": ag_pb_data[acc_id]["30_days"],
                    "60_days": ag_pb_data[acc_id]["60_days"],
                    "90_days": ag_pb_data[acc_id]["90_days"],
                    "120_days": ag_pb_data[acc_id]["120_days"],
                    "older": ag_pb_data[acc_id]["older"],
                    "total": ag_pb_data[acc_id]["total"],
                    "partners": [],
                }
            )
            for prt_id in ag_pb_data[acc_id]:
                if isinstance(prt_id, int):
                    partner = {
                        "name": partners_data[prt_id]["name"],
                        "code": partners_data[prt_id]["code"],
                        "residual": ag_pb_data[acc_id][prt_id]["residual"],
                        "current": ag_pb_data[acc_id][prt_id]["current"],
                        "30_days": ag_pb_data[acc_id][prt_id]["30_days"],
                        "60_days": ag_pb_data[acc_id][prt_id]["60_days"],
                        "90_days": ag_pb_data[acc_id][prt_id]["90_days"],
                        "120_days": ag_pb_data[acc_id][prt_id]["120_days"],
                        "older": ag_pb_data[acc_id][prt_id]["older"],
                        "total": ag_pb_data[acc_id][prt_id]["total"],
                    }
                    if show_move_line_details:
                        move_lines = []
                        for ml in ag_pb_data[acc_id][prt_id]["move_lines"]:
                            ml.update(
                                {
                                    "journal": journals_data[ml["jnl_id"]]["code"],
                                    "account": accounts_data[ml["acc_id"]]["code"],
                                }
                            )
                            self._compute_maturity_date(ml, date_at_oject,wiz_obj)
                            move_lines.append(ml)
                        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                        partner.update({"move_lines": move_lines})
                    account["partners"].append(partner)
            aged_partner_data.append(account)
        return aged_partner_data

    @api.model
    def _calculate_percent(self, aged_partner_data):
        for account in aged_partner_data:
            if abs(account["residual"]) > 0.01:
                total = account["residual"]
                account.update(
                    {
                        "percent_current": abs(
                            round((account["current"] / total) * 100, 2)
                        ),
                        "percent_30_days": abs(
                            round((account["30_days"] / total) * 100, 2)
                        ),
                        "percent_60_days": abs(
                            round((account["60_days"] / total) * 100, 2)
                        ),
                        "percent_90_days": abs(
                            round((account["90_days"] / total) * 100, 2)
                        ),
                        "percent_120_days": abs(
                            round((account["120_days"] / total) * 100, 2)
                        ),
                        "percent_older": abs(
                            round((account["older"] / total) * 100, 2)
                        ),
                    }
                )
            else:
                account.update(
                    {
                        "percent_current": 0.0,
                        "percent_30_days": 0.0,
                        "percent_60_days": 0.0,
                        "percent_90_days": 0.0,
                        "percent_120_days": 0.0,
                        "percent_older": 0.0,
                    }
                )
        return aged_partner_data
    
    def _get_report_values(self, docids, data):
        wiz_obj = self.env["aged.partner.balance.report.wizard"].browse(data["wizard_id"])
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        account_ids = data["account_ids"]
        partner_ids = data["partner_ids"]
        journal_code_ids = wiz_obj.journal_code_ids.ids
        invoice_type_ids = wiz_obj.invoice_type_ids.ids
        date_at = data["date_at"]
        date_at_object = datetime.strptime(date_at, "%Y-%m-%d").date()
        date_from = data["date_from"]
        only_posted_moves = data["only_posted_moves"]
        show_move_line_details = data["show_move_line_details"]
        (
            ag_pb_data,
            accounts_data,
            partners_data,
            journals_data,
        ) = self._get_move_lines_data(
            company_id,
            account_ids,
            partner_ids,
            journal_code_ids,
            invoice_type_ids,
            date_at_object,
            date_from,
            only_posted_moves,
            show_move_line_details,
            wiz_obj
        )
        aged_partner_data = self._create_account_list(
            ag_pb_data,
            accounts_data,
            partners_data,
            journals_data,
            show_move_line_details,
            date_at_object,
            wiz_obj
        )
        aged_partner_data = self._calculate_percent(aged_partner_data)
        return {
            "doc_ids": [wizard_id],
            "doc_model": "open.items.report.wizard",
            "docs": self.env["open.items.report.wizard"].browse(wizard_id),
            "company_name": company.display_name,
            "currency_name": company.currency_id.name,
            "date_at": date_at,
            "only_posted_moves": only_posted_moves,
            "aged_partner_balance": aged_partner_data,
            "show_move_lines_details": show_move_line_details,
        }
