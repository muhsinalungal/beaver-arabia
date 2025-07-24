# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import Counter, defaultdict

from odoo import _, api, fields, tools, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import OrderedSet
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockProductionLot(models.Model):
	_inherit = "stock.production.lot"

	unit_price = fields.Float( string='Unit Price')
	price_line_ids = fields.One2many('price.lines', 'lot_id', 'Price Lines')

class PriceLines(models.Model):
	_name = 'price.lines'
	
	name = fields.Char(string='Name',)
	desc = fields.Char(string='Description',)
	unit_price = fields.Float(string='Unit Price',)
	date = fields.Date(string='Date',)
	lot_id = fields.Many2one('stock.production.lot', 'Lot')

	# @api.model
	# @api.depends('name')
	# def name_search(self, name, args=None, operator='ilike', limit=100):
	# 	args = args or []
	# 	domain = []
	# 	result = []
	# 	print ('name===',name)
	# 	if name:
	# 		domain = [('unit_price', operator, name)]
	# 	csm = self.search(domain + args, limit=limit)
	# 	print ('csm======',csm)
		
	# 	for site in csm:
	# 		name = site.unit_price
	# 		print ('vnamel=======',site.unit_price)
	# 		result.append((site.id, name))
	# 	print ('result========',result)
	# 	return result

class StockMove(models.Model):
	_inherit = "stock.move"

	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
	
	def _action_assign(self):
		"""
		Generate accounting moves if the product being moved is subject
		to real_time valuation tracking,
		and the source or destination location are
		a transit location or is outside of the company or the source or
		destination locations belong to different operating units.
		"""
		res = super(StockMove, self)._action_assign()
		for stock_line in self.move_line_ids:
			stock_line.price_line_id =self.env['price.lines'].search([('lot_id', '=', stock_line.lot_id.id)],limit=1, order='id desc').id
			stock_line.unit_price = stock_line.price_line_id.unit_price

class StockLocation(models.Model):
	_inherit = "stock.location"

	is_project_location = fields.Boolean('Is Project Location',default=False)


