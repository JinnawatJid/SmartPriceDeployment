// src/utils/printQuotation.js
import { PDFDocument, rgb } from "pdf-lib";
import fontkit from "@pdf-lib/fontkit";

// helper: format numbers th-TH
const n = (v) => (typeof v === "number" ? v.toLocaleString("th-TH") : (v ?? ""));
// helper: format currency
const c = (v) =>
  Number.isFinite(v) ? v.toLocaleString("th-TH", { style: "currency", currency: "THB" }) : "";

// ====== ปรับตำแหน่งให้ตรงเทมเพลตของคุณ ======
// หมายเหตุ: ค่าต่ำกว่านี้คือ "พิกัดตัวอย่าง" ให้ใช้เป็น base แล้วขยับ x,y ตามจริง
// หน่วยเป็น points (A4: ~595x842), origin = มุมซ้ายล่าง
const POS = {
  // header / customer box
  date: { x: 460, y: 745 }, // วันที่:
  docNo: { x: 460, y: 765 }, // เลขที่เอกสาร: (ถ้ามี)
  custId: { x: 120, y: 705 }, // รหัสลูกค้า:
  custName: { x: 120, y: 685 }, // ชื่อลูกค้า:
  custPhone: { x: 120, y: 665 }, // เบอร์โทร:
  deliveryType: { x: 420, y: 705 }, // กำหนดส่ง:
  salesman: { x: 420, y: 685 }, // พนักงานขาย:

  // table columns (กำหนด "ขอบขวา" ของแต่ละคอลัมน์เพื่อชิดขวา)
  cols: {
    codeL: 60,
    codeR: 120, // Code (ชิดซ้าย)
    nameL: 130,
    nameR: 350, // Name (ตัดคำ)
    qtyR: 380, // Qty (ชิดขวา)
    unitR: 470, // Unit Price (ชิดขวา)
    amtR: 560, // Amount (ชิดขวา)
  },
  table: {
    startY: 620,
    lineGap: 18,
    minY: 140, // เว้นพื้นที่สรุปท้ายหน้า
  },

  // totals (พิมพ์เฉพาะ "หน้าสุดท้าย")
  subTotal: { x: 400, y: 185 },
  shipping: { x: 400, y: 167 },
  vat: { x: 400, y: 149 },
  grandTotal: { x: 400, y: 129 },
};

// ====== helper drawing ======
const drawRight = (page, text, xRight, y, font, size, color = rgb(0, 0, 0)) => {
  const t = String(text ?? "");
  const w = font.widthOfTextAtSize(t, size);
  page.drawText(t, { x: xRight - w, y, size, font, color });
};

const drawTrim = (page, text, x, y, font, size, maxWidth, color = rgb(0, 0, 0)) => {
  let t = String(text ?? "");
  let width = font.widthOfTextAtSize(t, size);
  if (width <= maxWidth) {
    page.drawText(t, { x, y, size, font, color });
    return;
  }
  // ตัดให้พอดี + ใส่ …
  const ellipsis = "…";
  const ellW = font.widthOfTextAtSize(ellipsis, size);
  while (t.length > 0 && width + ellW > maxWidth) {
    t = t.slice(0, -1);
    width = font.widthOfTextAtSize(t, size);
  }
  page.drawText(t + ellipsis, { x, y, size, font, color });
};

