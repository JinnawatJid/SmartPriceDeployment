// src/pages/CreateQuote/Step6_Summary.jsx
import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "../../hooks/useAuth.js";
import api from "../../services/api.js";
import ProgressBar from "../../components/wizard/ProgressBar.jsx";
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
  
  const getCustomerCode = (cust = {}) => {
    return (
    cust.id ||
    cust.customerCode ||
    cust.CustomerCode ||
    cust.Customer ||
    cust.No_ ||
    cust.no_ ||
    ""
    );
  };
  
  const handleRepeatFromHistory = (order) => {
    if (!order) return;
    navigate("/create", {
      state: {
        repeatOrder: {
          customer: order.customer,
          cart: order.cart,
          needTaxInvoice: order.needTaxInvoice,
          billTaxName: order.billTaxName,
          deliveryType: order.deliveryType || "PICKUP",
          shippingRaw: order.totals?.shippingRaw ?? 0,
          shippingCustomerPay: order.totals?.shippingCustomerPay ?? 0,
          note: order.note || "",
        },
      },
    });
  };
  
  
  useEffect(() => {
    if (state.cart.length === 0) {
      setCalculation({ cart: [], totals: {}, loading: false, error: null });
      return;
    }

    setCalculation((p) => ({ ...p, loading: true }));
    
    const calc = async () => {
      try {
        const res = await api.post("/api/pricing/calculate", {
         customerData: {
          customerCode: getCustomerCode(state.customer),
          customerName: state.customer?.name || "",
          paymentTerm: state.customer?.paymentTerm || "",
          paymentMethod: state.customer?.paymentMethod || "",
          deliveryType: state.deliveryType,
          shippingCustomerPay: state.shippingCustomerPay || 0,
        },
        

          deliveryType: state.deliveryType,
          cart: state.cart.map((it) => ({
            sku: it.sku,
            name: it.name ?? "",
            qty: Number(it.qty || 0),
            sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
            cost: it.cost,
            pkg_size: it.packageSize ?? it.pkg_size ?? 1,
            category: it.category,
            unit: it.unit ?? "",
            DeliveryType: state.deliveryType,
            _RelevantSales: state._RelevantSales ?? 0,
          })),
        });
        const pricingPayload = {
          customerData: {
            customerCode: state.customer?.code || "",
            customerName: state.customer?.name || "",
            paymentTerm: state.customer?.paymentTerm || "",
            paymentMethod: state.customer?.paymentMethod || "",
            deliveryType: state.deliveryType,
            shippingCustomerPay: state.shippingCustomerPay || 0,
          },
          deliveryType: state.deliveryType,
          cart: state.cart.map((it) => ({
            sku: it.sku,
            qty: Number(it.qty || 0),
            sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
          })),
        };
        console.log("=== PRICING PAYLOAD (REAL) ===", pricingPayload);
        console.log("=== PRICING CUSTOMER (REAL) ===", pricingPayload.customerData);
        console.log("=== PRICING CART (REAL) ===", pricingPayload.cart);

        console.log("=== PRICING RESPONSE ===", res.data);

        console.log(
          "=== PRICING RESPONSE ITEMS ===",
          res.data.items.map(i => ({
            sku: i.sku,
            unit: i.unit
          }))
        );

        
        const items = res.data.items || [];
        
        const {
          subtotal,
          vat,
          product_total,
          shippingCustomerPay,
          total,
          profit,
        } = res.data.totals;
        
        
        const fmt = (v) =>
        v.toLocaleString("th-TH", {
          style: "currency",
          currency: "THB",
        });
        
        setCalculation({
          cart: items,
          totals: {
            exVat: subtotal,               // = subtotal
            vat: vat,                      // = vat
            productTotal: product_total,   // = subtotal + vat (ยังไม่รวมขนส่ง)
            shippingCustomerPay,           // = ค่าขนส่งที่ลูกค้าจ่าย
            total: total,                  // = product_total + shippingCustomerPay
            profit: profit ?? 0,
            
            // รูปแบบแสดงผล
            exVatFmt: fmt(subtotal),
            vatFmt: fmt(vat),
            totalFmt: fmt(total),
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.cart, state.customer, state.deliveryType, state.shippingCustomerPay]);
  
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
        qty: 1, // ⭐ default = 1
        price: item.priceR2 ?? item.prices?.R2 ?? 0,
        cost: Number(item.cost || 0),
        category: item.category || "",
        unit: item.unit || item.saleUnit || item.uom || "",
      },
    });

    // reset search
    setProductSearch("");
    setSearchResults([]);
    setShowDropdown(false);
  };

  
  // sku -> item (ราคาที่คำนวณใหม่)
  const calcMap = useMemo(
  () => Object.fromEntries(calculation.cart.map((it) => [it.sku, it])),
  [calculation.cart]
  );
  
  
  const fmtTHB = (n) =>
  n.toLocaleString("th-TH", { style: "currency", currency: "THB" });
  
  const [saving, setSaving] = useState(false);
  
  // NOTE:
  // - new quote: qty = piece count
  // - edit draft: qty = total sqft

  // payload ใบเสนอราคา
  const isEditDraft = state.status === "open";

  const buildQuotationPayload = (status) => {
    const cartPayload = state.cart.map((it) => {
      const calc = calcMap[it.sku];
      const price = Number(
        calc?.price_per_sheet
        ?? calc?.UnitPrice
        ?? calc?.NewPrice
        ?? 0
      );


      const lineTotal = Number(calc?._LineTotal || 0);
      
      return {
        sku: it.sku,
        name: it.name,
        qty: Number(it.qty ?? 0),
        price,
        lineTotal,
        category: it.category ?? "",
        unit: calc?.unit ?? it.unit ?? "",
        sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
      };
    });
    
    return {
      status,
      employee: employee
      ? {
        id: employee.id,
        name: employee.name,
        branchId: employee.branchId ?? null,
      }
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
        //shippingRaw: state.shippingCost ?? 0,
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


    const payload = {
      quoteNo: state.quoteNo || "",
      date: new Date().toLocaleDateString("th-TH"),
      sales: employee?.name || "",
      customer: {
        code: state.customer?.id || state.customer?.code || "",
        name: state.customer?.name || "ผู้ไม่ประสงค์ออกนาม",
        phone: state.customer?.phone || "",
      },
      items: calculation.cart.map((it) => {
        const original = state.cart.find((x) => x.sku === it.sku);
        const isGlass = (original?.category || it.category) === "G";

        const price = isGlass
          ? Number(it.price_per_sheet ?? it.UnitPrice)
          : Number(it.UnitPrice);

        const unit = isGlass
          ? "แผ่น"
          : (
              original?.unit && original.unit.trim() !== ""
                ? original.unit
                : it.unit && it.unit.trim() !== ""
                  ? it.unit
                  : "-"
            );

        return {
          code: it.sku,
          name: original?.name || it.name || "",
          qty: it.qty,
          unit,            // ⭐ แผ่น สำหรับกระจก
          price,           // ⭐ บาท/แผ่น สำหรับกระจก
          amount: it._LineTotal,
        };
      })

      ,

      comment: state.remark || "",
      shipping: Number(state.shippingCustomerPay || 0),
      amountText: "", // ค่อยทำทีหลัง
      total: calculation.totals.productTotal,
      discount: "0.00",
      afterDiscount: calculation.totals.productTotal,
      exVat: calculation.totals.exVat,
      vat: calculation.totals.vat,
      netTotal: calculation.totals.total,
    };

    // Use api instance for consistent baseURL handling
    const res = await api.post("/print/quotation", payload, {
      responseType: "blob", // Important for PDF
    });

    // Axios returns the data in res.data
    const blob = new Blob([res.data], { type: "application/pdf" });
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
    key={it.sku}
    item={it}
    index={i}
    dispatch={dispatch}
    calculatedItem={calcMap[it.sku]}
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
    profit: calculation.totals?.profit ?? 0,
  }}
  onClose={() => setShippingOpen(false)}
  onConfirm={(data) => {
    dispatch({
      type: "SET_SHIPPING",
      payload: {
        distance: data.distanceKm,
        cost: Number(data.shipping_cost || 0),
        companyPay: data.company_pay,
        customerPay: data.customer_pay,
        vehicleType: data.vehicleType,
        unloadHours: data.unloadHours,
        staffCount: data.staffCount,
      },
      
    });
    setShippingOpen(false);
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