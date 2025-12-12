// src/pages/CreateQuote/CreateQuoteWizard.jsx
import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useQuote } from "../../hooks/useQuote.js";
import Step6_Summary from "./Step6_Summary.jsx";



function CreateQuoteWizard() {
  const { state, dispatch } = useQuote();
  const location = useLocation();
  const repeatOrder = location.state?.repeatOrder;
  
  useEffect(() => {
    const r = location.state?.repeatOrder;
    if (!r) return;

    // 1) ลูกค้า
    dispatch({ type: "SET_CUSTOMER", payload: r.customer });

    // 2) ตะกร้าสินค้าเดิม
    dispatch({ type: "SET_CART", payload: r.cart });

    // 3) Tax + Delivery
    dispatch({
      type: "SET_TAX_DELIVERY",
      payload: {
        needsTax: r.needTaxInvoice,
        deliveryType: r.deliveryType || "PICKUP",
        billTaxName: r.billTaxName || "",
      },
    });

    // 4) ค่าขนส่ง
    dispatch({
      type: "SET_SHIPPING",
      payload: {
        cost: r.shippingRaw ?? 0,
        distance: r.distance ?? "",
      },
    });

    // 5) Note
    dispatch({
      type: "SET_REMARK",
      payload: r.note || "",
    });

    // 6) เปิด Step6 ทันที
    dispatch({ type: "SET_STEP", payload: 6 });

  }, [location.state, dispatch]);



  // ✅ โหลด draft เข้าสู่ QuoteContext ถ้ามีส่งมาจากหน้า Draft
  useEffect(() => {
    
    const draft = location.state?.draft;
    if (!draft) return;

    dispatch({ type: "LOAD_DRAFT", payload: draft });
  }, [location.state, dispatch]);

  if (!state) {
    return <div>Loading Quote Context...</div>;
  }

  return <Step6_Summary state={state} dispatch={dispatch} />;
}

export default CreateQuoteWizard;
