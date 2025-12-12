// src/pages/Dashboard.jsx (REFACTORED for Navbar component)
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';
import { useQuote } from '../hooks/useQuote.js';
import Navbar from '../components/Navbar'; 
import GlassSemiSizeModal from "../components/wizard/GlassSemiSizeModal.jsx";
import api from "../services/api";


// --- คอมโพเนนต์หลัก ---
function Dashboard() {
  const { employee } = useAuth(); 
  const { dispatch } = useQuote();
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState('');

  // โหลดวันที่ปัจจุบัน (ภาษาไทย)
  useEffect(() => {
    const date = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', timeZone: 'Asia/Bangkok' };
    const thaiDate = date.toLocaleDateString('th-TH', options);
    // เพิ่ม "พ.ศ."
    const year = date.toLocaleDateString('th-TH', { year: 'numeric', timeZone: 'Asia/Bangkok' }).split(' ')[0];
    setCurrentDate(thaiDate.replace(year, ` พ.ศ. ${year}`));
  }, []);

  const handleCreateQuote = () => {
    dispatch({ type: 'RESET_QUOTE' });
    navigate('/create');
  };

  const handlePendingQuotes = () => {
    navigate("/quote-drafts");
  };

  const handleTodayQuotes = () => {
  navigate("/confirmed-quotes");
  };

  const [isSemiModalOpen, setIsSemiModalOpen] = useState(false);

  const handleSemiSize = () => {
  dispatch({ type: 'RESET_SemiSize' });
  setIsSemiModalOpen(true);     
  }
  
  const [todayCount, setTodayCount] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const [contactCustomerCount, setContactCustomerCount] = useState(0);

  useEffect(() => {
  async function loadDashboardData() {
    try {
      // โหลดใบเสนอราคาทั้งหมด
      const resComplete = await api.get("/api/quotation", {
        params: { status: "complete" },
      });
      const completeList = resComplete.data || [];

      const resDraft = await api.get("/api/quotation", {
        params: { status: "open" },
      });
      const draftList = resDraft.data || [];

      // ---- 1) ใบเสนอราคาวันนี้ ----
      const today = new Date().toISOString().split("T")[0];
      const todayCountValue = completeList.filter(q =>
        (q.updatedAt || "").startsWith(today)
      ).length;
      setTodayCount(todayCountValue);

      // ---- 2) รอดำเนินการ ----
      setPendingCount(draftList.length);

      // ---- 3) ลูกค้าที่ติดต่อวันนี้ ----
      const uniqueCustomers = new Set(
        completeList
          .filter(q => (q.updatedAt || "").startsWith(today))
          .map(q => q.customer?.id)
      );
      setContactCustomerCount(uniqueCustomers.size);

    } catch (err) {
      console.error("Dashboard load error:", err);
    }
  }

  loadDashboardData();
}, []);



  return (
    <div className="min-h-screen w-full bg-[#F5F5F5]">
      {/* ===== 2. Main Content (เนื้อหาหลัก) ===== */}
      <main className="mx-auto max-w-7xl p-6 lg:p-10">

        {/* --- 2.1 Welcome Banner (ป้ายต้อนรับสีน้ำเงิน) --- */}
        <div className="flex flex-col md:flex-row justify-between items-center rounded-[30px] bg-[#0084FF] p-8 text-white shadow-lg">
          <div className="space-y-2">
            <p className="font-bold">{currentDate}</p>
            <h1 className="text-4xl md:text-6xl font-bold">
              สวัสดี, {employee?.name || '...'}
            </h1>
            <p className="font-bold text-white/70">
              พนักงานรหัส: {employee?.id || '...'}
            </p>
            <p className="text-sm text-white/70">
              ยินดีต้อนรับเข้าสู่ระบบจัดการใบเสนอราคา ระบบพร้อมให้บริการแล้ว
            </p>
          </div>
          <div className="mt-6 md:mt-0 md:ml-8">
            <img 
              src="/assets/waving-hand.png" 
              alt="Checklist" 
              className="w-20 h-20 mr-10" 
            />
          </div>
        </div>

        {/* --- 2.2 Stats Cards (การ์ดสถิติ 3 ใบ) --- */}
        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          
          {/* Card 1: ใบเสนอราคาวันนี้ */}
          <div className="rounded-[30px] bg-white p-8 shadow-lg cursor-pointer hover:bg-gray-100"
               onClick={handleTodayQuotes}>
            <div className="flex justify-between items-start">
              {/* Icon */}
              <div className="rounded-xl bg-[#0084FF] p-3 shadow-md">
                <img 
                  src="/assets/document-text-svgrepo-com.svg" 
                  alt="Document Icon" 
                  className="w-8 h-8" 
                />
              </div>
              {/* Text */}
              <div className="text-right">
                <p className="text-xl font-bold text-gray-400">ใบเสนอราคาวันนี้</p>
                <p className="text-6xl font-bold text-black">{todayCount}</p>
                <span className="text-sm font-bold text-gray-400">รายการทั้งหมด</span>
              </div>
            </div>
          </div>

          {/* Card 2: ลูกค้าที่ติดต่อ */}
          <div className="rounded-[30px] bg-white p-8 shadow-lg">
            <div className="flex justify-between items-start">
              {/* Icon */}
              <div className="rounded-xl bg-[#05A628] p-3 shadow-md">
                <img 
                  src="/assets/people-icon.svg"
                  alt="People Icon" 
                  className="w-8 h-8" 
                />
              </div>
              {/* Text */}
              <div className="text-right">
                <p className="text-xl font-bold text-gray-400">ลูกค้าที่ติดต่อ</p>
                <p className="text-6xl font-bold text-black">{contactCustomerCount}</p>
                <span className="text-sm font-bold text-gray-400">รายการทั้งหมด</span>
              </div>
            </div>
          </div>

          {/* Card 3: รอดำเนินการ */}
          <div 
            className="rounded-[30px] bg-white p-8 shadow-lg cursor-pointer hover:bg-gray-100 "
            onClick={handlePendingQuotes}>
            <div className="flex justify-between items-start">
              {/* Icon */}
              <div className="rounded-xl bg-[#EF833F] p-3 shadow-md">
                <img 
                  src="/assets/time-svgrepo-com.svg" 
                  alt="Time Icon" 
                  className="w-8 h-8 " 
                />
              </div>
              {/* Text */}
              <div className="text-right ">
                <p className="text-xl font-bold text-gray-400 ">รอดำเนินการ</p>
                <p className="text-6xl font-bold text-black">{pendingCount}</p>
                <span className="text-sm font-bold text-gray-400 ">รายการทั้งหมด</span>
              </div>
            </div>
          </div>
        </div>

          <div 
            className="mt-6 group relative cursor-pointer overflow-hidden rounded-[33px] bg-[#EFB73F] p-8 text-white shadow-lg transition-all hover:shadow-xl"
            onClick={handleSemiSize}
          >
            <img 
                src="/assets/box.png" 
                alt="Arrow" 
                className="w-28 h-28 mb-4 ml-1" 
              />
            <h2 className="text-4xl font-bold">ตรวจสอบรายละเอียดสินค้า</h2>
            <p className="mt-2 text-lg text-white/70">
              รายละเอียดของสินค้าต่างๆ
            </p>
            <div className="mt-6 flex items-center text-lg font-bold text-white/70 transition-all group-hover:translate-x-1">
              <span>เริ่มต้นเลย</span>
              <img 
                src="/assets/right-arrow.png" 
                alt="Arrow" 
                className="w-5 h-5 ml-1" 
              />
            </div>
          </div>
        
        {/* --- 2.3 Action Cards (การ์ดทำงาน 2 ใบ) --- */}
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Action 1: สร้างใบเสนอราคา (สีแดง) */}
          <div 
            className="group relative cursor-pointer overflow-hidden rounded-[33px] bg-red-600/[.85] p-8 text-white shadow-lg transition-all hover:shadow-xl"
            onClick={handleCreateQuote}
          >
            <img 
                src="/assets/plus.png" 
                alt="Arrow" 
                className="w-16 h-16 mb-4 ml-1" 
              />
            <h2 className="text-4xl font-bold">สร้างใบเสนอราคา</h2>
            <p className="mt-2 text-lg text-white/70">
              เริ่มสร้างใบเสนอราคาใหม่
            </p>
            <div className="mt-6 flex items-center text-lg font-bold text-white/70 transition-all group-hover:translate-x-1">
              <span>เริ่มต้นเลย</span>
              <img 
                src="/assets/right-arrow.png" 
                alt="Arrow" 
                className="w-5 h-5 ml-1" 
              />
            </div>
          </div>

          {/* Action 2: ค้นหาข้อมูลลูกค้า (สีน้ำเงิน) */}
          <div className="group relative cursor-pointer overflow-hidden rounded-[33px] bg-blue-600/[.83] p-8 text-white shadow-lg transition-all hover:shadow-xl">
            <img 
                src="/assets/magnifier.png" 
                alt="Arrow" 
                className="w-16 h-16 mb-4 ml-1" 
              />
            <h2 className="text-4xl font-bold">ค้นหาข้อมูลลูกค้า</h2>
            <p className="mt-2 text-lg text-white/70">
              ตรวจสอบข้อมูลลูกค้าและประวัติการซื้อ
            </p>
            <div className="mt-6 flex items-center text-lg font-bold text-white/70 transition-all group-hover:translate-x-1">
              <span>เริ่มต้นเลย</span>
              <img 
                src="/assets/right-arrow.png" 
                alt="Arrow" 
                className="w-5 h-5 ml-1" 
              />
            </div>
          </div>
          
        </div>
              {/* === Modal: Glass Semi Size === */}
        <GlassSemiSizeModal
        isOpen={isSemiModalOpen}
        onClose={() => setIsSemiModalOpen(false)}
        branchCode="B01"
      />



      </main>

    </div>
  );
}

export default Dashboard;