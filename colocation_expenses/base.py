# -*- coding: utf-8 -*-
###############################################################################
#
#   colocation_expensess for OpenERP
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

from openerp.osv import orm


class res_company(orm.Model):
    _inherit="res.company"

    def expense_attendance_reminder(self, cr, uid, context=None):
        data_obj = self.pool['ir.model.data']
        template_obj = self.pool['email.template']
        model, template_id = data_obj.get_object_reference(cr, uid,
                'colocation_expenses', 'expense_reminder_template')
        template_obj.send_mail(cr, uid, template_id, 1, force_send=False,
                               context=context)
        return True
