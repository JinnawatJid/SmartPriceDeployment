// src/utils/roleUtils.js

/**
 * ตรวจสอบว่า employee มี role ที่อนุญาตหรือไม่
 * @param {Object} employee - ข้อมูล employee จาก useAuth
 * @param {string|string[]} allowedRoles - role ที่อนุญาต (string หรือ array)
 * @returns {boolean}
 */
export const hasRole = (employee, allowedRoles) => {
  if (!employee || !employee.role) return false;
  
  const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
  return roles.includes(employee.role);
};

/**
 * ตรวจสอบว่า employee อยู่ใน region ที่อนุญาตหรือไม่
 * @param {Object} employee - ข้อมูล employee จาก useAuth
 * @param {string|string[]} allowedRegions - region ที่อนุญาต (string หรือ array)
 * @returns {boolean}
 */
export const hasRegion = (employee, allowedRegions) => {
  if (!employee || !employee.region) return false;
  
  const regions = Array.isArray(allowedRegions) ? allowedRegions : [allowedRegions];
  return regions.includes(employee.region);
};

/**
 * ตรวจสอบว่า employee เป็น Regional Manager (RM) หรือไม่
 * @param {Object} employee - ข้อมูล employee จาก useAuth
 * @returns {boolean}
 */
export const isRegionalManager = (employee) => {
  return hasRole(employee, 'RM');
};

/**
 * ตรวจสอบว่า employee เป็น Zone Manager (ZM) หรือไม่
 * @param {Object} employee - ข้อมูล employee จาก useAuth
 * @returns {boolean}
 */
export const isZoneManager = (employee) => {
  return hasRole(employee, 'ZM');
};

/**
 * ตรวจสอบว่า employee เป็น Manager (RM หรือ ZM) หรือไม่
 * @param {Object} employee - ข้อมูล employee จาก useAuth
 * @returns {boolean}
 */
export const isManager = (employee) => {
  return hasRole(employee, ['RM', 'ZM']);
};

/**
 * ดึงชื่อ role แบบเต็ม
 * @param {string} roleCode - รหัส role (RM, ZM)
 * @returns {string}
 */
export const getRoleName = (roleCode) => {
  const roleNames = {
    'RM': 'Regional Manager',
    'ZM': 'Zone Manager',
  };
  return roleNames[roleCode] || roleCode;
};

/**
 * ดึงชื่อ region แบบเต็ม
 * @param {string} regionCode - รหัส region (N, S, NE, C, BE)
 * @returns {string}
 */
export const getRegionName = (regionCode) => {
  const regionNames = {
    'N': 'ภาคเหนือ',
    'S': 'ภาคใต้',
    'NE': 'ภาคตะวันออกเฉียงเหนือ',
    'C': 'ภาคกลาง',
    'BE': 'กรุงเทพและปริมณฑล',
  };
  return regionNames[regionCode] || regionCode;
};
