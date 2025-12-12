// frontend/src/utils/glassSku.js
const pad2 = (n) => String(n).padStart(2, "0");
const pad3 = (n) => String(n).padStart(3, "0");

// Fallback ชื่อสี (ใช้เมื่อ API ไม่ส่งชื่อมา)
export const COLOR_MAP = {
  "00": { code:"00", name:"อื่นๆ", nameEn:"Others" },
  "01": { code:"01", name:"สีใส", nameEn:"Clear" },
  "02": { code:"02", name:"สีชาดำ", nameEn:"Dark Bronze" },
  "03": { code:"03", name:"สีเขียว", nameEn:"Green" },
  "04": { code:"04", name:"สีฟ้า", nameEn:"Blue" },
  "05": { code:"05", name:"สี Gray", nameEn:"Gray" },
  "06": { code:"06", name:"สี Bronze", nameEn:"Bronze" },
  "07": { code:"07", name:"สีน้ำเงิน", nameEn:"Navy Blue" },
  "08": { code:"08", name:"สีม่วง", nameEn:"Purple" },
  "09": { code:"09", name:"สีเหลือง", nameEn:"Yellow" },
  "10": { code:"10", name:"สีชมพู", nameEn:"Pink" },
  "11": { code:"11", name:"สีทองแดง", nameEn:"Copper" },
  "12": { code:"12", name:"สีขาว", nameEn:"White" },
  "13": { code:"13", name:"สีดำ", nameEn:"Black" },
};

/**
 * G + BB(2) + TT(2) + SSS(3) + CC(2) + TH(2) + WWW(3) + LLL(3)
 * เช่น G01010010106024060
 */
export function buildGlassSku({
  brand, type, subType, color, thicknessMM, widthIn, lengthIn,
}) {
  const b = pad2(brand);
  const t = pad2(type);
  const s = String(subType).padStart(3, "0");
  const c = pad2(color);
  const th = pad2(thicknessMM);
  const w = pad3(Math.round(Number(widthIn) || 0));
  const l = pad3(Math.round(Number(lengthIn) || 0));
  return `G${b}${t}${s}${c}${th}${w}${l}`;
}

export function parseGlassSku(sku) {
  const re = /^G(\d{2})(\d{2})(\d{3})(\d{2})(\d{2})(\d{3})(\d{3})$/;
  const m = String(sku || "").match(re);
  if (!m) return null;
  const [, brand, type, subType, color, thickness2, width3, length3] = m;
  return {
    brand, type, subType, color,
    thicknessMM: Number(thickness2),
    widthIn: Number(width3),
    lengthIn: Number(length3),
  };
}

export function getThicknessFromSku(sku) {
  if (!sku || sku.length < 12) return null;
  const code = sku.slice(10, 12);
  return /^\d{2}$/.test(code) ? Number(code) : null;
}

export function getSizeInchesFromSku(sku) {
  if (!sku || sku.length < 6) return null;
  const last6 = sku.slice(-6);
  if (!/^\d{6}$/.test(last6)) return null;
  return {
    widthIn: Number(last6.slice(0, 3)),
    lengthIn: Number(last6.slice(3, 6)),
  };
}
