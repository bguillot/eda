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
from datetime import datetime, date
from openerp.tools.translate import _

MONTH = [('1', 'January'),
         ('2', 'February'),
         ('3', 'March'),
         ('5', 'April'),
         ('6', 'June'),
         ('7', 'July'),
         ('8', 'August'),
         ('9', 'September'),
         ('10', 'October'),
         ('11', 'November'),
         ('12', 'December')]


class coloc_expense(orm.Model):
    _name = "coloc.expense"
    _description="Coloc Expenses"

    def _get_default_month(self, cr, uid, context=None):
        return str(date.today().month)

    def _get_default_partner(self, cr, uid, context=None):
        partner_id = False
        user_obj = self.pool['res.users']
        if uid != 1:
            partner_id = user_obj.read(cr, uid, uid, ['partner_id'],
                                       context=context)['partner_id'][0]
        return partner_id

    def _get_default_concerned_partners(self, cr, uid, context=None):
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        partners = user.company_id.flatmate_ids
        partner_ids  = [x.id for x in partners]
        return partner_ids

    def _get_balanced(self, cr, uid, ids, name, args, context=None):
        res = {}
        for expense in self.browse(cr, uid, ids, context=context):
            if expense.balance_id:
                res[expense.id] = True
            else:
                res[expense.id] = False
        return res

    _columns={
        'product_id': fields.many2one(
            'product.product',
            'Product',
            domain="[('type', '=', 'expense')]"),
        'create_date': fields.datetime('Create date'),
        'amount': fields.float(
            'Amount',
            required=True),
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            required=True),
        'comment': fields.char('Comment', size=128),
        'month': fields.selection(
            MONTH,
            'Month',
            required=True),
        'balance_id': fields.many2one('balance.result', 'Balance result'),
        'balanced': fields.function(
            _get_balanced,
            string='Balanced',
            type='boolean',
            store={
                'coloc.expense':
                    (lambda self, cr, uid, ids, c=None:
                        ids,
                        ['balance_id'],
                        10),
                }),
        'concerned_partner_ids': fields.many2many(
            'res.partner',
            'expense_partner_rel',
            'expense_id',
            'partner_id',
            'Concerned Partners',
            required=True),
        }

    _defaults={
        'month': _get_default_month,
        'partner_id': _get_default_partner,
        'concerned_partner_ids': _get_default_concerned_partners,
        }

    def unlink(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=context):
            if expense.balance_id:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _("You can't delete and expense already "
                                    "balanced, you stupid fuck!"))
        return super(coloc_expense, self).unlink(cr, uid, ids, context=context)


class meal_attendance(orm.Model):
    _name="meal.attendance"
    _description="Meal attendance"

    _order = "month asc"

    def _get_default_month(self, cr, uid, context=None):
        return str(date.today().month)

    _columns={
        'partner_id': fields.many2one('res.partner', string="Partner"),
        'meal_qty': fields.float('Meal quantity'),
        'write_date': fields.datetime('Write date'),
        'month': fields.selection(
            MONTH,
            'month'),
        'color': fields.integer('Color Index'),
        }

    _defaults={
        'month': _get_default_month
        }

    _sql_constraints = [
        ('month_partner_uniq',
         'unique(month, partner_id)',
         'Balance has to be uniq per partner and per month!'),
    ]

    def add_meal_attendance(self, cr, uid, ids, context=None):
        month = str(date.today().month)
        for attendance in self.browse(cr, uid, ids, context=context):
            if month != attendance.month:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _("You try to add an attendance of "
                                       "another month, you stupid fuck!"))
            attendance.write({'meal_qty': attendance.meal_qty + 1})
        return True

    def remove_meal_attendance(self, cr, uid, ids, context=None):
        month = str(date.today().month)
        for attendance in self.browse(cr, uid, ids, context=context):
            if month != attendance.month:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _("You try to add an attendance of "
                                       "another month, you stupid fuck!"))
            attendance.write({'meal_qty': attendance.meal_qty - 1})
        return True


