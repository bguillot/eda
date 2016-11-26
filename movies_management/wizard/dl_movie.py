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
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DlMovie(models.TransientModel):
    _name = "dl.movie"
    _description = "Download movie"

    language = fields.Selection(
       [('vo', 'VO'),
        ('fr', 'FR'),
        ('vostfr','VOSTFR'),
        ('vosten', 'VOSTEN'),
        ('multi', 'MULTI')],
       'Language',
       required=True)
    quality = fields.Selection(
       [('1080p', '1080p'),
        ('720p', '720p'),
        ('bdrip', 'BDRIP'),
        ('dvdrip', 'DVDRIP'),
        ('cam_ts', 'CAM-TS...')],
       'Quality',
       required=True)

    @api.multi
    def dl_movie(self):
        self.ensure_one()
        movie = self.env['movie.movie'].search([('id', '=', self._context.get('active_id'))])
        vals = {
            'language': self.language,
            'quality': self.quality,
            'state': 'ready'
            }
        movie.write(vals)
        return {'type': 'ir.actions.act_window_close'}
