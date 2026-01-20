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
import CrossSellPanel from "../../components/cross-sell/CrossSellPanel.jsx";

function Step6_Summary({ state, dispatch }) {
  const { employee } = useAuth();
  const navigate = useNavigate();

  // -----------------------------
  // helpers
  // -----------------------------
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

  const hasValidCustomer = () => {
    const code = String(getCustomerCode(state.customer) || "").trim();
    if (!code) return false;
    if (code.toUpperCase() === "N/A") return false;
    return true;
  };

  // -----------------------------
  // history state
  // -----------------------------
  const [historyOrders, setHistoryOrders] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  // -----------------------------
  // โหลดประวัติการซื้อ (เฉพาะลูกค้าที่มีรหัสจริง)
  // -----------------------------
  useEffect(() => {
    const custCode = String(getCustomerCode(state.customer) || "").trim();

    // ❌ ไม่มีลูกค้า / N-A → ไม่โหลด ไม่แสดง
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
          const qCode = String(getCustomerCode(q.customer) || "").trim();
          if (qCode !== custCode) return false;

          if (!currentSkus.size) return true;

          return (q.cart || []).some((line) =>
            currentSkus.has(line.sku)
          );
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

  // -----------------------------
  // UI
  // -----------------------------
  return (
    <div className="rounded-lg bg-white p-6 shadow-lg">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">
        สรุปใบเสนอราคา
      </h1>

      {/* -----------------------------
          ลูกค้า
      ----------------------------- */}
      <CustomerSearchSection
        customer={state.customer}
        onCustomerChange={(cust) =>
          dispatch({ type: "SET_CUSTOMER", payload: cust })
        }
      />

      <div className="mt-2 text-sm text-gray-600">
        {!hasValidCustomer() && (
          <span>
            หากไม่เลือกหรือไม่ระบุลูกค้า ระบบจะบันทึกเป็น{" "}
            <span className="font-semibold">ผู้ไม่ประสงค์ออกนาม</span>
          </span>
        )}

        {hasValidCustomer() && (
          <span>
            ลูกค้า:{" "}
            <span className="font-semibold">
              {state.customer?.name || "-"}
            </span>
          </span>
        )}
      </div>

      {/* -----------------------------
          BODY
      ----------------------------- */}
      <div className="grid grid-cols-8 gap-4 mt-6">
        {/* =============================
            LEFT : HISTORY + CATEGORY
        ============================== */}
        <div className="col-span-2 space-y-4">
          {/* ✅ แสดงประวัติ เฉพาะลูกค้าที่มีรหัสจริง */}
          {hasValidCustomer() && (
            <div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
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
                    ยังไม่พบประวัติการซื้อสำหรับลูกค้ารายนี้
                  </p>
                )}

              <div className="space-y-2">
                {historyOrders.map((ord) => (
                  <OrderHistoryCard
                    key={ord.id}
                    order={ord}
                    onRepeat={(order) =>
                      dispatch({
                        type: "LOAD_DRAFT",
                        payload: order,
                      })
                    }
                  />
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">
              เลือกประเภทสินค้า
            </h3>
            {/* category list เดิม */}
          </div>
        </div>

        {/* =============================
            CENTER : CART
        ============================== */}
        <div className="col-span-4">
          {/* cart table เดิม */}
        </div>

        {/* =============================
            RIGHT : SUMMARY
        ============================== */}
        <div className="col-span-2">
          {/* summary เดิม */}
          <CrossSellPanel />
        </div>
      </div>

      {/* modal ต่าง ๆ คงเดิม */}
      <ShippingModal />
      <ItemPickerModal />
      <GlassPickerModal />
    </div>
  );
}

export default Step6_Summary;
