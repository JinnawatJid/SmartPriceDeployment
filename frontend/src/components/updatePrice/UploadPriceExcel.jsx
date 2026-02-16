import React, { useState, useEffect } from "react";
import api from "../../services/api";

export default function UploadPriceExcel({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState("");
  const [loadingBranches, setLoadingBranches] = useState(true);

  // Fetch branches on component mount
  useEffect(() => {
    const fetchBranches = async () => {
      try {
        console.log("Fetching branches from /api/branches");
        const res = await api.get("/api/branches");
        console.log("Branches response:", res.data);
        
        setBranches(res.data.branches || []);
        
        // Auto-select first branch if available
        if (res.data.branches && res.data.branches.length > 0) {
          setSelectedBranch(res.data.branches[0].Code);
        }
      } catch (error) {
        console.error("Failed to fetch branches:", error);
        console.error("Error response:", error.response?.data);
      } finally {
        setLoadingBranches(false);
      }
    };

    fetchBranches();
  }, []);

  const handleUpload = async () => {
    if (!file || !selectedBranch) return;

    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);

      // Send branch_code as query parameter
      const res = await api.post(`/api/admin/prices/upload?branch_code=${selectedBranch}`, form);
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
      <div className="flex flex-col gap-4">
        {/* Branch Selection */}
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-gray-700">
            เลือกสาขา <span className="text-red-500">*</span>
          </label>
          <select
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            disabled={loadingBranches}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {loadingBranches ? (
              <option>กำลังโหลดสาขา...</option>
            ) : branches.length === 0 ? (
              <option>ไม่พบข้อมูลสาขา</option>
            ) : (
              <>
                <option value="">-- เลือกสาขา --</option>
                {branches.map((branch) => (
                  <option key={branch.Code} value={branch.Code}>
                    {branch.Code} - {branch.Name}
                  </option>
                ))}
              </>
            )}
          </select>
        </div>

        {/* File Upload Section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-6">
          {/* File Picker */}
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={(e) => setFile(e.target.files[0])}
            />

            <span className="px-4 py-2 rounded-lg border border-gray-300 bg-gray-50 hover:bg-gray-100 text-sm font-medium text-gray-700">
              เลือกไฟล์ Excel
            </span>
          </label>

          {/* Selected file + clear */}
          {file && (
            <div className="items-center gap-2 bg-gray-100 px-3 py-2 rounded-lg">
              <span className="text-sm text-gray-700 truncate max-w-xs">{file.name}</span>

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
            disabled={!file || !selectedBranch || loading}
            className={`
              px-6 py-2 rounded-lg text-sm font-semibold text-white
              transition-all
              ${
                loading || !file || !selectedBranch
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 active:scale-95"
              }
            `}
          >
            {loading ? "กำลังอัปโหลด..." : "อัปโหลดไฟล์"}
          </button>
        </div>

        {/* Hint */}
        <div className="mt-1 text-xs text-gray-400">
          รองรับเฉพาะไฟล์ .xlsx • กรุณาเลือกสาขาก่อนอัปโหลด
        </div>
      </div>
    </div>
  );
}
