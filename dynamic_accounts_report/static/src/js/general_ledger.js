odoo.define('dynamic_cash_flow_statements.general_ledger', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;

    window.click_num = 0;
    var GeneralLedger = AbstractAction.extend({
    template: 'GeneralTemp',
        events: {
            'click .parent-line': 'journal_line_click',
            'click .child_col1': 'journal_line_click',
            'click #apply_filter': 'apply_filter',
            'click #pdf': 'print_pdf',
            'click #xlsx': 'print_xlsx',
            'click .gl-line': 'show_drop_down',
            'click .view-account-move': 'view_acc_move',
        },

        init: function(parent, action) {
        this._super(parent, action);
                this.currency=action.currency;
                this.report_lines = action.report_lines;
                this.wizard_id = action.context.wizard | null;
            },


          start: function() {
            var self = this;
            self.initial_render = true;
            if (this.searchModel.config.domain.length != 0) {
                rpc.query({
                    model: 'account.general.ledger',
                    method: 'create',
                    args: [{
                         account_ids : [this.searchModel.config.domain[0][2]]
                    }]
                }).then(function(t_res) {
                    self.wizard_id = t_res;
                    self.load_data(self.initial_render);
                })
            }else{
            rpc.query({
                    model: 'account.general.ledger',
                    method: 'create',
                    args: [{

                    }]
                }).then(function(t_res) {
                    self.wizard_id = t_res;
                    self.load_data(self.initial_render);
                })
            }
        },


        load_data: function (initial_render = true) {
            var self = this;
                self.$(".categ").empty();
                try{
                    var self = this;
                    var action_title = self._title
                    self._rpc({
                        model: 'account.general.ledger',
                        method: 'view_report',
                        args: [[this.wizard_id], action_title],
                    }).then(function(datas) {
                    _.each(datas['report_lines'], function(rep_lines) {
                            rep_lines.debit = self.format_currency(datas['currency'],rep_lines.debit);
                            rep_lines.credit = self.format_currency(datas['currency'],rep_lines.credit);
                            rep_lines.balance = self.format_currency(datas['currency'],rep_lines.balance);




                            });

                            if (initial_render) {
                                    self.$('.filter_view_tb').html(QWeb.render('GLFilterView', {
                                        filter_data: datas['filters'],
                                        title : datas['name'],
                                    }));
                                    self.$el.find('.journals').select2({
                                        placeholder: ' Journals...',
                                    });
                                    self.$el.find('.account').select2({
                                        placeholder: ' Accounts...',
                                    });
                                    self.$el.find('.cost_centers').select2({
                                        placeholder: 'Departments...',
                                    });
                                    self.$el.find('.budgets').select2({
                                        placeholder: 'Cost Centers...',
                                    });
                                    self.$el.find('.accoms').select2({
                                        placeholder: 'Accomodation...',
                                    });
                                    self.$el.find('.assets').select2({
                                        placeholder: 'Assets...',
                                    });
                                    self.$el.find('.employees').select2({
                                        placeholder: 'Employees...',
                                    });
                                    self.$el.find('.journal_code').select2({
                                        placeholder: 'Journal Code...',
                                    });
                                    self.$el.find('.analytics').select2({
                                        placeholder: 'Analytic Accounts...',
                                    });
                                    self.$el.find('.analytic_tags').select2({
                                        placeholder: 'Analytic Tags...',
                                    });
                                    self.$el.find('.target_move').select2({
                                        placeholder: 'Target Move...',
                                    });

                            }
                            var child=[];

                        self.$('.table_view_tb').html(QWeb.render('GLTable', {

                                            report_lines : datas['report_lines'],
                                            filter : datas['filters'],
                                            currency : datas['currency'],
                                            credit_total : datas['credit_total'],
                                            debit_total : datas['debit_total'],
                                            debit_balance : datas['debit_balance']
                                        }));

                });

                    }
                catch (el) {
                    window.location.href
                    }
            },

            print_pdf: function(e) {
            e.preventDefault();
            var self = this;
            var action_title = self._title
            self._rpc({
                model: 'account.general.ledger',
                method: 'view_report',
                args: [
                    [self.wizard_id], action_title
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'dynamic_accounts_report.general_ledger',
                    'report_file': 'dynamic_accounts_report.general_ledger',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'account.general.ledger',
                        'landscape': 1,
                        'trial_pdf_report': true
                    },
                    'display_name': action_title,
                };
                return self.do_action(action);
            });
        },

        print_xlsx: function() {
            var self = this;
            var action_title = self._title
            self._rpc({
                model: 'account.general.ledger',
                method: 'view_report',
                args: [
                    [self.wizard_id], action_title
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir_actions_dynamic_xlsx_download',
                    'data': {
                         'model': 'account.general.ledger',
                         'options': JSON.stringify(data['filters']),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data['report_lines']),
                         'report_name': action_title,
                         'dfr_data': JSON.stringify(data),
                    },
                };
                return self.do_action(action);
            });
        },





        create_lines_with_style: function(rec, attr, datas) {
            var temp_str = "";
            var style_name = "border-bottom: 1px solid #e6e6e6;";
            var attr_name = attr + " style="+style_name;

            temp_str += "<td  class='child_col1' "+attr_name+" >"+rec['code'] +rec['name'] +"</td>";
            if(datas.currency[1]=='after'){
            temp_str += "<td  class='child_col2' "+attr_name+" >"+rec['debit'].toFixed(2)+datas.currency[0]+"</td>";
            temp_str += "<td  class='child_col3' "+attr_name+" >"+rec['credit'].toFixed(2) +datas.currency[0]+ "</td>";
            }
            else{
            temp_str += "<td  class='child_col2' "+attr_name+" >"+datas.currency[0]+rec['debit'].toFixed(2) + "</td>";
            temp_str += "<td  class='child_col3' "+attr_name+">"+datas.currency[0]+rec['credit'].toFixed(2) + "</td>";

            }
            return temp_str;
        },


        journal_line_click: function (el){
            click_num++;
            var self = this;
            var line = $(el.target).parent().data('id');
            return self.do_action({
                type: 'ir.actions.act_window',
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: 'account.move',
                    views: [
                        [false, 'form']
                    ],
                    res_id: line,
                    target: 'current',
            });

        },
        format_currency: function(currency, amount) {
                if (typeof(amount) != 'number') {
                    amount = parseFloat(amount);
                }
                var formatted_value = (parseFloat(amount)).toLocaleString('en-SA', {
                 minimumFractionDigits: 2,
                 maximumFractionDigits: 2,
                })
                return formatted_value
            },

        show_drop_down: function(event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
                    var action_title = self._title
                    self._rpc({
                        model: 'account.general.ledger',
                        method: 'view_report',
                        args: [
                            [self.wizard_id], action_title
                        ],
                    }).then(function(data) {
                    _.each(data['report_lines'], function(rep_lines) {
                            _.each(rep_lines['move_lines'], function(move_line) {
                            //     move_line.debit = move_line.debit;
                            // move_line.credit = move_line.credit;
                            // move_line.balance = move_line.balance;

                             move_line.debit = self.format_currency(data['currency'],move_line.debit);
                            move_line.credit = self.format_currency(data['currency'],move_line.credit);
                            move_line.balance = self.format_currency(data['currency'],move_line.balance);


                             });
                             });

                    for (var i = 0; i < data['report_lines'].length; i++) {

                    if (account_id == data['report_lines'][i]['id'] ){

                    $(event.currentTarget).next('tr').find('td .gl-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('SubSection', {
                            account_data: data['report_lines'][i]['move_lines'],
                            currency_symbol : data.currency[0],
                            currency_position : data.currency[1],

                        }))
                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                     }
                    }

                    });
            }
        },

        view_acc_move: function(event) {
            event.preventDefault();
            var self = this;
            var context = {};
            var show_acc_move = function(res_model, res_id, view_id) {
                var action = {
                    type: 'ir.actions.act_window',
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: res_model,
                    views: [
                        [view_id || false, 'form']
                    ],
                    res_id: res_id,
                    target: 'current',
                    context: context,
                };
                return self.do_action(action);
            };
            rpc.query({
                    model: 'account.move',
                    method: 'search_read',
                    domain: [
                        ['id', '=', $(event.currentTarget).data('move-id')]
                    ],
                    fields: ['id'],
                    limit: 1,
                })
                .then(function(record) {
                    if (record.length > 0) {
                        show_acc_move('account.move', record[0].id);
                    } else {
                        show_acc_move('account.move', $(event.currentTarget).data('move-id'));
                    }
                });
        },

        apply_filter: function(event) {

            event.preventDefault();
            var self = this;
            self.initial_render = false;

            var filter_data_selected = {};


            var account_ids = [];
            var account_text = [];

            var account_res = document.getElementById("acc_res")
            var account_list = $(".account").select2('data')
            for (var i = 0; i < account_list.length; i++) {
                if(account_list[i].element[0].selected === true){

                    account_ids.push(parseInt(account_list[i].id))
                    if(account_text.includes(account_list[i].text) === false){
                        account_text.push(account_list[i].text)
                    }
                    account_res.value = account_text
                    account_res.innerHTML=account_res.value;
                }
            }
            if (account_list.length == 0){
               account_res.value = ""
                    account_res.innerHTML="";

            }
            filter_data_selected.account_ids = account_ids



             var journal_ids = [];
            var journal_text = [];
            var journal_res = document.getElementById("journal_res")
            var journal_list = $(".journals").select2('data')

            for (var i = 0; i < journal_list.length; i++) {
                if(journal_list[i].element[0].selected === true){

                    journal_ids.push(parseInt(journal_list[i].id))
                    if(journal_text.includes(journal_list[i].text) === false){
                        journal_text.push(journal_list[i].text)
                    }
                    journal_res.value = journal_text
                    journal_res.innerHTML=journal_res.value;
                }
            }
            if (journal_list.length == 0){
               journal_res.value = ""
                    journal_res.innerHTML="";

            }
            filter_data_selected.journal_ids = journal_ids


            var journal_code_ids = [];
            var journal_code_text = [];
            var journal_code_res = document.getElementById("journal_code_res")
            var journal_code_list = $(".journal_code").select2('data')

            for (var i = 0; i < journal_code_list.length; i++) {
                if(journal_code_list[i].element[0].selected === true){

                    journal_code_ids.push(parseInt(journal_code_list[i].id))
                    if(journal_code_text.includes(journal_code_list[i].text) === false){
                        journal_code_text.push(journal_code_list[i].text)
                    }
                    journal_code_res.value = journal_code_text
                    journal_code_res.innerHTML=journal_code_res.value;
                }
            }
            if (journal_code_list.length == 0){
               journal_code_res.value = ""
                    journal_code_res.innerHTML="";

            }
            filter_data_selected.journal_code_ids = journal_code_ids


            var cost_center_ids = []
            var cost_center_text = [];
            var cost_center_res = document.getElementById("cost_center_res")
            var cost_centers_list = $(".cost_centers").select2('data')

            for (var i = 0; i < cost_centers_list.length; i++) {
                if(cost_centers_list[i].element[0].selected === true){

                    cost_center_ids.push(parseInt(cost_centers_list[i].id))
                    if(cost_center_text.includes(cost_centers_list[i].text) === false){
                        cost_center_text.push(cost_centers_list[i].text)
                    }
                    cost_center_res.value = cost_center_text
                    cost_center_res.innerHTML=cost_center_res.value;
                }
            }
            if (cost_centers_list.length == 0){
               cost_center_res.value = ""
                    cost_center_res.innerHTML="";

            }
            filter_data_selected.cost_center_ids = cost_center_ids


            var budgetary_ids = []
            var budget_text = [];
            var budget_res = document.getElementById("budget_res")
            var budget_list = $(".budgets").select2('data')

            for (var i = 0; i < budget_list.length; i++) {
                if(budget_list[i].element[0].selected === true){

                    budgetary_ids.push(parseInt(budget_list[i].id))
                    if(budget_text.includes(budget_list[i].text) === false){
                        budget_text.push(budget_list[i].text)
                    }
                    budget_res.value = budget_text
                    budget_res.innerHTML=budget_res.value;
                }
            }
            if (budget_list.length == 0){
               budget_res.value = ""
                    budget_res.innerHTML="";

            }
            filter_data_selected.budgetary_ids = budgetary_ids



            var accom_ids = []
            var accom_text = [];
            var accom_res = document.getElementById("accom_res")
            var accom_list = $(".accoms").select2('data')

            for (var i = 0; i < accom_list.length; i++) {
                if(accom_list[i].element[0].selected === true){

                    accom_ids.push(parseInt(accom_list[i].id))
                    if(accom_text.includes(accom_list[i].text) === false){
                        accom_text.push(accom_list[i].text)
                    }
                    accom_res.value = accom_text
                    accom_res.innerHTML=accom_res.value;
                }
            }
            if (accom_list.length == 0){
               accom_res.value = ""
                    accom_res.innerHTML="";

            }
            filter_data_selected.accom_ids = accom_ids



            var asset_ids = []
            var asset_text = [];
            var asset_res = document.getElementById("asset_res")
            var asset_list = $(".assets").select2('data')

            for (var i = 0; i < asset_list.length; i++) {
                if(asset_list[i].element[0].selected === true){

                    asset_ids.push(parseInt(asset_list[i].id))
                    if(asset_text.includes(asset_list[i].text) === false){
                        asset_text.push(asset_list[i].text)
                    }
                    asset_res.value = asset_text
                    asset_res.innerHTML=asset_res.value;
                }
            }
            if (asset_list.length == 0){
               asset_res.value = ""
                    asset_res.innerHTML="";

            }
            filter_data_selected.asset_ids = asset_ids



            var employee_ids = []
            var employee_text = [];
            var employee_res = document.getElementById("employee_res")
            var employee_list = $(".employees").select2('data')

            for (var i = 0; i < employee_list.length; i++) {
                if(employee_list[i].element[0].selected === true){

                    employee_ids.push(parseInt(employee_list[i].id))
                    if(employee_text.includes(employee_list[i].text) === false){
                        employee_text.push(employee_list[i].text)
                    }
                    employee_res.value = employee_text
                    employee_res.innerHTML=employee_res.value;
                }
            }
            if (employee_list.length == 0){
               employee_res.value = ""
                    employee_res.innerHTML="";

            }
            filter_data_selected.employee_ids = employee_ids



            // var site_ids = []
            // var site_text = [];
            // var site_res = document.getElementById("site_res")
            // var site_list = $(".sites").select2('data')

            // for (var i = 0; i < site_list.length; i++) {
            //     if(site_list[i].element[0].selected === true){

            //         site_ids.push(parseInt(site_list[i].id))
            //         if(site_text.includes(site_list[i].text) === false){
            //             site_text.push(site_list[i].text)
            //         }
            //         site_res.value = site_text
            //         site_res.innerHTML=site_res.value;
            //     }
            // }
            // if (site_list.length == 0){
            //    site_res.value = ""
            //         site_res.innerHTML="";

            // }
            // filter_data_selected.site_ids = site_ids





            var analytic_ids = []
            var analytic_text = [];
            var analytic_res = document.getElementById("analytic_res")
            var analytic_list = $(".analytics").select2('data')

            for (var i = 0; i < analytic_list.length; i++) {
                if(analytic_list[i].element[0].selected === true){

                    analytic_ids.push(parseInt(analytic_list[i].id))
                    if(analytic_text.includes(analytic_list[i].text) === false){
                        analytic_text.push(analytic_list[i].text)
                    }
                    analytic_res.value = analytic_text
                    analytic_res.innerHTML=analytic_res.value;
                }
            }
            if (analytic_list.length == 0){
               analytic_res.value = ""
                    analytic_res.innerHTML="";

            }
            filter_data_selected.analytic_ids = analytic_ids

            var analytic_tag_ids = []
            var analytic_tag_text = [];
            var analytic_tag_res = document.getElementById("analytic_tag_res")
            var analytic_tag_list = $(".analytic_tags").select2('data')
            for (var i = 0; i < analytic_tag_list.length; i++) {
                if(analytic_tag_list[i].element[0].selected === true){

                    analytic_tag_ids.push(parseInt(analytic_tag_list[i].id))
                    if(analytic_tag_text.includes(analytic_tag_list[i].text) === false){
                        analytic_tag_text.push(analytic_tag_list[i].text)
                    }
                    analytic_tag_res.value = analytic_tag_text
                    analytic_tag_res.innerHTML=analytic_tag_res.value;
                }
            }
            if (analytic_tag_list.length == 0){
               analytic_tag_res.value = ""
                    analytic_tag_res.innerHTML="";

            }
            filter_data_selected.analytic_tag_ids = analytic_tag_ids

            if ($("#date_from").val()) {

                var dateString = $("#date_from").val();
                filter_data_selected.date_from = dateString;
            }
            if ($("#date_to").val()) {
                var dateString = $("#date_to").val();
                filter_data_selected.date_to = dateString;
            }

            if ($(".target_move").length) {
            var post_res = document.getElementById("post_res")
            filter_data_selected.target_move = $(".target_move")[1].value
            post_res.value = $(".target_move")[1].value
                    post_res.innerHTML=post_res.value;
              if ($(".target_move")[1].value == "") {
              post_res.innerHTML="posted";

              }
            }
            rpc.query({
                model: 'account.general.ledger',
                method: 'write',
                args: [
                    self.wizard_id, filter_data_selected
                ],
            }).then(function(res) {
            self.initial_render = false;
                self.load_data(self.initial_render);
            });
        },

    });
    core.action_registry.add("g_l", GeneralLedger);
    return GeneralLedger;
});