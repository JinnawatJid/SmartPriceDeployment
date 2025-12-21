import { createContext, useReducer, useContext } from "react";

export const QuoteContext = createContext(null);
export function useQuote() {
  return useContext(QuoteContext);
}

const initialState = {
  step: 1,

  customer: null,
  deliveryAddress: null,
  vehicle: null,
  deliveryType: "PICKUP",

  cart: [],

  totals: {
    exVat: 0,
    vat: 0,
    grandTotal: 0,
    shippingRaw: 0,
    shippingCustomerPay: 0,
  },

  needsTax: false,
  billTaxName: "",
  remark: "",
  status: "new",
  quoteNo: null,
};


function quoteReducer(state, action) {
  switch (action.type) {

    case "SET_STEP":
      return { ...state, step: action.payload };

    case "SET_CUSTOMER":
      return { ...state, customer: action.payload };

    case "SET_TAX_DELIVERY":
      return {
        ...state,
        needsTax: action.payload.needsTax,
        deliveryType: action.payload.deliveryType,
        billTaxName: action.payload.billTaxName,
      };

    case "SET_SHIPPING":
      return {
        ...state,
        shippingCost: action.payload.cost,
        distance: action.payload.distance,
        shippingCustomerPay: action.payload.customerPay ?? state.shippingCustomerPay,
        shippingCompanyPay: action.payload.companyPay ?? state.shippingCompanyPay,
        vehicleType: action.payload.vehicleType ?? state.vehicleType,
        unloadHours: action.payload.unloadHours ?? state.unloadHours,
        staffCount: action.payload.staffCount ?? state.staffCount,
      };


    case "SET_DELIVERY_ADDRESS":
      return { ...state, deliveryAddress: action.payload };

    case "SET_VEHICLE":
      return { ...state, vehicle: action.payload };



// ⭐ ADD ITEM (รองรับ Variant)
// -------------------------
  case "ADD_ITEM": {
    const newItem = action.payload;

    // 🔑 เงื่อนไข merge:
    // sku + variantCode + sqft ต้องเหมือนกัน
    const exists = state.cart.find((it) =>
      it.sku === newItem.sku &&
      (it.variantCode ?? null) === (newItem.variantCode ?? null) &&
      Number(it.sqft ?? 0) === Number(newItem.sqft ?? 0)
    );

    // ❌ ไม่มีรายการซ้ำ → เพิ่มบรรทัดใหม่
    if (!exists) {
      return {
        ...state,
        cart: [...state.cart, newItem],
      };
    }

    // ✅ มีรายการเดียวกันจริง → merge โดยเพิ่มจำนวน
    return {
      ...state,
      cart: state.cart.map((it) =>
        it === exists
          ? { ...it, qty: Number(it.qty) + Number(newItem.qty ?? 0) }
          : it
      ),
    };
  }


    // -------------------------
    // ⭐ UPDATE QTY
    // -------------------------
    case "UPDATE_CART_QTY":
      return {
        ...state,
        cart: state.cart.map((it) =>
          it.sku === action.payload.sku
            ? { ...it, qty: action.payload.qty }
            : it
        ),
      };

    // -------------------------
    // ⭐ REMOVE ITEM
    // -------------------------
    case "REMOVE_ITEM":
      return {
        ...state,
        cart: state.cart.filter((i) => i.sku !== action.payload),
      };


    // -------------------------
    // SET_CART (ใช้ใน load draft)
    // -------------------------
    case "SET_CART":
      return { ...state, cart: action.payload };

    // -------------------------
    // SET_TOTALS
    // -------------------------
    case "SET_TOTALS":
      return { ...state, totals: { ...state.totals, ...action.payload } };


    // -------------------------
    // LOAD_DRAFT
    // -------------------------
    case "LOAD_DRAFT":
      return {
        ...state,
        status: "open",
        id: action.payload.id,
        quoteNo: action.payload.quoteNo,
        step: 6,
        customer: {
          id: action.payload.customer?.id || "",
          code: action.payload.customer?.code || action.payload.customer?.id || "",
          name: action.payload.customer?.name || "",
          phone: action.payload.customer?.phone || "",
        },

        deliveryType: action.payload.deliveryType ?? "PICKUP",
        billTaxName: action.payload.billTaxName || "",
        remark: action.payload.note || "",
        cart: action.payload.cart || [],
        shippingCost: action.payload.totals?.shippingRaw ?? 0,
        shippingCustomerPay: action.payload.totals?.shippingCustomerPay ?? 0,
        shippingCompanyPay: action.payload.totals?.shippingCompanyPay ?? 0, // ถ้าคุณต้องการ
        totals: {
          ...state.totals,
          exVat: action.payload.totals?.exVat ?? 0,
          vat: action.payload.totals?.vat ?? 0,
          grandTotal: action.payload.totals?.grandTotal ?? 0,
          shippingRaw: action.payload.totals?.shippingRaw ?? 0,
          shippingCustomerPay: action.payload.totals?.shippingCustomerPay ?? 0
        },

      };


    // -------------------------
    // RESET QUOTE
    // -------------------------
    case "RESET_QUOTE":
      return { ...initialState };

    default:
      return state;
  }
}


export function QuoteProvider({ children }) {
  const [state, dispatch] = useReducer(quoteReducer, initialState);
  return (
    <QuoteContext.Provider value={{ state, dispatch }}>
      {children}
    </QuoteContext.Provider>
  );
}
