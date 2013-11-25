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

from openerp.osv import fields, orm


class res_company(orm.Model):
    _inherit="res.company"

    def _get_company_from_partner(self, cr, uid, ids, context=None):
        company_obj = self.pool['res.company']
        company_ids = company_obj.search(cr, uid, [('roomate_ids', 'in', ids)],
                                         context=context)
        return company_ids

    def _get_roomate_email(self, cr, uid, ids, name, args, context=None):
        res = {}
        for company in self.browse(cr, uid, ids, context=context):
            emails = ''
            for roomate in company.roomate_ids:
                if roomate.email:
                    if emails:
                        emails = emails + ', ' + roomate.email
                    else:
                        emails = roomate.email
            res[company.id] = emails
        return res

    _columns={
        'roomate_ids': fields.many2many(
            'res.partner',
            'partner_company_rel',
            'company_id',
            'partner_id',
            'Roomates',
            ),
        'roomates_email': fields.function(
            _get_roomate_email,
            type='char',
            string='Roomates emails',
            store={
                'res.company':
                    (lambda self, cr, uid, ids, c=None:
                        ids,
                        ['roomate_ids'],
                        10),
                'res.partner': (_get_company_from_partner, ['email'], 20),
                }),
        }

