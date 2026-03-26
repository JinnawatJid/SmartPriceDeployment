// src/components/wizard/TaxDeliverySection.jsx
import React from "react";
import SelectionButton from "./SelectionButton.jsx";
import ShippingModal from "../../components/wizard/ShippingModal.jsx";
import { useState } from "react";
// ไอคอน
const CheckIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
  </svg>
);
const XIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
  </svg>
);
const TruckIcon = () => (
  <img src="/assets/fast-delivery.png" alt="Truck Icon" className="w-8 h-8 object-contain" />
);
const BoxIcon = () => (
  <img src="/assets/pickup.png" alt="Box Icon" className="w-10 h-10 object-contain" />
);

function TaxDeliverySection({ needsTax, deliveryType, onChange, onOpenShipping, billTaxName, ibtBranch, branches = [] }) {
  const update = (change) => {
    if (onChange) onChange(change);
  };
  
  return (
    <div className="flex flex-col gap-4 rounded-lg bg-gray-50 py-4 px-8">
      <div className="flex justify-between gap-16 md:grid-cols-3">
        {/* ใบกำกับภาษี */}
        <div className="flex flex-col rounded-lg h-full">
          <h3 className="text-lg font-bold text-gray-800">ใบกำกับภาษี</h3>
          <p className="mt-1 text-gray-500">กรุณาเลือกรูปแบบใบกำกับภาษี</p>
          <div className="flex mt-2 ">
            <SelectionButton
              title="ต้องการใบกำกับภาษี"
              selected={needsTax === true}
              onClick={() => update({ needsTax: true })}
            />
            <SelectionButton
              title="ไม่ต้องการ"
              selected={needsTax === false}
              onClick={() => update({ needsTax: false })}
            />
          </div>
        </div>

        {/* ช่องทางการรับสินค้า */}
        <div className="flex flex-col col-span-2 rounded-lg h-full">
          <h3 className="text-lg font-bold text-gray-800">ช่องทางการรับสินค้า</h3>
          <p className="mt-1 text-gray-500">กรุณาเลือกช่องทางการรับสินค้าที่ต้องการ</p>
          <div className="flex mt-2 gap-2">
            <SelectionButton
              icon={<TruckIcon />}
              title="จัดส่ง"
              selected={deliveryType === "DELIVERY"}
              onClick={() => update({ deliveryType: "DELIVERY" })}
            />
            <SelectionButton
              icon={<BoxIcon />}
              title="รับเอง"
              selected={deliveryType === "PICKUP"}
              onClick={() => update({ deliveryType: "PICKUP" })}
            />
          </div>

          {deliveryType === "DELIVERY" && (
            <div className="mt-3">
              <button
                onClick={() => onOpenShipping && onOpenShipping()}
                className="w-ful mt-2 rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white shadow-sm hover:bg-blue-700"
              >
                คำนวณค่าขนส่ง
              </button>
            </div>
          )}

          {/* Dropdown เลือกสาขา (ส่งระหว่างสาขา) */}
          <div className="mt-2 w-48">
              <p className="text-sm font-semibold text-gray-700">ส่งระหว่างสาขา (IBT)</p>
            <select
              value={ibtBranch || ""}
              onChange={(e) => {
                if (e.target.value) {
                  update({ deliveryType: "IBT", ibtBranch: e.target.value });
                } else {
                  update({ ibtBranch: null });
                }
              }}
              className="w-full mt-1 rounded-lg border border-gray-300 bg-white px-3 py-1 text-sm text-gray-800 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">ไม่เลือก</option>
              {branches.map((branch) => (
                <option key={branch.Code} value={branch.Code}>
                   {branch.Code}-{branch.Name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TaxDeliverySection;
