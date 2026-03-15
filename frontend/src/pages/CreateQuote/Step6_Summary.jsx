// src/pages/CreateQuote/Step6_Summary.jsx
import React, { useState, useEffect, useMemo } from "react";
import { useAuth } from "../../hooks/useAuth.js";
import api from "../../services/api.js";
import { useNavigate } from "react-router-dom";

import ShippingModal from "../../components/wizard/ShippingModal.jsx";
import CustomerSearchSection from "../../components/wizard/CustomerSearchSection.jsx";
import CustomerPromotionBanner from "../../components/wizard/CustomerPromotionBanner.jsx";
import TaxDeliverySection from "../../components/wizard/TaxDeliverySection.jsx";
import ItemPickerModal from "../../components/wizard/ItemPickerModal.jsx";
import GlassPickerModal from "../../components/wizard/GlassPickerModal.jsx";
import CategoryCard from "../../components/wizard/CategoryCard.jsx";
import CartItemRow from "../../components/wizard/CartItemRow.jsx";
import OrderHistoryCard from "../../components/wizard/OrderHistoryCard.jsx";
import DynamicsImportConfirmModal from "../../components/wizard/DynamicsImportConfirmModal.jsx";
import SpecialPriceRequestModal from "../../components/wizard/SpecialPriceRequestModal.jsx";

import ProductList from "../../components/products/ProductList.jsx";
import ProductDetail from "../../components/products/ProductDetail.jsx";
import ProductImage from "../../components/products/ProductImage.jsx";
import ProductCategorySelector from "../../components/products/ProductCategorySelector.jsx";
import DynamicsProductFilter from "../../components/products/DynamicsProductFilter.jsx";
import CrossSellPanel from "../../components/cross-sell/CrossSellPanel.jsx";
import CustomDropdown from "../../components/common/CustomDropdown.jsx";
import PromotionBanner from "../../components/wizard/PromotionBanner.jsx";

import { uiKeyOf, pricingKeyOf, printKeyOf } from "./utils/quoteKeys";
import { getCustomerCode } from "./utils/customer";
import { fmtTHB } from "./utils/format";

// ---- Icons ----
const FileIcon = () => (
  <img src="/assets/folder.png" alt="Print" className="h-6 w-6 mr-2 object-contain" />
);

const SaveIcon = () => (
  <img src="/assets/Save.png" alt="Print" className="h-5 w-5 mr-2 object-contain" />
);

const DraftIcon = () => (
  <img src="/assets/draft.png" alt="Print" className="h-6 w-6 mr-2 object-contain" />
);

const PrintIcon = () => (
  <img src="/assets/printer.png" alt="Print" className="h-5 w-5 mr-2 object-contain" />
);

const ArrowLeftIcon = () => (
  <svg
    className="w-5 h-5 mr-2"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={2}
    stroke="currentColor"
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
  </svg>
);

