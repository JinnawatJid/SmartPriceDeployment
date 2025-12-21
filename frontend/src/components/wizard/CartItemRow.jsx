// src/components/wizard/CartItemRow.jsx
import React from 'react';
import { useQuote } from '../../hooks/useQuote.js';

// ไอคอนถังขยะ
const TrashIcon = () => (
  <img src="/assets/delete.png" alt="delete" className="h-5 w-5 mr-4 mt-1 object-contain" />
);


const CartItemRow = ({ item, index, calculatedItem, dispatch }) => {
  const handleRemove = () => {
    dispatch({ type: 'REMOVE_ITEM', payload: item.sku });
  };

  const handleQtyChange = (e) => {
    const newQty = Math.max(1, Number(e.target.value));
    dispatch({ type: 'UPDATE_CART_QTY', payload: { sku: item.sku, qty: newQty } });
  };
  const unitPrice = item.price_per_sheet ?? item.UnitPrice;

  return (
    <tr className="border-b border-gray-200 bg-white hover:bg-gray-50">
      {/* Index */}
      <td className="px-4 py-3 text-sm font-medium text-gray-600">{index + 1}</td>
      
      {/* Name/SKU */}
      <td className="px-4 py-3">
        <p className="font-semibold text-xs text-gray-900">{item.name}</p>
        <p className="text-xs text-gray-500">{item.sku}</p>
      </td>
      
      
      {/* Qty */}
      <td className="px-4 py-3" style={{ minWidth: '100px' }}>
        <input
          type="number"
          value={item.qty}
          onChange={handleQtyChange}
          className="w-20 rounded-md border border-gray-300 p-1 text-center font-medium shadow-sm"
          min="1"
        />
      </td>
      
      {/* Price */}
      <td className="px-4 py-3 text-start text-sm text-gray-700">
        {Number(
          calculatedItem?.price_per_sheet
            ?? item.price_per_sheet
            ?? calculatedItem?.UnitPrice
            ?? item.UnitPrice
            ?? item.price
        ).toLocaleString('th-TH')}
      </td>

      
      
      {/* Total */}
      <td className="px-4 py-3 text-start text-sm font-semibold text-gray-900">
        {Number(calculatedItem?._LineTotal ?? (item.price * item.qty)).toLocaleString('th-TH')}
      </td>
      
      {/* Actions */}
      <td className="text-center">
        <button
          onClick={handleRemove}
          className="text-red-500 hover:text-red-700"
        >
          <TrashIcon />
        </button>
      </td>
    </tr>
  );
};

export default CartItemRow;