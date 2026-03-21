/**
 * Format date to Thai format: วันที่/เดือน/พ.ศ.
 * Example: 21/3/2569
 * @param {string|Date} dateStr - Date string or Date object
 * @returns {string} Formatted date string
 */
export const formatDateThai = (dateStr) => {
  if (!dateStr) return "-";
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return "-";
    
    const day = date.getDate();
    const month = date.getMonth() + 1;
    const year = date.getFullYear() + 543; // Convert to Buddhist year
    
    return `${day}/${month}/${year}`;
  } catch (err) {
    console.error("Error formatting date:", err);
    return "-";
  }
};

/**
 * Format date to Thai format with month name: วันที่ เดือน พ.ศ.
 * Example: 21 มีนาคม 2569
 * @param {string|Date} dateStr - Date string or Date object
 * @returns {string} Formatted date string
 */
export const formatDateThaiLong = (dateStr) => {
  if (!dateStr) return "-";
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return "-";
    
    return date.toLocaleDateString("th-TH", {
      day: "numeric",
      month: "long",
      year: "numeric",
      timeZone: "Asia/Bangkok",
    });
  } catch (err) {
    console.error("Error formatting date:", err);
    return "-";
  }
};

/**
 * Format date to Thai format with short month: วันที่ เดือน(ย่อ) พ.ศ.
 * Example: 21 มี.ค. 2569
 * @param {string|Date} dateStr - Date string or Date object
 * @returns {string} Formatted date string
 */
export const formatDateThaiShort = (dateStr) => {
  if (!dateStr) return "-";
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return "-";
    
    return date.toLocaleDateString("th-TH", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Bangkok",
    });
  } catch (err) {
    console.error("Error formatting date:", err);
    return "-";
  }
};

/**
 * Format date and time to Thai format
 * Example: 21/3/2569 14:30
 * @param {string|Date} dateStr - Date string or Date object
 * @returns {string} Formatted date and time string
 */
export const formatDateTimeThaiShort = (dateStr) => {
  if (!dateStr) return "-";
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return "-";
    
    const day = date.getDate();
    const month = date.getMonth() + 1;
    const year = date.getFullYear() + 543;
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  } catch (err) {
    console.error("Error formatting date:", err);
    return "-";
  }
};