// ====== main ======
export async function printQuotation({ state, calculation, employee }) {
  // load template
  const tplRes = await fetch("/templates/QT-Template.pdf");
  if (!tplRes.ok) throw new Error("ไม่พบไฟล์เทมเพลต /templates/QT-Template.pdf");
  const tplBytes = await tplRes.arrayBuffer();

  const pdfDoc = await PDFDocument.load(tplBytes);
  pdfDoc.registerFontkit(fontkit);

  // embed Thai fonts
  const [regRes, boldRes] = await Promise.all([
    fetch("/fonts/Sarabun-Regular.ttf"),
    fetch("/fonts/Sarabun-Bold.ttf"),
  ]);
  if (!regRes.ok || !boldRes.ok) throw new Error("ไม่พบไฟล์ฟอนต์ไทยใน /fonts/");
  const [regBytes, boldBytes] = await Promise.all([regRes.arrayBuffer(), boldRes.arrayBuffer()]);
  const font = await pdfDoc.embedFont(regBytes, { subset: true });
  const fontBold = await pdfDoc.embedFont(boldBytes, { subset: true });

  // data
  const page0 = pdfDoc.getPages()[0];
  const copyTemplate = async () => {
    const [newPage] = await pdfDoc.copyPages(pdfDoc, [0]);
    pdfDoc.addPage(newPage);
    return newPage;
  };

  const items = calculation?.cart ?? [];
  const totals = calculation?.totals ?? {};
  const customer = state?.customer ?? {};
  const employeeName = employee?.name ?? "";
  const deliveryLabel = state?.deliveryType === "DELIVERY" ? "จัดส่ง" : "รับเอง";
  const now = new Date();
  const thDate = now.toLocaleDateString("th-TH");

  // ===== เติมช่องหัว (อย่าวาดหัวเอกสาร/หัวตารางซ้ำ) =====
  // (ปรับ x,y ใน POS ให้ตรงช่องว่างของเทมเพลตคุณ)
  page0.drawText(thDate, { x: POS.date.x, y: POS.date.y, size: 11, font });
  // page0.drawText(state?.docNo ?? '',      { x: POS.docNo.x,        y: POS.docNo.y,        size: 11, font }); // ถ้ามีเลขเอกสาร
  page0.drawText(String(customer.id || ""), { x: POS.custId.x, y: POS.custId.y, size: 11, font });
  page0.drawText(String(customer.name || ""), {
    x: POS.custName.x,
    y: POS.custName.y,
    size: 11,
    font,
  });
  page0.drawText(String(customer.phone || ""), {
    x: POS.custPhone.x,
    y: POS.custPhone.y,
    size: 11,
    font,
  });
  page0.drawText(deliveryLabel, { x: POS.deliveryType.x, y: POS.deliveryType.y, size: 11, font });
  page0.drawText(String(employeeName), { x: POS.salesman.x, y: POS.salesman.y, size: 11, font });

  // ===== วาดรายการสินค้า (แค่แถว ไม่วาดหัวตาราง) + แยกหน้าอัตโนมัติ =====
  const sizes = { row: 10, totals: 11, totalsBold: 12 };
  const { codeL, codeR, nameL, nameR, qtyR, unitR, amtR } = POS.cols;

  let page = page0;
  let y = POS.table.startY;

  const drawRow = (it) => {
    // ตัดชื่อให้พอดีช่อง
    drawTrim(page, it.name || "", nameL, y, font, sizes.row, nameR - nameL);
    // code (ซ้าย)
    page.drawText(String(it.sku || ""), { x: codeL, y, size: sizes.row, font });
    // qty/unit/amount (ขวา)
    drawRight(page, n(it.Quantity ?? it.qty ?? 0), qtyR, y, font, sizes.row);
    drawRight(page, n(it.NewPrice ?? 0), unitR, y, font, sizes.row);
    drawRight(page, n(it._LineTotal ?? 0), amtR, y, font, sizes.row);
  };

  for (const it of items) {
    if (y < POS.table.minY) {
      // สร้างหน้าใหม่ โดย "ก็อปหน้าเทมเพลต" เพื่อคงหัวกระดาษ
      page = await copyTemplate();
      y = POS.table.startY;
    }
    drawRow(it);
    y -= POS.table.lineGap;
  }

  // ===== พิมพ์ totals เฉพาะหน้าสุดท้าย =====
  const st = totals?.subtotalFmt ?? "";
  const ship = totals?.shippingFmt ?? "";
  const vat = totals?.taxFmt ?? "";
  const grand = totals?.totalFmt ?? "";

  page.drawText(`รวมจำนวนเงิน (สินค้า) : ${st}`, {
    x: POS.subTotal.x,
    y: POS.subTotal.y,
    size: sizes.totals,
    font: fontBold,
  });
  page.drawText(`ค่าจัดส่ง : ${ship}`, {
    x: POS.shipping.x,
    y: POS.shipping.y,
    size: sizes.totals,
    font,
  });
  page.drawText(`ภาษีมูลค่าเพิ่ม : ${vat}`, {
    x: POS.vat.x,
    y: POS.vat.y,
    size: sizes.totals,
    font,
  });
  page.drawText(`จำนวนเงินรวมสุทธิ : ${grand}`, {
    x: POS.grandTotal.x,
    y: POS.grandTotal.y,
    size: sizes.totalsBold,
    font: fontBold,
  });

  // save + print
  const pdfBytes = await pdfDoc.save();
  const blob = new Blob([pdfBytes], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);

  const w = window.open(url, "_blank");
  if (w) {
    w.onload = () => {
      try {
        w.focus();
        w.print();
      } catch {}
    };
  } else {
    alert("กรุณาอนุญาต Pop-up เพื่อใช้งานฟังก์ชันพิมพ์");
  }
}
