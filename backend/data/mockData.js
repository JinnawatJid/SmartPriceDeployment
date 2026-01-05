// data/mockData.js
import * as XLSX from "xlsx";
// โหลดไฟล์ Excel
const workbook = XLSX.readFile("/src/data/Items.xlsx");
const sheet = workbook.Sheets["G"];
const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });

// ===== Helper: ดึงความหนา (มม.) จากชื่อ =====
const extractThickness = (name = "") => {
  const match = name.match(/(\d+)\s*มม/);
  return match ? match[1] : "";
};

// ===== สร้างข้อมูลสินค้า G จาก Excel =====
const productsG = rows.slice(1).map((row) => {
  const [sku, , name, stock] = row;

  // ราคาสุ่มในช่วง 100–300
  const base = Math.floor(Math.random() * 200) + 100;

  return {
    sku: sku?.toString().trim() || "",
    name: name?.toString().trim() || "",
    type: "G",
    thickness: extractThickness(name),
    priceR2: base + 20,
    priceR1: base + 10,
    priceW2: base,
    priceW1: base - 10,
    stock: Number(stock) || 0,
    unit: "ตร.ฟุต",
  };
});

export const MOCK_DATA = {
  customers: [
    {
      id: 'DAY208',
      name: 'บริษัท กระจกใส จำกัด',
      contact: 'นายสมศักดิ์',
      phone: '081-111-2222',
      email: 'somsak@glass.com',
      address: '123 ถ.พระราม4 กรุงเทพฯ 10110',
      taxId: '0105558001234',
      customerDate: '2024-02-05',
      accum6m: 935976.457943925,
      frequency: 85,
      genBus: 'R',
      accumByCategory: {
        G: 198014.738317757,
        A: 565819,
        S: 31271.8971962617,
        E: 120502.028037383,
        Y: 13135.6728971963,
      },
    },
    // ... (ข้อมูลลูกค้ารายอื่น ๆ ตามเดิม)
  ],

  products: {
    
    G: productsG,

    Y: [
      { sku: 'Y001', name: 'ยิปซั่มบอร์ดธรรมดา', type: 'Y', size: '120x240x0.95 ซม.', priceR2: 180, priceR1: 170, priceW2: 160, priceW1: 150, stock: 500, unit: 'แผ่น' },
      { sku: 'Y002', name: 'ยิปซั่มบอร์ดกันชื้น', type: 'Y', size: '120x240x1.2 ซม.', priceR2: 250, priceR1: 235, priceW2: 220, priceW1: 210, stock: 300, unit: 'แผ่น' },
      { sku: 'Y003', name: 'ยิปซั่มบอร์ดกันไฟ', type: 'Y', size: '120x240x1.2 ซม.', priceR2: 280, priceR1: 265, priceW2: 250, priceW1: 240, stock: 200, unit: 'แผ่น' },
      { sku: 'Y004', name: 'เพดานยิปซั่ม 60x60', type: 'Y', size: '60x60x0.8 ซม.', priceR2: 85, priceR1: 80, priceW2: 75, priceW1: 72, stock: 1000, unit: 'แผ่น' },
      { sku: 'Y005', name: 'ยิปซั่มฉาบเรียบ', type: 'Y', size: 'ถุง 25 กก.', priceR2: 220, priceR1: 210, priceW2: 200, priceW1: 190, stock: 150, unit: 'ถุง' }
    ],
    C: [
      { sku: 'C001', name: 'โครงคร่าวเพดานหลัก', type: 'C', size: '3.6 ม.', priceR2: 95, priceR1: 90, priceW2: 85, priceW1: 82, stock: 500, unit: 'เส้น' },
      { sku: 'C002', name: 'โครงคร่าวเพดานรอง', type: 'C', size: '3.6 ม.', priceR2: 75, priceR1: 72, priceW2: 68, priceW1: 65, stock: 600, unit: 'เส้น' },
      { sku: 'C003', name: 'ซีลายน์บอร์ด', type: 'C', size: '120x240 ซม.', priceR2: 320, priceR1: 305, priceW2: 290, priceW1: 280, stock: 200, unit: 'แผ่น' },
      { sku: 'C004', name: 'มุมฉาก L-Shape', type: 'C', size: '3 ม.', priceR2: 45, priceR1: 43, priceW2: 41, priceW1: 39, stock: 300, unit: 'เส้น' },
      { sku: 'C005', name: 'คานขวาง T-Bar', type: 'C', size: '60 ซม.', priceR2: 35, priceR1: 33, priceW2: 31, priceW1: 30, stock: 800, unit: 'ชิ้น' }
    ],
    E: [
      { sku: 'E001', name: 'ยางอุดรูบานเลื่อน สีดำ', type: 'E', detail: 'ขนาด 1 นิ้ว', priceR2: 0.4, priceR1: 0.35, priceW2: 0.28, priceW1: 0.25, stock: 5000, unit: 'ตัว' },
      { sku: 'E002', name: 'น็อตตะปู', type: 'E', detail: 'M6x50', priceR2: 2, priceR1: 1.9, priceW2: 1.8, priceW1: 1.7, stock: 3000, unit: 'ตัว' },
      { sku: 'E003', name: 'เทปกาวยิปซั่ม', type: 'E', detail: 'กว้าง 5 ซม. x 90 ม.', priceR2: 65, priceR1: 62, priceW2: 59, priceW1: 57, stock: 200, unit: 'ม้วน' },
      { sku: 'E004', name: 'มุมบัว PVC', type: 'E', detail: '3 ม.', priceR2: 45, priceR1: 43, priceW2: 41, priceW1: 39, stock: 400, unit: 'เส้น' },
      { sku: 'E005', name: 'ยาแนว', type: 'E', detail: 'ถุง 3 กก.', priceR2: 120, priceR1: 115, priceW2: 110, priceW1: 105, stock: 150, unit: 'ถุง' }
    ],
    A: [
      { sku: 'A001', name: 'อลูมิเนียมโปรไฟล์ 3x3', type: 'A', size: '3"x3" หนา 1.2 มม.', pricePerKg: 185, priceR2: 185, priceR1: 178, priceW2: 172, priceW1: 168, weightPerPiece: 2.5, stock: 300, unit: 'เส้น' },
      { sku: 'A002', name: 'อลูมิเนียมโปรไฟล์ 4x4', type: 'A', size: '4"x4" หนา 1.5 มม.', pricePerKg: 180, priceR2: 180, priceR1: 173, priceW2: 167, priceW1: 163, weightPerPiece: 3.8, stock: 250, unit: 'เส้น' },
      { sku: 'A003', name: 'อลูมิเนียมฝ้าเพดาน', type: 'A', size: 'กว้าง 10 ซม.', pricePerKg: 175, priceR2: 175, priceR1: 168, priceW2: 162, priceW1: 158, weightPerPiece: 1.2, stock: 500, unit: 'เส้น' },
      { sku: 'A004', name: 'บานเกล็ดอลูมิเนียม', type: 'A', size: 'กว้าง 8 ซม.', pricePerKg: 190, priceR2: 190, priceR1: 183, priceW2: 177, priceW1: 172, weightPerPiece: 0.8, stock: 600, unit: 'เส้น' },
      { sku: 'A005', name: 'มุมอลูมิเนียม L-Shape', type: 'A', size: '2"x2" หนา 1.0 มม.', pricePerKg: 170, priceR2: 170, priceR1: 164, priceW2: 158, priceW1: 154, weightPerPiece: 1.5, stock: 400, unit: 'เส้น' }
    ],
    S: [
      { sku: 'S001', name: 'ซิลิโคนใส', type: 'S', size: 'หลอด 300 มล.', priceR2: 85, priceR1: 82, priceW2: 79, priceW1: 76, stock: 500, unit: 'หลอด' },
      { sku: 'S002', name: 'ซิลิโคนสีขาว', type: 'S', size: 'หลอด 300 มล.', priceR2: 90, priceR1: 87, priceW2: 84, priceW1: 81, stock: 400, unit: 'หลอด' },
      { sku: 'S003', name: 'ซิลิโคนกรดอะซิติก', type: 'S', size: 'หลอด 300 มล.', priceR2: 75, priceR1: 72, priceW2: 69, priceW1: 67, stock: 300, unit: 'หลอด' },
      { sku: 'S004', name: 'ซีแลนท์กันน้ำ PU', type: 'S', size: 'ถุง 600 มล.', priceR2: 145, priceR1: 140, priceW2: 135, priceW1: 130, stock: 250, unit: 'ถุง' },
      { sku: 'S005', name: 'โฟมโพลียูรีเทน', type: 'S', size: 'กระป๋อง 750 มล.', priceR2: 195, priceR1: 188, priceW2: 182, priceW1: 177, stock: 200, unit: 'กระป๋อง' }
    ],
  },

  invoiceHistory: {
    // ... (ตามเดิม)
  }
};
