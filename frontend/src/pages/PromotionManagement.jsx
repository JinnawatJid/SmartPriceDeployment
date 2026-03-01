import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Power, PowerOff, Megaphone } from 'lucide-react';
import api from '../services/api';

const PromotionManagement = ({ standalone = false }) => {
  const [promotions, setPromotions] = useState([]);
  const [branches, setBranches] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    promotion_name: '',
    branches: ['ALL'], // เปลี่ยนเป็น array
    start_date: '',
    end_date: '',
    items: []
  });
  const [newItem, setNewItem] = useState({ sku: '', promotion_text: '' });

  useEffect(() => {
    loadPromotions();
    loadBranches();
  }, []);

  const loadPromotions = async () => {
    try {
      const response = await api.get('/api/promotions/');
      setPromotions(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error loading promotions:', error);
      setPromotions([]);
    }
  };

  const loadBranches = async () => {
    try {
      console.log('🔍 Loading branches...');
      const response = await api.get('/api/branches');
      console.log('📦 Branches response:', response.data);
      const branchList = response.data?.branches || [];
      console.log('✅ Branch list:', branchList);
      setBranches(branchList);
    } catch (error) {
      console.error('❌ Error loading branches:', error);
      setBranches([]);
    }
  };

  const handleBranchToggle = (branchCode) => {
    setFormData(prev => {
      let newBranches = [...prev.branches];
      
      if (branchCode === 'ALL') {
        // ถ้าเลือก ALL ให้เคลียร์ทั้งหมดและเลือกแค่ ALL
        newBranches = ['ALL'];
      } else {
        // ถ้าเลือกสาขาอื่น ให้ลบ ALL ออกก่อน
        newBranches = newBranches.filter(b => b !== 'ALL');
        
        if (newBranches.includes(branchCode)) {
          // ถ้ามีอยู่แล้ว ให้ลบออก
          newBranches = newBranches.filter(b => b !== branchCode);
        } else {
          // ถ้ายังไม่มี ให้เพิ่มเข้าไป
          newBranches.push(branchCode);
        }
        
        // ถ้าไม่มีสาขาใดเลย ให้กลับไปเป็น ALL
        if (newBranches.length === 0) {
          newBranches = ['ALL'];
        }
      }
      
      return { ...prev, branches: newBranches };
    });
  };

  const handleAddItem = () => {
    if (newItem.sku && newItem.promotion_text) {
      setFormData({
        ...formData,
        items: [...formData.items, { ...newItem }]
      });
      setNewItem({ sku: '', promotion_text: '' });
    }
  };

  const handleRemoveItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.post('/api/promotions/', formData);
      alert('สร้าง Promotion สำเร็จ!');
      setShowModal(false);
      setFormData({
        promotion_name: '',
        branches: ['ALL'],
        start_date: '',
        end_date: '',
        items: []
      });
      loadPromotions();
    } catch (error) {
      console.error('Error creating promotion:', error);
      alert('เกิดข้อผิดพลาด: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (promotionId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    try {
      await api.put(`/api/promotions/${promotionId}/status?status=${newStatus}`);
      loadPromotions();
    } catch (error) {
      console.error('Error updating status:', error);
      alert('เกิดข้อผิดพลาดในการอัพเดทสถานะ');
    }
  };

  const deletePromotion = async (promotionId) => {
    if (!confirm('คุณต้องการลบ Promotion นี้หรือไม่?')) return;

    try {
      await api.delete(`/api/promotions/${promotionId}`);
      loadPromotions();
    } catch (error) {
      console.error('Error deleting promotion:', error);
      alert('เกิดข้อผิดพลาดในการลบ');
    }
  };

  return (
    <div className={standalone ? "p-6 max-w-7xl mx-auto" : ""}>
      {standalone && (
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <Megaphone className="w-8 h-8 text-red-600" />
            <h1 className="text-3xl font-bold text-gray-800">จัดการโปรโมชั่น</h1>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            เพิ่มโปรโมชั่น
          </button>
        </div>
      )}

      {!standalone && (
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setShowModal(true)}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            เพิ่มโปรโมชั่น
          </button>
        </div>
      )}

      <div className="grid gap-4">
        {!promotions || promotions.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
            ยังไม่มีโปรโมชั่น คลิก "เพิ่มโปรโมชั่น" เพื่อสร้างโปรโมชั่นใหม่
          </div>
        ) : (
          promotions.map((promo) => (
            <div key={promo.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-800">{promo.promotion_name}</h3>
                <p className="text-sm text-gray-600">
                  สาขา: {promo.branch === 'ALL' || promo.branch.includes('ALL') ? 'ทุกสาขา' : promo.branch} | {promo.start_date} - {promo.end_date}
                </p>
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm ${
                  promo.status === 'active' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {promo.status === 'active' ? 'ใช้งาน' : 'ปิดใช้งาน'}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => toggleStatus(promo.id, promo.status)}
                  className={`p-2 rounded-lg ${
                    promo.status === 'active'
                      ? 'bg-yellow-100 hover:bg-yellow-200 text-yellow-700'
                      : 'bg-green-100 hover:bg-green-200 text-green-700'
                  }`}
                  title={promo.status === 'active' ? 'ปิดใช้งาน' : 'เปิดใช้งาน'}
                >
                  {promo.status === 'active' ? <PowerOff className="w-5 h-5" /> : <Power className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => deletePromotion(promo.id)}
                  className="p-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg"
                  title="ลบ"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-semibold text-gray-700">สินค้าในโปรโมชั่น:</h4>
              {promo.items.map((item, idx) => (
                <div key={idx} className="bg-gray-50 p-3 rounded-lg">
                  <p className="font-medium text-gray-800">SKU: {item.SKU || item.sku}</p>
                  <p className="text-gray-600 text-sm">{item.PromotionText || item.promotion_text}</p>
                </div>
              ))}
            </div>
          </div>
        ))
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4">เพิ่มโปรโมชั่นใหม่</h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">ชื่อโปรโมชั่น</label>
                  <input
                    type="text"
                    value={formData.promotion_name}
                    onChange={(e) => setFormData({ ...formData, promotion_name: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">สาขา (เลือกได้หลายสาขา)</label>
                  <div className="border rounded-lg p-3 max-h-48 overflow-y-auto">
                    <label className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.branches.includes('ALL')}
                        onChange={() => handleBranchToggle('ALL')}
                        className="w-4 h-4"
                      />
                      <span className="font-medium">ทุกสาขา</span>
                    </label>
                    <div className="border-t my-2"></div>
                    {branches.map((branch) => (
                      <label key={branch.Code} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.branches.includes(branch.Code)}
                          onChange={() => handleBranchToggle(branch.Code)}
                          className="w-4 h-4"
                        />
                        <span>{branch.Name} ({branch.Code})</span>
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    เลือกแล้ว: {formData.branches.includes('ALL') ? 'ทุกสาขา' : `${formData.branches.length} สาขา`}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">วันที่เริ่มต้น</label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">วันที่สิ้นสุด</label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2"
                      required
                    />
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-3">เพิ่มสินค้า</h3>
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      placeholder="SKU สินค้า"
                      value={newItem.sku}
                      onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })}
                      className="flex-1 border rounded-lg px-3 py-2"
                    />
                    <input
                      type="text"
                      placeholder="รายละเอียดโปรโมชั่น"
                      value={newItem.promotion_text}
                      onChange={(e) => setNewItem({ ...newItem, promotion_text: e.target.value })}
                      className="flex-1 border rounded-lg px-3 py-2"
                    />
                    <button
                      type="button"
                      onClick={handleAddItem}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                    >
                      <Plus className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    {formData.items.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-gray-50 p-3 rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium">{item.sku}</p>
                          <p className="text-sm text-gray-600">{item.promotion_text}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 justify-end pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                  >
                    ยกเลิก
                  </button>
                  <button
                    type="submit"
                    disabled={loading || formData.items.length === 0}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                  >
                    {loading ? 'กำลังบันทึก...' : 'บันทึก'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PromotionManagement;
