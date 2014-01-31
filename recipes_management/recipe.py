# -*- coding: utf-8 -*-
###############################################################################
#
#   recipes_management for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com). All Rights Reserved
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


class mrp_bom(orm.Model):
    _inherit = "mrp.bom"

    _columns = {
        'last_date_done': fields.date('Last date done'),
        'season': fields.selection([
            ('summer', 'Summer'),
            ('spring', 'Spring'),
            ('winter', 'Winter'),
            ('autumn', 'Autumn')], 'Season'),
        'difficulty': fields.selection([
            ('very_high', 'Very high'),
            ('high', 'High'),
            ('middle', 'Middle'),
            ('low', 'Low'),
            ('very_low', 'Very Low')],
            'Difficulty/time',
            required=True),
        'image': fields.binary('Image'),
    }


class product_product(orm.Model):
    _inherit = "product.product"

    _columns = {
        'recipe': fields.boolean('Recipe'),
        }


class product_template(orm.Model):
    _inherit = "product.template"

    def _get_uom_id(self, cr, uid, context=None):
        data_obj = self.pool['ir.model.data']
        uom_id = 1
        if context is None:
            context={}
        if context.get('force_product_uom'):
            uom_id = data_obj.get_object_reference(
                cr, uid, 'recipes_management', context['force_product_uom'])[1]
        return uom_id

    _defaults = {
        'uom_id': _get_uom_id,
        }
