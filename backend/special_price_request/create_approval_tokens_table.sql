-- ============================================
-- สร้างตาราง approval_tokens
-- สำหรับเก็บ token การอนุมัติผ่าน URL
-- ============================================

CREATE TABLE IF NOT EXISTS approval_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL,
    
    FOREIGN KEY (request_number) REFERENCES special_price_requests(request_number)
);

-- สร้าง index เพื่อเพิ่มความเร็วในการค้นหา
CREATE INDEX IF NOT EXISTS idx_approval_tokens_token ON approval_tokens(token);
CREATE INDEX IF NOT EXISTS idx_approval_tokens_request_number ON approval_tokens(request_number);
