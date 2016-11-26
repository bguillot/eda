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
from openerp import fields, api, models, _
from openerp.exceptions import Warning as UserError
from datetime import date, datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from collections import defaultdict
import operator


class ResUsers(models.Model):
    _inherit="res.users"

    wished_movie_ids = fields.Many2many(
        'movie.movie',
        'movie_watcher_rel',
        'user_id',
        'movie_id',
        'Wished movies')
    watched_movie_ids = fields.Many2many(
        'movie.movie',
        'movie_watched_user_rel',
        'user_id',
        'movie_id',
        'Watched movies')


class MovieMovie(models.Model):
    _name="movie.movie"
    _description="Movies"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _order = "sequence desc, state asc"

    @api.model
    def _get_years(self):
        current_year = date.today().year
        years=[]
        year = current_year
        while year >= 1906:
            years.append((str(year), str(year)))
            year -= 1
        return years

    @api.depends('watcher_ids')
    @api.multi
    def _get_sequence(self):
        for movie in self:
            movie.sequence = 10 + (movie.watcher_ids and len(movie.watcher_ids) or 0.0)

    name = fields.Char('Name', size=64,
        required=True,
        readonly=True,
        states={'to_dl': [('readonly', False)]})
    poster = fields.Binary('Poster')
    type_id = fields.Many2many(
        'movie.type',
        'movie_type_rel',
        'movie_id',
        'type_id',
        'Type',
        required=True,
        readonly=True,
        states={'to_dl': [('readonly', False)]})
    year = fields.Selection(
        _get_years,
        'Year',
        readonly=True,
        states={'to_dl': [('readonly', False)]},
        help='Year of release')
    synopsis = fields.Text('Synopsis')
    state = fields.Selection(
        [('to_dl', 'To download'),
         ('ready', 'Ready to be watched'),
         ('watched', 'Watched')],
        'State',
        required=True,
        readonly=True,
        default='to_dl')
    last_projection_date = fields.Date('Last projection date')
    watcher_ids = fields.Many2many(
        'res.users',
        'movie_watcher_rel',
        'movie_id',
        'user_id',
        'Watchers',
        help="Persons who want to watch the movie")
    director = fields.Char('Director', size=32)
    watched_user_ids = fields.Many2many(
        'res.users',
        'movie_watched_user_rel',
        'movie_id',
        'user_id',
        'Already watched users',
        help="Persons who have already watched the movie")
    language = fields.Selection(
        [('vo', 'VO'),
            ('fr', 'FR'),
            ('vostfr','VOSTFR'),
            ('vosten', 'VOSTEN'),
            ('multi', 'MULTI')],
        'Language',
        readonly=True,
        states={'to_dl': [('readonly', False)]})
    sequence = fields.Integer(
        compute="_get_sequence",
        string="Sequence",
        store=True)
    quality = fields.Selection(
        [('1080p', '1080p'),
            ('720p', '720p'),
            ('bdrip', 'BDRIP'),
            ('dvdrip', 'DVDRIP'),
            ('cam_ts', 'CAM-TS...')],
        'Quality',
        readonly=True,
        states={'to_dl': [('readonly', False)]})

    _sql_constraints = [
        ('name_year_uniq',
         'unique(name, year)',
         'Movie already created with this name and year!'),
    ]

    @api.multi
    def reset_to_draft(self):
        self.write({'state': 'to_dl'})
        return True

    @api.multi
    def watch_movie(self):
        self.write({'state': 'watched'})
        return True

    @api.multi
    def wanna_see(self):
        self.write({'watcher_ids': [(4, self._uid)]})
        return True

    @api.multi
    def already_watched(self):
        self.write({'watched_user_ids': [(4, self._uid)]})
        return True

    @api.multi
    def plan_projection(self):
        proj_obj = self.env['movie.projection']
        for movie in self:
            proj_vals = {
                'movie_id': movie.id,
                'state': 'draft',
                'planned_user_ids': [(6, 0, movie.watcher_ids.ids)]
                }
            proj = proj_obj.create(proj_vals)
        view = self.env.ref('movies_management.movie_projection_form_view')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'movie.projection',
            'res_id': proj.id,
            'type': 'ir.actions.act_window',
        }


