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


class dl_movie(orm.TransientModel):
    _name = "dl.movie"
    _description = "Download movie"

    _columns = {
        'language': fields.selection(
            [('vo', 'VO'),
             ('fr', 'FR'),
             ('vostfr','VOSTFR'),
             ('vosten', 'VOSTEN'),
             ('multi', 'MULTI')],
            'Language',
            required=True),
        'quality': fields.selection(
            [('1080p', '1080p'),
             ('720p', '720p'),
             ('bdrip', 'BDRIP'),
             ('dvdrip', 'DVDRIP'),
             ('cam_ts', 'CAM-TS...')],
            'Quality',
            required=True),
        }


    def dl_movie(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        movie_id = context.get('active_id')
        wizard = self.browse(cr, uid, ids[0], context=context)
        vals = {
            'language': wizard.language,
            'quality': wizard.quality,
            'state': 'ready'
            }
        self.pool['movie.movie'].write(cr, uid, movie_id, vals, context=context)
        return {'type': 'ir.actions.act_window_close'}
