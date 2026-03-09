# แก้ไข Filter UI ใน ProjectPriceManagement ให้เหมือน PromotionManagement

## ปัญหา
Filter UI ใน ProjectPriceManagement ใช้ปุ่มแบบธรรมดา แต่ต้องการให้เป็น MultiSelectDropdown เหมือน PromotionManagement

## วิธีแก้ไข

### 1. เพิ่ม Import
```javascript
import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Calendar, User, Building2, Filter, ChevronDown, Check } from 'lucide-react';
```

### 2. เพิ่ม State
```javascript
const [openDropdown, setOpenDropdown] = useState({});
```

### 3. เพิ่มฟังก์ชัน Helper
```javascript
const handleFilterToggle = (field, value) => {
  setFilterCriteria(prev => {
    const current = prev[field] || [];
    const newValues = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    return { ...prev, [field]: newValues };
  });
};

const handleCategoryToggle = (value) => {
  setFilterCriteria(prev => {
    const current = prev.categories || [];
    const newCategories = current.includes(value)
      ? current.filter(c => c !== value)
      : [...current, value];
    return { ...prev, categories: newCategories };
  });
};
```

### 4. แทนที่ Filter Modal UI

แทนที่ส่วน Filter Modal ทั้งหมด (บรรทัด 694-890) ด้วย:

