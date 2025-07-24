# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPickingLine(models.TransientModel):
	_inherit = "stock.return.picking.line"

	def _get_lot_id(self):

		active_id = self.env.context.get('active_id')
		picking_obj = self.env['stock.picking'].browse(active_id)

		lot_id = self.env['stock.production.lot']
		
		package_id = self.env['stock.quant.package']
		
		owner_id = self.env['res.partner']
		quants = self.env['stock.quant']._update_reserved_quantity(
						self.product_id, picking_obj.location_dest_id, self.quantity, lot_id=lot_id,
						package_id=package_id, owner_id=owner_id, strict=False
					)
		for reserved_quant, quantity in quants:
			lot_id = reserved_quant.lot_id.id
		return lot_id




	lot_id = fields.Many2one('stock.production.lot')
	lot_ids = fields.Many2many('stock.production.lot')
	price_line_id = fields.Many2one('price.lines',string='Price Line',)
	unit_price = fields.Float('Asset Value Price')

	@api.onchange('lot_id','quantity','price_line_id')
	def _onchange_cost(self):
		for line in self:
			if line.price_line_id:
				
				line.unit_price = line.price_line_id.unit_price
				

class ReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'
	_description = 'Return Picking'

	@api.model
	def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
		quantity = stock_move.product_qty
		for move in stock_move.move_dest_ids:
			if move.origin_returned_move_id and move.origin_returned_move_id != stock_move:
				continue
			if move.state in ('partially_available', 'assigned'):
				quantity -= sum(move.move_line_ids.mapped('product_qty'))
			elif move.state in ('done'):
				quantity -= move.product_qty
		quantity = float_round(quantity, precision_rounding=stock_move.product_id.uom_id.rounding)
		lot_id = self.env['stock.production.lot']
		
		package_id = self.env['stock.quant.package']
		
		owner_id = self.env['res.partner']
		lot_ids = []
		for line in stock_move.move_line_ids:
			lot_ids.append(line.lot_id.id)
		# print ('quantity=========',quantity)
		# quants = self.env['stock.quant']._update_reserved_quantity(
		# 				stock_move.product_id, stock_move.picking_id.location_dest_id, quantity, lot_id=lot_id,
		# 				package_id=package_id, owner_id=owner_id, strict=False
		# 			)
		# print ('quants=========',quants)
		# for reserved_quant, quantity in quants:
			
		# 	lot_ids.append(reserved_quant.lot_id.id)
		price_line_id =self.env['price.lines'].search([('lot_id', 'in',lot_ids)],limit=1, order='id desc')
		unit_price = price_line_id.unit_price
		return {
			'product_id': stock_move.product_id.id,
			'quantity': quantity,
			'lot_ids' : lot_ids,
			'price_line_id':price_line_id,
			'unit_price':unit_price,
			'move_id': stock_move.id,
			'uom_id': stock_move.product_id.uom_id.id,
		}

	def _create_returns(self):
		# TODO sle: the unreserve of the next moves could be less brutal
		for return_move in self.product_return_moves.mapped('move_id'):
			return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

		# create new picking for returned products
		picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
		new_picking = self.picking_id.copy({
			'move_lines': [],
			'picking_type_id': picking_type_id,
			'state': 'draft',
			'origin': _("Return of %s", self.picking_id.name),
			'location_id': self.picking_id.location_dest_id.id,
			'location_dest_id': self.location_id.id})
		new_picking.message_post_with_view('mail.message_origin_link',
			values={'self': new_picking, 'origin': self.picking_id},
			subtype_id=self.env.ref('mail.mt_note').id)
		returned_lines = 0
		for return_line in self.product_return_moves:
			if not return_line.move_id:
				raise UserError(_("You have manually created product lines, please delete them to proceed."))
			# TODO sle: float_is_zero?
			if return_line.quantity:
				returned_lines += 1
				vals = self._prepare_move_default_values(return_line, new_picking)
				r = return_line.move_id.copy(vals)
				vals = {}

				# +--------------------------------------------------------------------------------------------------------+
				# |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
				# |              | returned_move_ids              ↑                                  | returned_move_ids
				# |              ↓                                | return_line.move_id              ↓
				# |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
				# +--------------------------------------------------------------------------------------------------------+
				move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
				# link to original move
				move_orig_to_link |= return_line.move_id
				# link to siblings of original move, if any
				move_orig_to_link |= return_line.move_id\
					.mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))\
					.mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
				move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
				# link to children of originally returned moves, if any. Note that the use of
				# 'return_line.move_id.move_orig_ids.returned_move_ids.move_orig_ids.move_dest_ids'
				# instead of 'return_line.move_id.move_orig_ids.move_dest_ids' prevents linking a
				# return directly to the destination moves of its parents. However, the return of
				# the return will be linked to the destination moves.
				move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids')\
					.mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))\
					.mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
				vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
				vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
				r.write(vals)
				for lot in return_line.lot_ids:
					line_vals = {
										
						'unit_price':return_line.unit_price,
						'lot_id':lot.id,
						'date':fields.date.today(),	
						'name':str(return_line.unit_price),	
						'desc':'return of '	+ self.picking_id.name	
											
						}
					self.env['price.lines'].create(line_vals)
		if not returned_lines:
			raise UserError(_("Please specify at least one non-zero quantity."))

		new_picking.action_confirm()
		new_picking.action_assign()

		return new_picking.id, picking_type_id