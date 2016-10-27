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
from datetime import date

MONTH = [('1', 'January'),
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
         ('12', 'December')]


class ColocExpense(models.Model):
    _name = "coloc.expense"
    _description="Coloc Expenses"

    _order = "month desc, create_date desc"

    @api.model
    def _get_default_month(self):
        return str(date.today().month)

    @api.model
    def _get_default_partner(self):
        partner = None
        if self.env.user.id != 1:
            partner = self.env.user.partner_id
        return partner

    @api.model
    def _get_default_concerned_partners(self):
        return self.env.user.company_id.flatmate_ids.ids

    @api.depends('balance_id')
    @api.multi
    def _get_balanced(self):
        for expense in self:
            if expense.balance_id:
                expense.balanced = True
            else:
                expense.balanced = False

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain="[('colocation_type', '=', 'expense')]")
    create_date = fields.Datetime('Create date')
    amount = fields.Float(
        string='Amount',
        required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        default=_get_default_partner,
        required=True)
    comment = fields.Char('Comment', size=128)
    month = fields.Selection(
        MONTH,
        'Month',
        default=_get_default_month,
        required=True)
    balance_id = fields.Many2one(
        comodel_name='balance.result',
        string='Balance result')
    balanced = fields.Boolean(
        compute='_get_balanced',
        string='Balanced',
        store=True)
    concerned_partner_ids = fields.Many2many(
        'res.partner',
        'expense_partner_rel',
        'expense_id',
        'partner_id',
        'Concerned Partners',
        default=_get_default_concerned_partners,
        required=True)

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.balance_id:
                raise UserError(_('Keyboard/Chair error'),
                                _("You can't delete and expense already "
                                  "balanced, you stupid fuck!"))
        return super(ColocExpense, self).unlink()


class MealAttendance(models.Model):
    _name="meal.attendance"
    _description="Meal attendance"

    _order = "month desc"

    @api.model
    def _get_default_month(self):
        return str(date.today().month)

    partner_id = fields.Many2one('res.partner', string="Partner")
    meal_qty = fields.Float('Meal quantity')
    write_date = fields.Datetime('Write date')
    month = fields.Selection(
        MONTH,
        'month',
        default=_get_default_month)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('month_partner_uniq',
         'unique(month, partner_id)',
         'Balance has to be uniq per partner and per month!'),
    ]

    @api.multi
    def add_meal_attendance(self):
        month = str(date.today().month)
        for attendance in self:
            if month != attendance.month:
                raise UserError(_('Keyboard/Chair error'),
                                _("You try to add an attendance of "
                                  "another month, you stupid fuck!"))
            attendance.meal_qty += 1
        return True

    @api.multi
    def remove_meal_attendance(self):
        month = str(date.today().month)
        for attendance in self:
            if month != attendance.month:
                raise UserError(_('Keyboard/Chair error'),
                                _("You try to add an attendance of "
                                  "another month, you stupid fuck!"))
            attendance.meal_qty -= 1
        return True


class BalanceResult(models.Model):
    _name = "balance.result"
    _description = "Balance Result"

    _rec_name = "month"
    
#    def _get_name(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for balance in self.browse(cr, uid, ids, context=context):
#            res[balance.id] = _(dict(MONTH).get(balance.month, ''))
#        return res


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
    total_paid = fields.Float('Total paid')
    month = fields.Selection(
        MONTH,
        'Month')
    normal_average = fields.Float('Normal average')
    prop_total = fields.Float('Total proportional')
    prop_average = fields.Float('Proportional average')
    partner_balance_ids = fields.One2many(
       'partner.balance',
       'balance_id',
       'Partner balance')
    transaction_ids = fields.One2many(
       'balance.transaction',
       'balance_id',
       'Transactions')
    synthesis = fields.Text('Synthesis')
    state = fields.Selection(
       [('to_pay', 'To Pay'), ('paid', 'Paid')],
       'State',
       default='to_pay')
    payment_method = fields.Char(
        'Payment Method',
        size=128,
        help="Way to pay the balance result")

    _sql_constraints = [
        ('month_uniq', 'unique(month)', 'Balance has to be uniq per month!'),
    ]

    @api.multi
    def pay_balance(self):
        return self.write({'state': 'paid'})

    @api.multi
    def unlink(self):
        for result in self:
            if result.state == 'paid':
                raise UserError(_('Keyboard/Chair error'),
                                _("You can't delete a balance result that "
                                  "have already been paid, you stupid fuck!"))
        return super(BalanceResult, self).unlink()


class PartnerBalance(models.Model):
    _name = "partner.balance"
    _description = "Partner balance"

    balance_id = fields.Many2one(
        'balance.result',
        'Balance',
        ondelete="cascade")
    partner_id = fields.Many2one('res.partner', 'Partner')
    total_owe = fields.Float('Total owe')
    total_paid = fields.Float('Total paid')


class BalanceTransaction(models.Model):
    _name = "balance.transaction"
    _description = "Balance transaction"

    balance_id = fields.Many2one(
        'balance.result',
        'Balance',
        ondelete="cascade")
    ower_id = fields.Many2one('res.partner', 'Ower')
    receiver_id = fields.Many2one('res.partner', 'Receiver')
    amount = fields.Float('Amount')


class AutomaticExpense(models.Model):
    _name = "automatic.expense"
    _description = "Automatic Expenses"

    partner_id = fields.Many2one(
        'res.partner',
        'Partner',
        required=True)
    product_id = fields.Many2one(
        'product.product',
        'Product',
        required=True)
    amount = fields.Float(
        'Amount',
        required=True)
    active = fields.Boolean('Active', default=True)
    concerned_partner_ids = fields.Many2many(
        'res.partner',
        'expense_partner_rel',
        'expense_id',
        'partner_id',
        'Concerned Partners',
        required=True)

    @api.model
    def automatic_expense_scheduler(self):
        expense_obj = self.env['coloc.expense']
        month = str(date.today().month)
        for auto_expense in self.search([]):
            expense = expense_obj.search([
                ('month', '=', month),
                ('partner_id', '=', auto_expense.partner_id.id),
                ('product_id', '=', auto_expense.product_id.id),
                ('amount', '=', auto_expense.amount)])
            if not expense:
                concerned_ids = []
                for partner in auto_expense.concerned_partner_ids:
                    concerned_ids.append(partner.id)
                vals = {
                    'month': month,
                    'partner_id': auto_expense.partner_id.id,
                    'product_id': auto_expense.product_id.id,
                    'amount': auto_expense.amount,
                    'concerned_partner_ids': [(6, 0, concerned_ids)]
                    }
                expense_obj.create(vals)
        return True
