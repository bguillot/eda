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


class product_template(orm.Model):
    _inherit="product.template"

    _columns = {
        'type': fields.selection(
            [('product','Stockable Product'),
             ('consu', 'Consumable'),
             ('service','Service'),
             ('expense', 'Expense')],
            'Product Type',
            required=True,
            help="Consumable: Will not imply stock management for this product."
            "\nStockable product: Will imply stock management for this product."
            "\nExpense: Used for colocation expenses."),
        }

    def _get_default_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        product_type = 'consu'
        if context.get('force_type'):
            product_type = context['force_type']
        return product_type

    _defaults = {
        'type': _get_default_type,
        }

class product_product(orm.Model):
    _inherit="product.product"

    _columns={
        'expense_type': fields.selection(
            [('courses', 'Courses'),
             ('fournitures', 'Fournitures'),
             ('charges', 'Charges'),
             ('autres', 'Autres')],
            'Expense type'),
        }
