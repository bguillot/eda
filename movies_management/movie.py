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


class res_users(orm.Model):
    _inherit="res.users"

    _columns={
        'wished_movie_ids': fields.many2many(
            'movie.movie',
            'movie_watcher_rel',
            'user_id',
            'movie_id',
            'Wished movies'),
        'watched_movie_ids': fields.many2many(
            'movie.movie',
            'movie_watched_user_rel',
            'user_id',
            'movie_id',
            'Watched movies'),
        }


class movie_movie(orm.Model):
    _name="movie.movie"
    _description="Movies"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _order = "sequence desc"

    def _get_years(self, cr, uid, context=None):
        current_year = date.today().year
        years=[]
        year = current_year
        while year >= 1906:
            years.append((str(year), str(year)))
            year -= 1
        return years

    def _get_sequence(self, cr, uid, ids, name, args, context=None):
        res = {}
        for movie in self.browse(cr, uid, ids, context=context):
            res[movie.id] = 10 + len(movie.watcher_ids)
        return res

    _columns={
        'name': fields.char('Name', size=64),
        'type_id': fields.many2one(
            'movie.type',
            'Type',
            required=True),
        'subtype_id': fields.many2one(
            'movie.subtype',
            'Subtype',
            domain="[('type_id', '=', type_id)]"),
#        TODO http://fr.wikipedia.org/wiki/Genre_cin%C3%A9matographique
        'year': fields.selection(_get_years, 'Year', help='Year of release'),
        'synopsis': fields.text('Synopsis'),
        'state': fields.selection(
            [('to_dl', 'To download'),
             ('ready', 'Ready to be watched'),
             ('watched', 'Watched')],
            'State', required=True),
        'last_projection_date': fields.date('Last projection date'),
        'watcher_ids': fields.many2many(
            'res.users',
            'movie_watcher_rel',
            'movie_id',
            'user_id',
            'Watchers',
            help="Persons who want to watch the movie"),
        'director': fields.char('Director', size=32),
        'watched_user_ids': fields.many2many(
            'res.users',
            'movie_watched_user_rel',
            'movie_id',
            'user_id',
            'Already watched users',
            help="Persons who have already watched the movie"),
        'language': fields.selection(
            [('vo', 'VO'),
             ('fr', 'FR'),
             ('vostfr','VOSTFR'),
             ('vosten', 'VOSTEN')],
            'Language'),
        'sequence': fields.function(_get_sequence, type="integer",
            string="Sequence",
            store={
                'movie.movie': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['watcher_ids'],
                    10),})
        }

    _defaults={
        'state': 'to_dl',
        }

    def dl_movie(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'ready'}, context=context)
        return True

    def watch_movie(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'watched'}, context=context)
        return True

    def wanna_see(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'watcher_ids': [(4, uid)]}, context=context)
        return True

    def already_watched(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'watched_user_ids': [(4, uid)]},
                   context=context)
        return True

    def plan_projection(self, cr, uid, ids, context=None):
        proj_obj = self.pool['movie.projection']
        model_data_obj = self.pool['ir.model.data']
        for movie in self.browse(cr, uid, ids, context=context):
            proj_vals = {
                'movie_id': movie.id,
                'state': 'draft',
                'user_ids': [(6, 0, [x.id for x in movie.watcher_ids])]
                }
            proj_id = proj_obj.create(cr, uid, proj_vals, context=context)
        model, view_id = model_data_obj.get_object_reference(
            cr, uid, 'movies_management', 'movie_projection_form_view')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'movie.projection',
            'res_id': proj_id,
            'type': 'ir.actions.act_window',
             }



class movie_type(orm.Model):
    _name="movie.type"
    _description="Movie Type"

    _columns={
        'name': fields.char('Name', size=64, required=True),
        }


class movie_subtype(orm.Model):
    _name="movie.subtype"
    _description="Movie Subtype"

    _columns={
        'name': fields.char('Name', size=64, required=True),
        'type_id': fields.many2one('movie.type', 'Type', required=True),
        }


class movie_projection(orm.Model):
    _name="movie.projection"
    _description="Movie Projection"

    _columns = {
        'date_done': fields.datetime('Date done', readonly=True),
        'date_planned': fields.datetime('Date planned'),
        'movie_id': fields.many2one('movie.movie', 'Movie', required=True),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('planned', 'Planned'),
             ('done', 'Done'),
             ('cancel', 'Cancel')],
            'State'),
        'user_ids': fields.many2many(
            'res.users',
            'user_projection_rel',
            'projection_id',
            'user_id',
            'Users'),
        }

    _defaults = {
        'state': 'draft',
        }

    def action_plan(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'planned'}, context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        for proj in self.browse(cr, uid, ids, context=context):
            write_vals = {
                'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'state': 'done',
                }
            proj.write(write_vals, context=context)
            proj.movie_id.write({'state': 'watched'}, context=context)
            for user in proj.user_ids:
                user.write({
                    'wished_movie_ids': [(3, proj.movie_id.id)],
                    'watched_movie_ids': [(4, proj.movie_id.id)]},
                    context=context)
        return True