class MovieType(models.Model):
    _name="movie.type"
    _description="Movie Type"

    name = fields.Char('Name', size=64, translate=True, required=True)


class MovieProjection(models.Model):
    _name="movie.projection"
    _description="Movie Projection"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _order ="date_planned asc, best_date asc, ready_to_plan desc"

    @api.depends(
        'planned_user_ids', 'choice_ids', 'choice_ids.state',
        'choice_ids.date', 'choice_ids.user_id')
    @api.multi
    def _get_best_date(self):
        for proj in self:
            initial_user_ids = proj.planned_user_ids.ids
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
            proj.best_date = best_date
            proj.ready_to_plan = ready

    date_done = fields.Datetime('Date done', readonly=True)
    date_planned = fields.Datetime('Date planned')
    movie_id = fields.Many2one(
        'movie.movie',
        'Movie',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]})
    state = fields.Selection(
        [('draft', 'Draft'),
         ('planned', 'Planned'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        'State',
        default='draft')
    planned_user_ids = fields.Many2many(
        'res.users',
        'planned_user_projection_rel',
        'projection_id',
        'user_id',
        'Planned Users')
    actual_user_ids = fields.Many2many(
        'res.users',
        'actual_user_projection_rel',
        'projection_id',
        'user_id',
        'Actual Users')
    choice_ids = fields.One2many(
        'projection.choice',
        'projection_id',
        'Choices',
        readonly=True,
        states={'draft': [('readonly', False)]})
    best_date = fields.Date(
        compute='_get_best_date',
        string="Best Date",
        multi="best_date",
        store=True)
    ready_to_plan = fields.Boolean(
        compute='_get_best_date',
        string="Ready to plan",
        multi="best_date",
        store=True)
    company_id = fields.Many2one('res.company', 'Company', default=1)
        # TODO method get company

    @api.multi
    def action_plan(self):
        for proj in self:
            if not proj.date_planned:
                raise UserError(_('Keyboard/Chair error'),
                                _("You have to set the date planned "
                                  "before planning the projection, "
                                  "you stupid fuck!"))
            email_to = ""
            for user in proj.planned_user_ids:
                email_to += "%s, " % user.partner_id.email
            template = self.env.ref('movies_management.planned_projection_template')
            template.with_context(email_to=email_to).send_mail(proj.id)
        self.write({'state': 'planned'})
        return True

    @api.multi
    def action_unplan(self):
        self.write({'state': 'draft', 'date_planned': False})
        return True

    @api.multi
    def action_done(self):
        today = fields.Date.today()
        now = fields.Datetime.now()
        for proj in self:
            proj.date_done = now
            proj.state = 'done'
            proj.movie_id.write({'state': 'watched',
                                 'last_projection_date': today})
            if not proj.actual_user_ids:
                raise UserError(_('Keyboard/Chair error'),
                                _("Nobody watched the movie ? "
                                  "Of course not, you stupid fuck!"))
            for user in proj.actual_user_ids:
                user.write({
                    'wished_movie_ids': [(3, proj.movie_id.id)],
                    'watched_movie_ids': [(4, proj.movie_id.id)]})
                proj.movie_id.write({
                    'watcher_ids': [(3, user.id)],
                    'watched_user_ids': [(4, user.id)]})
        return True

    @api.multi
    def cancel(self):
        self.write({'state': 'cancel'})
        return True


class ProjectionChoice(models.Model):
    _name = "projection.choice"
    _description = "Projection choice"

    _order ='state asc'

    user_id = fields.Many2one('res.users', 'User', required=True)
    date = fields.Date(
        'Date',
        required=True,
        readonly=True,
        states={'unchoosed': [('readonly', False)]})
    projection_id = fields.Many2one(
        'movie.projection',
        'Projection',
        required=True,
        readonly=True,
        ondelete='cascade')
    state = fields.Selection(
        [('unchoosed', 'Unchoosed'),
         ('approved', 'Approved'),
         ('refused', 'Refused')],
        'State',
        default='unchoosed')
    movie_id = fields.Many2one(
        related='projection_id.movie_id',
        comodel_name='movie.movie',
        string='Movie',
        readonly=True,
        store=True)

    @api.multi
    def refuse(self):
        self.write({'state': 'refused'})
        return True

    @api.multi
    def approve(self):
        self.write({'state': 'approved'})
        return True
