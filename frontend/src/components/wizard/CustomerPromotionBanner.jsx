import React, { useState, useEffect } from 'react';
import { Megaphone, X } from 'lucide-react';
import api from '../../services/api';

const CustomerPromotionBanner = ({ customerCode }) => {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const fetchCustomerPromotions = async () => {
      console.log('🔍 [CUSTOMER PROMO] Starting fetch for customerCode:', customerCode);
      
      if (!customerCode) {
        console.log('⚠️ [CUSTOMER PROMO] No customerCode provided, clearing promotions');
        setPromotions([]);
        return;
      }

      setLoading(true);
      try {
        const url = `/api/promotions/active-by-customer?customerCode=${customerCode}`;
        console.log('📡 [CUSTOMER PROMO] Fetching from:', url);
        
        const response = await api.get(url);
        console.log('✅ [CUSTOMER PROMO] Response received:', response.data);
        
        setPromotions(response.data || []);
        setDismissed(false); // Reset dismissed state when customer changes
        
        if (response.data && response.data.length > 0) {
          console.log(`🎉 [CUSTOMER PROMO] Found ${response.data.length} promotions for customer ${customerCode}`);
        } else {
          console.log(`ℹ️ [CUSTOMER PROMO] No promotions found for customer ${customerCode}`);
        }
      } catch (error) {
        console.error('❌ [CUSTOMER PROMO] Error fetching customer promotions:', error);
        console.error('❌ [CUSTOMER PROMO] Error details:', error.response?.data);
        setPromotions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCustomerPromotions();
  }, [customerCode]);

  if (loading) {
    console.log('⏳ [CUSTOMER PROMO] Loading state...');
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-blue-700 text-sm">กำลังตรวจสอบโปรโมชั่นของลูกค้า...</p>
      </div>
    );
  }

  if (!promotions || promotions.length === 0) {
    console.log('ℹ️ [CUSTOMER PROMO] No promotions to display (dismissed:', dismissed, ')');
    return null;
  }

  if (dismissed) {
    console.log('🚫 [CUSTOMER PROMO] Banner dismissed by user');
    return null;
  }

  console.log('🎨 [CUSTOMER PROMO] Rendering banner with', promotions.length, 'promotions');

  return (
    <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-400 rounded-lg p-4 mb-4 shadow-md animate-fadeIn">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Megaphone className="w-5 h-5 text-red-600 flex-shrink-0" />
          <h3 className="text-red-700 font-bold text-sm">
            ลูกค้าท่านนี้มีโปรโมชั่นพิเศษ!
          </h3>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="ปิด"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-2">
        {promotions.map((promo, index) => (
          <div
            key={index}
            className="bg-white rounded-lg p-3 shadow-sm border border-red-200"
          >
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <p className="text-gray-800 text-sm font-semibold">
                  {promo.promotion_name}
                </p>
                {promo.promotion_text && (
                  <p className="text-gray-600 text-xs mt-1">
                    {promo.promotion_text}
                  </p>
                )}
                <p className="text-gray-500 text-xs mt-1">
                  ใช้ได้ถึง: {new Date(promo.end_date).toLocaleDateString('th-TH')}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CustomerPromotionBanner;
