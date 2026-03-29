import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Calendar, User, Building2, Filter, ChevronDown, Check } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const CATEGORY_OPTIONS = [
  { value: 'Glass', label: 'Glass' },
  { value: 'Aluminum', label: 'Aluminum' },
  { value: 'Sealant', label: 'Sealant' },
  { value: 'Gypsum', label: 'Gypsum' },
  { value: 'C-Line', label: 'C-Line' },
  { value: 'Accessories', label: 'Accessories' }
];

const ProjectPriceManagement = () => {
  const { employee } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState(null);
  
  // Customer search state
  const [customerSearchTerm, setCustomerSearchTerm] = useState('');
  
  // Mode selection
  const [priceMode, setPriceMode] = useState(null); // 'project' | 'branch' | 'customer'
  
  // Edit mode
  const [editingProjectId, setEditingProjectId] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    project_code: '',
    project_name: '',
    customer_code: '',
    customer_name: '',
    branch_code: '',
    price_start_date: '',
    price_end_date: '',
    request_by: '',
    request_date: new Date().toISOString().split('T')[0],
    remark: '',
  });
  
  const [items, setItems] = useState([]);
  const [branches, setBranches] = useState([]);
  
  // Filter selection state
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [filterCriteria, setFilterCriteria] = useState({
    categories: [],
    brands: [],
    groups: [],
    subGroups: [],
    colors: [],
    thicknesses: []
  });
  const [filterOptions, setFilterOptions] = useState({
    categories: CATEGORY_OPTIONS,
    brands: [],
    groups: [],
    subGroups: [],
    colors: [],
    thicknesses: []
  });
  const [matchedSkus, setMatchedSkus] = useState([]);
  const [loadingSkus, setLoadingSkus] = useState(false);
  const [openDropdown, setOpenDropdown] = useState({});
  
  // Global price and quantity for all filtered items
  const [globalPrice, setGlobalPrice] = useState('');
  const [globalQuantity, setGlobalQuantity] = useState('');
  const [globalUnit, setGlobalUnit] = useState('');

  useEffect(() => {
    if (employee?.id) {
      loadProjects();
    }
    loadBranches();
  }, [employee?.id]);

  // ⭐ Load filter options when categories change
  useEffect(() => {
    if (filterCriteria.categories.length > 0) {
      loadFilterOptions();
    }
  }, [filterCriteria.categories]);

  // ⭐ Reload matched SKUs when any filter changes
  useEffect(() => {
    if (filterCriteria.categories.length > 0) {
      loadMatchedSkus();
    }
  }, [filterCriteria.brands, filterCriteria.groups, filterCriteria.subGroups, filterCriteria.colors, filterCriteria.thicknesses]);

  // ⭐ Reload filter options when other filters change (to show only available options)
  useEffect(() => {
    if (filterCriteria.categories.length > 0) {
      loadFilterOptions();
    }
  }, [filterCriteria.brands, filterCriteria.groups, filterCriteria.subGroups, filterCriteria.colors, filterCriteria.thicknesses]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/api/project-prices/', {
        params: {
          employee_code: employee?.id
        }
      });
      // ข้อมูลจาก backend ถูกกรองแล้ว ไม่ต้องกรองอีก
      setProjects(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Error loading projects:', err);
      setError('ไม่สามารถโหลดข้อมูลโครงการได้');
      setProjects([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const loadBranches = async () => {
    try {
      const res = await api.get('/api/branches');
      // API returns {branches: [...]}
      const branchList = res.data?.branches || res.data || [];
      setBranches(Array.isArray(branchList) ? branchList : []);
    } catch (err) {
      console.error('Error loading branches:', err);
      setBranches([]); // Set empty array on error
    }
  };

  // Generate project code based on mode
  const generateProjectCode = () => {
    const now = new Date();
    const buddhistYear = String(now.getFullYear() + 543).slice(-2); // YY (พ.ศ.)
    const month = String(now.getMonth() + 1).padStart(2, '0'); // MM

    if (priceMode === 'project') {
      return `PJ${buddhistYear}${month}`;
    } else if (priceMode === 'branch') {
      const branchCode = formData.branch_code || 'XX';
      return `${branchCode}${buddhistYear}${month}`;
    } else if (priceMode === 'customer') {
      const custCode = formData.customer_code || '';
      return `${buddhistYear}${month}${custCode}`;
    }
    return '';
  };

  // Handle mode change
  const handleModeChange = (mode) => {
    setPriceMode(mode);
    setFormData({
      project_code: '',
      project_name: '',
      customer_code: '',
      customer_name: '',
      branch_code: '',
      price_start_date: '',
      price_end_date: '',
      request_by: '',
      request_date: new Date().toISOString().split('T')[0],
      remark: '',
    });
    setItems([]);
  };

  // Fetch customer name from API
  const fetchCustomerName = async (customerCode) => {
    try {
      const res = await api.post(`/api/customer/search?code=${customerCode}`);
      if (res.data && res.data.name) {
        setFormData(prev => ({...prev, customer_name: res.data.name}));
      }
    } catch (err) {
      console.error('Error fetching customer name:', err);
      setFormData(prev => ({...prev, customer_name: ''}));
    }
  };

  // ⭐ Load filter options dynamically based on current filters
  const loadFilterOptions = async () => {
    try {
      const selectedCategories = filterCriteria.categories || [];
      
      if (selectedCategories.length === 0) {
        setFilterOptions({
          categories: CATEGORY_OPTIONS,
          brands: [],
          groups: [],
          subGroups: [],
          colors: [],
          thicknesses: []
        });
        return;
      }

      const categoryMap = {
        'Glass': 'G',
        'Aluminum': 'A',
        'Sealant': 'S',
        'Gypsum': 'Y',
        'C-Line': 'C',
        'Accessories': 'E'
      };

      const allOptions = {
        brands: new Set(),
        groups: new Set(),
        subGroups: new Set(),
        colors: new Set(),
        thicknesses: new Set()
      };

      await Promise.all(
        selectedCategories.map(async (cat) => {
          const categoryCode = categoryMap[cat];
          
          if (!categoryCode) return;

          try {
            const url = categoryCode === 'G' 
              ? '/api/glass/filter-options'
              : `/api/items/categories/${categoryCode}/filter-options`;
            
            // ⭐ Build filter params - pass individual values, not arrays
            const params = {};
            if (filterCriteria.brands?.length > 0) params.brand = filterCriteria.brands[0];
            if (filterCriteria.groups?.length > 0) params.group = filterCriteria.groups[0];
            if (filterCriteria.subGroups?.length > 0) params.subGroup = filterCriteria.subGroups[0];
            if (filterCriteria.colors?.length > 0) params.color = filterCriteria.colors[0];
            if (filterCriteria.thicknesses?.length > 0) params.thickness = filterCriteria.thicknesses[0];
            
            const response = await api.get(url, { params });
            const data = response.data;

            // ⭐ Parse filter options from API response
            // Glass endpoint returns: brands, types, subGroups, colors, thicknesses with {value, label}
            // Items endpoint returns: brand, group, subGroup, color, thickness with {code, name}
            
            if (data.brands) {
              data.brands.forEach(b => {
                allOptions.brands.add(JSON.stringify({
                  value: b.value,
                  label: b.label
                }));
              });
            } else if (data.brand) {
              data.brand.forEach(b => {
                allOptions.brands.add(JSON.stringify({
                  value: b.code,
                  label: b.name
                }));
              });
            }
            
            if (data.types) {
              data.types.forEach(g => {
                allOptions.groups.add(JSON.stringify({
                  value: g.value,
                  label: g.label
                }));
              });
            } else if (data.group) {
              data.group.forEach(g => {
                allOptions.groups.add(JSON.stringify({
                  value: g.code,
                  label: g.name
                }));
              });
            }
            
            if (data.subGroups) {
              data.subGroups.forEach(s => {
                allOptions.subGroups.add(JSON.stringify({
                  value: s.value,
                  label: s.label
                }));
              });
            } else if (data.subGroup) {
              data.subGroup.forEach(s => {
                allOptions.subGroups.add(JSON.stringify({
                  value: s.code,
                  label: s.name
                }));
              });
            }
            
            if (data.colors) {
              data.colors.forEach(c => {
                allOptions.colors.add(JSON.stringify({
                  value: c.value,
                  label: c.label
                }));
              });
            } else if (data.color) {
              data.color.forEach(c => {
                allOptions.colors.add(JSON.stringify({
                  value: c.code,
                  label: c.name
                }));
              });
            }
            
            if (data.thicknesses) {
              data.thicknesses.forEach(t => {
                allOptions.thicknesses.add(JSON.stringify({
                  value: t.value,
                  label: t.label
                }));
              });
            } else if (data.thickness) {
              data.thickness.forEach(t => {
                allOptions.thicknesses.add(JSON.stringify({
                  value: t.code,
                  label: t.name
                }));
              });
            }
          } catch (err) {
            console.error(`Error loading filter options for category ${categoryCode}:`, err);
          }
        })
      );

      const finalOptions = {
        categories: CATEGORY_OPTIONS,
        brands: Array.from(allOptions.brands).map(b => JSON.parse(b)).sort((a, b) => a.label.localeCompare(b.label)),
        groups: Array.from(allOptions.groups).map(g => JSON.parse(g)).sort((a, b) => a.label.localeCompare(b.label)),
        subGroups: Array.from(allOptions.subGroups).map(s => JSON.parse(s)).sort((a, b) => a.label.localeCompare(b.label)),
        colors: Array.from(allOptions.colors).map(c => JSON.parse(c)).sort((a, b) => a.label.localeCompare(b.label)),
        thicknesses: Array.from(allOptions.thicknesses).map(t => JSON.parse(t)).sort((a, b) => a.label.localeCompare(b.label))
      };
      
      setFilterOptions(finalOptions);
    } catch (error) {
      console.error('Error loading filter options:', error);
      setFilterOptions({
        categories: CATEGORY_OPTIONS,
        brands: [],
        groups: [],
        subGroups: [],
        colors: [],
        thicknesses: []
      });
    }
  };

  // ⭐ Load matched SKUs with filters sent to backend
  const loadMatchedSkus = async () => {
    try {
      setLoadingSkus(true);
      
      // ⭐ Build filter params to send to backend
      const filterParams = {
        categories: filterCriteria.categories || [],
        brands: filterCriteria.brands || [],
        groups: filterCriteria.groups || [],
        subGroups: filterCriteria.subGroups || [],
        colors: filterCriteria.colors || [],
        thicknesses: filterCriteria.thicknesses || []
      };
      
      const res = await api.post('/api/promotions/get-skus-by-filter', filterParams);
      const skus = res.data?.skus || [];
      setMatchedSkus(skus);
    } catch (err) {
      console.error('Error loading matched SKUs:', err);
      setMatchedSkus([]);
    } finally {
      setLoadingSkus(false);
    }
  };

  // ⭐ Handle filter toggle (for multi-select filters)
  const handleFilterToggle = (field, value) => {
    setFilterCriteria(prev => {
      const current = prev[field] || [];
      const newValues = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [field]: newValues };
    });
  };

  // ⭐ Handle category toggle
  const handleCategoryToggle = (value) => {
    setFilterCriteria(prev => {
      const current = prev.categories || [];
      const newCategories = current.includes(value)
        ? current.filter(c => c !== value)
        : [...current, value];
      return { ...prev, categories: newCategories };
    });
  };

  // ⭐ Clear all filters
  const clearAllFilters = () => {
    setFilterCriteria({
      categories: [],
      brands: [],
      groups: [],
      subGroups: [],
      colors: [],
      thicknesses: []
    });
    setMatchedSkus([]);
  };

  const addItemsFromFilter = () => {
    if (matchedSkus.length === 0) {
      alert('ไม่พบสินค้าที่ตรงกับเงื่อนไข');
      return;
    }

    // ตรวจสอบว่ากรอกราคาแล้ว
    if (!globalPrice || parseFloat(globalPrice) <= 0) {
      alert('กรุณากรอกราคา');
      return;
    }

    // เพิ่มสินค้าทั้งหมดด้วยราคาและจำนวนเดียวกัน
    // ดึง brand, thickness จาก SKU ที่เลือก, unit ใช้ที่กรอกมา
    const newItems = matchedSkus.map(sku => ({
      sku: sku.sku,
      product_name: sku.description || '',
      brand: sku.brand || '',
      thickness: sku.thickness || '',
      unit: globalUnit || sku.unit || '',
      price: globalPrice,
      quantity: globalQuantity || '',
    }));

    setItems([...items, ...newItems]);
    setShowFilterModal(false);
    
    // Reset filter and global values
    setFilterCriteria({
      categories: [],
      brands: [],
      groups: [],
      subGroups: [],
      colors: [],
      thicknesses: []
    });
    setMatchedSkus([]);
    setGlobalPrice('');
    setGlobalQuantity('');
    setGlobalUnit('');
    setOpenDropdown({});
    
    alert(`เพิ่มสินค้า ${newItems.length} รายการเรียบร้อยแล้ว`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (items.length === 0) {
      alert('กรุณาเพิ่มรายการสินค้าอย่างน้อย 1 รายการ');
      return;
    }

    // Validate วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มใช้ราคา
    if (formData.price_end_date && formData.price_start_date) {
      if (formData.price_end_date <= formData.price_start_date) {
        alert('วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มใช้ราคา');
        return;
      }
    }

    try {
      const payload = {
        ...formData,
        // ✅ เพิ่ม employee code
        created_by_employee_code: employee?.id,
        items: items.map(item => ({
          sku: item.sku,
          product_name: item.product_name,
          brand: item.brand,
          thickness: item.thickness,
          unit: item.unit,
          price: parseFloat(item.price),
          quantity: item.quantity ? parseFloat(item.quantity) : null,
        }))
      };

      if (editingProjectId) {
        // Update existing project
        await api.put(`/api/project-prices/${editingProjectId}`, payload);
        alert('อัพเดทราคาโครงการเรียบร้อยแล้ว');
        setEditingProjectId(null);
      } else {
        // Create new project - เลขที่จะถูกสร้างโดย backend
        const response = await api.post('/api/project-prices/', payload);
        const generatedCode = response.data?.project_code || 'สร้างสำเร็จ';
        alert(`บันทึกราคาโครงการเรียบร้อยแล้ว\nเลขที่ใบคำขอ: ${generatedCode}`);
      }
      
      // Reset form
      setFormData({
        project_code: '',
        project_name: '',
        customer_code: '',
        customer_name: '',
        branch_code: '',
        price_start_date: '',
        price_end_date: '',
        request_by: '',
        request_date: new Date().toISOString().split('T')[0],
        remark: '',
      });
      setItems([]);
      setPriceMode(null);
      setShowForm(false);
      loadProjects();
    } catch (err) {
      console.error('Error saving project:', err);
      const errorMsg = err.response?.data?.detail || 'เกิดข้อผิดพลาดในการบันทึก';
      alert(errorMsg);
    }
  };

  const addItem = () => {
    setItems([...items, {
      sku: '',
      product_name: '',
      brand: '',
      thickness: '',
      unit: '',
      price: '',
      quantity: '',
    }]);
  };

  const removeItem = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const updateItem = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  const deleteProject = async (projectId) => {
    if (!confirm('ต้องการลบราคาโครงการนี้หรือไม่?')) return;
    
    try {
      await api.delete(`/api/project-prices/${projectId}`);
      alert('ลบราคาโครงการเรียบร้อยแล้ว');
      loadProjects();
    } catch (err) {
      console.error('Error deleting project:', err);
      alert('เกิดข้อผิดพลาดในการลบ');
    }
  };

  const updateStatus = async (projectId, status) => {
    try {
      await api.put(`/api/project-prices/${projectId}/status`, null, {
        params: { status }
      });
      loadProjects();
    } catch (err) {
      console.error('Error updating status:', err);
    }
  };

  // Check if project is within date range
  const isProjectActive = (project) => {
    const today = new Date().toISOString().split('T')[0];
    return project.price_start_date <= today && today <= project.price_end_date;
  };

  // Start editing project
  const startEditProject = (project) => {
    setEditingProjectId(project.project_id);
    setFormData({
      project_code: project.project_code,
      project_name: project.project_name || '',
      customer_code: project.customer_code || '',
      customer_name: project.customer_name || '',
      branch_code: project.branch_code || '',
      price_start_date: project.price_start_date || '',
      price_end_date: project.price_end_date || '',
      request_by: project.request_by || '',
      request_date: project.request_date || new Date().toISOString().split('T')[0],
      remark: project.remark || '',
    });
    setItems(project.items || []);
    setShowForm(true);
  };

  // Filter projects by customer search term
  const filteredProjects = projects.filter(project => {
    if (!customerSearchTerm.trim()) return true;
    
    const searchLower = customerSearchTerm.toLowerCase();
    const customerCode = (project.customer_code || '').toLowerCase();
    const customerName = (project.customer_name || '').toLowerCase();
    const projectCode = (project.project_code || '').toLowerCase();
    const projectName = (project.project_name || '').toLowerCase();
    
    return customerCode.includes(searchLower) || 
           customerName.includes(searchLower) ||
           projectCode.includes(searchLower) ||
           projectName.includes(searchLower);
  });

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">ขอราคาพิเศษ</h1>
        <button
          onClick={() => {
            setPriceMode(null);
            setShowForm(!showForm);
          }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" />
          เพิ่มราคาโครงการ
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {showForm && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">เพิ่มราคาโครงการใหม่</h2>
          
          {/* Mode Selection */}
          {!priceMode && !editingProjectId ? (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-medium text-gray-700 mb-3">เลือกประเภทราคาโครงการ:</p>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => handleModeChange('project')}
                  className="p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-100 transition"
                >
                  <div className="font-semibold text-gray-800 hover:text-lg">โครงการ</div>
                  <div className="text-xs text-gray-500 mt-1">ราคาโครงการ</div>
                </button>
                
                <button
                  type="button"
                  onClick={() => handleModeChange('branch')}
                  className="p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-100 transition"
                >
                  <div className="font-semibold text-gray-800 hover:text-lg">สาขา</div>
                  <div className="text-xs text-gray-500 mt-1">ราคาโครงการของสาขา</div>
                </button>
                
                <button
                  type="button"
                  onClick={() => handleModeChange('customer')}
                  className="p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-100 transition"
                >
                  <div className="font-semibold text-gray-800 hover:text-lg">ลูกค้าพิเศษ</div>
                  <div className="text-xs text-gray-500 mt-1">ราคาพิเศษ/ลูกค้า</div>
                </button>
              </div>
            </div>
          ) : (
            <div className="mb-4 flex items-center gap-2">
              {!editingProjectId && (
                <>
                  <button
                    type="button"
                    onClick={() => setPriceMode(null)}
                    className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
                  >
                    ← เปลี่ยนประเภท
                  </button>
                  <span className="text-sm font-medium text-gray-600">
                    {priceMode === 'project' && 'โหมด: โครงการ (PJYYMMXXX)'}
                    {priceMode === 'branch' && 'โหมด: สาขา (BRYYMMXX)'}
                    {priceMode === 'customer' && 'โหมด: ลูกค้าพิเศษ (YYMMCUSTCODE)'}
                  </span>
                </>
              )}
              {editingProjectId && (
                <span className="text-sm font-medium text-blue-600">
                  🔧 กำลังแก้ไขโครงการ
                </span>
              )}
            </div>
          )}
          
          {(priceMode || editingProjectId) && (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Row 1: Project Name for Branch Mode */}
            {(priceMode === 'branch' || (editingProjectId && formData.branch_code)) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ชื่อโครงการ
              </label>
              <input
                type="text"
                value={formData.project_name}
                onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="เช่น โครงการคอนโดXXX"
              />
            </div>
            )}

            {/* Row 1: Project Info (for project mode) */}
            {(priceMode === 'project' || editingProjectId) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ชื่อโครงการ *
              </label>
              <input
                type="text"
                required
                value={formData.project_name}
                onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="เช่น โครงการคอนโดXXX"
              />
            </div>
            )}
            
            {/* Row 2: Customer Info */}
            {(priceMode !== 'customer' || editingProjectId) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  รหัสลูกค้า
                </label>
                <input
                  type="text"
                  value={formData.customer_code}
                  onChange={(e) => {
                    const code = e.target.value.toUpperCase();
                    setFormData({...formData, customer_code: code});
                    
                    // Auto-fetch customer name when code is entered
                    if (code.trim().length > 0) {
                      fetchCustomerName(code.trim());
                    } else {
                      setFormData(prev => ({...prev, customer_name: ''}));
                    }
                  }}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="เช่น 08015AY"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ชื่อลูกค้า
                </label>
                <input
                  type="text"
                  value={formData.customer_name}
                  readOnly
                  className="w-full border rounded-lg px-3 py-2 bg-gray-50 text-gray-700"
                  placeholder="ชื่อลูกค้า (อัตโนมัติ)"
                />
              </div>
            </div>
            )}

            {(priceMode === 'customer' && !editingProjectId) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  รหัสลูกค้า *
                </label>
                <input
                  type="text"
                  required
                  value={formData.customer_code}
                  onChange={(e) => {
                    const code = e.target.value.toUpperCase();
                    setFormData({...formData, customer_code: code});
                    
                    // Auto-fetch customer name when code is entered
                    if (code.trim().length > 0) {
                      fetchCustomerName(code.trim());
                    } else {
                      setFormData(prev => ({...prev, customer_name: ''}));
                    }
                  }}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="เช่น 08015AY"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ชื่อลูกค้า
                </label>
                <input
                  type="text"
                  value={formData.customer_name}
                  readOnly
                  className="w-full border rounded-lg px-3 py-2 bg-gray-50 text-gray-700"
                  placeholder="ชื่อลูกค้า (อัตโนมัติ)"
                />
              </div>
            </div>
            )}

            {/* Row 3: Branch & Dates */}
            <div className="grid grid-cols-4 gap-4">
              {(priceMode === 'branch' || (editingProjectId && formData.branch_code)) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  สาขา *
                </label>
                <select
                  required
                  value={formData.branch_code}
                  onChange={(e) => setFormData({...formData, branch_code: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">เลือกสาขา</option>
                  {Array.isArray(branches) && branches.map(b => (
                    <option key={b.Code} value={b.Code}>{b.Name} ({b.Code})</option>
                  ))}
                </select>
              </div>
              )}
              
              {(priceMode === 'project' || (editingProjectId && !formData.branch_code)) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  สาขา
                </label>
                <select
                  value={formData.branch_code}
                  onChange={(e) => setFormData({...formData, branch_code: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">เลือกสาขา</option>
                  {Array.isArray(branches) && branches.map(b => (
                    <option key={b.Code} value={b.Code}>{b.Name}</option>
                  ))}
                </select>
              </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  วันที่เริ่มใช้ราคา *
                </label>
                <input
                  type="date"
                  required
                  value={formData.price_start_date}
                  onChange={(e) => setFormData({...formData, price_start_date: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  วันที่สิ้นสุด *
                </label>
                <input
                  type="date"
                  required
                  value={formData.price_end_date}
                  onChange={(e) => setFormData({...formData, price_end_date: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  วันที่อนุมัติ
                </label>
                <input
                  type="date"
                  value={formData.request_date}
                  onChange={(e) => setFormData({...formData, request_date: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>

            {/* ⭐ Row 3.5: Project Name for Branch Mode */}
            {(priceMode === 'branch' || (editingProjectId && formData.branch_code)) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ชื่อโครงการ
              </label>
              <input
                type="text"
                value={formData.project_name}
                onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="เช่น โครงการคอนโดXXX"
              />
            </div>
            )}

            {/* Row 4: Request By & Remark */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ผู้ขอ
                </label>
                <input
                  type="text"
                  value={formData.request_by}
                  onChange={(e) => setFormData({...formData, request_by: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="ชื่อผู้ขอ"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  รายการสินค้า
                </label>
                <input
                  type="text"
                  value={formData.remark}
                  onChange={(e) => setFormData({...formData, remark: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="กรอกรายละเอียดรายการสินค้า เช่น กระจกใส AGC 6 มม."
                />
              </div>
            </div>

            {/* Items Section */}
            <div className="border-t pt-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-semibold">รายการสินค้า</h3>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowFilterModal(true)}
                    className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    <Filter className="w-4 h-4" />
                    เลือกตาม Filter
                  </button>
                  <button
                    type="button"
                    onClick={addItem}
                    className="flex items-center gap-1 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4" />
                    เพิ่มทีละรายการ
                  </button>
                </div>
              </div>

              <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
                <div className="space-y-2 p-2">
                  {items.map((item, index) => (
                    <div key={index} className="grid grid-cols-8 gap-2 items-end bg-gray-50 p-2 rounded">
                      <input
                        type="text"
                        placeholder="SKU"
                        value={item.sku}
                        onChange={(e) => updateItem(index, 'sku', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="ชื่อสินค้า"
                        value={item.product_name}
                        onChange={(e) => updateItem(index, 'product_name', e.target.value)}
                        className="border rounded px-2 py-1 text-sm col-span-2"
                      />
                      <input
                        type="text"
                        placeholder="Brand"
                        value={item.brand}
                        onChange={(e) => updateItem(index, 'brand', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="ความหนา"
                        value={item.thickness}
                        onChange={(e) => updateItem(index, 'thickness', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="หน่วย"
                        value={item.unit}
                        onChange={(e) => updateItem(index, 'unit', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="ราคา"
                        value={item.price}
                        onChange={(e) => updateItem(index, 'price', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="จำนวน"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-2 justify-end pt-4 border-t">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setPriceMode(null);
                  setEditingProjectId(null);
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                ยกเลิก
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                {editingProjectId ? 'อัพเดท' : 'บันทึก'}
              </button>
            </div>
          </form>
          )}
        </div>
      )}

      {/* Filter Modal */}
      {showFilterModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col">
            {/* Header - Fixed */}
            <div className="p-6 border-b flex-shrink-0">
              <h2 className="text-xl font-bold">เลือกสินค้าตาม Filter</h2>
            </div>

            {/* Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6">
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

              {/* MultiSelect Dropdowns - Show only if category selected */}
              {filterCriteria.categories?.length > 0 && (
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

              {/* Matched SKUs Display with Global Price Input */}
              {!loadingSkus && matchedSkus.length > 0 && (
                <div className="space-y-3">
                  {/* SKU List - Compact with Scroll */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-green-800 font-semibold mb-2 text-sm">
                      ✅ พบ {matchedSkus.length} SKU ที่ตรงกับเงื่อนไข
                    </p>
                    <div className="max-h-32 overflow-y-auto space-y-1 bg-white rounded p-2">
                      {matchedSkus.map((item, idx) => (
                        <p key={idx} className="text-xs text-gray-700">
                          • {item.sku} - {item.description}
                        </p>
                      ))}
                    </div>
                  </div>

                  {/* Global Price and Quantity Input - Compact */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-blue-800 font-semibold mb-2 text-sm">
                      📝 กรอกราคา หน่วย และจำนวน
                    </p>
                    
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          ราคา *
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="0.00"
                          value={globalPrice}
                          onChange={(e) => setGlobalPrice(e.target.value)}
                          className="w-full border rounded-lg px-3 py-2 font-semibold border-red-300 focus:border-red-500 focus:ring-red-500"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          หน่วย *
                        </label>
                        <input
                          type="text"
                          placeholder="เช่น ตารางฟุต"
                          value={globalUnit}
                          onChange={(e) => setGlobalUnit(e.target.value)}
                          className="w-full border rounded-lg px-3 py-2 border-red-300 focus:border-red-500 focus:ring-red-500"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          จำนวน
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="0"
                          value={globalQuantity}
                          onChange={(e) => setGlobalQuantity(e.target.value)}
                          className="w-full border rounded-lg px-3 py-2"
                        />
                      </div>
                    </div>

                    <p className="text-xs text-gray-500 mt-2">
                      💡 ใช้กับสินค้าทั้งหมด {matchedSkus.length} รายการ (Brand, ความหนา ดึงจาก SKU)
                    </p>
                  </div>
                </div>
              )}

              {/* No Results */}
              {!loadingSkus && matchedSkus.length === 0 && filterCriteria.categories.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-yellow-800 text-sm">
                    ⚠️ ไม่พบ SKU ที่ตรงกับเงื่อนไข
                  </p>
                </div>
              )}
            </div>
            </div>

            {/* Footer - Fixed */}
            <div className="flex gap-2 justify-between p-4 border-t flex-shrink-0 bg-gray-50">
              <button
                type="button"
                onClick={clearAllFilters}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100 text-sm font-medium"
              >
                ล้างทั้งหมด
              </button>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowFilterModal(false);
                    clearAllFilters();
                  }}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  ยกเลิก
                </button>
                <button
                  type="button"
                  onClick={addItemsFromFilter}
                  disabled={matchedSkus.length === 0 || !globalPrice || parseFloat(globalPrice) <= 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  เพิ่มสินค้า {matchedSkus.length > 0 && `(${matchedSkus.length} รายการ)`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Projects List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">รายการราคาโครงการ</h2>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-gray-500">กำลังโหลด...</div>
        ) : filteredProjects.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {customerSearchTerm ? 'ไม่พบโครงการที่ตรงกับคำค้นหา' : 'ยังไม่มีข้อมูลราคาโครงการ'}
          </div>
        ) : (
          <div className="divide-y max-h-[600px] overflow-y-auto">
            {filteredProjects.map((project) => (
              <div key={project.project_id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold text-lg">{project.project_code}</h3>
                    {project.project_name && (
                      <p className="text-gray-600">{project.project_name}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {isProjectActive(project) && (
                      <button
                        onClick={() => startEditProject(project)}
                        className="text-blue-600 hover:text-blue-800 px-2 py-1 border rounded-md font-bold"
                      >
                        แก้ไข
                      </button>
                    )}
                    <select
                      value={project.status}
                      onChange={(e) => updateStatus(project.project_id, e.target.value)}
                      className={`px-2 py-1 rounded text-sm font-medium ${
                        project.status === 'active' ? 'bg-white text-green-800' :
                        project.status === 'expired' ? 'bg-gray-100 text-gray-800' :
                        'bg-red-100 text-red-800'
                      }`}
                    >
                      <option value="active">Active</option>
                      <option value="expired">Expired</option>
                      <option value="cancel">Cancel</option>
                    </select>
                    <button
                      onClick={() => deleteProject(project.project_id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    <span className="truncate">{project.customer_name || project.customer_code || '-'}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Building2 className="w-4 h-4" />
                    <span className="truncate">สาขา: {project.branch_code || '-'}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span className="truncate">{project.price_start_date} - {project.price_end_date}</span>
                  </div>
                  <div className="truncate">
                    <span>ผู้ขอ: {project.request_by || '-'}</span>
                  </div>
                </div>

                {/* ⭐ แสดง Remark */}
                {project.remark && (
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-2 mb-3 rounded">
                    <p className="text-xs font-semibold text-blue-800 mb-1">รายการสินค้าที่ขอราคาพิเศษ:</p>
                    <p className="text-sm text-blue-700">{project.remark}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// MultiSelectDropdown Component
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
          {selectedValues.slice(0, 5).map((value) => {
            const label = options.find(opt => opt.value === value)?.label || value;
            return (
              <span
                key={value}
                className="bg-red-50 text-red-700 text-xs px-2 py-1 rounded-full"
              >
                {label}
              </span>
            );
          })}
          {selectedValues.length > 5 && (
            <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
              +{selectedValues.length - 5} อื่นๆ
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

export default ProjectPriceManagement;
