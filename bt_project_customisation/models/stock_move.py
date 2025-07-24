# © 2019 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2019 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, exceptions, models


class StockMove(models.Model):
    _inherit = "stock.move"


    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            if self._is_returned(valued_type='in'):
                self.with_company(company_to)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)
            else:
                wip_acc = self.env['account.account'].search([('code', '=','1103102'),
                                                      ], limit=1)
                if self.location_dest_id.is_project_location == True:
                    self.with_company(company_to)._create_account_move_line(acc_src, wip_acc.id, journal_id, qty, description, svl_id, cost)
                else:
                    self.with_company(company_to)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = -1 * cost
            if self._is_returned(valued_type='out'):
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost)
            else:
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            if self._is_dropshipped():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost)
            elif self._is_dropshipped_returned():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            self._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=self.product_id)


    def _generate_valuation_lines_data(
        self,
        partner_id,
        qty,
        debit_value,
        credit_value,
        debit_account_id,
        credit_account_id,
        description,
    ):
        res = super(StockMove, self)._generate_valuation_lines_data(
            partner_id,
            qty,
            debit_value,
            credit_value,
            debit_account_id,
            credit_account_id,
            description,
        )
        if res:
            debit_line_vals = res.get("debit_line_vals")
            credit_line_vals = res.get("credit_line_vals")
            price_diff_line_vals = res.get("price_diff_line_vals", {})

            # if (
            #     self.operating_unit_id
            #     and self.operating_unit_dest_id
            #     and self.operating_unit_id != self.operating_unit_dest_id
            #     and debit_line_vals["account_id"] != credit_line_vals["account_id"]
            # ):
            #     raise exceptions.UserError(
            #         _(
            #             "You cannot create stock moves involving separate source"
            #             " and destination accounts related to different "
            #             "operating units."
            #         )
            #     )

            # if not self.operating_unit_dest_id and not self.operating_unit_id:
            #     ou_id = (
            #         self.picking_id.picking_type_id.warehouse_id.operating_unit_id.id
            #     )
            # else:
            #     ou_id = False

            # debit_line_vals["operating_unit_id"] = (
            #     ou_id or self.operating_unit_dest_id.id or self.operating_unit_id.id
            # )
            # credit_line_vals["operating_unit_id"] = (
            #     ou_id or self.operating_unit_id.id or self.operating_unit_dest_id.id
            # )
            # if self.picking_id.picking_type_id.code == 'internal':
            debit_line_vals["analytic_account_id"] = self.analytic_account_id.id or False
            credit_line_vals["analytic_account_id"] = self.analytic_account_id.id or False
            rslt = {
                "credit_line_vals": credit_line_vals,
                "debit_line_vals": debit_line_vals,
            }
            # if price_diff_line_vals:
            #     price_diff_line_vals["operating_unit_id"] = (
            #         ou_id or self.operating_unit_id.id or self.operating_unit_dest_id.id
            #     )
            #     rslt["price_diff_line_vals"] = price_diff_line_vals
            return rslt
        return res

    def _action_done(self, cancel_backorder=False):
        """
        Generate accounting moves if the product being moved is subject
        to real_time valuation tracking,
        and the source or destination location are
        a transit location or is outside of the company or the source or
        destination locations belong to different operating units.
        """
        res = super(StockMove, self)._action_done(cancel_backorder)
        for move in self:

            if move.product_id.valuation == "real_time":
                # Inter-operating unit moves do not accept to
                # from/to non-internal location
                if (
                    move.location_id.company_id and move.picking_id.picking_type_id.code == 'internal'
                    and move.location_id.company_id == move.location_dest_id.company_id and move.location_id.is_project_location != True
                    
                ):
                    (
                        journal_id,
                        acc_src,
                        acc_dest,
                        acc_valuation,
                    ) = move._get_accounting_data_for_valuation()
                    wip_acc = self.env['account.account'].search([('code', '=','1103102'),
                                                      ], limit=1)
                    for stock_line in move.move_line_ids:

                        move_lines = move._prepare_account_move_line(
                            stock_line.qty_done,
                            stock_line.unit_price * stock_line.qty_done,
                            acc_valuation,
                            wip_acc.id,
                            _("%s - OU Move") % move.product_id.display_name,
                        )
                        am = (
                            self.env["account.move"]
                            .with_context(
                                force_company=move.location_id.company_id.id,
                                company_id=move.company_id.id,
                            )
                            .create(
                                {
                                    "journal_id": journal_id,
                                    "line_ids": move_lines,
                                    "company_id": move.company_id.id,
                                    "ref": move.picking_id and move.picking_id.name,
                                    "stock_move_id": move.id,
                                }
                            )
                        )
                        am.post()
                if (
                    move.location_id.company_id and move.picking_id.picking_type_id.code == 'internal'
                    and move.location_id.company_id == move.location_dest_id.company_id and move.location_id.is_project_location == True
                    
                ):
                    (
                        journal_id,
                        acc_src,
                        acc_dest,
                        acc_valuation,
                    ) = move._get_accounting_data_for_valuation()
                    wip_acc = self.env['account.account'].search([('code', '=','1103102'),
                                                      ], limit=1)
                    for stock_line in move.move_line_ids:

                        move_lines = move._prepare_account_move_line(
                            stock_line.qty_done,
                            stock_line.unit_price * stock_line.qty_done,
                            wip_acc.id,
                            acc_valuation,
                            
                            _("%s - OU Move") % move.product_id.display_name,
                        )
                        am = (
                            self.env["account.move"]
                            .with_context(
                                force_company=move.location_id.company_id.id,
                                company_id=move.company_id.id,
                            )
                            .create(
                                {
                                    "journal_id": journal_id,
                                    "line_ids": move_lines,
                                    "company_id": move.company_id.id,
                                    "ref": move.picking_id and move.picking_id.name,
                                    "stock_move_id": move.id,
                                }
                            )
                        )
                        am.post()
            return res
