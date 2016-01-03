# -*- coding: utf-8 -*-
###############################################################################
#
#   base_colocation_tools for OpenERP
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


class product_product(orm.Model):
    _inherit="product.product"

    def _get_colocation_type(self, cr, uid, context=None):
        return []

    def __get_colocation_type(self, cr, uid, context=None):
        return self._get_colocation_type(cr, uid, context=context)

    _columns = {
        'colocation_type': fields.selection(
            __get_colocation_type,
            'Colocation type'),
        }

