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

class expense_balance(orm.Model):
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

    _columns = {
#        'participant_ids': fields.many2many(
#            'res.partner',
#            'expense_balance_partner_rel',
#            'balance_id',
#            'partner_id',
#            'Partners'),
        'month': fields.selection(
            [('1', 'January'),
             ('2', 'February'),
             ('3', 'March'),
             ('5', 'April'),
             ('6', 'June'),
             ('7', 'July'),
             ('8', 'August'),
             ('9', 'Septembre'),
             ('10', 'October'),
             ('11', 'November'),
             ('12', 'December')],
            'Month'),
    }

    _defaults={
        'month': _get_default_month,
        }

    def calculate_expense_balance(self, cr, uid, id, context=None):
        expense_obj = self.pool['coloc.expense']
        attendance_obj = self.pool['meal.attendance']
        result_obj = self.pool['balance.result']
        model_data_obj = self.pool['ir.model.data']
        wizard = self.browse(cr, uid, id, context=context)[0]
        month = wizard.month
        normal_amount = 0.0
        proportional_amount = 0.0
        partner_expense = {}
        for expense in expense_obj.browse(cr, uid, context['active_ids'], context=context):
            if expense.month != month:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _('All the expenses should be from the '
                                       'same month, you stupid fuck!'))
            partner_id = expense.partner_id.id
            if not partner_id in partner_expense.keys():
                partner_expense[partner_id] = {'normal_amount': 0.0,
                                               'proportional_amount': 0.0}
            if expense.product_id.coloc_type == 'courses':
                proportional_amount += expense.amount
                partner_expense[partner_id]['proportional_amount'] += expense.amount
            else:
                normal_amount += expense.amount
                partner_expense[partner_id]['normal_amount'] += expense.amount
        attendance_ids = attendance_obj.search(
            cr, uid, [('partner_id', 'in', partner_expense.keys()),
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
        normal_average = normal_amount/len(partner_expense.keys())
        prop_average = proportional_amount/total_attendance
        partner_balances = []
        balance_ids = []
        for partner_id, expenses in partner_expense.iteritems():
            if not partner_id in partner_attendance:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _('You have to set up attendance for all '
                                       'partners, you stupid fuck!'))
            partner_normal = normal_average - expenses['normal_amount']
            partner_prop = (prop_average*partner_attendance[partner_id]) - expenses['proportional_amount']
            partner_balance = partner_normal + partner_prop
            partner_balances.append({
                'partner_id': partner_id,
                'partner_balance': partner_balance})
            balance_ids.append((0, 0, {
                'partner_id': partner_id,
                'amount': partner_balance}))
        transaction_ids = []
        for balance in partner_balances:
            todel = False
            partner_balance = abs(round(balance['partner_balance'], 3))
            for other_balance in partner_balances:
                other_partner_balance = abs(round(other_balance['partner_balance'], 3))
                if other_balance['partner_id'] != balance['partner_id'] and partner_balance == other_partner_balance:
                    if balance['partner_balance'] > 0:
                        ower = balance['partner_id']
                        receiver = other_balance['partner_id']
                    else:
                        ower = other_balance['partner_id']
                        receiver = balance['partner_id']
                    transaction_ids.append((0, 0, {
                        'ower_id': ower,
                        'receiver_id': receiver,
                        'amount': abs(balance['partner_balance'])}))
                    todel = True
            if todel:
                del partner_balances[0]
        result = {
            'total_paid': normal_amount + proportional_amount,
            'month': month,
            'normal_average': normal_average,
            'prop_average': prop_average,
            'partner_balance_ids': balance_ids,
            'transaction_ids': transaction_ids,
            }
        balance_id = result_obj.create(cr, uid, result, context=context)
        model, view_id = model_data_obj.get_object_reference(
            cr, uid, 'colocation_tools', 'balance_result_form_view')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain' : "[('month','=',%s)]" % (month),
            'res_model': 'balance.result',
            'res_id': balance_id,
            'type': 'ir.actions.act_window',
             }

