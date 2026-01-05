// src/pages/CreateQuote/Step6_Summary.jsx
import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "../../hooks/useAuth.js";
import api from "../../services/api.js";
import { useNavigate } from "react-router-dom";

import ShippingModal from "../../components/wizard/ShippingModal.jsx";
import CustomerSearchSection from "../../components/wizard/CustomerSearchSection.jsx";
import TaxDeliverySection from "../../components/wizard/TaxDeliverySection.jsx";
import ItemPickerModal from "../../components/wizard/ItemPickerModal.jsx";
import GlassPickerModal from "../../components/wizard/GlassPickerModal.jsx";
import CategoryCard from "../../components/wizard/CategoryCard.jsx";
import CartItemRow from "../../components/wizard/CartItemRow.jsx";
import OrderHistoryCard from "../../components/wizard/OrderHistoryCard.jsx";

import ProductList from "../../components/products/ProductList.jsx";
import ProductDetail from "../../components/products/ProductDetail.jsx";
import ProductImage from "../../components/products/ProductImage.jsx";
import ProductCategorySelector from "../../components/products/ProductCategorySelector.jsx";
import DynamicsProductFilter from "../../components/products/DynamicsProductFilter.jsx";
// ---- Icons ----
  const PlusIcon = () => (
    <svg
        className="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={2.5}
        stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 4.5v15m7.5-7.5h-15"
      />
    </svg>
  );

  const FileIcon = () => (
    <img
    src="/assets/folder.png"
    alt="Print"
    className="h-6 w-6 mr-2 object-contain"
    />
  )

  const SaveIcon = () => (
    <img
    src="/assets/Save.png"
    alt="Print"
    className="h-5 w-5 mr-2 object-contain"
    />
  );

  const DraftIcon = () => (
    <img
    src="/assets/draft.png"
    alt="Print"
    className="h-6 w-6 mr-2 object-contain"
    />
  )

  const PrintIcon = () => (
    <img
    src="/assets/printer.png"
    alt="Print"
    className="h-5 w-5 mr-2 object-contain"
    />
  );

const ArrowLeftIcon = () => (
  <svg
  className="w-5 h-5 mr-2"
  fill="none"
  viewBox="0 0 24 24"
  strokeWidth={2}
  stroke="currentColor"
  >
  <path
  strokeLinecap="round"
  strokeLinejoin="round"
  d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
  />
  </svg>
);

const SummaryRow = ({ label, value, isTotal = false, loading = false }) => (
  <div className="flex justify-between py-2">
    <span
      className={`font-semibold ${
        isTotal ? "text-lg text-gray-900" : "text-gray-600"
      }`}
      >
      {label}
    </span>
    <span
      className={`font-bold ${
        isTotal ? "text-xl text-blue-600" : "text-gray-800"
      }`}
      >
      {loading ? (
      <span className="inline-block h-4 w-24 animate-pulse rounded-md bg-gray-300" />
      ) : (
      value
      )}
    </span>
  </div>
);

