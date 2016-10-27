# -*- coding: utf-8 -*-
###############################################################################
#
#   colocation_tools for OpenERP
#   Copyright (C) 2013 Akretion (http://www.akretion.com). All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import fields, api, models, _
from openerp.exceptions import Warning as UserError


class ExpenseBalance(models.TransientModel):
    _name = "expense.balance"
    _description="Expense Balance"

    @api.model
    def _get_default_month(self):
        expense_obj = self.env['coloc.expense']
        month=False
        if self._context.get('active_ids'):
            expense = expense_obj.browse(self._context['active_ids'][0])
            month = expense.month
        return month

    @api.model
    def _get_default_participants(self):
        expense_obj = self.env['coloc.expense']
        participant_ids = []
        if self._context.get('active_ids'):
            for expense in expense_obj.browse(self._context['active_ids']):
                if not expense.partner_id.id in participant_ids:
                    participant_ids.append(expense.partner_id.id)
                for concerned_partner in expense.concerned_partner_ids:
                    if not concerned_partner.id in participant_ids:
                        participant_ids.append(concerned_partner.id)
        return participant_ids

    participant_ids = fields.Many2many(
        'res.partner',
        'expense_balance_partner_rel',
        'balance_id',
        'partner_id',
        'Partners',
        default= _get_default_participants)
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')],
        'Month',
        default=_get_default_month)

    @api.model
    def _prepare_partner_balance(self, expense_ids, month, attendance, partner_ids, total_attendance):
        expense_obj = self.env['coloc.expense']
        normal_amount = 0.0
        prop_amount = 0.0
        partner_balances = {}
        for partner_id in partner_ids:
            partner_balances[partner_id] = {'total_paid': 0.0,
                                            'total_owe': 0.0}
        for expense in expense_obj.browse(expense_ids):
            if expense.month != month:
                raise UserError(_('Keyboard/Chair error'),
                                _('All the expenses should be from the '
                                  'same month, you stupid fuck!'))
            partner_id = expense.partner_id.id
            partner_balances[partner_id]['total_paid'] += expense.amount
            if expense.product_id.expense_type == 'courses':
                prop_amount += expense.amount
                for concerned_partner in expense.concerned_partner_ids:
                    partner_balances[concerned_partner.id]['total_owe'] += expense.amount*(attendance[concerned_partner.id]/total_attendance)
            else:
                normal_amount += expense.amount
                nb_concerned = len(expense.concerned_partner_ids)
                for concerned_partner in expense.concerned_partner_ids:
                    partner_balances[concerned_partner.id]['total_owe'] += expense.amount/nb_concerned
        return normal_amount, prop_amount, partner_balances

    @api.model
    def _prepare_attendance(self, partner_ids, month):
        attendance_obj = self.env['meal.attendance']
        attendance_ids = attendance_obj.search(
            [('partner_id', 'in', partner_ids), ('month', '=', month)])
        if not attendance_ids:
            raise UserError(_('Keyboard/Chair error'),
                            _('You have to set up attendance for this '
                              'month, you stupid fuck!'))

        partner_attendance = {}
        total_attendance = 0
        for attendance in attendance_ids:
            total_attendance += attendance.meal_qty
            partner_attendance[attendance.partner_id.id] = attendance.meal_qty
        return total_attendance, partner_attendance

    @api.model
    def _get_exactmatch_transactions(self, partner_balances):
        transactions = []
        done_partner_ids = []
        for partner_id, totals in partner_balances.iteritems():
            if partner_id in done_partner_ids:
                continue
            partner_balance = totals['total_paid']-totals['total_owe']
            partner_balance_format = abs(round(partner_balance, 3))
            for other_partner_id, other_totals in partner_balances.iteritems():
                other_partner_balance = other_totals['total_paid']-other_totals['total_owe']
                other_partner_balance_format = abs(round(other_partner_balance, 3))
                if other_partner_id != partner_id and partner_balance_format == other_partner_balance_format:
                    if partner_balance > 0:
                        ower = other_partner_id
                        receiver = partner_id
                    else:
                        ower = partner_id
                        receiver = other_partner_id
                    transactions.append((0, 0, {
                        'ower_id': ower,
                        'receiver_id': receiver,
                        'amount': abs(partner_balance)}))
                    done_partner_ids += [partner_id, other_partner_id]
        return transactions, done_partner_ids

    @api.model
    def _get_transactions(self, partner_balances):
        transactions, done_partner_ids = self._get_exactmatch_transactions(
            partner_balances)
        for partner_id in done_partner_ids:
            del partner_balances[partner_id]
        return transactions

    @api.multi
    def calculate_expense_balance(self):
        self.ensure_one()
        expense_obj = self.env['coloc.expense']
        result_obj = self.env['balance.result']
        partner_obj = self.env['res.partner']
        month = self.month
        partner_ids = self.participant_ids.ids
        total_attendance, partner_attendance = self._prepare_attendance(
            partner_ids, month)
        normal_amount, prop_amount, partner_balances = self._prepare_partner_balance(
            self._context['active_ids'], month, partner_attendance,
            partner_ids, total_attendance)
        normal_average = normal_amount/len(partner_ids)
        prop_average = prop_amount/total_attendance
        balance_ids = []
        for partner_id, totals in partner_balances.iteritems():
            balance_ids.append((0, 0,
                {'partner_id': partner_id,
                 'total_paid': totals['total_paid'],
                 'total_owe': totals['total_owe']}))

        transactions = self._get_transactions(partner_balances)
        synthesis = ''
        for transaction in transactions:
            amount = round(transaction[2]['amount'], 2)
            ower = partner_obj.browse(
                transaction[2]['ower_id']).name
            receiver = partner_obj.browse(
                transaction[2]['receiver_id']).name
            synthesis = u'%s doit %s€ à %s\n' %(ower, amount, receiver)
        result = {
            'total_paid': normal_amount + prop_amount,
            'month': month,
            'normal_average': normal_average,
            'prop_total': prop_amount,
            'prop_average': prop_average,
            'partner_balance_ids': balance_ids,
            'transaction_ids': transactions,
            'synthesis': synthesis,
            }
        balance_id = result_obj.create(result).id
        expense_obj.browse(self._context['active_ids']).write({'balance_id': balance_id})
        view_id = self.env.ref('colocation_expenses.balance_result_form_view').id
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain' : "[('month','=',%s)]" % (month),
            'res_model': 'balance.result',
            'res_id': balance_id,
            'type': 'ir.actions.act_window',
             }

