// src/pages/CreateQuote/CreateQuoteWizard.jsx
import React, { useEffect, useRef  } from "react";
import { useLocation } from "react-router-dom";
import { useQuote } from "../../hooks/useQuote.js";
import Step6_Summary from "./Step6_Summary.jsx";



function CreateQuoteWizard() {
  const { state, dispatch } = useQuote();
  const location = useLocation();
  const repeatOrder = location.state?.repeatOrder;
  
  const consumedRef = useRef(false);

  useEffect(() => {
    if (consumedRef.current) return;

    const r = location.state?.repeatOrder;
    if (!r) return;

    consumedRef.current = true;

    dispatch({
      type: "LOAD_DRAFT",
      payload: {
        customer: r.customer,
        cart: Array.isArray(r.cart)
          ? r.cart.map((it) => ({
              ...it,
              cost: Number(it.cost ?? 0),
              pkg_size: it.pkg_size ?? 1,
            }))
          : [],
        deliveryType: r.deliveryType || "PICKUP",
        billTaxName: r.billTaxName || "",
        note: r.note || "",
        totals: {
          shippingRaw: r.shippingRaw ?? 0,
          shippingCustomerPay: r.shippingCustomerPay ?? 0,
        },
      },
    });
  }, []);//
console.log("STATE AFTER REPEAT", state);


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