const SummaryRow = ({ label, value, isTotal = false, loading = false }) => (
  <div className="flex justify-between py-2">
    <span className={`font-semibold ${isTotal ? "text-lg text-gray-900" : "text-gray-600"}`}>
      {label}
    </span>
    <span className={`font-bold ${isTotal ? "text-xl text-blue-600" : "text-gray-800"}`}>
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
  const CATEGORY_ORDER = ["G", "A", "C", "Y", "S", "E"];


  // ประวัติการซื้อ
  const [historyOrders, setHistoryOrders] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  // local UI state
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [shippingOpen, setShippingOpen] = useState(false);
  const [glassOpen, setGlassOpen] = useState(false);
  const [editingShippingCost, setEditingShippingCost] = useState(false);
  const [tempShippingCost, setTempShippingCost] = useState(0);

  // Product browser state
  const [productFilters, setProductFilters] = useState({});
  
  // Special Price Request state
  const [specialPriceRequest, setSpecialPriceRequest] = useState(null);
  const [loadingSPR, setLoadingSPR] = useState(false);
  
  // Load special price request when quote is loaded
  useEffect(() => {
    const loadSpecialPriceRequest = async () => {
      if (!state.quoteNo) return;
      
      try {
        setLoadingSPR(true);
        const response = await api.get(`/api/special-price-requests/quote/${encodeURIComponent(state.quoteNo)}`);
        const sprList = response.data || [];
        const latestSPR = sprList.length > 0 ? sprList[0] : null;
        setSpecialPriceRequest(latestSPR);
        console.log('[SPR] Loaded special price request:', latestSPR);
      } catch (err) {
        console.log('[SPR] No special price request found for this quote');
        setSpecialPriceRequest(null);
      } finally {
        setLoadingSPR(false);
      }
    };
    
    loadSpecialPriceRequest();
  }, [state.quoteNo]);
  const [productItems, setProductItems] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productLoading, setProductLoading] = useState(false);
  const [productLoadingMore, setProductLoadingMore] = useState(false);
  const [productOffset, setProductOffset] = useState(0);
  const [productHasMore, setProductHasMore] = useState(true);
  const [productTotal, setProductTotal] = useState(0);

  // UI Tabs: "quote" | "customer" | "products"
  const [activeTab, setActiveTab] = useState("quote");

  // Promotions state
  const [promotions, setPromotions] = useState([]);

  // Project price state
  const [customerProjects, setCustomerProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [projectPrices, setProjectPrices] = useState({});

  // Category list
  const [categories, setCategories] = useState([]);
  const [catLoading, setCatLoading] = useState(true);
  const [catError, setCatError] = useState("");
  const [itemModalOpen, setItemModalOpen] = useState(false);
  const [sendingToBC, setSendingToBC] = useState(false);
  const [showDynamicsConfirm, setShowDynamicsConfirm] = useState(false);
  const [showSpecialPriceModal, setShowSpecialPriceModal] = useState(false);
  const [itemsBelowR1, setItemsBelowR1] = useState([]);

  const sumCartLineTotal = (cart) =>
    cart.reduce((sum, it) => sum + Number(it.lineTotal ?? 0), 0);



  // ราคาที่ได้จาก backend
  const [calculation, setCalculation] = useState({
    cart: [],
    totals: {},
    loading: true,
    error: null,
  });


  const handleCrossSellAdd = (ruleItem) => {
    // TODO: เปิด modal ค้นหาสินค้า
    // filter ด้วย ruleItem.displayName หรือ ruleItem.ruleGroup
    console.log("cross sell add:", ruleItem);
  };

  const handleRepeatFromHistory = (order) => {
    if (!order) return;

    console.log("=== REPEAT CLICKED ===");
    console.log("order.id:", order?.id);
    console.log("order.cart (raw from API):", order?.cart);

    (order?.cart || []).forEach((it, i) => {
      console.log(`[order.cart][${i}]`, {
        sku: it.sku,
        qty: it.qty,
        sqft_sheet: it.sqft_sheet,
        Sqft_Sheet: it.Sqft_Sheet,
        variantCode: it.variantCode,
        VariantCode: it.VariantCode,
      });
    });

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
        note: order.note ?? "",

        cart: (order.cart || []).map((it) => ({
          ...it,

          // ⭐ normalize สำคัญมาก
          sqft_sheet: Number(it.sqft_sheet ?? it.Sqft_Sheet ?? it.sqft ?? 0),

          variantCode: it.variantCode ?? it.VariantCode ?? "",

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

  useEffect(() => {
    if (state.status === "open") {
      const itemsNeedingPricing = (state.cart || []).filter(
        (it) => it.source === "ui" && it.needsPricing
      );

      const sumLine = (arr) =>
        arr.reduce(
          (sum, it) => sum + Number(it.lineTotal ?? Number(it.price || 0) * Number(it.qty || 0)),
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
              
              // ⭐ sales by category (สำหรับคำนวณ relevantSales ตาม product_group)
              sales_g_cust: Number(state.customer?.sales_g_cust || 0),
              sales_a_cust: Number(state.customer?.sales_a_cust || 0),
              sales_s_cust: Number(state.customer?.sales_s_cust || 0),
              sales_y_cust: Number(state.customer?.sales_y_cust || 0),
              sales_c_cust: Number(state.customer?.sales_c_cust || 0),
              sales_e_cust: Number(state.customer?.sales_e_cust || 0),

              shippingCustomerPay: Number(state.shippingCustomerPay || 0),
            },

            deliveryType: state.deliveryType,
            cart: itemsNeedingPricing.map((it) => ({
              sku: it.sku,
              name: it.name ?? "",
              qty: Number(it.qty || 0),
              sqft_sheet: Number(it.sqft_sheet ?? it.sqft ?? 0),
              cost: it.cost,
              pkg_size: Number(it.pkg_size ?? 1),
              category: it.category,
              unit: it.unit ?? "",
              product_weight: it.product_weight ?? 0,
              isSoldByPack: it.isSoldByPack ?? false,
            })),
          });

          const pricedItems = res.data.items || [];

          pricedItems.forEach((pi) => {
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
            
            // ⭐ sales by category (สำหรับคำนวณ relevantSales ตาม product_group)
            sales_g_cust: Number(state.customer?.sales_g_cust || 0),
            sales_a_cust: Number(state.customer?.sales_a_cust || 0),
            sales_s_cust: Number(state.customer?.sales_s_cust || 0),
            sales_y_cust: Number(state.customer?.sales_y_cust || 0),
            sales_c_cust: Number(state.customer?.sales_c_cust || 0),
            sales_e_cust: Number(state.customer?.sales_e_cust || 0),

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
            isSoldByPack: it.isSoldByPack ?? false,
            DeliveryType: state.deliveryType,
          })),
        });

        const items = res.data.items || [];
        const { subtotal, vat, total, product_total, shippingCustomerPay, profit } =
          res.data.totals || {};

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
  }, [state.status, state.cart, state.customer, state.deliveryType, state.shippingCustomerPay]);

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
    calculation.loading, // ⭐ ตัวควบคุมลำดับ
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

        const items = res.data || [];
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
    const custCode = getCustomerCode(cust || "")
      .toString()
      .trim();

    if (!custCode || custCode.toUpperCase() === "N/A") {
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


  // โหลดรายการโครงการของลูกค้า
  useEffect(() => {
    const custCode = getCustomerCode(state.customer);
    
    if (!custCode || custCode.toUpperCase() === "N/A") {
      setCustomerProjects([]);
      setSelectedProject(null);
      setProjectPrices({});
      return;
    }

    const fetchProjects = async () => {
      try {
        console.log('🏗️ Loading projects for customer:', custCode);
        const res = await api.get('/api/project-prices/by-customer', {
          params: { customerCode: custCode }
        });
        
        const projects = res.data || [];
        console.log('📦 Found projects:', projects);
        setCustomerProjects(projects);
      } catch (err) {
        console.error('❌ Error loading projects:', err);
        setCustomerProjects([]);
      }
    };

    fetchProjects();
  }, [state.customer]);

  // โหลดราคาโครงการเมื่อเลือกโครงการ และคำนวณราคาใหม่
  useEffect(() => {
    console.log('🔄 [PROJECT CHANGE] useEffect triggered, selectedProject:', selectedProject);
    
    // ถ้าไม่มีสินค้าในตะกร้า ไม่ต้องคำนวณ
    if (!state.cart || state.cart.length === 0) {
      console.log('❌ [PROJECT CHANGE] No cart items, skipping calculation');
      return;
    }

    // ถ้าไม่มีลูกค้า ไม่ต้องคำนวณ
    const customerCode = getCustomerCode(state.customer);
    if (!customerCode || customerCode.toUpperCase() === "N/A") {
      console.log('❌ [PROJECT CHANGE] No customer, skipping calculation');
      return;
    }

    const recalculateWithProject = async () => {
      try {
        console.log('🔄 [PROJECT CHANGE] Recalculating prices with project_id:', selectedProject);
        
        // ตั้งค่า loading
        setCalculation((prev) => ({ ...prev, loading: true }));
        
        const calcRes = await api.post("/api/pricing/calculate", {
          customerData: {
            customerCode,
            customerName: state.customer?.name || "",
            paymentTerm:
              state.customer?.paymentTerm ??
              state.customer?.creditTerm ??
              state.customer?.payment_terms ??
              "",
            paymentMethod: state.customer?.paymentMethod || "",
            customer_date: state.customer?.customer_date,
            accum_6m: Number(state.customer?.accum_6m || 0),
            frequency: Number(state.customer?.frequency || 0),
            gen_bus: state.customer?.gen_bus,
            sales_g_cust: Number(state.customer?.sales_g_cust || 0),
            sales_a_cust: Number(state.customer?.sales_a_cust || 0),
            sales_s_cust: Number(state.customer?.sales_s_cust || 0),
            sales_y_cust: Number(state.customer?.sales_y_cust || 0),
            sales_c_cust: Number(state.customer?.sales_c_cust || 0),
            sales_e_cust: Number(state.customer?.sales_e_cust || 0),
            shippingCustomerPay: Number(state.shippingCustomerPay || 0),
            project_id: selectedProject, // 🔥 ส่ง project_id ที่เลือก (null ถ้าไม่เลือก)
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
            product_weight: it.product_weight ?? 0,
          })),
        });

        const items = calcRes.data.items || [];
        const { subtotal, vat, total, product_total, shippingCustomerPay, profit } =
          calcRes.data.totals || {};

        console.log('📦 [PROJECT CHANGE] API Response items:', items.map(it => ({
          sku: it.sku,
          UnitPrice: it.UnitPrice,
          price_per_sheet: it.price_per_sheet,
          price_source: it.price_source,
          _LineTotal: it._LineTotal
        })));

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
        
        console.log('✅ [PROJECT CHANGE] Recalculation complete, calculation.cart updated');
      } catch (err) {
        console.error('❌ [PROJECT CHANGE] Error recalculating with project:', err);
        setCalculation((prev) => ({
          ...prev,
          loading: false,
          error: 'เกิดข้อผิดพลาดในการคำนวณราคาโครงการ',
        }));
      }
    };

    recalculateWithProject();
  }, [selectedProject, state.customer, state.cart]); // 🔥 เพิ่ม dependencies เพื่อให้คำนวณใหม่เมื่อมีการเปลี่ยนแปลง

  // โหลด Promotion ตาม SKU ที่เลือก
  useEffect(() => {
    console.log('🎯 Promotions useEffect triggered');
    console.log('📦 state.cart:', state.cart);
    
    if (!state.cart || state.cart.length === 0) {
      console.log('⚠️ No cart items, clearing promotions');
      setPromotions([]);
      return;
    }

    const skus = state.cart.map(item => item.sku).filter(Boolean).join(',');
    
    console.log('🔍 SKUs to fetch promotions for:', skus);
    
    if (!skus) {
      console.log('⚠️ No valid SKUs, clearing promotions');
      setPromotions([]);
      return;
    }

    const fetchPromotions = async () => {
      try {
        console.log('🔍 Loading promotions for SKUs:', skus);
        const res = await api.get('/api/promotions/active-by-skus', {
          params: { skus }
        });
        
        console.log('📦 Promotions API response:', res.data);
        
        const promoData = res.data || {};
        const promoList = [];
        
        // แปลง object เป็น array สำหรับแสดงผล
        Object.entries(promoData).forEach(([sku, promos]) => {
          console.log(`🎁 Processing promotions for SKU ${sku}:`, promos);
          promos.forEach(promo => {
            const item = state.cart.find(it => it.sku === sku);
            const categoryName = 
              item?.category === 'G' ? 'กระจก' :
              item?.category === 'A' ? 'อลูมิเนียม' :
              item?.category === 'C' ? 'ซิลิโคน' :
              item?.category === 'Y' ? 'อุปกรณ์' :
              item?.category === 'S' ? 'บริการ' :
              item?.category === 'E' ? 'อื่นๆ' : 'สินค้า';
            
            promoList.push({
              type: item?.category === 'G' ? 'glass' : 'other',
              title: `${promo.promotion_name || 'โปรโมชั่น'}`,
              description: promo.promotion_text,
              sku: sku,
              categoryName: categoryName
            });
          });
        });
        
        console.log('✅ Processed promotions:', promoList);
        setPromotions(promoList);
      } catch (err) {
        console.error('❌ Error loading promotions:', err);
        setPromotions([]);
      }
    };

    fetchPromotions();
  }, [state.cart]);


  const handleQuickAdd = (item) => {
    // ⭐ สำหรับกระจก (category G) ไม่ต้องส่ง price
    // ให้ pricing engine คำนวณจาก sqft_sheet แทน
    const isGlass = item.category === "G";
    
    console.log("🔍 handleQuickAdd - item:", item);
    console.log("🔍 isGlass:", isGlass);
    console.log("🔍 sqft_sheet:", item.sqft_sheet);
    
    // ⭐ ดึงราคาจากหลายแหล่ง (prices.R2, priceR2, price)
    const price = item.prices?.R2 ?? item.priceR2 ?? item.price ?? 0;
    const cost = Number(item.cost || 0);
    
    console.log("🔍 price resolved:", price);
    console.log("🔍 cost resolved:", cost);
    
    const payload = {
      sku: item.sku,
      name: item.name,
      qty: 1,
      category: item.category || "",
      unit: item.unit || item.saleUnit || item.uom || "",
      product_weight: Number(item.product_weight || 0),
      sqft_sheet: Number(item.sqft_sheet || 0),
      pkg_size: Number(item.pkg_size || 1),
      product_group: item.product_group ?? null,
      product_sub_group: item.product_sub_group ?? null,
    };
    
    // ⭐ เฉพาะสินค้าที่ไม่ใช่กระจก ถึงจะส่ง price และ cost
    if (!isGlass) {
      payload.price = price;
      payload.cost = cost;
    }
    
    console.log("🔍 payload to dispatch:", payload);
    
    dispatch({
      type: "ADD_ITEM",
      payload,
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

  // ❌ ไม่มีรหัสลูกค้า หรือเป็น N/A → ไม่ hydrate
  if (!custCode || custCode.toUpperCase() === "N/A") return;

  if (!cust?._needsHydrate) return;

  let cancelled = false;

  (async () => {
    try {
      const res = await api.get("/api/customer/search", {
        params: { code: custCode },
      });

      if (cancelled) return;

      const full = res.data || {};

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
  const calcMap = useMemo(() => {
    const map = Object.fromEntries((calculation.cart || []).map((it) => [pricingKeyOf(it), it]));
    console.log('🔍 [calcMap] Updated:', {
      cartLength: calculation.cart?.length,
      mapKeys: Object.keys(map),
      sampleItems: calculation.cart?.slice(0, 2).map(it => ({
        sku: it.sku,
        key: pricingKeyOf(it),
        UnitPrice: it.UnitPrice,
        price_per_sheet: it.price_per_sheet,
        priceSource: it.priceSource
      }))
    });
    return map;
  }, [calculation.cart]);

  const _round2 = (n) => Math.round(Number(n || 0) * 100) / 100;

  const computeEffectiveTotals = (cart, pricedMap) => {
    const shipping = Number(
      state.deliveryType === "DELIVERY" ? (state.shippingCustomerPay || 0) : 0
    );

    const subtotal = (cart || []).reduce((sum, it) => {
      const key = pricingKeyOf(it);
      const priced = pricedMap?.[key];

      // manual → ใช้ lineTotal ใน state เป็นหลัก
      if (it.priceSource === "manual") {
        const lt = Number(it.lineTotal ?? 0);
        if (lt > 0) return sum + lt;

        // fallback ถ้า lineTotal ว่าง
        const qty = Number(it.qty ?? 0);
        const sqft = Number(it.sqft_sheet ?? it.sqft ?? 0);
        const cat = (it.category || String(it.sku || "").slice(0, 1)).toUpperCase();
        const isGlass = cat === "G";
        const unit = isGlass
          ? Number(it.price_per_sheet ?? Number(it.UnitPrice ?? 0) * sqft)
          : Number(it.UnitPrice ?? it.price ?? 0);
        return sum + unit * qty;
      }

      // not manual → ใช้ pricing ถ้ามี
      const cat = (it.category || String(it.sku || "").slice(0, 1)).toUpperCase();
      const isGlass = cat === "G";
      const isSoldByPack = it.isSoldByPack || false;
      
      // ⭐ สำหรับกระจกขายยกแพ็ก: คำนวณใหม่
      if (isGlass && isSoldByPack) {
        const qty = Number(it.qty ?? 0);
        const unitPrice = Number(priced?.UnitPrice ?? it.UnitPrice ?? it.price ?? 0);
        return sum + unitPrice * qty;
      }
      
      const lt = Number(priced?._LineTotal ?? priced?.lineTotal ?? it.lineTotal ?? 0);
      if (lt > 0) return sum + lt;

      // fallback
      const qty = Number(it.qty ?? 0);
      const unit = Number(
        priced?.price_per_sheet ??
          priced?.UnitPrice ??
          it.price_per_sheet ??
          it.UnitPrice ??
          it.price ??
          0
      );
      return sum + unit * qty;
    }, 0);

    const grossBeforeVat = Number(subtotal) + shipping;
    const vat = _round2(grossBeforeVat * 0.07);
    const exVat = _round2(grossBeforeVat - vat);
    const total = _round2(grossBeforeVat);

    return {
      exVat,
      vat,
      total,
      exVatFmt: fmtTHB(exVat),
      vatFmt: fmtTHB(vat),
      totalFmt: fmtTHB(total),
    };
  };

  // ⭐ ทำให้ Summary + payload totals เปลี่ยนตามเมื่อ user แก้ราคา/qty หรือเลือกโครงการ
  useEffect(() => {
    const next = computeEffectiveTotals(state.cart, calcMap);
    setCalculation((prev) => ({
      ...prev,
      totals: { ...prev.totals, ...next },
    }));
  }, [state.cart, state.deliveryType, state.shippingCustomerPay, calcMap]);

  // ตรวจสอบสินค้าที่ราคาต่ำกว่า R1 หรืออยู่ในช่วงที่ต้องขออนุมัติ
  const checkPricesBelowR1 = () => {
    const belowR1Items = [];
    
    (state.cart || []).forEach((item) => {
      const key = pricingKeyOf(item);
      const calc = calcMap?.[key];
      
      // ⭐ เช็คเฉพาะสินค้าที่มีการแก้ไขราคาด้วยตนเอง (manual)
      if (item.priceSource !== 'manual') {
        return; // ข้ามสินค้าที่ใช้ราคาจากระบบ
      }
      
      // ดึงราคา threshold จาก calculation (เรียงจากมากไปน้อย)
      const r2Price = Number(calc?.priceR2 || 0);
      const r1Price = Number(calc?.priceR1 || 0);
      const w2Price = Number(calc?.priceW2 || 0);
      const w1Price = Number(calc?.priceW1 || 0);
      const sdmPrice = Number(calc?.priceSDM || 0);
      
      // 🔍 LOG: แสดงราคาทั้ง 5 ระดับ (เรียงจากมากไปน้อย)
      console.log(`📊 [PRICE CHECK] SKU: ${item.sku} | ${item.name} (MANUAL PRICE)`);
      console.log(`   R2:  ${r2Price.toFixed(2)} บาท (ราคาสูงสุด)`);
      console.log(`   R1:  ${r1Price.toFixed(2)} บาท (ราคาขั้นต่ำ)`);
      console.log(`   W2:  ${w2Price.toFixed(2)} บาท (ขั้นกลาง)`);
      console.log(`   W1:  ${w1Price.toFixed(2)} บาท (ขั้นสูง)`);
      console.log(`   SDM: ${sdmPrice.toFixed(2)} บาท (ราคาต่ำสุด)`);
      
      if (r1Price === 0) {
        console.log(`   ⚠️ ไม่มีข้อมูล threshold สำหรับสินค้านี้`);
        return; // ไม่มีข้อมูล threshold
      }
      
      // คำนวณราคาที่ขอ
      const sqft = Number(item.sqft_sheet ?? item.sqft ?? 0);
      const isGlass = (item.category || "").toUpperCase() === "G";
      
      let requestedPrice;
      if (item.priceSource === "manual") {
        if (isGlass && sqft > 0) {
          requestedPrice = Number(item.price_per_sheet ?? Number(item.UnitPrice ?? 0) * sqft);
        } else {
          requestedPrice = Number(item.UnitPrice ?? item.price ?? 0);
        }
      } else {
        if (isGlass && sqft > 0) {
          requestedPrice = Number(calc?.price_per_sheet ?? item.price_per_sheet ?? 0);
        } else {
          requestedPrice = Number(calc?.UnitPrice ?? item.UnitPrice ?? item.price ?? 0);
        }
      }
      
      // 🔍 LOG: แสดงราคาที่ขอ
      console.log(`   💰 ราคาที่ขอ: ${requestedPrice.toFixed(2)} บาท`);
      
      // ตรวจสอบว่าราคาอยู่ในช่วงที่ต้องขออนุมัติหรือไม่
      // ลำดับราคา: R2 > R1 > W2 > W1 > SDM (จากมากไปน้อย)
      // เงื่อนไข:
      // - W1 ≤ ราคา ≤ W2: ต้องอนุมัติจาก ZM เท่านั้น
      // - W2 < ราคา < R1: ต้องอนุมัติจาก ZM และ RM
      // - ราคา < W1 หรือ ราคา ≥ R1: ปฏิเสธ (นอกช่วง)
      
      if (requestedPrice > 0 && requestedPrice >= r1Price) {
        // ราคา ≥ R1 = ปฏิเสธ (ราคาสูงเกินไป ไม่ต้องขออนุมัติ หรือใช้ราคาปกติ)
        console.log(`   ✅ OK: ราคาปกติ ไม่ต้องขออนุมัติ (${requestedPrice.toFixed(2)} ≥ ${r1Price.toFixed(2)})`);
        return; // ไม่ต้องขออนุมัติ
      } else if (requestedPrice >= w2Price && requestedPrice < r1Price) {
        // W2 ≤ ราคา < R1 = ต้องอนุมัติจาก ZM และ RM (multi-level)
        console.log(`   ⚠️ ZM_THEN_RM: ต้องอนุมัติจาก ZM และ RM (${w2Price.toFixed(2)} ≤ ${requestedPrice.toFixed(2)} < ${r1Price.toFixed(2)})`);
        belowR1Items.push({
          sku: item.sku,
          name: item.name,
          qty: item.qty,
          unit: item.unit,
          requested_price: requestedPrice,
          r1_price: r1Price,
          w2_price: w2Price,
          w1_price: w1Price,
          approval_level: 'ZM_THEN_RM', // Multi-level
        });
      } else if (requestedPrice >= w1Price && requestedPrice < w2Price) {
        // W1 ≤ ราคา < W2 = ต้องอนุมัติจาก ZM เท่านั้น (single-level)
        console.log(`   ✅ ZM_ONLY: ต้องอนุมัติจาก Zone Manager (${w1Price.toFixed(2)} ≤ ${requestedPrice.toFixed(2)} < ${w2Price.toFixed(2)})`);
        belowR1Items.push({
          sku: item.sku,
          name: item.name,
          qty: item.qty,
          unit: item.unit,
          requested_price: requestedPrice,
          r1_price: r1Price,
          w2_price: w2Price,
          w1_price: w1Price,
          approval_level: 'ZM_ONLY', // Single-level
        });
      } else if (requestedPrice < w1Price) {
        // ราคา < W1 = ปฏิเสธ (ราคาต่ำเกินไป)
        console.log(`   ❌ REJECTED: ราคาต่ำกว่า W1 (${requestedPrice.toFixed(2)} < ${w1Price.toFixed(2)})`);
        belowR1Items.push({
          sku: item.sku,
          name: item.name,
          qty: item.qty,
          unit: item.unit,
          requested_price: requestedPrice,
          r1_price: r1Price,
          w2_price: w2Price,
          w1_price: w1Price,
          approval_level: 'REJECTED', // ต่ำกว่า W1
        });
      }
    });
    
    if (belowR1Items.length > 0) {
      console.log(`\n📋 สรุปผลการตรวจสอบราคา: พบ ${belowR1Items.length} รายการที่แก้ไขราคาและต้องขออนุมัติ`);
      const zmOnly = belowR1Items.filter(i => i.approval_level === 'ZM_ONLY').length;
      const zmThenRm = belowR1Items.filter(i => i.approval_level === 'ZM_THEN_RM').length;
      const rejected = belowR1Items.filter(i => i.approval_level === 'REJECTED').length;
      
      console.log(`   ✅ ZM_ONLY: ${zmOnly} รายการ`);
      console.log(`   ⚠️ ZM_THEN_RM: ${zmThenRm} รายการ`);
      console.log(`   ❌ REJECTED: ${rejected} รายการ`);
    } else {
      console.log(`\n✅ ไม่มีสินค้าที่ต้องขออนุมัติ (ไม่มีการแก้ไขราคาด้วยตนเอง)`);
    }
    console.log('─'.repeat(60));
    
    return belowR1Items;
  };

  // ตรวจสอบราคาเมื่อ cart หรือ calcMap เปลี่ยน
  useEffect(() => {
    const items = checkPricesBelowR1();
    setItemsBelowR1(items);
  }, [state.cart, calcMap]);

  // แยกรายการที่สามารถขออนุมัติได้ และที่ไม่สามารถขออนุมัติได้
  const approvableItems = itemsBelowR1.filter(item => item.approval_level !== 'REJECTED');
  const rejectedItems = itemsBelowR1.filter(item => item.approval_level === 'REJECTED');


  const [saving, setSaving] = useState(false);

  const buildQuotationPayload = (status) => {
    const isEditDraft = state.status === "open";

    const cartPayload = (state.cart || []).map((it) => {
      // ✅ 1) คำนวณ key ให้ถูก
      const key = pricingKeyOf(it);

      // ✅ 2) ดึง calculated item (pricing result)
      const calc = calcMap?.[key];

      // ===============================
      // PRICE / LINETOTAL RESOLUTION
      // ===============================
      const sqft = Number(it.sqft_sheet ?? it.sqft ?? 0);
      const isGlass = (it.category || "").toUpperCase() === "G";

      // -------------------------------
      // 1) UNIT PRICE (บาท / หน่วย)
      // -------------------------------
      let unitPrice;

      if (it.priceSource === "manual") {
        // ⭐ manual = ใช้ค่าที่ user ใส่
        if (isGlass && sqft > 0) {
          // กระจก: UnitPrice ใน state = บาท/ตรฟ → แปลงเป็นบาท/แผ่น
          unitPrice = Number(it.price_per_sheet ?? Number(it.UnitPrice ?? 0) * sqft);
        } else {
          unitPrice = Number(it.UnitPrice ?? it.price ?? 0);
        }
      } else {
        // system pricing
        if (isGlass && sqft > 0) {
          // กระจก: ใช้ price_per_sheet จาก pricing
          unitPrice = Number(calc?.price_per_sheet ?? it.price_per_sheet ?? 0);
        } else {
          unitPrice = Number(
            calc?.UnitPrice ??
            it.UnitPrice ??
            it.price ??
            0
          );
        }
      }

      // -------------------------------
      // 2) LINE TOTAL (source of truth)
      // -------------------------------
      let lineTotal;

      if (it.priceSource === "manual") {
        // ⭐⭐ สำคัญที่สุด
        // manual → ใช้ lineTotal ที่ user แก้ ห้ามคำนวณใหม่เด็ดขาด
        lineTotal = Number(it.lineTotal || 0);
      } else {
        // system pricing
        lineTotal = unitPrice * Number(it.qty ?? 0);
      }

      // -------------------------------
      // 3) SYSTEM PRICE (reference) - ต้องเป็นราคาจากระบบเสมอ
      // -------------------------------
      const systemUnitPrice = isGlass && sqft > 0
        ? Number(calc?.price_per_sheet ?? it.price_per_sheet ?? 0)
        : Number(
            calc?.UnitPrice ??
            it.UnitPrice ??
            it.price ??
            0
          );

      // -------------------------------
      // 4) RETURN CART PAYLOAD ITEM
      // -------------------------------
      const isAluminium = (it.category || "").toUpperCase() === "A";
      
      // ⭐ น้ำหนักสินค้า
      // - ถ้าเป็น manual และมีการแก้น้ำหนัก → ใช้น้ำหนักที่แก้
      // - ไม่งั้นใช้จาก pricing หรือค่าเดิม
      const productWeight = 
        it.priceSource === "manual" && isAluminium && it.weight !== undefined
          ? Number(it.weight)
          : Number(calc?.product_weight ?? it.product_weight ?? it.weight ?? 0);

      return {
        sku: it.sku,
        name: it.name,
        qty: Number(it.qty ?? 0),

        // ⭐ ราคาที่ใช้จริง
        price: unitPrice,
        lineTotal: lineTotal,

        // ⭐ ราคาอ้างอิงจากระบบ
        Price_System: systemUnitPrice,

        UnitPrice: unitPrice,   // optional
        LineTotal: lineTotal,   // optional

        unit: it.unit ?? calc?.unit ?? "",
        product_weight: productWeight,
        category: it.category ?? "",
        sqft_sheet: sqft,
        variantCode: it.variantCode ?? "",
      };
    });

    // ⭐ ใช้ logic เดียวกับ Summary หน้า Step6
    const effectiveTotals = computeEffectiveTotals(state.cart, calcMap);

    return {
      id: state.id || null,
      quoteNo: state.quoteNo || null,
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
        exVat: effectiveTotals.exVat,
        vat: effectiveTotals.vat,
        grandTotal: effectiveTotals.total,
        shippingCustomerPay: state.shippingCustomerPay ?? 0,
        shippingRaw: state.shippingCost ?? 0, // ⭐ ค่าขนส่งที่ระบบคิด
      },
      note: state.remark || "",
    };
  };

  // โหลดสินค้าใน product tab (แบบ pagination)
  const loadProductItems = async (reset = false) => {
    if (activeTab !== "products" || !selectedCategory) return;
    if (!productHasMore && !reset) return;

    // แยก loading state
    if (reset) {
      setProductLoading(true);
    } else {
      if (productLoadingMore) return;
      setProductLoadingMore(true);
    }

    const currentOffset = reset ? 0 : productOffset;

    try {
      let url = "";
      const params = {
        limit: 50,
        offset: currentOffset,
        ...productFilters,
      };

      switch (selectedCategory) {
        case "A":
          url = "/api/items/categories/A/list";
          break;
        case "C":
          url = "/api/items/categories/C/list";
          break;
        case "E":
          url = "/api/items/categories/E/list";
          break;
        case "G":
          url = "/api/glass/list";
          break;
        case "Y":
          url = "/api/items/categories/Y/list";
          break;
        case "S":
          url = "/api/items/categories/S/list";
          break;
        default:
          setProductLoading(false);
          setProductLoadingMore(false);
          return;
      }

      const res = await api.get(url, { params });
      const newItems = res.data.items || [];
      const totalCount = res.data.total || 0;

      const mappedItems = newItems.map((it) => ({
        ...it,
        name: it.name || it.description || it.Description || "",
      }));

      setProductItems((prev) => (reset ? mappedItems : [...prev, ...mappedItems]));
      setProductTotal(totalCount);

      const newOffset = currentOffset + newItems.length;
      setProductOffset(newOffset);
      setProductHasMore(newOffset < totalCount);
    } catch (err) {
      console.error("load items error:", err);
    } finally {
      setProductLoading(false);
      setProductLoadingMore(false);
    }
  };

  // โหลดครั้งแรกเมื่อเปิดแท็บหรือเปลี่ยน category
  useEffect(() => {
    if (activeTab !== "products" || !selectedCategory) return;

    setProductItems([]);
    setProductOffset(0);
    setProductHasMore(true);
    setProductTotal(0);
    loadProductItems(true);
  }, [activeTab, selectedCategory]);

  // โหลดใหม่เมื่อ filter เปลี่ยน
  useEffect(() => {
    if (activeTab !== "products" || !selectedCategory) return;

    setProductItems([]);
    setProductOffset(0);
    setProductHasMore(true);
    loadProductItems(true);
  }, [productFilters]);

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

      const unitPrice = Number(
        item.priceSource === "manual"
          ? item.price_per_sheet ?? item.price ?? item.UnitPrice ?? 0
          : calculatedItem?.price_per_sheet ??
            calculatedItem?.UnitPrice ??
            item.price ??
            item.UnitPrice ??
            0
      );


      const lineTotal = Number(
        item.priceSource === "manual"
          ? item.lineTotal ?? unitPrice * qty
          : calculatedItem?._LineTotal ?? calculatedItem?.lineTotal ?? item.lineTotal ?? 0
      );

      // =========================
      // GLASS PRICE NORMALIZATION
      // =========================
      let priceToSend = unitPrice;

      // ⭐ FIX: manual glass → ใช้ lineTotal เป็น truth
      if (isGlass && item.priceSource === "manual" && item.lineTotal > 0 && qty > 0) {
        priceToSend = Number(item.lineTotal) / qty; // ต่อแผ่น
      }


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
        isSoldByPack: item.isSoldByPack ?? false, // ⭐ เพิ่ม flag สำหรับขายยกแพ็ก
      };
    });
  };

  const handleSaveQuotation = async (status) => {
    try {
      setSaving(true);

      const payload = buildQuotationPayload(status);
      const res = await saveQuotation(payload, state);

      // ⭐ สำคัญที่สุด
      if (res?.data) {
        dispatch({
          type: "SET_QUOTE_META",
          payload: {
            id: res.data.id,
            quoteNo: res.data.quoteNo,
            status: res.data.status,
          },
        });
      }

      if (status === "open") {
        navigate("/quote-drafts");
        return;
      }

      alert("บันทึกใบเสนอราคาเรียบร้อยแล้ว กรุณาตรวจสอบก่อนส่งเข้า BC");

    } catch (err) {
      console.error(err);
      alert("บันทึกใบเสนอราคาไม่สำเร็จ");
    } finally {
      setSaving(false);
    }
  };


  const handleSendToBC = async () => {
    try {
      setSendingToBC(true);

      const payload = buildQuotationPayload("complete");

      // ⭐ เตรียมข้อมูลสำหรับ RPA Local Agent
      const rpaItems = payload.cart.map((it) => {
        const isGlass = (it.category || "").toUpperCase() === "G";
        
        if (isGlass) {
          // สำหรับกระจก: ต้องคำนวณราคาต่อ sqft จาก price_per_sheet
          const sqft = Number(it.sqft_sheet || 0);
          const pricePerSheet = Number(it.price_per_sheet || it.price || 0);
          const pricePerSqft = sqft > 0 ? (pricePerSheet / sqft).toFixed(2) : "0";
          
          return {
            sku: it.sku,
            description: it.name,
            quantity: String(it.qty || 0),
            price_per_sqft: String(pricePerSqft),
            price_per_sheet: String(pricePerSheet),
          };
        } else {
          // สำหรับสินค้าอื่น
          return {
            sku: it.sku,
            description: it.name,
            quantity: String(it.qty || 0),
            unit_price: String(it.price || 0),
          };
        }
      });

      // ⭐ เพิ่มค่าขนส่งเป็นรายการสุดท้าย (ถ้ามี)
      const shippingCost = Number(state.shippingCustomerPay || 0);
      if (shippingCost > 0) {
        rpaItems.push({
          sku: "OT01-014",
          description: "ค่าขนส่ง",
          quantity: "1",
          unit_price: String(shippingCost),
        });
      }

      const rpaPayload = {
        quote_code: payload.quoteNo?.substring(0, 4) || "TRQT", // เอา 4 ตัวแรกของเลขที่ใบเสนอราคา
        customer_no: payload.customer.code,
        sales_admin: payload.employee?.id || "20614", // ใช้ employee ID หรือค่า default
        your_reference: payload.quoteNo || "", // ใส่เลขที่ใบเสนอราคาในระบบเรา
        // ไม่ต้องใช้ remote_chrome_address อีกต่อไปเพราะ Local Agent รันที่เครื่องเดียวกัน (127.0.0.1) เสมอ
        remote_chrome_address: "127.0.0.1:9222",
        items: rpaItems,
      };

      // ⭐ เรียก Local RPA Agent ที่พอร์ต 8001 (Client-Side Agent)
      // ลองหลาย URL เพื่อรองรับทั้งกรณีที่เปิดจากเครื่องเดียวกันและเครื่องอื่น
      const rpaUrls = [
        "http://127.0.0.1:8001/api/rpa/create-quote",      // ลอง localhost ก่อน (เครื่องที่เปิด browser)
        "http://192.192.0.37:8001/api/rpa/create-quote",   // ลองเครื่อง Server
        "http://192.168.1.185:8001/api/rpa/create-quote",  // ลองเครื่อง Dev (สำหรับทดสอบ)
        "http://192.192.99.1:8001/api/rpa/create-quote"    // ลองเครื่องผ่าน SonicWall
      ];

      let rpaRes = null;
      let lastError = null;

      for (const url of rpaUrls) {
        try {
          console.log(`[RPA] Trying to send request to: ${url}`);
          rpaRes = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(rpaPayload),
          });

          if (rpaRes.ok) {
            console.log(`[RPA] Successfully connected to: ${url}`);
            break; // สำเร็จแล้ว ออกจาก loop
          } else {
            console.warn(`[RPA] Failed with status ${rpaRes.status} from: ${url}`);
            lastError = `HTTP ${rpaRes.status}`;
          }
        } catch (err) {
          console.warn(`[RPA] Connection failed to: ${url}`, err);
          lastError = err.message;
          rpaRes = null; // Reset เพื่อลอง URL ถัดไป
        }
      }

      if (!rpaRes || !rpaRes.ok) {
        let errorDetail = "ไม่สามารถเชื่อมต่อ RPA Agent ได้ - โปรดตรวจสอบว่า RPA Agent เปิดอยู่หรือไม่";
        if (lastError) {
          errorDetail += ` (${lastError})`;
        }
        if (rpaRes && !rpaRes.ok) {
          try {
            const errorData = await rpaRes.json();
            errorDetail = errorData.detail || errorDetail;
          } catch(e) {}
        }
        throw new Error(errorDetail);
      }

      alert("ส่งข้อมูลเข้า Dynamics 365 ผ่าน RPA เรียบร้อยแล้ว");

      // ✅ RESET ตรงนี้แทน
      dispatch({ type: "RESET_QUOTE" });
      navigate("/confirmed-quotes");

    } catch (err) {
      console.error(err);
      const errorMsg = err.message || "ส่งข้อมูลเข้า Dynamics 365 ไม่สำเร็จ - โปรดตรวจสอบว่า RPA Agent บนเครื่องเปิดอยู่หรือไม่";
      alert(errorMsg);
    } finally {
      setSendingToBC(false);
    }
  };

  const handleDynamicsImportClick = () => {
    setShowDynamicsConfirm(true);
  };

  const handleConfirmDynamicsImport = () => {
    setShowDynamicsConfirm(false);
    handleSendToBC();
  };

  const handleSpecialPriceRequest = async (reason) => {
    try {
      // ตรวจสอบว่ามีสินค้าที่ไม่สามารถขออนุมัติได้หรือไม่
      const rejectedItems = itemsBelowR1.filter(item => item.approval_level === 'REJECTED');
      if (rejectedItems.length > 0) {
        alert('พบสินค้าที่ราคานอกช่วงที่อนุมัติได้ กรุณาแก้ไขราคาก่อนส่งขออนุมัติ');
        return;
      }
      
      // เฉพาะสินค้าที่สามารถขออนุมัติได้
      const approvableItems = itemsBelowR1.filter(item => item.approval_level !== 'REJECTED');
      
      if (approvableItems.length === 0) {
        alert('ไม่มีสินค้าที่ต้องขออนุมัติ');
        return;
      }
      
      // 1. บันทึกใบเสนอราคาเป็น Draft ก่อน
      const payload = buildQuotationPayload("open");
      const res = await saveQuotation(payload, state);

      if (res?.data) {
        dispatch({
          type: "SET_QUOTE_META",
          payload: {
            id: res.data.id,
            quoteNo: res.data.quoteNo,
            status: res.data.status,
          },
        });
      }

      // 2. สร้างใบขอราคาพิเศษ
      const customerCode = getCustomerCode(state.customer);
      
      const specialPricePayload = {
        quote_no: res.data.quoteNo, // ⭐ ส่ง quote_no ที่ได้จากการบันทึก
        customer_code: customerCode,
        customer_name: state.customer?.name || "",
        customer_type: state.customer?.gen_bus || null,
        items: approvableItems.map(item => ({
          sku: item.sku,
          item_name: item.name,
          quantity: Number(item.qty),
          unit: item.unit,
          normal_price: item.r1_price,
          requested_price: item.requested_price,
          approval_level: item.approval_level, // ส่ง approval_level ไปด้วย
        })),
        request_reason: reason,
      };

      const specialPriceRes = await api.post('/api/special-price-requests', specialPricePayload);

      // ไม่ต้องเรียก submit อีก เพราะ create API จะ submit ให้อัตโนมัติแล้ว
      
      setShowSpecialPriceModal(false);
      alert('ส่งใบขอราคาพิเศษเรียบร้อยแล้ว\nใบเสนอราคาถูกบันทึกเป็น Draft และรอการอนุมัติ');
      navigate("/quote-drafts");
    } catch (err) {
      console.error('Error creating special price request:', err);
      alert('ไม่สามารถส่งใบขอราคาพิเศษได้: ' + (err.response?.data?.detail || err.message));
    }
  };


  const handleGoBack = () => dispatch({ type: "SET_STEP", payload: 3 });
  const handlePrint = async () => {
    if (calculation.loading || calculation.error) return;
    console.log(
      "=== PRINT SOURCE ===",
      calculation.cart.map((i) => ({
        sku: i.sku,
        unit: i.unit,
      }))
    );

    const grandTotal = calculation.totals.total ?? calculation.totals.grandTotal ?? 0;
    const printSourceItems =
      calculation.cart && calculation.cart.length > 0
        ? calculation.cart // new quote (pricing ใหม่)
        : state.cart; // repeat / draft

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
        const original = state.cart.find((x) => printKeyOf(x) === printKeyOf(it));
        const unit =
          it.unit || // จาก pricing
          original?.unit || // จาก cart
          "-";
        const isGlass = (original.category || it.category) === "G";
        const isSoldByPack = original?.isSoldByPack || false; // ⭐ เช็ค flag ขายยกแพ็ก

        // ⭐ สำหรับกระจกที่ขายยกแพ็ก ใช้ UnitPrice แทน price_per_sheet
        const price = Number(
          original?.priceSource === "manual"
            ? (isGlass && isSoldByPack)
              ? original.UnitPrice ?? original.price ?? 0  // ⭐ ขายยกแพ็ก: ใช้ราคาต่อหน่วยตรงๆ
              : original.price_per_sheet ?? original.price ?? original.UnitPrice ?? 0
            : (isGlass && isSoldByPack)
              ? it.UnitPrice ?? it.price ?? original?.price ?? 0  // ⭐ ขายยกแพ็ก: ใช้ราคาต่อหน่วยตรงๆ
              : it.price_per_sheet ?? it.UnitPrice ?? it.price ?? original?.price ?? 0
        );


        const amount =
          original?.priceSource === "manual"
            ? Number(original.lineTotal ?? 0)
            : Number(it._LineTotal ?? it.lineTotal ?? price * Number(it.qty || 0));


        return {
          code: it.sku,
          name: original.name || it.name || "",
          qty: Number(it.qty || 0),
          unit,
          price: price,
          amount: amount,
        };
      }),

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
    const res = await fetch("/api/print/quotation", {
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
    
    // ⭐ ดึงราคาจากหลายแหล่ง (prices.R2, priceR2, price)
    const price = item.prices?.R2 ?? item.priceR2 ?? item.price ?? 0;
    const cost = Number(item.cost || 0);
    
    console.log("🔍 handleItemPicked - item:", item);
    console.log("🔍 price resolved:", price);
    console.log("🔍 cost resolved:", cost);
    
    dispatch({
      type: "ADD_ITEM",
      payload: {
        sku: item.sku,
        name: item.name,
        qty,
        price,
        cost,
        category: item.category || selectedCategory || "",
        unit: item.unit || item.saleUnit || item.uom || "",
        product_weight: Number(item.product_weight || 0),
        pkg_size: Number(item.pkg_size || 1),
        product_group: item.product_group ?? null,
        product_sub_group: item.product_sub_group ?? null,
      },
    });
  };
  console.log("=== STEP6 STATE AFTER LOAD_DRAFT ===", state);

  const customerCode = useMemo(
    () => getCustomerCode(state.customer),
    [state.customer]
  );


  return (
    <div className="rounded-lg bg-white p-6 shadow-lg flex flex-col animate-fadeIn">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">สรุปใบเสนอราคา</h1>
      {/*<ProgressBar currentStepId={4} />8/}
  
  {/* Top: ใบกำกับภาษี + ช่องทางรับสินค้า + ลูกค้า */}
      <div className="mt-2 flex justify-center mr-4 ">
        <div className="flex">
          <div >
            <CustomerSearchSection
              customer={state.customer}
              onCustomerChange={(cust) => {
                console.log('👤 [STEP6] Customer changed:', cust);
                dispatch({ type: "SET_CUSTOMER", payload: cust });
              }}
            />
            
            {/* แสดงโปรโมชั่นของลูกค้า */}
            {(() => {
              console.log('🔍 [STEP6] Checking customer for promotion banner:', state.customer);
              console.log('🔍 [STEP6] Customer id:', state.customer?.id);
              console.log('🔍 [STEP6] Customer code:', state.customer?.code);
              const custCode = state.customer?.id || state.customer?.code;
              return custCode ? (
                <div className="mt-3">
                  <CustomerPromotionBanner customerCode={custCode} />
                </div>
              ) : (
                <div className="mt-3 text-xs text-gray-500">
                  (ยังไม่ได้เลือกลูกค้า - ไม่มีโปรโมชั่นพิเศษ)
                </div>
              );
            })()}
            
            {/* แสดงสถานะลูกค้า / anonymous */}
            <div className="mt-2 text-sm text-gray-600">
                  หากไม่เลือกหรือไม่ระบุลูกค้า ระบบจะบันทึกเป็น{" "}
                  <span className="font-semibold">ผู้ไม่ประสงค์ออกนาม</span>            
            </div>
          </div>
          <TaxDeliverySection
            needsTax={state.needsTax}
            deliveryType={state.deliveryType}
            onOpenShipping={() => setShippingOpen(true)}
            onChange={(change) => {
              const payload = {
                needsTax: Object.prototype.hasOwnProperty.call(change, "needsTax")
                  ? change.needsTax
                  : state.needsTax,
                deliveryType: Object.prototype.hasOwnProperty.call(change, "deliveryType")
                  ? change.deliveryType
                  : state.deliveryType,};
              dispatch({ type: "SET_TAX_DELIVERY", payload });
            }}
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex mt-4">
        <button
          onClick={() => setActiveTab("quote")}
          className={`font-bold text-lg p-2 rounded-t-lg ml-0
      ${activeTab === "quote" ? "bg-[#0BD537] text-black" : "bg-gray-200 hover:bg-[#0BD537]"}
      `}
        >
          สร้างใบเสนอราคา
        </button>

        <button
          onClick={() => setActiveTab("customer")}
          className={`font-bold text-lg p-2 rounded-t-lg ml-2
      ${activeTab === "customer" ? "bg-[#0BD537] text-black" : "bg-gray-200 hover:bg-[#0BD537]"}
      `}
        >
          ข้อมูลลูกค้า
        </button>

        <button
          onClick={() => setActiveTab("products")}
          className={`font-bold text-lg p-2 rounded-t-lg ml-2
      ${activeTab === "products" ? "bg-[#0BD537] text-black" : "bg-gray-200 hover:bg-[#0BD537]"}
      `}
        >
          ข้อมูลสินค้า
        </button>
      </div>

      {/* TAB: QUOTE */}
      {activeTab === "quote" && (
        <div className="grid gap-4 grid-cols-9 flex-1 border-t-4 border-t-gray-200">
          {/* ซ้าย: ประวัติ+Category */}
          <div className="col-span-2 mt-6 space-y-4">
            {customerCode && customerCode.toUpperCase() !== "N/A" && (
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-3">
                  ประวัติการซื้อสินค้า
                </h3>

                {historyLoading && (
                  <p className="text-sm text-gray-500">กำลังโหลดประวัติการซื้อ...</p>
                )}
                {historyError && <p className="text-sm text-red-500">{historyError}</p>}
                {!historyLoading && !historyError && historyOrders.length === 0 && (
                  <p className="text-sm text-gray-500">
                    ยังไม่พบประวัติการซื้อสำหรับสินค้า/ลูกค้ารายนี้
                  </p>
                )}

                <div className="space-y-2">
                  {historyOrders.map((ord) => (
                    <OrderHistoryCard key={ord.id} order={ord} onRepeat={handleRepeatFromHistory} />
                  ))}
                </div>
              </div>
            )}

            <div className="relative mb-4">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">ค้นหาสินค้า</h3>
              <input
                type="text"
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="ค้นหาสินค้า (SKU / ชื่อ )"
                className="w-full mb-2 rounded-lg border px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />

              {showDropdown && searchResults.length > 0 && (
                <div className="absolute z-50 mt-1 w-full rounded-lg border bg-white shadow-lg max-h-96 overflow-y-auto">
                  {searchResults.map((it) => (
                    <div
                      key={it.sku}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        handleQuickAdd(it);
                      }}
                      className="cursor-pointer px-4 py-2 hover:bg-green-50 transition-colors"
                    >
                      <div className="text-sm font-semibold">{it.name}</div>
                      <div className="text-xs text-gray-500">
                        {it.sku} · ฿{(it.prices?.R2 ?? it.priceR2 ?? it.price ?? 0).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div id="category-section">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">เลือกประเภทสินค้า</h3>

              {catLoading && <p className="text-sm text-gray-500">กำลังโหลดประเภทสินค้า...</p>}
              {catError && <p className="text-sm text-red-500">{catError}</p>}

              {!catLoading && !catError && (
                <div className="space-y-2">
                  {[...categories]
                    .filter((cat) => cat && cat.name)
                    .sort(
                      (a, b) =>
                        CATEGORY_ORDER.indexOf(a.name) -
                        CATEGORY_ORDER.indexOf(b.name)
                    )
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
          <div className="col-span-5 p-6 rounded-lg bg-gray-50 mt-3">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xl font-semibold text-gray-800">รายการสินค้า</h3>
            </div>

            {/* กล่องตาราง (grid ไม่เปลี่ยน) */}
            <div className="rounded-lg border border-gray-200 bg-white">
              {/* header ไม่ scroll */}
              <table className="min-w-full table-fixed">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="w-[20px] px-2 pl-4 py-3 text-xs font-bold text-gray-500 text-left">#</th>
                    <th className="w-[120px]  py-3 text-xs font-bold text-gray-500 text-left">สินค้า</th>
                    <th className="w-[32px]  py-3 pr-6 text-xs  font-bold text-gray-500">จำนวน</th>
                    <th className="w-[60px]  py-3  text-xs font-bold text-gray-500 text-center">ราคา/หน่วย</th>
                    <th className="w-[80px]  first-line:px-2 py-3 pl-6 text-xs font-bold text-gray-500 text-left">ยอดรวม</th>
                  </tr>
                </thead>
              </table>

              {/* ✅ scroll เฉพาะ body */}
              <div className="max-h-[300px] overflow-y-auto">
                <table className="min-w-full table-fixed">
                  <tbody className="divide-y divide-gray-100">
                    {state.cart.length === 0 && (
                      <tr>
                        <td colSpan="6" className="py-6 text-center text-gray-500">
                          ยังไม่มีสินค้าในตะกร้า
                        </td>
                      </tr>
                    )}

                    {state.cart.map((it, i) => {
                      const key = pricingKeyOf(it);
                      const calculatedItem = calcMap[key];
                      
                      // Log เฉพาะ item แรกเพื่อไม่ให้ log เยอะเกินไป
                      if (i === 0) {
                        console.log('🎯 [CartItemRow] Rendering first item:', {
                          sku: it.sku,
                          key,
                          hasCalculatedItem: !!calculatedItem,
                          calculatedItem: calculatedItem ? {
                            UnitPrice: calculatedItem.UnitPrice,
                            price_per_sheet: calculatedItem.price_per_sheet,
                            priceSource: calculatedItem.priceSource,
                            _LineTotal: calculatedItem._LineTotal
                          } : null
                        });
                      }
                      
                      return (
                        <CartItemRow
                          key={uiKeyOf(it)}
                          item={it}
                          index={i}
                          dispatch={dispatch}
                          calculatedItem={calculatedItem}
                          customerCode={customerCode}
                        />
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ✅ cross sell อยู่นอก scroll */}
            <CrossSellPanel onAddRequest={handleCrossSellAdd} />
          </div>

          {/* ขวา: สรุปยอด */}
          <div className="col-span-2">
            <div className="sticky top-28 space-y-6 rounded-lg bg-gray-50 p-6 shadow-sm mt-3">
              {/* แสดง Promotion Banner */}
              <PromotionBanner promotions={promotions} />
              
              {/* Dropdown เลือกโครงการ */}
              {customerProjects.length > 0 && (
                <div className="border-b border-gray-200 pb-4">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    เลือกโครงการ (ถ้ามี)
                  </label>
                  <select
                    value={selectedProject || ''}
                    onChange={(e) => {
                      const projectId = e.target.value ? parseInt(e.target.value) : null;
                      setSelectedProject(projectId);
                      console.log('🏗️ Selected project:', projectId);
                    }}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    <option value="">กรุณาเลือกโครงการ</option>
                    {customerProjects.map((proj) => (
                      <option key={proj.project_id} value={proj.project_id}>
                        {proj.project_name || proj.project_code}
                      </option>
                    ))}
                  </select>
                  {selectedProject && (
                    <p className="mt-1 text-xs text-green-600">
                      ✓ ใช้ราคาโครงการ
                    </p>
                  )}
                </div>
              )}
              
              <div>
                <h4 className="mb-2 text-lg font-semibold text-gray-800">ข้อมูลใบเสนอราคา</h4>
              </div>

              <div className="space-y-2 border-t border-gray-200 pt-4">
                <h4 className="text-lg font-semibold text-gray-800">สรุปยอด</h4>
                {editingShippingCost && state.deliveryType === "DELIVERY" ? (
                  <div className="flex justify-between items-center py-2 gap-2">
                    <span className="font-semibold text-gray-600 text-sm">ค่าขนส่ง</span>
                    <input
                        type="number"
                        min="0"
                        step="1"
                        value={tempShippingCost}
                        onChange={(e) => setTempShippingCost(Number(e.target.value))}
                        className="w-20 rounded-lg border border-blue-500 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        autoFocus
                      />
                    <div className="flex flex-col  items-center gap-2">                     
                      <button
                        onClick={() => {
                          dispatch({
                            type: "SET_SHIPPING",
                            payload: {
                              distance: state.distance,
                              cost: state.shippingCost,
                              companyPay: state.shippingCompanyPay,
                              customerPay: tempShippingCost,
                              vehicleType: state.vehicleType,
                              unloadHours: state.unloadHours,
                              staffCount: state.staffCount,
                            },
                          });
                          setEditingShippingCost(false);
                        }}
                        className="px-2 py-1 text-xs font-semibold text-white bg-green-600 rounded hover:bg-green-700"
                      >
                        บันทึก
                      </button>
                      <button
                        onClick={() => setEditingShippingCost(false)}
                        className="px-2 py-1 text-xs font-semibold text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
                      >
                        ยกเลิก
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between py-2 cursor-pointer hover:bg-blue-50 px-2 rounded transition-colors" onDoubleClick={() => {
                    if (state.deliveryType === "DELIVERY") {
                      setTempShippingCost(Number(state.shippingCustomerPay || 0));
                      setEditingShippingCost(true);
                    }
                  }}>
                    <span className="font-semibold text-gray-600">ค่าขนส่ง</span>
                    <span className="font-bold text-gray-800">
                      {state.deliveryType === "DELIVERY"
                        ? fmtTHB(Number(state.shippingCustomerPay || 0))
                        : "รับเอง (ไม่มีค่าขนส่ง)"}
                    </span>
                  </div>
                )}
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

                {calculation.error && <p className="text-sm text-red-500">{calculation.error}</p>}
              </div>

              <div className="space-y-3 border-t border-gray-200 pt-4">
                <button className="flex w-full items-center justify-center rounded-lg bg-[#c1c1c1] px-6 py-3 font-semibold text-white shadow-md  disabled:opacity-50">
                  <FileIcon />
                  แนบไฟล์
                </button>
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
                
                {/* แสดงปุ่มขอราคาพิเศษถ้ามีสินค้าที่ราคาต่ำกว่า R1 */}
                {itemsBelowR1.length > 0 ? (
                  <>
                    {/* ถ้า special price request approved แล้ว แสดงปุ่มยืนยัน */}
                    {specialPriceRequest?.status === 'APPROVED' ? (
                      <>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-3">
                          <p className="text-sm font-semibold text-green-800">
                            ✓ ราคาพิเศษได้รับการอนุมัติแล้ว
                          </p>
                          
                        </div>
                        <button
                          disabled={calculation.loading || !!calculation.error}
                          onClick={() => handleSaveQuotation("complete")}
                          className="flex w-full items-center justify-center rounded-lg bg-[#DC2626] px-6 py-3 font-semibold text-white shadow-md hover:bg-[#c42222] disabled:opacity-50"
                        >
                          <SaveIcon /> ยืนยันใบเสนอราคา
                        </button>
                      </>
                    ) : specialPriceRequest?.status && ['SUBMITTED', 'PENDING_ZM', 'PENDING_RM'].includes(specialPriceRequest.status) ? (
                      <>
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-3">
                          <p className="text-sm font-semibold text-yellow-800">
                            ⏳ รอการอนุมัติราคาพิเศษ
                          </p>
                          <p className="text-xs text-yellow-700 mt-1">
                            สถานะ: {specialPriceRequest.status}
                          </p>
                        </div>
                        <button
                          disabled={true}
                          className="flex w-full items-center justify-center rounded-lg bg-gray-400 px-6 py-3 font-semibold text-white shadow-md cursor-not-allowed"
                        >
                          <SaveIcon /> รอการอนุมัติ
                        </button>
                      </>
                    ) : (
                      <>
                        {/* แสดงคำเตือนถ้ามีสินค้าที่ไม่สามารถขออนุมัติได้ */}
                        {rejectedItems.length > 0 && (
                          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-3">
                            <p className="text-sm font-semibold text-red-800">
                              ⚠️ พบสินค้า {rejectedItems.length} รายการที่ราคานอกช่วงที่อนุมัติได้
                            </p>
                            <p className="text-xs text-red-700 mt-1">
                              กรุณาแก้ไขราคาให้อยู่ในช่วง R1 ถึง W1 ก่อนส่งขออนุมัติ
                            </p>
                          </div>
                        )}
                        
                        <button
                          disabled={calculation.loading || !!calculation.error || rejectedItems.length > 0}
                          onClick={() => setShowSpecialPriceModal(true)}
                          className="flex w-full items-center justify-center rounded-lg bg-[#9333EA] px-6 py-3 font-semibold text-white shadow-md hover:bg-[#7e22ce] disabled:opacity-50"
                        >
                          <SaveIcon /> 
                          {rejectedItems.length > 0 
                            ? `ไม่สามารถขออนุมัติได้ (${rejectedItems.length} รายการนอกช่วง)`
                            : `ขอราคาพิเศษ (${approvableItems.length} รายการ)`
                          }
                        </button>
                      </>
                    )}
                  </>
                ) : (
                  <button
                    disabled={calculation.loading || !!calculation.error}
                    onClick={() => handleSaveQuotation("complete")}
                    className="flex w-full items-center justify-center rounded-lg bg-[#DC2626] px-6 py-3 font-semibold text-white shadow-md hover:bg-[#c42222] disabled:opacity-50"
                  >
                    <SaveIcon /> ยืนยัน
                  </button>
                )}
                {state.status === "complete" && (
                  <button
                    disabled={sendingToBC}
                    onClick={handleDynamicsImportClick}
                    className="flex w-full items-center justify-center rounded-lg bg-[#2563EB] px-6 py-3 font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {sendingToBC ? "กำลังส่งเข้า BC..." : "ส่งเข้า Dynamics 365"}
                  </button>
                )}

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
              setProductOffset(0);
              setProductHasMore(true);
              setProductTotal(0);
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

          <div className="grid grid-cols-8 gap-4">
            <div className="col-span-2">
              <ProductList
                items={productItems}
                loading={productLoading}
                loadingMore={productLoadingMore}
                hasMore={productHasMore}
                total={productTotal}
                onSelect={setSelectedProduct}
                onLoadMore={() => loadProductItems(false)}
                onCategoryClick={handleCategoryClick}
                selectedCategory={selectedCategory}
              />
            </div>

            <div className="col-span-4">
              <ProductDetail item={selectedProduct} />
            </div>

            <div className="col-span-2">
              <ProductImage item={selectedProduct} />
            </div>
          </div>
        </div>
      )}

      {/* TAB: CUSTOMER (ถ้าจะทำเพิ่มทีหลังได้) */}
      {activeTab === "customer" && <div className="border-t-4 border-gray-200 pt-4 "></div>}

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
          cost: state.shippingCost || 0, // ค่าขนส่งที่ระบบคิด
          customerPay: state.shippingCustomerPay || 0, // ค่าขนส่งที่ user แก้ไข
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
                cost: Number(res.data.shipping_cost || 0), // ค่าขนส่งที่ระบบคิด
                companyPay: Number(res.data.company_pay || 0),
                customerPay: Number(data.customerPay || res.data.customer_pay || 0), // ค่าขนส่งที่ user แก้ไข
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

      {/* Dynamics Import Confirmation Modal */}
      <DynamicsImportConfirmModal
        open={showDynamicsConfirm}
        onCancel={() => setShowDynamicsConfirm(false)}
        onConfirm={handleConfirmDynamicsImport}
      />

      {/* Special Price Request Modal */}
      <SpecialPriceRequestModal
        open={showSpecialPriceModal}
        onClose={() => setShowSpecialPriceModal(false)}
        onConfirm={handleSpecialPriceRequest}
        itemsBelowR1={itemsBelowR1}
      />
    </div>
  );
}

export default Step6_Summary;