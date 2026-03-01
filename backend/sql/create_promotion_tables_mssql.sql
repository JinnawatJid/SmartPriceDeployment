-- สร้างตาราง Promotion_Header สำหรับ MSSQL
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Promotion_Header' AND xtype='U')
BEGIN
    CREATE TABLE Promotion_Header (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        PromotionName NVARCHAR(255) NOT NULL,
        Branch NVARCHAR(500),
        StartDate DATE NOT NULL,
        EndDate DATE NOT NULL,
        Status NVARCHAR(50) DEFAULT 'active',  -- active / inactive
        CreatedBy NVARCHAR(100),
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
END
GO

-- สร้างตาราง Promotion_Items สำหรับ MSSQL
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Promotion_Items' AND xtype='U')
BEGIN
    CREATE TABLE Promotion_Items (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        PromotionId INT NOT NULL,
        SKU NVARCHAR(100) NOT NULL,
        PromotionText NVARCHAR(500) NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (PromotionId) REFERENCES Promotion_Header(Id) ON DELETE CASCADE
    );
END
GO

-- สร้าง index เพื่อเพิ่มประสิทธิภาพการค้นหา
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Promotion_Status')
BEGIN
    CREATE INDEX IX_Promotion_Status ON Promotion_Header(Status);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Promotion_Dates')
BEGIN
    CREATE INDEX IX_Promotion_Dates ON Promotion_Header(StartDate, EndDate);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PromotionItems_SKU')
BEGIN
    CREATE INDEX IX_PromotionItems_SKU ON Promotion_Items(SKU);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PromotionItems_PromotionId')
BEGIN
    CREATE INDEX IX_PromotionItems_PromotionId ON Promotion_Items(PromotionId);
END
GO
