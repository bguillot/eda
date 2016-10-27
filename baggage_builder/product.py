# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com). All Rights Reserved
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
import math
from .baggage import _BAGGAGE_AGE

class product_product(models.Model):
    _inherit = "product.product"

    colocation_type = fields.Selection(
        selection_add=[('baggage', 'Baggage')])
    baggage_tag_ids = fields.Many2many(
        comodel_name='destination.tag',
        relation='product_baggage_tag_rel',
        column1='tag_id',
        column2='product_id',
        string='Baggage tags')
    gender = fields.Selection(
        selection=[('male', 'Male'), ('female', 'Female')],
        string='Gender')
    age = fields.Selection(
        selection=_BAGGAGE_AGE)
    usability_coef = fields.Float(
        string='Usability Coefficient',
        default=-1,
        help="Number of products needed for one week (7 days). "
            "Select -1 if the product is unique, for example sun glasses."
            "Select -2 if the product is unique for everyone, for exemple sun cream")
    always_needed = fields.Boolean('Always needed')