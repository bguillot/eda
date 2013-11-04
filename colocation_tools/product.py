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


class coloc_expense(orm.Model):
    _name = "coloc.expense"
    _description="Coloc Expenses"

    def _get_default_month(self, cr, uid, context=None):
        return str(date.today().month)

    _columns={
        'product_id': fields.many2one('product.product', string="Produit"),
        'create_date': fields.datetime('Create date'),
        'amount': fields.float('amount'),
        'partner_id': fields.many2one('res.partner', string="Partner"),
        'comment': fields.char('Comment', size=128),
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
        'month': _get_default_month
        }


class meal_attendance(orm.Model):
    _name="meal.attendance"
    _description="Meal attendance"

    def _get_default_month(self, cr, uid, context=None):
        return str(date.today().month)

    _columns={
        'partner_id': fields.many2one('res.partner', string="Partner"),
        'meal_qty': fields.float('Meal quantity'),
        'write_date': fields.datetime('Write date'),
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
            'month'),
        'color': fields.integer('Color Index'),
        }

    _defaults={
        'month': _get_default_month
        }

    _sql_constraints = [
        ('month_partner__uniq',
         'unique(month, partner_id)',
         'Balance has to be uniq per partner and per month!'),
    ]


    def add_meal_attendance(self, cr, uid, ids, context=None):
        for attendance in self.browse(cr, uid, ids, context=context):
            attendance.write({'meal_qty': attendance.meal_qty + 1})
        return True

    def remove_meal_attendance(self, cr, uid, ids, context=None):
        for attendance in self.browse(cr, uid, ids, context=context):
            attendance.write({'meal_qty': attendance.meal_qty - 1})
        return True


class product_product(orm.Model):
    _inherit="product.product"

    _columns={
        'coloc_type': fields.selection(
            [('courses', 'Courses'),
             ('fournitures', 'Fournitures'),
             ('charges', 'Charges'),
             ('autres', 'Autres')],
            'Coloc type')
        }


class balance_result(orm.Model):
    _name = "balance.result"
    _description = "Balance Result"

    _columns={
        'total_paid': fields.float('Total paid'),
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
            'month'),
        'normal_average': fields.float('Normal average'),
        'prop_average': fields.float('Proportional average'),
        'partner_balance_ids': fields.one2many(
            'partner.balance',
            'balance_id',
            'Partner balance'),
        'transaction_ids': fields.one2many(
            'balance.transaction',
            'balance_id',
            'Transactions'),
        }

    _sql_constraints = [
        ('month_uniq', 'unique(month)', 'Balance has to be uniq per month!'),
    ]


class partner_balance(orm.Model):
    _name = "partner.balance"
    _description = "Partner balance"

    _columns={
        'balance_id': fields.many2one('balance.result', 'Balance'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'amount': fields.float('Amount'),
        }


class balance_transaction(orm.Model):
    _name = "balance.transaction"
    _description = "Balance transaction"

    _columns={
        'balance_id': fields.many2one('balance.result', 'Balance'),
        'ower_id': fields.many2one('res.partner', 'Ower'),
        'receiver_id': fields.many2one('res.partner', 'Receiver'),
        'amount': fields.float('Amount'),
        'dummy1': fields.char('owe', size=16),
        'dummy2': fields.char('to', size=16),
        }

    _defaults={
        'dummy1': 'owe',
        'dummy2': 'to',
    }
