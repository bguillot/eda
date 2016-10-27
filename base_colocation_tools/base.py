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

from openerp import fields, api, models


class ResCompany(models.Model):
    _inherit="res.company"

    @api.depends('flatmate_ids', 'flatmate_ids.email')
    @api.multi
    def _get_flatmate_email(self):
        for company in self:
            emails = []
            for flatmate in company.flatmate_ids:
                if flatmate.email:
                    emails.append(flatmate.email)
            company.flatmates_email = ', '.join(emails)

    flatmate_ids = fields.Many2many(
        'res.partner',
        'partner_company_rel',
        'company_id',
        'partner_id',
        'Flatmates',
        )
    flatmates_email = fields.Char(
        compute='_get_flatmate_email',
        string='Flatmates emails',
        store=True
        )
