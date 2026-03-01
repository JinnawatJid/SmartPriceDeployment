-- สร้างตาราง Promotion_Header
CREATE TABLE IF NOT EXISTS Promotion_Header (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_name TEXT NOT NULL,
    branch TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'active',  -- active / inactive
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- สร้างตาราง Promotion_Items
CREATE TABLE IF NOT EXISTS Promotion_Items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_id INTEGER NOT NULL,
    sku TEXT NOT NULL,
    promotion_text TEXT NOT NULL,  -- พนักงานพิมพ์เอง
    created_at TEXT,
    FOREIGN KEY (promotion_id) REFERENCES Promotion_Header(id) ON DELETE CASCADE
);

-- สร้าง index เพื่อเพิ่มประสิทธิภาพการค้นหา
CREATE INDEX IF NOT EXISTS idx_promotion_status ON Promotion_Header(status);
CREATE INDEX IF NOT EXISTS idx_promotion_dates ON Promotion_Header(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_promotion_items_sku ON Promotion_Items(sku);
CREATE INDEX IF NOT EXISTS idx_promotion_items_promotion_id ON Promotion_Items(promotion_id);
