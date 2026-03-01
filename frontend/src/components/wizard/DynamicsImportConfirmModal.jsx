import React from 'react';

const DynamicsImportConfirmModal = ({ open, onCancel, onConfirm }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
            <svg
              className="w-6 h-6 text-yellow-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 mb-1">
              ยืนยันการนำเข้าสู่ Dynamics 365
            </h3>
          </div>
        </div>

        {/* Warning Alert */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-yellow-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-semibold text-yellow-800 mb-1">
                โปรดตรวจสอบก่อนดำเนินการ!
              </p>
              <p className="text-sm text-yellow-700">
                กรุณาตรวจสอบให้แน่ใจว่าคุณอยู่ในหน้า <span className="font-semibold">Sales Quotes</span> ใน Dynamics 365 Business Central
              </p>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mb-4 pl-2">
          <p className="text-sm text-gray-600 mb-2 font-medium">
            ขั้นตอนการตรวจสอบ:
          </p>
          <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
            <li>เปิด Dynamics 365 Business Central</li>
            <li>ไปที่เมนู <span className="font-semibold">Sales → Sales Quotes</span></li>
            <li>ตรวจสอบว่าหน้าจอแสดงรายการใบเสนอราคา</li>
            <li>กดปุ่ม "ตกลง" เพื่อเริ่มกระบวนการ RPA</li>
          </ol>
        </div>

        <p className="text-xs text-gray-500 italic mb-6">
          หากคุณยังไม่ได้เปิดหน้า Sales Quotes กรุณากด "ยกเลิก" เพื่อไปตรวจสอบก่อน
        </p>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            ยกเลิก (ไปตรวจสอบ)
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-3 bg-blue-600 rounded-lg font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            ตกลง (เริ่ม RPA)
          </button>
        </div>
      </div>
    </div>
  );
};

export default DynamicsImportConfirmModal;
