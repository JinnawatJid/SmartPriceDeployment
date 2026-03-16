import React, { useState, useEffect } from 'react';
import { X, AlertCircle, User, Building2 } from 'lucide-react';
import api from '../../services/api';

export default function SpecialPriceRequestModal({ open, onClose, onConfirm, itemsBelowR1 }) {
  const [reason, setReason] = useState('');
  const [validFrom, setValidFrom] = useState('');
  const [validTo, setValidTo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [approverInfo, setApproverInfo] = useState(null);
  const [loadingApprover, setLoadingApprover] = useState(false);

  // Load approver information when modal opens
  useEffect(() => {
    if (open) {
      loadApproverInfo();
      // ตั้งค่าวันที่เริ่มต้นเป็นวันนี้
      const today = new Date().toISOString().split('T')[0];
      setValidFrom(today);
      // ตั้งค่าวันที่สิ้นสุดเป็น 30 วันจากวันนี้
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 30);
      setValidTo(futureDate.toISOString().split('T')[0]);
    }
  }, [open]);

  const loadApproverInfo = async () => {
    try {
      setLoadingApprover(true);
      const res = await api.get('/api/special-price-requests/approver-info');
      setApproverInfo(res.data);
    } catch (err) {
      console.error('Error loading approver info:', err);
    } finally {
      setLoadingApprover(false);
    }
  };

  if (!open) return null;

  // Filter out rejected items - only show approvable items
  const approvableItems = itemsBelowR1.filter(item => item.approval_level !== 'REJECTED');
  const rejectedItems = itemsBelowR1.filter(item => item.approval_level === 'REJECTED');
  
  // Separate items by approval level
  const zmOnlyItems = approvableItems.filter(item => item.approval_level === 'ZM_ONLY');
  const zmThenRmItems = approvableItems.filter(item => item.approval_level === 'ZM_THEN_RM');

  const handleSubmit = async () => {
    if (!reason.trim()) {
      alert('กรุณาระบุเหตุผลในการขอราคาพิเศษ');
      return;
    }

    if (!validFrom || !validTo) {
      alert('กรุณาระบุวันที่เริ่มต้นและวันที่สิ้นสุดของราคาพิเศษ');
      return;
    }

    if (new Date(validFrom) > new Date(validTo)) {
      alert('วันที่เริ่มต้นต้องไม่เกินวันที่สิ้นสุด');
      return;
    }

    if (rejectedItems.length > 0) {
      alert('พบสินค้าที่ราคานอกช่วงที่อนุมัติได้ กรุณาแก้ไขราคาก่อนส่งขออนุมัติ');
      return;
    }

    setSubmitting(true);
    try {
      await onConfirm(reason, validFrom, validTo);
      setReason('');
      setValidFrom('');
      setValidTo('');
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB'
    }).format(value);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">ขอราคาพิเศษ</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-yellow-800">
                พบสินค้าที่ต้องขออนุมัติราคาพิเศษ
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                ใบเสนอราคานี้ต้องได้รับการอนุมัติก่อนจึงจะสามารถยืนยันได้
              </p>
            </div>
          </div>

          {/* Show rejected items warning if any */}
          {rejectedItems.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-800">
                  พบสินค้า {rejectedItems.length} รายการที่ราคานอกช่วงที่อนุมัติได้
                </p>
                <p className="text-sm text-red-700 mt-1">
                  กรุณาแก้ไขราคาให้อยู่ในช่วง R1 ถึง W1 ก่อนส่งขออนุมัติ
                </p>
              </div>
            </div>
          )}

          {/* Approver Information */}
          {loadingApprover ? (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">กำลังโหลดข้อมูลผู้อนุมัติ...</p>
            </div>
          ) : approverInfo ? (
            <div className="space-y-3">
              {/* Zone Manager Info (for all approvable items) */}
              {zmOnlyItems.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <User className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-semibold text-blue-900">
                        ผู้อนุมัติ: Zone Manager
                      </p>
                      <div className="mt-2 space-y-1 text-sm">
                        <div className="flex items-center gap-2">
                          <span className="text-blue-700 font-medium">รหัสพนักงาน:</span>
                          <span className="text-blue-900 font-mono bg-blue-100 px-2 py-0.5 rounded">
                            {approverInfo.zone_manager.employee_id}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-blue-600" />
                          <span className="text-blue-700">สาขา: {approverInfo.zone_manager.branch}</span>
                        </div>
                      </div>
                      <p className="text-xs text-blue-600 mt-2">
                        จำนวน {zmOnlyItems.length} รายการ (อนุมัติโดย ZM เท่านั้น)
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Regional Manager Info (for multi-level items) */}
              {zmThenRmItems.length > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <User className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-semibold text-orange-900">
                        ผู้อนุมัติ: Zone Manager → Regional Manager
                      </p>
                      <div className="mt-2 space-y-2">
                        {/* ZM Info */}
                        <div className="bg-orange-100 rounded p-2">
                          <p className="text-xs font-semibold text-orange-800 mb-1">1. Zone Manager</p>
                          <div className="space-y-1 text-sm">
                            <div className="flex items-center gap-2">
                              <span className="text-orange-700 font-medium">รหัส:</span>
                              <span className="text-orange-900 font-mono bg-white px-2 py-0.5 rounded text-xs">
                                {approverInfo.zone_manager.employee_id}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Building2 className="w-3 h-3 text-orange-600" />
                              <span className="text-orange-700 text-xs">สาขา: {approverInfo.zone_manager.branch}</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* RM Info */}
                        {approverInfo.regional_manager && (
                          <div className="bg-orange-100 rounded p-2">
                            <p className="text-xs font-semibold text-orange-800 mb-1">2. Regional Manager</p>
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center gap-2">
                                <span className="text-orange-700 font-medium">รหัส:</span>
                                <span className="text-orange-900 font-mono bg-white px-2 py-0.5 rounded text-xs">
                                  {approverInfo.regional_manager.employee_id}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Building2 className="w-3 h-3 text-orange-600" />
                                <span className="text-orange-700 text-xs">ภูมิภาค: {approverInfo.regional_manager.region}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      <p className="text-xs text-orange-600 mt-2">
                        จำนวน {zmThenRmItems.length} รายการ (ต้องอนุมัติ 2 ระดับ)
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {/* Items that can be approved */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">
              รายการสินค้าที่ต้องขออนุมัติ ({approvableItems.length} รายการ)
            </h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {approvableItems.map((item, idx) => {
                // Determine approval level display
                let approvalLevelText = '';
                let approvalLevelColor = '';
                
                if (item.approval_level === 'REJECTED') {
                  approvalLevelText = 'ไม่สามารถขออนุมัติได้ (ราคานอกช่วง)';
                  approvalLevelColor = 'text-red-600';
                } else if (item.approval_level === 'ZM_ONLY') {
                  approvalLevelText = 'ต้องอนุมัติจาก Zone Manager';
                  approvalLevelColor = 'text-blue-600';
                } else if (item.approval_level === 'ZM_THEN_RM') {
                  approvalLevelText = 'ต้องอนุมัติจาก Zone Manager และ Regional Manager';
                  approvalLevelColor = 'text-orange-600';
                }
                
                return (
                  <div key={idx} className="bg-gray-50 p-3 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{item.name}</p>
                        <p className="text-sm text-gray-600">SKU: {item.sku}</p>
                        <p className="text-sm text-gray-600">
                          จำนวน: {item.qty} {item.unit}
                        </p>
                        <p className={`text-sm font-semibold mt-1 ${approvalLevelColor}`}>
                          {approvalLevelText}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">ราคาขั้นต่ำ (R1)</p>
                        <p className="font-semibold text-gray-900">
                          {formatCurrency(item.r1_price)}
                        </p>
                        <p className="text-sm text-red-600 mt-1">ราคาที่ขอ</p>
                        <p className="font-semibold text-red-600">
                          {formatCurrency(item.requested_price)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                วันที่เริ่มต้น <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={validFrom}
                onChange={(e) => setValidFrom(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={submitting}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                วันที่สิ้นสุด <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={validTo}
                onChange={(e) => setValidTo(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={submitting}
              />
            </div>
          </div>

          {/* Reason */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              เหตุผลในการขอราคาพิเศษ <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="กรุณาระบุเหตุผล เช่น ลูกค้าประจำ, โครงการขนาดใหญ่, แข่งขันกับคู่แข่ง..."
              className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px]"
              disabled={submitting}
            />
          </div>

          {/* Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>หมายเหตุ:</strong> เมื่อส่งใบขอราคาพิเศษแล้ว
            </p>
            <ul className="text-sm text-blue-700 mt-2 ml-4 list-disc space-y-1">
              <li>ใบเสนอราคาจะถูกบันทึกเป็น Draft</li>
              <li>คำขอจะถูกส่งไปยังผู้อนุมัติตามลำดับ</li>
              <li>ไม่สามารถยืนยันใบเสนอราคาได้จนกว่าจะได้รับการอนุมัติ</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            disabled={submitting}
            className="flex-1 px-6 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-100 disabled:opacity-50 transition-colors"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !reason.trim() || !validFrom || !validTo || rejectedItems.length > 0}
            className="flex-1 px-6 py-3 bg-blue-600 rounded-lg font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? 'กำลังส่ง...' : 
             rejectedItems.length > 0 ? 'ไม่สามารถส่งได้ (มีสินค้านอกช่วง)' : 
             'ส่งใบขอราคาพิเศษ'}
          </button>
        </div>
      </div>
    </div>
  );
}
