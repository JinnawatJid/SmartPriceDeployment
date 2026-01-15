// customer helper
// ใช้ normalize customer code จากหลาย source

export const getCustomerCode = (cust) => {
  if (!cust) return "";

  const code =
    cust.id ||
    cust.customerCode ||
    cust.CustomerCode ||
    cust.Customer ||
    cust.No_ ||
    cust.no_;

  return typeof code === "string" ? code.trim() : "";
};
