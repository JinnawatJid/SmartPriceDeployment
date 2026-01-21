// key helpers สำหรับ cart / pricing / print
export const uiKeyOf = (it) =>
  `${it.sku}__${it.variantCode ?? ""}__${Number(it.sqft_sheet ?? it.sqft ?? 0)}`;

export const pricingKeyOf = (it) => `${it.sku}__${Number(it.sqft_sheet ?? it.sqft ?? 0)}`;

export const printKeyOf = (it) => `${it.sku}__${Number(it.sqft_sheet ?? it.sqft ?? 0)}`;
