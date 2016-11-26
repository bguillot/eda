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
from openerp import fields, api, models


class ProjectionDates(models.TransientModel):
    _name = "projection.dates"
    _description = "Projection dates"

    generate_projection_id = fields.Many2one(
        'generate.projection.choice',
        'Generate projection',
        ondelete='cascade',
        required=True)
    date = fields.Date('Date')


class GenerateProjectionChoice(models.TransientModel):
    _name = "generate.projection.choice"
    _description = "Generate Projection choice"

    @api.model
    def _get_user_ids(self):
        proj = self.env['movie.projection'].browse(self._context.get('active_id'))
        return proj.planned_user_ids

    dates = fields.One2many(
        'projection.dates',
        'generate_projection_id',
        'Dates')
    user_ids = fields.Many2many(
        'res.users',
        'user_igenerate_projection_rel',
        'projection_id',
        'user_id',
        'Users',
        default=_get_user_ids)

    @api.multi
    def generate_dates(self):
        self.ensure_one()
        proj_id = self._context.get('active_id')
        email_to = ""
        for user in self.user_ids:
            email_to += "%s, " % user.partner_id.email
            for date in self.dates:
                vals = {
                    'projection_id': proj_id,
                    'user_id': user.id,
                    'date': date.date,
                    'state': 'unchoosed'
                    }
                self.env['projection.choice'].create(vals)
        template = self.env.ref('movies_management.start_planning_projection_template')
        template.with_context(email_to=email_to).send_mail(proj_id)
        return {'type': 'ir.actions.act_window_close'}
