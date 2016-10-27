# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
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
import math

_BAGGAGE_AGE = [('baby', 'Baby'),
                ('child', 'Child'),
                ('stupid_teenager', 'Stupid teenager'),
                ('adult', 'Adult'),
                ('veteran', 'Veteran'),
                ('ancesters', 'Ancester')]


class destination_tag(orm.Model):
    _name = "destination.tag"
    _description = "Destination Tag"

    _columns = {
        'name': fields.char('Name', required=True),
        'tag_type': fields.selection([('activity', 'Activity')], string='Type'),
        }

    _sql_constraints = [('name_uniq', 'unique(name)',
                        'Destination tag must be unique. You stupid fuck!')]


class trip_destination(orm.Model):
    _name = "trip.destination"
    _description = "Trip Destination"

    _columns = {
        'name': fields.char('Name', required=True),
        'tag_ids': fields.many2many(
            'destination.tag',
            'destination_tag_rel',
            'tag_id',
            'trip_id',
            'Tags'),
        'summer_tag_ids': fields.many2many(
            'destination.tag',
            'summer_destination_tag_rel',
            'tag_id',
            'trip_id',
            'Summer Tags'),
        'winter_tag_ids': fields.many2many(
            'destination.tag',
            'winter_destination_tag_rel',
            'tag_id',
            'trip_id',
            'Winter Tags'),

        }


class trip_baggage(orm.Model):
    _name = "trip.baggage"
    _description = "Trip Baggage"

    def _product_baggage_count(self, cr, uid, ids, field_name, arg, context=None):
        r = dict.fromkeys(ids, 0)
        for trip_id in ids:
            domain = [
                ('state', 'in', ['to_buy', 'to_pack']),
                ('trip_id', '=', trip_id),
            ]
            product_baggage_ids = self.pool['product.baggage'].search(cr, uid, domain, context=context)
            r[trip_id] = len(product_baggage_ids)
        return r

    def action_view_product_baggages(self, cr, uid, ids, context=None):
        result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'baggage_builder.product_baggage_action_form', raise_if_not_found=True)
        result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
        result['domain'] = "[('trip_id','in',[" + ','.join(map(str, ids)) + "])]"
        result['context'] = "{'search_default_to_pack': 1, 'search_default_to_buy': 1}"
        return result

    _columns = {
        'name': fields.char('Name', required=True),
        'destination_id': fields.many2one('trip.destination','Destination'),
        'time_laps': fields.integer(
            'Time laps',
            required=True,
            help="Trip number of days"),
        'partner_ids': fields.many2many(
            'res.partner',
            'baggage_partner_rel',
            'baggage_id',
            'partner_id',
            'Partners',
            required=True),
        'product_baggage_ids': fields.one2many(
            'product.baggage',
            'trip_id',
            'Product baggage'),
        'tag_ids': fields.many2many(
            'destination.tag',
            'baggage_tag_rel',
            'tag_id',
            'baggage_id',
            'Tags'),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('started', 'Started'),
             ('done', 'Done'),
             ('cancel', 'Cancel')],
            'State'),
        'season': fields.selection(
            [('summer', 'Summer'), ('winter', 'Winter')],
            'Season'),
        'activity_tag_ids': fields.many2many(
            'destination.tag',
            'baggage_activity_tag_rel',
            'tag_id',
            'baggage_id',
            'Activities'),
        'product_baggage_count': fields.function(
            _product_baggage_count,
            string='# Product Baggage',
            type='integer'),
        }

    _defaults = {
        'state': 'draft',
        }

    def start_baggage(self, cr, uid, ids, context=None):
        product_obj = self.pool['product.product']
        for baggage in self.browse(cr, uid, ids, context=context):
            vals = {'state': 'started'}
            ages = genders = []
            for partner in baggage.partner_ids:
                ages.append(partner.age)
                genders.append(partner.gender)
            tag_ids = [x.id for x in baggage.tag_ids]
            activity_ids = [x.id for x in baggage.activity_tag_ids]
            tag_ids = list(set(tag_ids).union(set(activity_ids)))
            product_ids = product_obj.search(
                cr, uid, [('colocation_type', '=', 'baggage'),
                          '|', ('baggage_tag_ids', 'in', tag_ids), ('always_needed', '=', True),
                          '|', ('gender', 'in', genders), ('gender', '=', False),
                          '|', ('age', 'in', ages), ('age', '=', False)],
                context=context)
            lines = []
            unique_product_ids = []
            for partner in baggage.partner_ids:
                for product in product_obj.browse(cr, uid, product_ids, context=context):
                    if product.gender and product.gender != partner.gender:
                        continue
                    if product.age and product.age != partner.age:
                        continue
                    if product.id in unique_product_ids:
                        continue
                    if product.usability_coef == -1:
                        qty = 1
                    elif product.usability_coef == -2:
                        qty = 1
                        unique_product_ids.append(product.id)
                    else:
                        qty = math.ceil((product.usability_coef * baggage.time_laps)/7)
                    line_vals = {
                        'name': product.name,
                        'product_id': product.id,
                        'quantity': qty,
                        'partner_id': partner.id}
                    lines.append((0, 0, line_vals))
            vals.update({'product_baggage_ids': lines})
            print vals
            self.write(cr, uid, [baggage.id], vals, context=context)
        return True

    def done_baggage(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True

    def cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def onchange_destination(self, cr, uid, ids, destination_id, season, context=None):
        dest_obj = self.pool['trip.destination']
        res = {'value': {}}
        if not destination_id:
            return res
        destination = dest_obj.browse(cr, uid, destination_id, context=context)
        tag_ids = [x.id for x in destination.tag_ids]
        if season:
            if season == 'summer':
                tag_ids += [x.id for x in destination.summer_tag_ids]
            elif season == 'winter':
                tag_ids += [x.id for x in destination.winter_tag_ids]
        res['value']['tag_ids'] = list(set(tag_ids))
        return res

    def copy(self, cr, uid, id,default=None, context=None):
        if default is None:
            default = {}
        default.update({'product_baggage_ids': []})
        return super(trip_baggage, self).copy(cr, uid, id, default=default,
                                              context=context)


class product_baggage(orm.Model):
    _name = "product.baggage"
    _description = "Product Baggage"

    _order = "state desc, partner_id"

    _columns = {
        'name': fields.char('Name'),
        'trip_id': fields.many2one(
            'trip.baggage',
            'Trip',
            required=True,
            ondelete="cascade"),
        'product_id': fields.many2one(
            'product.product',
            'Product',
            required=True,
            domain="[('colocation_type', '=', 'baggage')]"),
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            required=True),
        'quantity': fields.float('Quantity', required=True),
        'state': fields.selection(
            [('to_pack', 'To Pack'),
             ('to_buy', 'To Buy'),
             ('packed', 'Packed')],
            'State'),
        }

    _defaults = {
        'quantity': 1,
        'state': 'to_pack',
        }

    _sql_constraints = [
        ('product_baggage_uniq', 'unique(trip_id, product_id, partner_id)',
         'Product baggage must be unique for a same partner and a same trip'),
    ]

    def pack_product_baggage(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'packed'}, context=context)
        return True

    def buy_product_baggage(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'to_buy'}, context=context)
        return True


class res_partner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'gender': fields.selection(
            [('male', 'Male'),
             ('female', 'Female'),
             ('undefined', 'Undefined')],
            'Gender'),
        'age': fields.selection(
            _BAGGAGE_AGE,
            'Age'),
        }

    _defaults = {
        'gender': 'undefined',
        }
