// src/pages/CreateQuote/CreateQuoteWizard.jsx
import React, { useEffect, useRef  } from "react";
import { useLocation } from "react-router-dom";
import { useQuote } from "../../hooks/useQuote.js";
import Step6_Summary from "./Step6_Summary.jsx";



function CreateQuoteWizard() {
  const { state, dispatch } = useQuote();
  const location = useLocation();

  // โหลด draft อย่างเดียว
  useEffect(() => {
    const draft = location.state?.draft;
    if (!draft) return;
    dispatch({ type: "LOAD_DRAFT", payload: draft });
  }, [location.state, dispatch]);

  return <Step6_Summary state={state} dispatch={dispatch} />;
}


export default CreateQuoteWizard;