```jsx
{/* Filter Modal */}
{showFilterModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <h2 className="text-xl font-bold mb-4">เลือกสินค้าตาม Filter</h2>
      
      <div className="space-y-4">
        {/* Categories - Checkbox Style */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ประเภทสินค้า *
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {CATEGORY_OPTIONS.map(cat => (
              <label
                key={cat.value}
                className={`flex items-center border rounded-lg px-3 py-2 cursor-pointer transition-colors ${
                  filterCriteria.categories.includes(cat.value)
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={filterCriteria.categories.includes(cat.value)}
                  onChange={() => handleCategoryToggle(cat.value)}
                  className="mr-2"
                />
                <span className="font-medium">{cat.label}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            เลือก Category ก่อน จากนั้นจึงจะสามารถเลือก Brand, Group ฯลฯ ได้
          </p>
        </div>

        {/* MultiSelect Dropdowns */}
        {filterCriteria.categories.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <MultiSelectDropdown
              label="Brand"
              options={filterOptions.brands}
              selectedValues={filterCriteria.brands}
              onToggle={(value) => handleFilterToggle('brands', value)}
              isOpen={openDropdown.brands}
              onOpen={() => setOpenDropdown(prev => ({ ...prev, brands: true }))}
              onClose={() => setOpenDropdown(prev => ({ ...prev, brands: false }))}
            />

            <MultiSelectDropdown
              label="Group"
              options={filterOptions.groups}
              selectedValues={filterCriteria.groups}
              onToggle={(value) => handleFilterToggle('groups', value)}
              isOpen={openDropdown.groups}
              onOpen={() => setOpenDropdown(prev => ({ ...prev, groups: true }))}
              onClose={() => setOpenDropdown(prev => ({ ...prev, groups: false }))}
            />

            <MultiSelectDropdown
              label="SubGroup"
              options={filterOptions.subGroups}
              selectedValues={filterCriteria.subGroups}
              onToggle={(value) => handleFilterToggle('subGroups', value)}
              isOpen={openDropdown.subGroups}
              onOpen={() => setOpenDropdown(prev => ({ ...prev, subGroups: true }))}
              onClose={() => setOpenDropdown(prev => ({ ...prev, subGroups: false }))}
            />

            <MultiSelectDropdown
              label="Color"
              options={filterOptions.colors}
              selectedValues={filterCriteria.colors}
              onToggle={(value) => handleFilterToggle('colors', value)}
              isOpen={openDropdown.colors}
              onOpen={() => setOpenDropdown(prev => ({ ...prev, colors: true }))}
              onClose={() => setOpenDropdown(prev => ({ ...prev, colors: false }))}
            />

            <MultiSelectDropdown
              label="Thickness"
              options={filterOptions.thicknesses}
              selectedValues={filterCriteria.thicknesses}
              onToggle={(value) => handleFilterToggle('thicknesses', value)}
              isOpen={openDropdown.thickness}
              onOpen={() => setOpenDropdown(prev => ({ ...prev, thickness: true }))}
              onClose={() => setOpenDropdown(prev => ({ ...prev, thickness: false }))}
            />
          </div>
        )}

        {/* Loading State */}
        {loadingSkus && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <p className="text-blue-700">กำลังค้นหา SKU ที่ตรงกับเงื่อนไข...</p>
          </div>
        )}

        {/* Matched SKUs Display */}
        {!loadingSkus && matchedSkus.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800 font-semibold mb-2">
              ✅ พบ {matchedSkus.length} SKU ที่ตรงกับเงื่อนไข
            </p>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {matchedSkus.slice(0, 10).map((item, idx) => (
                <p key={idx} className="text-sm text-gray-700">
                  • {item.sku} - {item.description}
                </p>
              ))}
              {matchedSkus.length > 10 && (
                <p className="text-sm text-gray-500 italic">
                  ... และอีก {matchedSkus.length - 10} รายการ
                </p>
              )}
            </div>
          </div>
        )}

        {/* No Results */}
        {!loadingSkus && matchedSkus.length === 0 && filterCriteria.categories.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800">
              ⚠️ ไม่พบ SKU ที่ตรงกับเงื่อนไข กรุณาลองเปลี่ยนเงื่อนไขการค้นหา
            </p>
          </div>
        )}
      </div>

      {/* Modal Actions */}
      <div className="flex gap-2 justify-end mt-6 pt-4 border-t">
        <button
          type="button"
          onClick={() => {
            setShowFilterModal(false);
            setFilterCriteria({
              categories: [],
              brands: [],
              groups: [],
              subGroups: [],
              colors: [],
              thicknesses: []
            });
            setMatchedSkus([]);
            setOpenDropdown({});
          }}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          ยกเลิก
        </button>
        <button
          type="button"
          onClick={addItemsFromFilter}
          disabled={matchedSkus.length === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          เพิ่มสินค้า {matchedSkus.length > 0 && `(${matchedSkus.length} รายการ)`}
        </button>
      </div>
    </div>
  </div>
)}
```

### 5. เพิ่ม MultiSelectDropdown Component

เพิ่มก่อน `export default ProjectPriceManagement;`:

```jsx
function MultiSelectDropdown({
  label,
  options = [],
  selectedValues = [],
  onToggle,
  isOpen,
  onOpen,
  onClose
}) {
  const ref = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        onClose?.();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const selectedLabels = options
    .filter((opt) => selectedValues.includes(opt.value))
    .map((opt) => opt.label);

  const handleItemClick = (e, value) => {
    e.stopPropagation();
    onToggle(value);
  };

  const handleButtonClick = () => {
    if (isOpen) {
      onClose();
    } else {
      onOpen();
    }
  };

  return (
    <div className="relative" ref={ref}>
      <label className="block text-sm font-medium mb-1">{label}</label>

      <button
        type="button"
        onClick={handleButtonClick}
        className="w-full border rounded-lg px-3 py-2 flex items-center justify-between bg-white hover:border-gray-400 transition-colors"
      >
        <span className="text-sm text-left truncate">
          {selectedLabels.length > 0
            ? `${selectedLabels.length} รายการที่เลือก`
            : `เลือก ${label}`}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {selectedValues.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedLabels.slice(0, 5).map((text, index) => (
            <span
              key={`${text}-${index}`}
              className="bg-red-50 text-red-700 text-xs px-2 py-1 rounded-full"
            >
              {text}
            </span>
          ))}
          {selectedLabels.length > 5 && (
            <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
              +{selectedLabels.length - 5} อื่นๆ
            </span>
          )}
        </div>
      )}

      {isOpen && (
        <div className="absolute z-20 mt-2 w-full bg-white border rounded-lg shadow-lg">
          <div className="max-h-64 overflow-y-auto">
            {options.length === 0 ? (
              <div className="p-3 text-sm text-gray-500">ไม่มีข้อมูล</div>
            ) : (
              options.map((opt) => {
                const checked = selectedValues.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={(e) => handleItemClick(e, opt.value)}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center justify-between transition-colors ${
                      checked ? 'bg-red-50' : ''
                    }`}
                  >
                    <span className="text-sm flex-1">{opt.label}</span>
                    {checked && <Check className="w-4 h-4 text-green-600 flex-shrink-0 ml-2" />}
                  </button>
                );
              })
            )}
          </div>
          
          <div className="border-t p-2 bg-gray-50">
            <button
              type="button"
              onClick={onClose}
              className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
            >
              เสร็จสิ้น ({selectedValues.length} รายการ)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

## สรุป

หลังจากแก้ไขแล้ว Filter UI จะเหมือน PromotionManagement เป๊ะๆ:
- ✅ Category เป็น Checkbox
- ✅ Brand, Group, SubGroup, Color, Thickness เป็น MultiSelectDropdown
- ✅ แสดงจำนวนรายการที่เลือก
- ✅ แสดง SKU ที่ตรงกับเงื่อนไข
- ✅ มีปุ่ม "เสร็จสิ้น" ใน dropdown
- ✅ แสดง selected items ด้านล่าง dropdown
