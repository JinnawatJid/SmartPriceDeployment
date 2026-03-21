-- SQL Script to add project_code column to Quote_Header table
-- Run this on your MSSQL database

-- Check if column exists before adding
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Quote_Header' AND COLUMN_NAME = 'project_code'
)
BEGIN
    ALTER TABLE Quote_Header
    ADD project_code VARCHAR(50) NULL;
    
    PRINT 'Column project_code added successfully to Quote_Header table';
END
ELSE
BEGIN
    PRINT 'Column project_code already exists in Quote_Header table';
END
GO