function Step6_Summary({ state, dispatch }) {
  const { employee } = useAuth();
  const navigate = useNavigate();

  //search
  const [productSearch, setProductSearch] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  
  // ประวัติการซื้อ
  const [historyOrders, setHistoryOrders] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  
  
  // local UI state
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [shippingOpen, setShippingOpen] = useState(false);
  const [glassOpen, setGlassOpen] = useState(false);
  
  // Product browser state
  const [productFilters, setProductFilters] = useState({});
  const [productItems, setProductItems] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productLoading, setProductLoading] = useState(false);
  
  // UI Tabs: "quote" | "customer" | "products"
  const [activeTab, setActiveTab] = useState("quote");
  
  // Category list
  const [categories, setCategories] = useState([]);
  const [catLoading, setCatLoading] = useState(true);
  const [catError, setCatError] = useState("");
  const [itemModalOpen, setItemModalOpen] = useState(false);
  
  
  // ราคาที่ได้จาก backend
  const [calculation, setCalculation] = useState({
    cart: [],
    totals: {},
    loading: true,
    error: null,
  });
  
  const getCustomerCode = (cust) => {
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

  
  const handleRepeatFromHistory = (order) => {
    if (!order) return;

    dispatch({
      type: "LOAD_DRAFT",
      payload: {
        id: null,
        quoteNo: null,

        customer: {
          id: order.customer?.id || order.customer?.code || "",
          code: order.customer?.id || order.customer?.code || "",
          name: order.customer?.name || "",
          phone: order.customer?.phone || "",
          _needsHydrate: true, // ⭐ ให้ Step6 auto search
        },

        deliveryType: order.deliveryType ?? "PICKUP",
        billTaxName: order.billTaxName ?? "",
        note: order.note ?? "",

        cart: (order.cart || []).map(it => ({
          ...it,
          source: "db",
          needsPricing: false,
          isDraftItem: true,
        })),

        totals: {
          exVat: 0,
          vat: 0,
          grandTotal: 0,
          shippingRaw: 0,
          shippingCustomerPay: 0,
          shippingCompanyPay: 0,
        },
      },
    });

  };

  // ⭐ unique key กัน sku ซ้ำ / variant / sqft
// ⭐ 1) key สำหรับ UI (กันซ้ำ)
const uiKeyOf = (it) =>
  `${it.sku}__${it.variantCode ?? ""}__${Number(it.sqft_sheet ?? it.sqft ?? 0)}`;

// ⭐ 2) key สำหรับจับคู่ pricing (ห้ามใส่ variantCode)
const pricingKeyOf = (it) =>
  `${it.sku}__${Number(it.sqft_sheet ?? it.sqft ?? 0)}`;
// key สำหรับ print / pricing (ห้ามมี variantCode)
const printKeyOf = (it) =>
  `${it.sku}__${Number(it.sqft_sheet ?? it.sqft ?? 0)}`;




const isDraftLike = (state, it) => {
  if (state.status !== "open") return false;
  return it.isDraftItem === true || it.source === "db";
};


  
useEffect(() => {
  const fmtTHB = (v) =>
    Number(v || 0).toLocaleString("th-TH", {
      style: "currency",
      currency: "THB",
    });


  if (state.status === "open") {
    const itemsNeedingPricing = (state.cart || []).filter(
      it => it.source === "ui" && it.needsPricing
    );

    const sumLine = (arr) =>
      arr.reduce(
        (sum, it) =>
          sum +
          Number(
            it.lineTotal ??
            (Number(it.price || 0) * Number(it.qty || 0))
          ),
        0
      );

    const shipping = Number(state.shippingCustomerPay || 0);


    // ✅ ถ้า "ไม่มีสินค้าใหม่" → ใช้ยอดเดิมทั้งหมด
    if (itemsNeedingPricing.length === 0) {
    const subtotalGross = sumLine(state.cart);
    const grossBeforeVat = subtotalGross + shipping;
    const vat = Math.round(grossBeforeVat * 0.07 * 100) / 100;
    const exVat = grossBeforeVat - vat;
    const total = grossBeforeVat;

    setCalculation({
      cart: [], // Draft ไม่ใช้ calculated.cart
      totals: {
        exVat,
        vat,
        total,
        exVatFmt: fmtTHB(exVat),
        vatFmt: fmtTHB(vat),
        totalFmt: fmtTHB(total),
      },
      loading: false,
      error: null,
    });
    return;
  }


    // ✅ ถ้ามีสินค้าใหม่ → pricing เฉพาะสินค้าใหม่
    setCalculation((prev) => ({ ...prev, loading: true }));

  const calcDraft = async () => {
    try {
      const customerCode = getCustomerCode(state.customer);

      const res = await api.post("/api/pricing/calculate", {
        customerData: {
        customerCode,
        customerName: state.customer?.name || "",
        paymentTerm:
          state.customer?.paymentTerm ??
          state.customer?.creditTerm ??
          state.customer?.payment_terms ??
          "",

        paymentMethod: state.customer?.paymentMethod || "",

        // ⭐ scoring fields
        customer_date: state.customer?.customer_date,
        accum_6m: Number(state.customer?.accum_6m || 0),
        frequency: Number(state.customer?.frequency || 0),
        gen_bus: state.customer?.gen_bus,

        shippingCustomerPay: Number(state.shippingCustomerPay || 0),
      },
        
        deliveryType: state.deliveryType,
        cart: itemsNeedingPricing.map(it => ({
          sku: it.sku,
          name: it.name ?? "",
          qty: Number(it.qty || 0),
          sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
          cost: it.cost,
          pkg_size: Number(it.pkg_size ?? 1),
          category: it.category,
          unit: it.unit ?? "",
          product_weight: it.product_weight ?? 0,

          relevantSales:
              it.category === "S"
                ? Number(state.customer?.sales_s_cust ?? 0)
              : it.category === "G"
                ? Number(state.customer?.sales_g_cust ?? 0)
              : it.category === "A"
                ? Number(state.customer?.sales_a_cust ?? 0)
              : it.category === "C"
                ? Number(state.customer?.sales_c_cust ?? 0)
              : it.category === "E"
                ? Number(state.customer?.sales_e_cust ?? 0)
              : it.category === "Y"
                ? Number(state.customer?.sales_y_cust ?? 0)
              : 0,
        })),
      });

      const pricedItems = res.data.items || [];


          pricedItems.forEach(pi => {
            const key = `${pi.sku}__${Number(pi.sqft_sheet ?? 0)}`;

            dispatch({
              type: "APPLY_PRICING_RESULT",
              payload: { key, priced: pi },
            });
          });


            const subtotalGross = sumLine(state.cart);
            const grossBeforeVat = subtotalGross + shipping;
            const vat = Math.round(grossBeforeVat * 0.07 * 100) / 100;
            const exVat = grossBeforeVat - vat;
            const total = grossBeforeVat;

            setCalculation({
              cart: [],
              totals: {
                exVat,
                vat,
                total,
                exVatFmt: fmtTHB(exVat),
                vatFmt: fmtTHB(vat),
                totalFmt: fmtTHB(total),
              },
              loading: false,
              error: null,
            });

      } catch (err) {
        console.error(err);
        setCalculation({
          cart: [],
          totals: {},
          loading: false,
          error: "เกิดข้อผิดพลาดในการคำนวณราคา (Draft + New Items)",
        });
      }
    };

    calcDraft();
    return;
  }


  // -------------------------------------------------
  // 3) NO ITEMS
  // -------------------------------------------------
  if (!state.cart || state.cart.length === 0) {
    setCalculation({
      cart: [],
      totals: {},
      loading: false,
      error: null,
    });
    return;
  }

  // -------------------------------------------------
  // 4) NEW QUOTE → PRICING BACKEND
  // -------------------------------------------------
  setCalculation((prev) => ({ ...prev, loading: true }));

  const calc = async () => {
    try {
      const customerCode = getCustomerCode(state.customer);

      const res = await api.post("/api/pricing/calculate", {
        customerData: {
          customerCode,
          customerName: state.customer?.name || "",
          paymentTerm:
            state.customer?.paymentTerm ??
            state.customer?.creditTerm ??
            state.customer?.payment_terms ??
            "",

          paymentMethod: state.customer?.paymentMethod || "",

          // ✅ scoring fields (ต้องเพิ่มตรงนี้)
          customer_date: state.customer?.customer_date,
          accum_6m: Number(state.customer?.accum_6m || 0),
          frequency: Number(state.customer?.frequency || 0),
          gen_bus: state.customer?.gen_bus,

          shippingCustomerPay: Number(state.shippingCustomerPay || 0),
        },

        deliveryType: state.deliveryType,
        cart: state.cart.map((it) => ({
          sku: it.sku,
          name: it.name ?? "",
          qty: Number(it.qty || 0),
          sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
          cost: it.cost,
          pkg_size: Number(it.pkg_size ?? 1),
          category: it.category,
          unit: it.unit ?? "",
          DeliveryType: state.deliveryType,
          _RelevantSales: state._RelevantSales ?? 0,

          relevantSales:
             it.category === "S"
              ? Number(state.customer?.sales_s_cust ?? 0)
             : it.category === "G"
              ? Number(state.customer?.sales_g_cust ?? 0)
             : it.category === "A"
              ? Number(state.customer?.sales_a_cust ?? 0)
             : it.category === "C"
              ? Number(state.customer?.sales_c_cust ?? 0)
             : it.category === "E"
              ? Number(state.customer?.sales_e_cust ?? 0)
             : it.category === "Y"
              ? Number(state.customer?.sales_y_cust ?? 0)
             : 0,
        })),
      });

      const items = res.data.items || [];
      const {
        subtotal,
        vat,
        total,
        product_total,
        shippingCustomerPay,
        profit,
      } = res.data.totals || {};

      setCalculation({
        cart: items,
        totals: {
          exVat: subtotal,
          vat,
          total,
          productTotal: product_total,
          shippingCustomerPay,
          profit: profit ?? 0,
          exVatFmt: fmtTHB(subtotal),
          vatFmt: fmtTHB(vat),
          totalFmt: fmtTHB(total),
        },
        loading: false,
        error: null,
      });
    } catch (err) {
      console.error(err);
      setCalculation({
        cart: [],
        totals: {},
        loading: false,
        error: "เกิดข้อผิดพลาดในการคำนวณราคา",
      });
    }
  };

  calc();
}, [
  state.status,
  state.cart,
  state.customer,
  state.deliveryType,
  state.shippingCustomerPay,
]);

// ===============================
// AUTO RECALC SHIPPING (AFTER PRICING)
// ===============================
useEffect(() => {
  // ต้องเป็น delivery
  if (state.deliveryType !== "DELIVERY") return;

  // ต้อง dirty
  if (!state.shippingDirty) return;

  // ต้อง pricing เสร็จแล้ว
  if (calculation.loading) return;

  const t = setTimeout(() => {
    recalcShippingFromCart();
  }, 500);

  return () => clearTimeout(t);
}, [
  calculation.loading,     // ⭐ ตัวควบคุมลำดับ
  state.shippingDirty,
  state.deliveryType,
  state.vehicleType,
  state.distance,
  state.unloadHours,
  state.staffCount,
]);


  
    //FullSearch
    useEffect(() => {
      if (!productSearch || productSearch.length < 3) {
        setSearchResults([]);
        setShowDropdown(false);
        return;
      }

      const t = setTimeout(async () => {
        try {
          const res = await api.get("/api/items/search", {
            params: { q: productSearch },
          });

          const items = (res.data || [])
          setSearchResults(items);
          setShowDropdown(true);
        } catch (e) {
          console.error(e);
        }
      }, 300);

      return () => clearTimeout(t);
    }, [productSearch]);


  // โหลดประวัติการซื้อ
  useEffect(() => {
    const cust = state.customer;
    const custCode = getCustomerCode(cust || "").toString().trim();
    
    if (!custCode) {
      setHistoryOrders([]);
      setHistoryError("");
      setHistoryLoading(false);
      return;
    }
    
    const currentSkus = new Set(
    (state.cart || []).map((it) => it.sku).filter(Boolean)
    );
    
    const fetchHistory = async () => {
      try {
        setHistoryLoading(true);
        setHistoryError("");
        
        const res = await api.get("/api/quotation?status=complete");
        const all = res.data || [];
        
        const filtered = all.filter((q) => {
          const qc = q.customer || {};
          const qCode = getCustomerCode(qc).toString().trim();
          if (qCode !== custCode) return false;
          
          if (!currentSkus.size) return true;
          
          const cart = q.cart || [];
          return cart.some((line) => currentSkus.has(line.sku));
        });
        
        filtered.sort((a, b) =>
        (a.createdAt || a.updatedAt || "") <
        (b.createdAt || b.updatedAt || "")
        ? 1
        : -1
        );
        
        setHistoryOrders(filtered.slice(0, 5));
      } catch (err) {
        console.error("load history error:", err);
        setHistoryError("ไม่สามารถโหลดประวัติการซื้อ");
      } finally {
        setHistoryLoading(false);
      }
    };
    
    fetchHistory();
  }, [state.customer, state.cart]);

  const handleQuickAdd = (item) => {
  dispatch({
    type: "ADD_ITEM",
    payload: {
      sku: item.sku,
      name: item.name,
      qty: 1,
      price: item.priceR2 ?? item.prices?.R2 ?? 0,
      cost: Number(item.cost || 0),
      category: item.category || "",
      unit: item.unit || item.saleUnit || item.uom || "",

      // ✅ forward meta จาก items master เพื่อให้ pricing/shipping/save ใช้ได้ทันที
      product_weight: Number(item.product_weight || 0),
      sqft_sheet: Number(item.sqft_sheet || 0),
      pkg_size: Number(item.pkg_size || 1),
    },
  });

  setProductSearch("");
  setSearchResults([]);
  setShowDropdown(false);
};

// -------------------------------------------------
// Auto-hydrate customer (Draft/Repeat) โดยไม่ยิง pricing ซ้ำ
// -------------------------------------------------
useEffect(() => {
  const cust = state.customer;
  const custCode = String(getCustomerCode(cust || {}) || "").trim();

  // ไม่มีรหัสลูกค้า → ไม่ต้อง hydrate
  if (!custCode) return;

  // ใช้ flag จาก QuoteContext (LOAD_DRAFT / REPEAT_FROM_HISTORY)
  if (!cust?._needsHydrate) return;

  let cancelled = false;

  (async () => {
    try {
      const res = await api.get("/api/customer/search", {
        params: { code: custCode },
      });

      if (cancelled) return;

      const full = res.data || {};

      // merge: ยึดของเดิมไว้ก่อน แล้วเติม scoring fields จาก search
      // ✅ ไม่แตะ cart → ไม่ทำให้สินค้าที่อยู่แล้วถูก pricing ซ้ำ
      dispatch({
        type: "SET_CUSTOMER",
        payload: {
          ...(cust || {}),
          ...full,
          id: full.id || cust.id || custCode,
          code: full.id || cust.code || custCode,
          _needsHydrate: false,
        },
      });
    } catch (err) {
      console.error("auto hydrate customer failed:", err);

      // กัน loop: hydrate ไม่สำเร็จก็ปิด flag ไว้ก่อน
      if (!cancelled) {
        dispatch({
          type: "SET_CUSTOMER",
          payload: {
            ...(cust || {}),
            _needsHydrate: false,
          },
        });
      }
    }
  })();

  return () => {
    cancelled = true;
  };
}, [state.customer]);


  
  // sku -> item (ราคาที่คำนวณใหม่)
  const calcMap = useMemo(
  () => Object.fromEntries((calculation.cart || []).map((it) => [pricingKeyOf(it), it])),
  [calculation.cart]
);
  
  
  const fmtTHB = (n) =>
  n.toLocaleString("th-TH", { style: "currency", currency: "THB" });
  
  const [saving, setSaving] = useState(false);
  
 

const buildQuotationPayload = (status) => {
  const isEditDraft = state.status === "open";

  const cartPayload = (state.cart || []).map((it) => {
    // ✅ 1) คำนวณ key ให้ถูก
    const key = pricingKeyOf(it);

    // ✅ 2) ดึง calculated item (pricing result)
    const calc = calcMap?.[key];

    let unitPrice = 0;
    let lineTotal = 0;

    // ✅ 3) ราคา
    if (isEditDraft) {
      unitPrice = Number(it.UnitPrice ?? it.price ?? 0);
      lineTotal = Number(
        it.lineTotal ?? unitPrice * Number(it.qty ?? 0)
      );
    } else {
      unitPrice = Number(
        calc?.UnitPrice ?? it.UnitPrice ?? it.price ?? 0
      );
      lineTotal = Number(
        calc?._LineTotal ?? unitPrice * Number(it.qty ?? 0)
      );
    }

    // ✅ 4) คืน payload ที่ใช้ "effective value"
    return {
      sku: it.sku,
      name: it.name,
      qty: Number(it.qty ?? 0),

      // ⭐ ราคา (source of truth)
      price: unitPrice,
      lineTotal: lineTotal,

      UnitPrice: unitPrice, // optional
      LineTotal: lineTotal, // optional

      // ⭐ meta (สำคัญ)
      unit:
        calc?.unit ??
        it.unit ??
        "",

      product_weight:
        calc?.product_weight ??
        it.product_weight ??
        0,

      category: it.category ?? "",
      sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
      variantCode: it.variantCode ?? "",
    };
  });

  return {
    status,
    employee: employee
      ? { id: employee.id, name: employee.name, branchId: employee.branchId ?? null }
      : null,
    needTaxInvoice: state.needsTax ?? false,
    customer: {
      ...state.customer,
      code: state.customer?.id || state.customer?.code || "",
    },
    deliveryType: state.deliveryType || null,
    cart: cartPayload,
    totals: {
      exVat: calculation.totals.exVat ?? null,
      vat: calculation.totals.vat ?? null,
      grandTotal: calculation.totals.total ?? null,
      shippingCustomerPay: state.shippingCustomerPay ?? 0,
    },
    billTaxName: state.billTaxName || "",
    note: state.remark || "",
  };
};

  
  // โหลดสินค้าใน product tab
  useEffect(() => {
    if (activeTab !== "products" || !selectedCategory) return;
    
    async function loadItems() {
      try {
        setProductLoading(true);
        let url = "";
        switch (selectedCategory) {
          case "A":
          url = "/api/aluminium/items";
          break;
          case "C":
          url = "/api/cline/items";
          break;
          case "E":
          url = "/api/accessories/items";
          break;
          case "G":
          url = "/api/glass/list";
          break;
          case "Y":
          url = "/api/gypsum/items";
          break;
          case "S":
          url = "/api/sealant/items";
          break;
          default:
          setProductLoading(false);
          return;
        }
        
        const res = await api.get(url, { params: productFilters });
        const items = res.data.items || res.data;
        setProductItems(
        items.map((it) => ({
          ...it,
          name: it.name || it.description || it.Description || "",
        }))
        );
        
      } catch (err) {
        console.error("load items error:", err);
      } finally {
        setProductLoading(false);
      }
    }
    
    loadItems();
  }, [activeTab, productFilters, selectedCategory]);
  
  async function saveQuotation(payload, state) {
    if (state.id) {
      return await api.put(`/api/quotation/${state.id}`, payload);
    }
    return await api.post("/api/quotation", payload);
  }
  
  console.log("PAYLOAD TO SAVE", buildQuotationPayload(status));

  

// ===============================
// RECALCULATE SHIPPING FROM CART
// ===============================
const recalcShippingFromCart = async () => {
  // ไม่ต้องคำนวณถ้าไม่ใช่ delivery
  if (state.deliveryType !== "DELIVERY") return;

  // ยังไม่ dirty ไม่ต้องยิง
  if (!state.shippingDirty) return;

  // ต้องมีข้อมูลครบก่อน
  if (
    !state.vehicleType ||
    !state.distance ||
    state.unloadHours == null ||
    state.staffCount == null
  ) {
    return;
  }

  try {
    const res = await api.post("/api/shipping/calculate_from_cart", {
      vehicle_type: state.vehicleType,
      distance_km: Number(state.distance || 0),
      unload_hours: Number(state.unloadHours || 0),
      staff_count: Number(state.staffCount || 0),
      cart: buildCartForShipping(state.cart),
    });

    dispatch({
      type: "SET_SHIPPING",
      payload: {
        distance: state.distance,
        cost: Number(res.data.shipping_cost || 0),
        companyPay: Number(res.data.company_pay || 0),
        customerPay: Number(res.data.customer_pay || 0),
        vehicleType: state.vehicleType,
        unloadHours: state.unloadHours,
        staffCount: state.staffCount,
      },
    });
  } catch (err) {
    console.error("auto recalc shipping error", err);
  }
};




// ===============================
// BUILD CART FOR SHIPPING
// ===============================
const buildCartForShipping = () => {
  return state.cart.map((item) => {
    const sqft = Number(item.sqft_sheet ?? item.sqft ?? 0);
    const qty = Number(item.qty ?? 0);

    const key = `${item.sku}__${sqft}`;
    const calculatedItem = calcMap[key];

    const isGlass = item.category === "G";

    const unitPrice =
      Number(
        calculatedItem?.price_per_sheet ??
        calculatedItem?.UnitPrice ??
        item.price ??
        item.UnitPrice ??
        0
      );

    const lineTotal =
      Number(
        calculatedItem?._LineTotal ??
        calculatedItem?.lineTotal ??
        item.lineTotal ??
        0
      );

    // =========================
    // GLASS PRICE NORMALIZATION
    // =========================
    let priceToSend = unitPrice;

    if (isGlass) {
      // 1) NewQuote → pricing ส่ง price_per_sheet มาแล้ว
      if (calculatedItem?.price_per_sheet > 0) {
        priceToSend = Number(calculatedItem.price_per_sheet);

      // 2) Draft / Repeat → reconstruct หน่วย
      } else if (lineTotal > 0 && qty > 0) {
        const perUnit = lineTotal / qty;

        // ถ้า lineTotal ใกล้ unitPrice*qty*sqft → unitPrice คือ ต่อ sqft
        if (sqft > 0 && Math.abs(perUnit - unitPrice * sqft) < 0.01) {
          priceToSend = unitPrice * sqft; // แปลงเป็น ต่อแผ่น
        } else {
          priceToSend = perUnit; // assume ต่อแผ่น
        }

      // 3) fallback สุดท้าย (Draft เก่า)
      } else if (sqft > 0) {
        priceToSend = unitPrice * sqft;
      }
    }

    return {
      sku: item.sku,
      qty,
      price: Number(priceToSend || 0), // ✅ กระจก = ต่อแผ่น เสมอ
      sqft_sheet: sqft,
      cost: item.cost ?? 0,
      category: item.category,
      unit: item.unit,
      product_weight: item.product_weight,
    };
  });
};



const handleSaveQuotation = async (status) => {
    try {
      setSaving(true);
      const payload = buildQuotationPayload(status);
      await saveQuotation(payload, state);
      
      dispatch({ type: "RESET_QUOTE" });
      
      if (status === "open") {
        navigate("/quote-drafts");
      } else {
        if (state.id) {
          navigate("/confirmed-quotes");
        } else {
          alert("บันทึกใบเสนอราคา (สถานะ Complete) เรียบร้อยแล้ว");
        }
      }
    } catch (err) {
      console.error(err);
      alert("บันทึกใบเสนอราคาไม่สำเร็จ");
    } finally {
      setSaving(false);
    }
  };
  
  const handleGoBack = () => dispatch({ type: "SET_STEP", payload: 3 });
  const handlePrint = async () => {
    if (calculation.loading || calculation.error) return;
      console.log(
        "=== PRINT SOURCE ===",
        calculation.cart.map(i => ({
          sku: i.sku,
          unit: i.unit
        }))
      );

    const grandTotal =
          calculation.totals.total ??
          calculation.totals.grandTotal ??
          0;
    const printSourceItems =
      calculation.cart && calculation.cart.length > 0
        ? calculation.cart   // new quote (pricing ใหม่)
        : state.cart;        // repeat / draft

    const payload = {
      quoteNo: state.quoteNo || "",
      date: new Date().toLocaleDateString("th-TH"),
      sales: employee?.name || "",
      customer: {
        code: state.customer?.id || state.customer?.code || "",
        name: state.customer?.name || "ผู้ไม่ประสงค์ออกนาม",
        phone: state.customer?.phone || "",
      },
      items: printSourceItems.map((it) => {
      const original =
        state.cart.find(x => printKeyOf(x) === printKeyOf(it));;
        const unit =
          it.unit ||                 // จาก pricing
          original?.unit ||          // จาก cart
          "-";
        const isGlass = (original.category || it.category) === "G";

        const price = Number(
          it.price_per_sheet ??
          it.UnitPrice ??
          it.price ??
          original?.price ??
          0
        );

        const amount = Number(
          it._LineTotal ??
          it.lineTotal ??
          price * Number(it.qty || 0)
        );

        return {
          code: it.sku,
          name: original.name || it.name || "",
          qty: Number(it.qty || 0),
          unit,
         price: Number(
          it.price_per_sheet ??
          it.UnitPrice ??
          it.price ??
          original?.price ??
          0
        ),
        amount: Number(
          it._LineTotal ??
          it.lineTotal ??
          0
        ),
        };
      })


      ,

      comment: state.remark || "",
      shipping: Number(state.shippingCustomerPay || 0),
      amountText: "", // ค่อยทำทีหลัง
      total: grandTotal, 
      discount: "0.00",
      afterDiscount: grandTotal,
      exVat: calculation.totals.exVat ?? 0,
      vat: calculation.totals.vat ?? 0,
      netTotal: grandTotal,
    };

    // Use relative path for print endpoint to work in both Docker (Nginx proxy) and Native (Backend serve)
    const res = await fetch("/print/quotation"
      , {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url); // เปิด PDF
  };

  
  // โหลด Category
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await api.get("/api/items/categories/list");
        setCategories(res.data || []);
      } catch (err) {
        console.error(err);
        setCatError("ไม่สามารถโหลดประเภทสินค้า");
      } finally {
        setCatLoading(false);
      }
    };
    fetchCategories();
  }, []);
  
  const handleCategoryClick = (categoryName) => {
    if (!categoryName) return;
    setSelectedCategory(categoryName);
    
    if (activeTab === "products") {
      // ใช้ product browser
      return;
    }
    
    if (categoryName === "G") {
      setGlassOpen(true);
    } else {
      setItemModalOpen(true);
    }
  };
  
  const handleItemPicked = (item, qty) => {
    if (!item) return;
    dispatch({
      type: "ADD_ITEM",
      payload: {
        sku: item.sku,
        name: item.name,
        qty,
        price: item.prices?.R2 || 0,
        cost: Number(item.cost || 0),
        category: item.category || selectedCategory || "",
        unit: item.unit || item.saleUnit || item.uom || "",
        product_weight: Number(item.product_weight || 0),
        pkg_size: Number(item.pkg_size || 1),
      },
    });
  };
  console.log("=== STEP6 STATE AFTER LOAD_DRAFT ===", state);

  
  return (
  <div className="rounded-lg bg-white p-6 shadow-lg flex flex-col animate-fadeIn">
  <h1 className="text-2xl font-bold text-gray-900 mb-4">
  สรุปใบเสนอราคา
  </h1>
  {/*<ProgressBar currentStepId={4} />8/}
  
  {/* Top: ใบกำกับภาษี + ช่องทางรับสินค้า + ลูกค้า */}
  <div className="mt-4 flex justify-center mr-4 ">
  <div>
  <TaxDeliverySection
  needsTax={state.needsTax}
  deliveryType={state.deliveryType}
  billTaxName={state.billTaxName}
  onOpenShipping={() => setShippingOpen(true)}
  onChange={(change) => {
    const payload = {
      needsTax: Object.prototype.hasOwnProperty.call(
      change,
      "needsTax"
      )
      ? change.needsTax
      : state.needsTax,
      deliveryType: Object.prototype.hasOwnProperty.call(
      change,
      "deliveryType"
      )
      ? change.deliveryType
      : state.deliveryType,
      billTaxName: Object.prototype.hasOwnProperty.call(
      change,
      "billTaxName"
      )
      ? change.billTaxName
      : state.billTaxName || "",
    };
    dispatch({ type: "SET_TAX_DELIVERY", payload });
  }}
  />
  </div>
  
    <div className="ml-8">
      <CustomerSearchSection
      customer={state.customer}
      onCustomerChange={(cust) => {
        dispatch({ type: "SET_CUSTOMER", payload: cust });
      }}
      />
      {/* แสดงสถานะลูกค้า / anonymous */}
  <div className="mt-2 text-sm text-gray-600">
    {!getCustomerCode(state.customer || {}) && (
      <span>
        หากไม่เลือกหรือไม่ระบุลูกค้า ระบบจะบันทึกเป็น{" "}
        <span className="font-semibold">ผู้ไม่ประสงค์ออกนาม</span>
      </span>
    )}

    {getCustomerCode(state.customer || {}) && (
      <span>
        ลูกค้า:{" "}
        <span className="font-semibold">
          {state.customer?.name || "ผู้ไม่ประสงค์ออกนาม"}
        </span>
      </span>
    )}
  </div>
    </div>
  </div>
  
    {/* Tabs */}
    <div className="flex mt-4">
      
      <button
      onClick={() => setActiveTab("quote")}
      className={`font-bold text-lg p-2 rounded-t-lg ml-0
      ${activeTab === "quote"
      ? "bg-[#0BD537] text-black"
      : "bg-gray-200 hover:bg-[#0BD537]"}
      `}
      >
    สร้างใบเสนอราคา
    </button>
    
    
    <button
      onClick={() => setActiveTab("customer")}
      className={`font-bold text-lg p-2 rounded-t-lg ml-2
      ${activeTab === "customer"
      ? "bg-[#0BD537] text-black"
      : "bg-gray-200 hover:bg-[#0BD537]"}
      `}
    >
    ข้อมูลลูกค้า
    </button>
    
    <button
      onClick={() => setActiveTab("products")}
      className={`font-bold text-lg p-2 rounded-t-lg ml-2
      ${activeTab === "products"
      ? "bg-[#0BD537] text-black"
      : "bg-gray-200 hover:bg-[#0BD537]"}
      `}
    >
    ข้อมูลสินค้า
    </button>



    </div>
  
  {/* TAB: QUOTE */}
  {activeTab === "quote" && (
  <div className="grid gap-4 grid-cols-8 flex-1 border-t-4 border-t-gray-200">
  {/* ซ้าย: ประวัติ+Category */}
  <div className="col-span-2 mt-6 space-y-4">
    
    <div>
      <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-3">
        ประวัติการซื้อสินค้า
      </h3>
    
      {historyLoading && (
        <p className="text-sm text-gray-500">
          กำลังโหลดประวัติการซื้อ...
        </p>
      )}
      {historyError && (
        <p className="text-sm text-red-500">{historyError}</p>
      )}
      {!historyLoading &&
        !historyError &&
        historyOrders.length === 0 && (
        <p className="text-sm text-gray-500">
          ยังไม่พบประวัติการซื้อสำหรับสินค้า/ลูกค้ารายนี้
        </p>
      )}
    
    <div className="space-y-2">
      {historyOrders.map((ord) => (
        <OrderHistoryCard
          key={ord.id}
          order={ord}
          onRepeat={handleRepeatFromHistory}
        />
      ))}
    </div>
  </div>

  <div className="col-span-2 relative">
  <input
    type="text"
    value={productSearch}
    onChange={(e) => setProductSearch(e.target.value)}
    onFocus={() => setShowDropdown(true)}
    placeholder="ค้นหาสินค้า (SKU / ชื่อ )"
    className="w-full mb-2 rounded-lg border px-4 py-2 text-sm
               focus:outline-none focus:ring-2 focus:ring-blue-400"
  />

  {showDropdown && searchResults.length > 0 && (
    <div
      className="absolute z-50 mt-1 w-full rounded-lg border bg-white shadow-lg
                 max-h-96 overflow-y-auto"
    >
      {searchResults.map((it) => (
        <div
          key={it.sku}
          onClick={() => handleQuickAdd(it)}
          className="cursor-pointer px-4 py-2 hover:bg-green-50 transition-colors"
        >
          <div className="text-sm font-semibold">
            {it.name}
          </div>
          <div className="text-xs text-gray-500">
            {it.sku} · ฿
            {(it.priceR2 ?? it.prices?.R2 ?? 0).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  )}
</div>

  
  <div id="category-section">
    <h3 className="text-xl font-semibold text-gray-800 mb-3">
    เลือกประเภทสินค้า
  </h3>
  
    {catLoading && (
    <p className="text-sm text-gray-500">
      กำลังโหลดประเภทสินค้า...
    </p>
        )}
        {catError && (
          <p className="text-sm text-red-500">{catError}</p>
        )}
      
      {!catLoading && !catError && (
      <div className="space-y-2">
        {categories
          .filter((cat) => cat && cat.name)
          .map((cat) => (
        <CategoryCard
          key={cat.name}
          category={cat.name}
          name={cat.name}
          count={cat.count}
          onClick={() => handleCategoryClick(cat.name)}
        />
      ))}
      </div>
      )}
      </div>
    </div>
  
  {/* กลาง: รายการสินค้า */}
    <div className="col-span-4 p-6 rounded-lg bg-gray-50 mt-3">
      

      <h3 className="text-xl font-semibold text-gray-800 mb-3">
      รายการสินค้า
      </h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
      <tr>
    {[
    "#",
    "สินค้า",
    "จำนวน",
    "ราคา/หน่วย (ใหม่)",
    "ยอดรวม (ใหม่)",
    "",
    ].map((h) => (
    <th
    key={h}
    className="px-4 py-3 text-xs font-bold uppercase text-gray-500 text-left"
    >
    {h}
    </th>
    ))}
    </tr>
    </thead>
    <tbody className="divide-y divide-gray-100">
    {state.cart.length === 0 && (
    <tr>
    <td
    colSpan="6"
    className="py-6 text-center text-gray-500"
    >
    ยังไม่มีสินค้าในตะกร้า
    </td>
    </tr>
    )}
    {state.cart.map((it, i) => (
  <CartItemRow
    key={uiKeyOf(it)}
    item={it}
    index={i}
    dispatch={dispatch}
    calculatedItem={calcMap[pricingKeyOf(it)]}
  />
))}

    </tbody>
    </table>
    </div>
    </div>
  
    {/* ขวา: สรุปยอด */}
    <div className="col-span-2">
      <div className="sticky top-28 space-y-6 rounded-lg bg-gray-50 p-6 shadow-sm mt-3">
      <div>
      <h4 className="mb-2 text-lg font-semibold text-gray-800">
      ข้อมูลใบเสนอราคา
      </h4>
    </div>
  
  
  <div className="space-y-2 border-t border-gray-200 pt-4">
    <h4 className="text-lg font-semibold text-gray-800">
    สรุปยอด
    </h4>
    <SummaryRow
    label="ค่าขนส่ง"
    value={
      state.deliveryType === "DELIVERY"
      ? fmtTHB(Number(state.shippingCustomerPay || 0))
      : "รับเอง (ไม่มีค่าขนส่ง)"
    }
    
  />
    <SummaryRow
    label="ราคารวมก่อนภาษี (ไม่รวม VAT)"
    value={calculation.totals.exVatFmt || "..."}
    loading={calculation.loading}
    />
    <SummaryRow
    label="ภาษีมูลค่าเพิ่ม (7%)"
    value={calculation.totals.vatFmt || "..."}
    loading={calculation.loading}
    />
    <div className="border-t border-gray-300" />
    <SummaryRow
    label="ราคารวมสุทธิ (รวม VAT แล้ว)"
    value={calculation.totals.totalFmt || "..."}
    isTotal
    loading={calculation.loading}
    />
  {calculation.error && (
  <p className="text-sm text-red-500">
  {calculation.error}
  </p>
  )}
  </div>
  
          <div className="space-y-3 border-t border-gray-200 pt-4">
              <button
                className="flex w-full items-center justify-center rounded-lg bg-[#c1c1c1] px-6 py-3 font-semibold text-white shadow-md  disabled:opacity-50">
                  <FileIcon />แนบไฟล์</button>
              <button
                disabled={calculation.loading || !!calculation.error}
                onClick={() => handleSaveQuotation("open")}
                className="flex w-full items-center justify-center rounded-lg bg-gray-600 px-6 py-3 font-semibold text-white shadow-md hover:bg-gray-700 disabled:opacity-50"
              >
                <DraftIcon /> Save Draft
              </button>
                  <button
                    disabled={calculation.loading || !!calculation.error}
                    onClick={handlePrint}
                    className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-50"
                  >
                  <PrintIcon /> Print Quotation
              </button>
                <button
                  disabled={calculation.loading || !!calculation.error}
                  onClick={() => handleSaveQuotation("complete")}
                  className="flex w-full items-center justify-center rounded-lg bg-[#DC2626] px-6 py-3 font-semibold text-white shadow-md hover:bg-gray-700 disabled:opacity-50"
                >
                <SaveIcon /> ยืนยัน
              </button>
              
          </div>
      </div>
    </div>
  </div>
  )}
  
  {/* TAB: PRODUCTS */}
  {activeTab === "products" && (
  <div className="flex flex-col space-y-4 border-t-4 border-gray-200 pt-4 ">
  <ProductCategorySelector
  value={selectedCategory}
  onChange={(cat) => {
    setSelectedCategory(cat);
    setProductFilters({});
    setSelectedProduct(null);
    setProductItems([]);
  }}
  />
  
  {selectedCategory && (
  <DynamicsProductFilter
  category={selectedCategory}
  onFilterChange={(filters) => {
    setProductFilters(filters);
  }}
  />
  
  )}
  
  
  <div className="grid grid-cols-6 gap-4">
    
  <div className="col-span-1">
  <ProductList
  items={productItems}
  loading={productLoading}
  onSelect={setSelectedProduct}
  onCategoryClick={handleCategoryClick}
  selectedCategory={selectedCategory}
  />
  </div>
  
  <div className="col-span-3">
  <ProductDetail item={selectedProduct} />
  </div>
  
  <div className="col-span-2">
  <ProductImage item={selectedProduct} />
  </div>
  </div>
  </div>
  )}
  
  {/* TAB: CUSTOMER (ถ้าจะทำเพิ่มทีหลังได้) */}
  {activeTab === "customer" && (
  <div className="border-t-4 border-gray-200 pt-4 ">
  
  </div>
  )}
  
  {/* Bottom nav */}
  <div className="mt-8 flex justify-between">
  <button
  type="button"
  onClick={handleGoBack}
  className="flex items-center rounded-lg bg-gray-200 px-6 py-3 font-semibold text-gray-700 shadow-sm hover:bg-gray-300"
  >
  <ArrowLeftIcon /> ย้อนกลับ
  </button>
  </div>
  
  {/* Shipping modal */}
  <ShippingModal
  open={shippingOpen}
  initial={{
    vehicleType: state.vehicleType || "",
    distanceKm: state.distance || "",
    unloadHours: state.unloadHours || "",
    staffCount: state.staffCount || "",
  }}

    onClose={() => setShippingOpen(false)}
    onConfirm={async (data) => {
    try {
      const res = await api.post("/api/shipping/calculate_from_cart", {
        vehicle_type: data.vehicleType,
        distance_km: Number(data.distanceKm || 0),
        unload_hours: Number(data.unloadHours || 0),
        staff_count: Number(data.staffCount || 0),
        cart: buildCartForShipping(state.cart),
      });

      dispatch({
        type: "SET_SHIPPING",
        payload: {
          distance: data.distanceKm,
          cost: Number(res.data.shipping_cost || 0),
          companyPay: Number(res.data.company_pay || 0),
          customerPay: Number(res.data.customer_pay || 0),
          vehicleType: data.vehicleType,
          unloadHours: data.unloadHours,
          staffCount: data.staffCount,
        },
      });

      setShippingOpen(false);
    } catch (err) {
      console.error("calculate shipping error", err);
      alert("ไม่สามารถคำนวณค่าขนส่งได้");
    }
  }}

  />
  
  {/* Item picker modal */}
  <ItemPickerModal
  open={itemModalOpen}
  category={selectedCategory}
  onClose={() => setItemModalOpen(false)}
  onConfirm={(item, qty) => {
    handleItemPicked(item, qty);
    setItemModalOpen(false);
  }}
  />
  
  {/* Glass picker modal */}
  <GlassPickerModal
  open={glassOpen}
  onClose={() => setGlassOpen(false)}
  onConfirm={(payload) => {
    dispatch({ type: "ADD_ITEM", payload });
    setGlassOpen(false);
  }}
  />
  </div>
  );
}

export default Step6_Summary;