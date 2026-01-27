import { useMemo } from 'react';
import { useQuote } from './useQuote';

/**
 * Hook สำหรับตรวจสอบว่าสินค้าถูกเลือกแล้วหรือไม่
 * @param {string} sku - รหัสสินค้า
 * @param {string|null} variantCode - รหัส variant (optional)
 * @param {number} sqft - ขนาดตารางฟุต (สำหรับกระจก)
 * @returns {boolean} true ถ้าสินค้าถูกเลือกแล้ว, false ถ้ายังไม่ได้เลือก
 */
export function useSelectedStatus(sku, variantCode = null, sqft = 0) {
  const { state } = useQuote();

  return useMemo(() => {
    // Edge case: ถ้า sku เป็น null/undefined/empty → คืนค่า false
    if (!sku || (typeof sku === 'string' && sku.trim() === '')) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('useSelectedStatus: Product missing SKU');
      }
      return false;
    }

    // Normalize values สำหรับการเปรียบเทียบ
    const normalizeVariant = (v) => {
      if (v === '' || v === undefined || v === null) return null;
      return v;
    };

    const normalizeSqft = (v) => {
      if (v === '' || v === undefined || v === null) return 0;
      return Number(v);
    };

    const targetVariant = normalizeVariant(variantCode);
    const targetSqft = normalizeSqft(sqft);

    // ตรวจสอบว่าสินค้ามีอยู่ใน cart หรือไม่
    const isSelected = state.cart.some((item) => {
      // 1. sku ต้องตรงกัน
      if (item.sku !== sku && item.SKU !== sku) return false;

      // 2. variantCode ต้องตรงกัน (หลังจาก normalize)
      const itemVariant = normalizeVariant(item.variantCode ?? item.VariantCode);
      if (itemVariant !== targetVariant) return false;

      // 3. sqft_sheet ต้องตรงกัน (รองรับทั้ง sqft_sheet และ sqft)
      const itemSqft = normalizeSqft(item.sqft_sheet ?? item.sqft);
      if (itemSqft !== targetSqft) return false;

      return true;
    });

    return isSelected;
  }, [sku, variantCode, sqft, state.cart]);
}