class StockMoveLine(models.Model):
	_inherit = "stock.move.line"

	def _get_priceline(self):
		price_line_id =self.env['price.lines'].search([('lot_id', '=', self.lot_id.id)],limit=1, order='id desc').id
		return price_line_id

	unit_price = fields.Float( string='Unit Price',store=True)
	price_line_id = fields.Many2one('price.lines',string='Price Line',domain="[('lot_id', '=', lot_id)]")
	total = fields.Float( string='Total',store=True)

	@api.onchange('lot_id','price_line_id')
	def _onchange_cost(self):
		for line in self:
			if line.lot_id and line.price_line_id:
				line.unit_price = line.price_line_id.unit_price
				# line.total = line.unit_price * line.qty_done

	@api.onchange('lot_id','qty_done','price_line_id','unit_price')
	def _onchange_total_cost(self):
		for line in self:
			if line.lot_id and line.price_line_id:
				# line.unit_price = line.price_line_id.unit_price
				line.total = line.unit_price * line.qty_done


	def _create_and_assign_production_lot(self):
		""" Creates and assign new production lots for move lines."""
		lot_vals = []
		# It is possible to have multiple time the same lot to create & assign,
		# so we handle the case with 2 dictionaries.
		key_to_index = {}  # key to index of the lot
		key_to_mls = defaultdict(lambda: self.env['stock.move.line'])  # key to all mls
		for ml in self:
			key = (ml.company_id.id, ml.product_id.id, ml.lot_name)
			key_to_mls[key] |= ml
			if ml.tracking != 'lot' or key not in key_to_index:
				key_to_index[key] = len(lot_vals)
				lot_vals.append({
					'company_id': ml.company_id.id,
					'name': ml.lot_name,
					'product_id': ml.product_id.id,
					'unit_price': ml.move_id.purchase_line_id.price_unit if ml.move_id.purchase_line_id else 0.00
				})

		lots = self.env['stock.production.lot'].create(lot_vals)
		for key, mls in key_to_mls.items():
			mls._assign_production_lot(lots[key_to_index[key]].with_prefetch(lots._ids))  # With prefetch to reconstruct the ones broke by accessing by index

	def _action_done(self):
		""" This method is called during a move's `action_done`. It'll actually move a quant from
		the source location to the destination location, and unreserve if needed in the source
		location.

		This method is intended to be called on all the move lines of a move. This method is not
		intended to be called when editing a `done` move (that's what the override of `write` here
		is done.
		"""
		Quant = self.env['stock.quant']

		# First, we loop over all the move lines to do a preliminary check: `qty_done` should not
		# be negative and, according to the presence of a picking type or a linked inventory
		# adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
		# the line. It is mandatory in order to free the reservation and correctly apply
		# `action_done` on the next move lines.
		ml_ids_tracked_without_lot = OrderedSet()
		ml_ids_to_delete = OrderedSet()
		ml_ids_to_create_lot = OrderedSet()
		for ml in self:
			# Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
			uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
			precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
			if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
				raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
								  defined on the unit of measure "%s". Please change the quantity done or the \
								  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

			qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
			if qty_done_float_compared > 0:
				if ml.product_id.tracking != 'none':
					picking_type_id = ml.move_id.picking_type_id
					if picking_type_id:
						if picking_type_id.use_create_lots:
							# If a picking type is linked, we may have to create a production lot on
							# the fly before assigning it to the move line if the user checked both
							# `use_create_lots` and `use_existing_lots`.
							if ml.lot_name and not ml.lot_id:
								lot = self.env['stock.production.lot'].search([
									('company_id', '=', ml.company_id.id),
									('product_id', '=', ml.product_id.id),
									('name', '=', ml.lot_name),
								], limit=1)
								if lot:
									ml.lot_id = lot.id
									line_vals = {
																
													'unit_price':ml.move_id.purchase_line_id.price_unit,
													'lot_id':ml.lot_id.id,
													'date':fields.date.today(),	
													'name':str(ml.move_id.purchase_line_id.price_unit),	
													'desc':str(ml.picking_id.name),				
																		
													}
									self.env['price.lines'].create(line_vals)
								else:
									ml_ids_to_create_lot.add(ml.id)
						elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
							# If the user disabled both `use_create_lots` and `use_existing_lots`
							# checkboxes on the picking type, he's allowed to enter tracked
							# products without a `lot_id`.
							continue
					elif ml.move_id.inventory_id:
						# If an inventory adjustment is linked, the user is allowed to enter
						# tracked products without a `lot_id`.
						continue

					if not ml.lot_id and ml.id not in ml_ids_to_create_lot:
						ml_ids_tracked_without_lot.add(ml.id)
			elif qty_done_float_compared < 0:
				raise UserError(_('No negative quantities allowed'))
			else:
				ml_ids_to_delete.add(ml.id)

		if ml_ids_tracked_without_lot:
			mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
			raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
							  '\n - '.join(mls_tracked_without_lot.mapped('product_id.display_name')))
		ml_to_create_lot = self.env['stock.move.line'].browse(ml_ids_to_create_lot)
		ml_to_create_lot._create_and_assign_production_lot()
		for move_line in ml_to_create_lot:
			line_vals = {
																	
							'unit_price':move_line.move_id.purchase_line_id.price_unit,
							'lot_id':move_line.lot_id.id,
							'date':fields.date.today(),					
							'name':str(move_line.move_id.purchase_line_id.price_unit),
							'desc':str(move_line.picking_id.name),
							}
			p_l = self.env['price.lines'].create(line_vals)
		# print ('line_vals=========',line_vals)
		# ml_to_create_lot.lot_id.price_line_ids = line_vals
		# print ('ml_to_create_lot========',ml_to_create_lot1)
		# ml_to_create_lot.lot_id.unit_price = ml_to_create_lot.move_id.purchase_line_id.price_unit

		mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
		mls_to_delete.unlink()

		mls_todo = (self - mls_to_delete)
		mls_todo._check_company()

		# Now, we can actually move the quant.
		ml_ids_to_ignore = OrderedSet()
		for ml in mls_todo:
			if ml.product_id.type == 'product':
				rounding = ml.product_uom_id.rounding

				# if this move line is force assigned, unreserve elsewhere if needed
				if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
					qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
					extra_qty = qty_done_product_uom - ml.product_qty
					ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
					ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
				# unreserve what's been reserved
				if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
					Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

				# move what's been actually done
				quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
				available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
				if available_qty < 0 and ml.lot_id:
					# see if we can compensate the negative quants with some untracked quants
					untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
					if untracked_qty:
						taken_from_untracked_qty = min(untracked_qty, abs(quantity))
						Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
						Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
				Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
			ml_ids_to_ignore.add(ml.id)
		# Reset the reserved quantity as we just moved it to the destination location.
		mls_todo.with_context(bypass_reservation_update=True).write({
			'product_uom_qty': 0.00,
			'date': fields.Datetime.now(),
		})
		

	def _get_price_unit(self):
		""" Returns the unit price for the move"""
		self.ensure_one()
		if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
			price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
			line = self.purchase_line_id
			order = line.order_id
			price_unit = line.price_unit
			if line.taxes_id:
				qty = line.product_qty or 1
				price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=qty)['total_void']
				price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
			if line.product_uom.id != line.product_id.uom_id.id:
				price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
			if order.currency_id != order.company_id.currency_id:
				# The date must be today, and not the date of the move since the move move is still
				# in assigned state. However, the move date is the scheduled date until move is
				# done, then date of actual move processing. See:
				# https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
				price_unit = order.currency_id._convert(
					price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self), round=False)
			return price_unit
		return super(StockMove, self)._get_price_unit()

