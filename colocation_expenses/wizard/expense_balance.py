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
from openerp.osv import fields, orm
from openerp.tools.translate import _


class expense_balance(orm.TransientModel):
    _name = "expense.balance"
    _description="Expense Balance"

    def _get_default_month(self, cr, uid, context=None):
        expense_obj = self.pool['coloc.expense']
        month=False
        if context.get('active_ids'):
            expense = expense_obj.read(cr, uid, context['active_ids'][0],
                                       ['month'], context=context)
            month = expense['month']
        return month

    def _get_default_participants(self, cr, uid, context=None):
        expense_obj = self.pool['coloc.expense']
        participant_ids = []
        if context.get('active_ids'):
            for expense in expense_obj.read(cr, uid, context['active_ids'], ['partner_id'], context=context):
                if not expense['partner_id'][0] in participant_ids:
                    participant_ids.append(expense['partner_id'][0])
        return participant_ids


    _columns = {
        'participant_ids': fields.many2many(
            'res.partner',
            'expense_balance_partner_rel',
            'balance_id',
            'partner_id',
            'Partners'),
        'month': fields.selection(
            [('1', 'January'),
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
            'Month'),
    }

    _defaults={
        'month': _get_default_month,
        'participant_ids': _get_default_participants,
        }

    def _prepare_partner_balance(self, cr, uid, ids, month, attendance, partner_ids, total_attendance, context=None):
        expense_obj = self.pool['coloc.expense']
        normal_amount = 0.0
        prop_amount = 0.0
        partner_balances = {}
        for partner_id in partner_ids:
            partner_balances[partner_id] = {'total_paid': 0.0,
                                            'total_owe': 0.0}
        for expense in expense_obj.browse(cr, uid, ids, context=context):
            if expense.month != month:
                raise orm.except_orm(_('Keyboard/Chair error'),
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

    def _prepare_attendance(self, cr, uid, partner_ids, month, context=None):
        attendance_obj = self.pool['meal.attendance']
        attendance_ids = attendance_obj.search(
            cr, uid, [('partner_id', 'in', partner_ids),
                      ('month', '=', month)],
            context=context)
        if not attendance_ids:
            raise orm.except_orm(_('Keyboard/Chair error'),
                                 _('You have to set up attendance for this '
                                   'month, you stupid fuck!'))

        partner_attendance = {}
        total_attendance = 0
        for attendance in attendance_obj.browse(cr, uid, attendance_ids, context=context):
            total_attendance += attendance.meal_qty
            partner_attendance[attendance.partner_id.id] = attendance.meal_qty
        return total_attendance, partner_attendance

    def _get_exactmatch_transactions(self, cr, uid, partner_balances, context=None):
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

    def _get_transactions(self, cr, uid, partner_balances, context=None):
        transactions, done_partner_ids = self._get_exactmatch_transactions(
            cr, uid, partner_balances, context=context)
        for partner_id in done_partner_ids:
            del partner_balances[partner_id]
        return transactions

    def calculate_expense_balance(self, cr, uid, id, context=None):
        expense_obj = self.pool['coloc.expense']
        result_obj = self.pool['balance.result']
        model_data_obj = self.pool['ir.model.data']
        partner_obj = self.pool['res.partner']
        wizard = self.browse(cr, uid, id, context=context)[0]
        month = wizard.month
        partner_ids = [x.id for x in wizard.participant_ids]
        total_attendance, partner_attendance = self._prepare_attendance(
            cr, uid, partner_ids, month, context=context)
        normal_amount, prop_amount, partner_balances = self._prepare_partner_balance(
            cr, uid, context['active_ids'], month, partner_attendance,
            partner_ids, total_attendance, context=context)
        normal_average = normal_amount/len(partner_ids)
        prop_average = prop_amount/total_attendance
        balance_ids = []
        for partner_id, totals in partner_balances.iteritems():
            balance_ids.append((0, 0,
                {'partner_id': partner_id,
                 'total_paid': totals['total_paid'],
                 'total_owe': totals['total_owe']}))

        transactions = self._get_transactions(cr, uid, partner_balances,
                                             context=context)
        synthesis = ''
        for transaction in transactions:
            amount = round(transaction[2]['amount'], 2)
            ower = partner_obj.read(cr, uid,
                                    transaction[2]['ower_id'],
                                    ['name'],
                                    context=context)['name']
            receiver = partner_obj.read(cr, uid,
                                        transaction[2]['receiver_id'],
                                        ['name'],
                                        context=context)['name']
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
        balance_id = result_obj.create(cr, uid, result, context=context)
        expense_obj.write(cr, uid,
            context['active_ids'],
            {'balance_id': balance_id},
            context=context)
        model, view_id = model_data_obj.get_object_reference(
            cr, uid, 'colocation_expenses', 'balance_result_form_view')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain' : "[('month','=',%s)]" % (month),
            'res_model': 'balance.result',
            'res_id': balance_id,
            'type': 'ir.actions.act_window',
             }