class balance_result(orm.Model):
    _name = "balance.result"
    _description = "Balance Result"

    _rec_name = "month"
    
#    def _get_name(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for balance in self.browse(cr, uid, ids, context=context):
#            res[balance.id] = _(dict(MONTH).get(balance.month, ''))
#        return res


    _columns={
#        'name': fields.function(
#            _get_name,
#            type='char',
#            size=32,
#            string='Name',
#            store={
#                'balance.result':
#                    (lambda self, cr, uid, ids, c=None:
#                        ids,
#                        ['month'],
#                        10),
#                }),
        'total_paid': fields.float('Total paid'),
        'month': fields.selection(
            MONTH,
            'Month'),
        'normal_average': fields.float('Normal average'),
        'prop_total': fields.float('Total proportional'),
        'prop_average': fields.float('Proportional average'),
        'partner_balance_ids': fields.one2many(
            'partner.balance',
            'balance_id',
            'Partner balance'),
        'transaction_ids': fields.one2many(
            'balance.transaction',
            'balance_id',
            'Transactions'),
        'synthesis': fields.text('Synthesis'),
        'state': fields.selection(
            [('to_pay', 'To Pay'), ('paid', 'Paid')],
            'State'),
        'payment_method': fields.char(
            'Payment Method',
            size=128,
            help="Way to pay the balance result"),
        }

    _defaults = {
        'state': 'to_pay',
        }

    _sql_constraints = [
        ('month_uniq', 'unique(month)', 'Balance has to be uniq per month!'),
    ]

    def pay_balance(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'paid'}, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for result in self.browse(cr, uid, ids, context=context):
            if result.state == 'paid':
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _("You can't delete a balance result that "
                                     "have already been paid, you stupid fuck!"))
        return super(balance_result, self).unlink(cr, uid, ids, context=context)


class partner_balance(orm.Model):
    _name = "partner.balance"
    _description = "Partner balance"

    _columns={
        'balance_id': fields.many2one(
            'balance.result',
            'Balance',
            ondelete="cascade"),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'total_owe': fields.float('Total owe'),
        'total_paid': fields.float('Total paid'),
        }


class balance_transaction(orm.Model):
    _name = "balance.transaction"
    _description = "Balance transaction"

    _columns={
        'balance_id': fields.many2one(
            'balance.result',
            'Balance',
            ondelete="cascade"),
        'ower_id': fields.many2one('res.partner', 'Ower'),
        'receiver_id': fields.many2one('res.partner', 'Receiver'),
        'amount': fields.float('Amount'),
        }

class automatic_expense(orm.Model):
    _name = "automatic.expense"
    _description = "Automatic Expenses"

    _columns = {
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            required=True),
        'product_id': fields.many2one(
            'product.product',
            'Product',
            required=True),
        'amount': fields.float(
            'Amount',
            required=True),
        'active': fields.boolean('Active'),
        }

    _defaults = {
        'active': True,
        }

    def automatic_expense_scheduler(self, cr, uid, context=None):
        expense_obj = self.pool['coloc.expense']
        ids = self.search(cr, uid, [], context=context)
        month = str(date.today().month)
        for auto_expense in self.browse(cr, uid, ids, context=context):
            expense_id = expense_obj.search(cr, uid,
                                            [('month', '=', month),
                                             ('partner_id', '=', auto_expense.partner_id.id),
                                             ('product_id', '=', auto_expense.product_id.id),
                                             ('amount', '=', auto_expense.amount)],
                                            context=context)
            if not expense_id:
                vals = {
                    'month': month,
                    'partner_id': auto_expense.partner_id.id,
                    'product_id': auto_expense.product_id.id,
                    'amount': auto_expense.amount,
                    }
                expense_obj.create(cr, uid, vals, context=context)
        return True
