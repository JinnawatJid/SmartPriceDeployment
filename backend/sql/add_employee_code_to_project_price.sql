-- Add CreatedByEmployeeCode column to Project_Price_Header table
-- This column stores the employee code who created the project price

ALTER TABLE Project_Price_Header
ADD CreatedByEmployeeCode NVARCHAR(50) NULL;

-- Add index for better query performance
CREATE INDEX IX_Project_Price_Header_CreatedByEmployeeCode 
ON Project_Price_Header(CreatedByEmployeeCode);

-- Optional: Add a comment/description
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Employee code who created this project price record',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Project_Price_Header',
    @level2type = N'COLUMN', @level2name = N'CreatedByEmployeeCode';
