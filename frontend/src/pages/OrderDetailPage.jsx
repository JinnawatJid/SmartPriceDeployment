import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../services/api";

export default function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);

  useEffect(() => {
  const load = async () => {
    try {
      const res = await api.get(`/api/quotation/${id}`);
      const h = res.data.header || {};
      const lines = res.data.lines || [];

      // ⭐ แปลงข้อมูลให้เป็นรูปแบบที่ FE ใช้เดิม
      const formatted = {
        quoteNo: h.QuoteNo,
        createdAt: h.CreateDate,
        customer: {
          id: h.CustomerCode,
          name: h.CustomerName,
          phone: h.Tel,
        },

        // ⭐ ฟิลด์ที่ต้องเพิ่มเพื่อรองรับ "สั่งซื้อซ้ำ"
        needTaxInvoice: h.NeedsTax === "Y",
        billTaxName: h.BillTaxName || "",
        deliveryType: h.ShippingMethod || "PICKUP",
        note: h.Remark || "",

        totals: {
          exVat: h.SubtotalAmount,
          vat: h.SubtotalAmount ? h.TotalAmount - h.SubtotalAmount : 0,
          grandTotal: h.TotalAmount,
          shippingRaw: h.ShippingCost || 0,
          shippingCustomerPay: h.ShippingCustomerPay || 0,
        },

        cart: lines.map((ln) => ({
          sku: ln.ItemCode,
          name: ln.ItemName,
          qty: ln.Quantity,
          price: ln.UnitPrice,
          lineTotal: ln.TotalPrice,
          category: ln.Category,
          unit: ln.Unit,
        })),
      };


      setOrder(formatted);

    } catch (err) {
      console.error("Error loading order:", err);
    }
  };

  load();
}, [id]);


  if (!order) return <div className="p-6">กำลังโหลด...</div>;

  const fmt = (n) => Number(n || 0).toLocaleString();

  return (
    <div className="p-6">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300"
      >
        ย้อนกลับ
      </button>

      {/* กล่องรายการสินค้า */}
      <div className="bg-white rounded-xl p-6 shadow mb-6">
        <h2 className="text-xl font-bold mb-4">รายละเอียดรายการสินค้า</h2>

        <div className="grid grid-cols-4 gap-4 mb-4">
          <div>
            <p className="text-gray-600">เลขที่ใบเสนอราคา</p>
            <p className="font-semibold">{order.quoteNo}</p>
          </div>
          <div>
            <p className="text-gray-600">วันที่สั่งซื้อ</p>
            <p className="font-semibold">
              {new Date(order.createdAt).toLocaleDateString("th-TH")}
            </p>
          </div>
          <div>
            <p className="text-gray-600">รหัสลูกค้า</p>
            <p className="font-semibold">{order.customer?.id}</p>
          </div>
          <div>
            <p className="text-gray-600">ชื่อลูกค้า</p>
            <p className="font-semibold">{order.customer?.name}</p>
          </div>
        </div>

        {/* ตารางรายการสินค้า */}
        <table className="min-w-full mt-4">
          <thead>
            <tr className="border-b bg-gray-100">
              <th className="p-3 text-left">#</th>
              <th className="p-3 text-left">สินค้า</th>
              <th className="p-3 text-center">จำนวน</th>
              <th className="p-3 text-right">ราคา/หน่วย</th>
              <th className="p-3 text-right">ยอดรวม</th>
            </tr>
          </thead>
          <tbody>
            {(order.cart ?? []).map((item, idx) => (
              <tr key={idx} className="border-b">
                <td className="p-3">{idx + 1}</td>
                <td className="p-3">
                  {item.name}
                  <br />
                  <span className="text-gray-500 text-sm">{item.sku}</span>
                </td>
                <td className="p-3 text-center">{item.qty}</td>
                <td className="p-3 text-right">{fmt(item.price)}</td>
                <td className="p-3 text-right">{fmt(item.lineTotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* สรุปยอด */}
      <div className="bg-white rounded-xl p-6 shadow">
        <h2 className="text-xl font-bold mb-4">สรุปยอด</h2>

        <div className="flex justify-between text-lg">
          <p>ค่าขนส่ง</p>
          <p className="font-semibold">฿{fmt(order.totals.shippingCustomerPay)}</p>
        </div>

        <div className="flex justify-between mt-2">
          <p>ราคารวมก่อน VAT</p>
          <p className="font-semibold">฿{fmt(order.totals.exVat)}</p>
        </div>

        <div className="flex justify-between mt-2">
          <p>ภาษีมูลค่าเพิ่ม (7%)</p>
          <p className="font-semibold">฿{fmt(order.totals.vat)}</p>
        </div>

        <hr className="my-4" />

        <div className="flex justify-between text-xl font-bold text-blue-600">
          <p>ราคารวมสุทธิ (รวม VAT)</p>
          <p>฿{fmt(order.totals.grandTotal)}</p>
        </div>

        <div className="mt-6 flex gap-4">
          <button className="px-6 py-2 rounded-lg bg-gray-200 hover:bg-gray-300">
            พิมพ์ใบเสนอราคา
          </button>
          <button
            className="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            onClick={() => {
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
            }}
          >
            สั่งซื้อซ้ำ
          </button>

        </div>
      </div>
    </div>
  );
}
