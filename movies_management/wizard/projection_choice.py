# -*- coding: utf-8 -*-
###############################################################################
#
#   movies_management for OpenERP
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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class projection_dates(orm.TransientModel):
    _name = "projection.dates"
    _description = "Projection dates"

    _columns = {
        'generate_projection_id': fields.many2one(
            'generate.projection.choice',
            'Generate projection',
            ondelete='cascade',
            required=True),
        'date': fields.date('Date'),
        }


class generate_projection_choice(orm.TransientModel):
    _name = "generate.projection.choice"
    _description = "Generate Projection choice"

    def _get_user_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        proj = self.pool['movie.projection'].browse(cr, uid,
                                                    context.get('active_id'),
                                                    context=context)
        user_ids = [x.id for x in proj.planned_user_ids]
        return user_ids

    _columns = {
        'dates': fields.one2many(
            'projection.dates',
            'generate_projection_id',
            'Dates'),
        'user_ids': fields.many2many(
            'res.users',
            'user_igenerate_projection_rel',
            'projection_id',
            'user_id',
            'Users'),
        }

    _defaults = {
        'user_ids': _get_user_ids,
        }

    def generate_dates(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        proj_id = context.get('active_id')
        wizard = self.browse(cr, uid, ids[0], context=context)
        email_to = ""
        for user in wizard.user_ids:
            email_to += "%s, " % user.partner_id.email
            for date in wizard.dates:
                vals = {
                    'projection_id': proj_id,
                    'user_id': user.id,
                    'date': date.date,
                    'state': 'unchoosed'
                    }
                self.pool['projection.choice'].create(cr, uid, vals,
                                                      context=context)
        context['email_to'] = email_to
        template_id = self.pool['ir.model.data'].get_object_reference(cr, uid,
            'movies_management', 'start_planning_projection_template')[1]
        self.pool.get('email.template').send_mail(cr, uid, template_id,
            proj_id, force_send=False, context=context)
        return {'type': 'ir.actions.act_window_close'}
