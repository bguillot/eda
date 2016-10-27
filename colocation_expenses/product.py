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

from openerp import fields, models, api


class ProductProduct(models.Model):
    _inherit="product.product"

    @api.model
    def _get_default_colocation_type(self):
        colocation_type = ''
        if self._context.get('force_colocation_type'):
            colocation_type = self._context['force_colocation_type']
        return colocation_type

    colocation_type = fields.Selection(
        selection_add=[('expense', 'Expense')],
        default=_get_default_colocation_type)
    expense_type = fields.Selection(
        selection=[('courses', 'Courses'),
            ('fournitures', 'Fournitures'),
            ('charges', 'Charges'),
            ('autres', 'Autres')],
        string='Expense type')


