// src/pages/QuoteDraftListPage.jsx
import React, { useState, useEffect } from "react";
import QuoteDraftCard from "../components/quotes/QuoteDraftCard.jsx";
import api from "../services/api.js";
import { useNavigate } from "react-router-dom";
import { useQuote } from "../context/QuoteContext";


export default function QuoteDraftListPage() {
  const navigate = useNavigate(); 
  const [searchText, setSearchText] = useState("");
  const [salesFilter, setSalesFilter] = useState("");
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDrafts = async () => {
      try {
        setLoading(true);
        const res = await api.get("/api/quotation", {
          params: { status: "open" },
        });
        setDrafts(res.data || []);
      } catch (err) {
        console.error(err);
        setError("ไม่สามารถโหลดใบเสนอราคาแบบร่างได้");
      } finally {
        setLoading(false);
      }
    };
    fetchDrafts();
  }, []);

  const filtered = drafts.filter((q) => {
    const text = (searchText || "").toLowerCase();

    const customerName = q.customer?.name?.toLowerCase() || "";
    const customerCode = q.customer?.id?.toLowerCase() || "";
    const quoteNo = (q.quoteNo || q.id || "").toLowerCase();
    const salesName = q.employee?.name?.toLowerCase() || "";

    const byText =
      !text ||
      quoteNo.includes(text) ||
      customerName.includes(text) ||
      customerCode.includes(text);

    const bySales =
      !salesFilter ||
      salesName.includes(salesFilter.toLowerCase());

    return byText && bySales;
  });
  const { dispatch } = useQuote();
  const handleEditDraft = async (q) => {
  const res = await api.get(`/api/quotation/${encodeURIComponent(q.quoteNo)}`);
  const h = res.data.header;
  const lines = res.data.lines;

  // 2) แปลง Quote_Line เป็น cart ที่ Step6 ใช้
  const cart = lines.map(ln => ({
    sku: ln.ItemCode,
    name: ln.ItemName,
    qty: ln.Quantity,
    price: ln.UnitPrice,
    lineTotal: ln.TotalPrice,
    category: ln.Category,
    unit: ln.Unit
  }));

  // 3) Dispatch → โหลดเข้าสู่ Context
  dispatch({
  type: "LOAD_DRAFT",
  payload: {
    id: q.quoteNo,
    quoteNo: q.quoteNo,

    customer: {
      id: h.CustomerCode,
      code: h.CustomerCode,
      name: h.CustomerName,
      phone: h.Tel || ""
    },

    deliveryType: h.ShippingMethod,
    billTaxName: h.BillTaxName,
    note: h.Remark,
    needTaxInvoice: h.NeedsTax === "Y",

    cart,

    // เพิ่มตรงนี้: ให้เข้า QuoteContext โดยตรง
    shippingCost: h.ShippingCost ?? 0,
    shippingCustomerPay: h.ShippingCustomerPay ?? 0,
    shippingCompanyPay: h.ShippingCompanyPay ?? 0,

    totals: {
      exVat: h.SubtotalAmount,
      vat: h.SubtotalAmount * 0.07,
      grandTotal: h.TotalAmount,
      shippingRaw: h.ShippingCost ?? 0,
      shippingCustomerPay: h.ShippingCustomerPay ?? 0,
      shippingCompanyPay: h.ShippingCompanyPay ?? 0
    }
  }
});



  // 4) นำไป Step6
  navigate("/create?step=6");
};
  const handleDeleteDraft = async (quoteNo) => {
  const ok = window.confirm(`ต้องการลบใบเสนอราคาเลขที่ ${quoteNo}?`);
  if (!ok) return;

  try {
    await api.delete(`/api/quotation/${quoteNo}`);

    // ใช้ quoteNo เป็น key ในการลบ
    setDrafts(prev => prev.filter(q => q.quoteNo !== quoteNo));

  } catch (err) {
    alert("ลบไม่ได้");
  }
};




  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-6">
        {/* Title & search bar */}
        <div className="mb-5 rounded-2xl bg-white shadow-sm border border-gray-200 px-5 py-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">🛒</span>
            <h1 className="text-lg md:text-xl font-bold text-gray-800">
              รอดำเนินการ - ใบเสนอราคาแบบร่าง
            </h1>
          </div>

          <div className="flex flex-col md:flex-row gap-3 md:items-end">
            {/* ช่องค้นหา */}
            <div className="flex-1">
              <label className="block font-medium text-gray-600 mb-1">
                ค้นหา
              </label>
              <input
                type="text"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="ค้นหาด้วย รหัสลูกค้า, ชื่อ หรือ เลขที่ใบเสนอราคา"
                className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            {/* พนักงานขาย */}
            <div className="w-full md:w-64">
              <label className="block font-medium text-gray-600 mb-1">
                พนักงานขาย
              </label>
              <input
                type="text"
                value={salesFilter}
                onChange={(e) => setSalesFilter(e.target.value)}
                placeholder="ทั้งหมด"
                className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div className="flex md:justify-end">
              <button
                type="button"
                className="mt-1 md:mt-0 inline-flex items-center justify-center rounded-lg bg-[#0084FF] px-6 py-2 text-sm font-semibold text-white hover:bg-blue-600"
              >
                ค้นหา
              </button>
            </div>
          </div>
        </div>

        {/* Grid cards */}
        {loading && (
          <p className="text-sm text-gray-500">กำลังโหลดข้อมูล...</p>
        )}
        {error && (
          <p className="text-sm text-red-500 mb-2">{error}</p>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 ">
          {!loading && filtered.length === 0 && (
            <p className="text-sm text-gray-500 col-span-full">
              ยังไม่มีใบเสนอราคาแบบร่าง
            </p>
          )}

          {filtered.map((q) => {
            const totalAmount =
              q.totals?.grandTotal ??
              q.cart?.reduce(
                (sum, it) => sum + Number(it.lineTotal || 0),
                0
              );

            return (
              <QuoteDraftCard
                key={q.id}
                quoteNo={q.quoteNo || q.id}
                customerName={
                  q.customerName ||
                  q.customer?.name ||
                  q.customer?.CustomerName ||
                  "ผู้ไม่ประสงค์ออกนาม"
                }
                customerCode={
                  q.customer?.id ||
                  q.customer?.code ||
                  q.customerCode ||
                  q.CustomerCode ||
                  "ผู้ไม่ประสงค์ออกนาม"
                }
                salesName={q.employee?.name || "-"}
                dueDateText={
                  q.createdAt
                    ? new Date(q.createdAt).toLocaleString("th-TH")
                    : "-"
                }
                totalAmount={totalAmount || 0}
                items={q.cart || []}
                onEdit={() => handleEditDraft(q)}
                onDelete={() => handleDeleteDraft(q.quoteNo)}
 
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
