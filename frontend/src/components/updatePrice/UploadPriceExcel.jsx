import React, { useState } from "react";
import api from "../../services/api";

export default function UploadPriceExcel({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);

      const res = await api.post("/api/item-update/upload", form);
      onUploaded(res.data);
    } finally {
      setLoading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
  };

  return (
    <div className="mt-4 p-6 border rounded-xl bg-white shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-6">

        {/* File Picker */}
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={e => setFile(e.target.files[0])}
          />

          <span className="px-4 py-2 rounded-lg border border-gray-300 bg-gray-50 hover:bg-gray-100 text-sm font-medium text-gray-700">
            เลือกไฟล์ Excel
          </span>
        </label>

        {/* Selected file + clear */}
        {file && (
          <div className="items-center gap-2 bg-gray-100 px-3 py-2 rounded-lg">
            <span className="text-sm text-gray-700 truncate max-w-xs">
              {file.name}
            </span>

            {/* ❌ Clear file */}
            <button
              onClick={clearFile}
              className="text-gray-400 hover:text-red-500 font-bold"
              title="เปลี่ยนไฟล์"
            >
              ✕
            </button>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className={`
            px-6 py-2 rounded-lg text-sm font-semibold text-white
            transition-all
            ${loading || !file
              ? "bg-gray-300 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 active:scale-95"}
          `}
        >
          {loading ? "กำลังอัปโหลด..." : "อัปโหลดไฟล์"}
        </button>
      </div>

      {/* Hint */}
      <div className="mt-3 text-xs text-gray-400">
        รองรับเฉพาะไฟล์ .xlsx 
      </div>
    </div>
  );
}
