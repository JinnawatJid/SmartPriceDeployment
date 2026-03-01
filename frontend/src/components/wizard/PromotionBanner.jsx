import React from 'react';
import { Megaphone, Tag, Package } from 'lucide-react';

const PromotionBanner = ({ promotions }) => {
  console.log('🎨 PromotionBanner rendered with promotions:', promotions);
  
  if (!promotions || promotions.length === 0) {
    console.log('⚠️ PromotionBanner: No promotions to display');
    return null;
  }

  console.log('✅ PromotionBanner: Displaying', promotions.length, 'promotions');

  return (
    <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-lg p-2 mb-4">
      <div className="flex items-start gap-3">
        <Megaphone className="w-4 h-4 text-red-600 flex-shrink-0 " />
        <div className="flex-1">
          <h3 className="text-red-700 font-semibold text-xs mb-3">
            โปรโมชั่นและรายละเอียด
          </h3>
        </div>
      </div>
       <div className="space-y-3">
            {promotions.map((promo, index) => (
              <div key={index} className="bg-white rounded-lg p-3 shadow-sm">
                <div className="flex items-start gap-2">
                  {promo.type === 'glass' ? (
                    <Package className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  ) : (
                    <Tag className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="text-gray-800 text-sm font-medium">
                      {promo.title}
                    </p>
                    <p className="text-gray-600 text-xs font-semibold mt-1">
                      {promo.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
    </div>
  );
};

export default PromotionBanner;
