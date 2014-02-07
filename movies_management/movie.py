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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from collections import defaultdict
import operator


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

    _order = "sequence desc, state asc"

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
            res[movie.id] = 10 + (movie.watcher_ids and len(movie.watcher_ids) or 0.0)
        return res

    _columns={
        'name': fields.char('Name', size=64,
            required=True,
            readonly=True,
            states={'to_dl': [('readonly', False)]}),
        'poster': fields.binary('Poster'),
        'type_id': fields.many2many(
            'movie.type',
            'movie_type_rel',
            'movie_id',
            'type_id',
            'Type',
            required=True,
            readonly=True,
            states={'to_dl': [('readonly', False)]}),
        'year': fields.selection(_get_years, 'Year',
            readonly=True,
            states={'to_dl': [('readonly', False)]},
            help='Year of release'),
        'synopsis': fields.text('Synopsis'),
        'state': fields.selection(
            [('to_dl', 'To download'),
             ('ready', 'Ready to be watched'),
             ('watched', 'Watched')],
            'State',
            required=True,
            readonly=True),
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
             ('vosten', 'VOSTEN'),
             ('multi', 'MULTI')],
            'Language',
            readonly=True,
            states={'to_dl': [('readonly', False)]}),
        'sequence': fields.function(_get_sequence, type="integer",
            string="Sequence",
            store={
                'movie.movie': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['watcher_ids', 'name'],
                    10),})
        }

    _defaults={
        'state': 'to_dl',
        }

    _sql_constraints = [
        ('name_year_uniq',
         'unique(name, year)',
         'Movie already created with this name and year!'),
    ]

    def dl_movie(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'ready'}, context=context)
        return True

    def reset_to_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'to_dl'}, context=context)
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
                'planned_user_ids': [(6, 0, [x.id for x in movie.watcher_ids])]
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
        'name': fields.char('Name', size=64, translate=True, required=True),
        }


class movie_projection(orm.Model):
    _name="movie.projection"
    _description="Movie Projection"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _order ="date_planned asc, best_date asc, ready_to_plan desc"

    def _get_best_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        for proj in self.browse(cr, uid, ids, context=context):
            res[proj.id] = {}
            initial_user_ids = [x.id for x in proj.planned_user_ids]
            dates = defaultdict(int)
            users = defaultdict(list)
            for choice in proj.choice_ids:
                if choice.state == 'approved':
                    dates[choice.date] += 1
                    users[choice.date].append(choice.user_id.id)
            best_date = False
            if dates:
                best_date = sorted(dates.iteritems(),
                                   key=operator.itemgetter(1),
                                   reverse=True)[0][0]
            ready= False
            if best_date and set(users[best_date]) == set(initial_user_ids):
                ready = True
            res[proj.id]['best_date'] = best_date
            res[proj.id]['ready_to_plan'] = ready
        return res

    def _get_proj_from_choice(self, cr, uid, ids, context=None):
        proj_obj = self.pool['movie.projection']
        proj_ids = proj_obj.search(cr, uid, [('choice_ids', 'in', ids)],
                                   context=context)
        return proj_ids

    _columns = {
        'date_done': fields.datetime('Date done', readonly=True),
        'date_planned': fields.datetime('Date planned'),
        'movie_id': fields.many2one(
            'movie.movie',
            'Movie',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('planned', 'Planned'),
             ('done', 'Done'),
             ('cancel', 'Cancel')],
            'State'),
        'planned_user_ids': fields.many2many(
            'res.users',
            'planned_user_projection_rel',
            'projection_id',
            'user_id',
            'Planned Users'),
        'actual_user_ids': fields.many2many(
            'res.users',
            'actual_user_projection_rel',
            'projection_id',
            'user_id',
            'Actual Users'),
        'choice_ids': fields.one2many(
            'projection.choice',
            'projection_id',
            'Choices',
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'best_date': fields.function(
            _get_best_date,
            type="date",
            string="Best Date",
            multi="best_date",
            store={
                'movie.projection': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['choice_ids'],
                    10),
                'projection.choice': (
                    _get_proj_from_choice,
                    ['state'],
                    20)
                }),
        'ready_to_plan': fields.function(
            _get_best_date,
            type="boolean",
            string="Ready to plan",
            multi="best_date",
            store={
                'movie.projection': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['choice_ids','best_date'],
                    10),
                'projection.choice': (
                    _get_proj_from_choice,
                    ['state'],
                    20)
                }),
        'company_id': fields.many2one('res.company', 'Company'),
        }

    _defaults = {
        'state': 'draft',
        'company_id': 1,  # TODO method get company
        }

    def action_plan(self, cr, uid, ids, context=None):
        for proj in self.browse(cr, uid, ids, context=context):
            if not proj.date_planned:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _("You have to set the date planned "
                                       "before planning the projection, "
                                       "you stupid fuck!"))
            email_to = ""
            for user in proj.planned_user_ids:
                email_to += "%s, " % user.partner_id.email
            context['email_to'] = email_to
            template_id = self.pool['ir.model.data'].get_object_reference(cr, uid,
                'movies_management', 'planned_projection_template')[1]
            self.pool.get('email.template').send_mail(cr, uid, template_id,
                proj.id, force_send=False, context=context)
        self.write(cr, uid, ids, {'state': 'planned'}, context=context)
        return True

    def action_unplan(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids,
                   {'state': 'draft', 'date_planned': False},
                   context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        today = date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for proj in self.browse(cr, uid, ids, context=context):
            write_vals = {
                'date_done': now,
                'state': 'done',
                }
            proj.write(write_vals, context=context)
            proj.movie_id.write({'state': 'watched',
                                 'last_projection_date': today}, context=context)
            if not proj.actual_user_ids:
                raise orm.except_orm(_('Keyboard/Chair error'),
                                     _("Nobody watched the movie ? "
                                       "Of course not, you stupid fuck!"))
            for user in proj.actual_user_ids:
                user.write({
                    'wished_movie_ids': [(3, proj.movie_id.id)],
                    'watched_movie_ids': [(4, proj.movie_id.id)]},
                    context=context)
                proj.movie_id.write({
                    'watcher_ids': [(3, user.id)],
                    'watched_user_ids': [(4, user.id)]},
                    context=context)
        return True

    def cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True


class projection_choice(orm.Model):
    _name = "projection.choice"
    _description = "Projection choice"

    _order ='state asc'

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=True),
        'date': fields.date(
            'Date',
            required=True,
            readonly=True,
            states={'unchoosed': [('readonly', False)]}),
        'projection_id': fields.many2one(
            'movie.projection',
            'Projection',
            required=True,
            readonly=True,
            ondelete='cascade'),
        'state': fields.selection(
            [('unchoosed', 'Unchoosed'),
             ('approved', 'Approved'),
             ('refused', 'Refused')],
            'State'),
        'movie_id': fields.related(
            'projection_id',
            'movie_id',
            type='many2one',
            relation='movie.movie',
            string='Movie',
            readonly=True),
        }

    _defaults = {
        'state': 'unchoosed',
        }

    def refuse(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'refused'}, context=context)
        return True

    def approve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'approved'}, context=context)
        return True
