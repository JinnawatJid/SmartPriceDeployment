# ตัวอย่างการใช้งาน Role-Based Access Control

## 1. ใช้งาน RoleGuard Component

```jsx
import RoleGuard from "../components/RoleGuard";

function MyComponent() {
  return (
    <div>
      {/* แสดงเฉพาะ Regional Manager */}
      <RoleGuard allowedRoles="RM">
        <button>ปุ่มสำหรับ RM เท่านั้น</button>
      </RoleGuard>

      {/* แสดงเฉพาะ RM หรือ ZM */}
      <RoleGuard allowedRoles={["RM", "ZM"]}>
        <div>เนื้อหาสำหรับ Manager</div>
      </RoleGuard>

      {/* แสดง fallback ถ้าไม่มีสิทธิ์ */}
      <RoleGuard 
        allowedRoles="RM"
        fallback={<p>คุณไม่มีสิทธิ์เข้าถึงส่วนนี้</p>}
      >
        <div>เนื้อหาสำหรับ RM</div>
      </RoleGuard>
    </div>
  );
}
```

## 2. ใช้งาน Role Utils Functions

```jsx
import { useAuth } from "../hooks/useAuth";
import { 
  hasRole, 
  hasRegion, 
  isRegionalManager, 
  isZoneManager,
  isManager,
  getRoleName,
  getRegionName 
} from "../utils/roleUtils";

function MyComponent() {
  const { employee } = useAuth();

  // ตรวจสอบ role
  const canApprove = hasRole(employee, ["RM", "ZM"]);
  const isRM = isRegionalManager(employee);
  const isZM = isZoneManager(employee);
  const isAnyManager = isManager(employee);

  // ตรวจสอบ region
  const isBangkok = hasRegion(employee, "BE");
  const isNorthOrSouth = hasRegion(employee, ["N", "S"]);

  // แสดงชื่อเต็ม
  const roleName = getRoleName(employee?.role); // "Regional Manager"
  const regionName = getRegionName(employee?.region); // "กรุงเทพและปริมณฑล"

  return (
    <div>
      {canApprove && (
        <button>อนุมัติ</button>
      )}
      
      <p>ตำแหน่ง: {roleName}</p>
      <p>ภูมิภาค: {regionName}</p>
    </div>
  );
}
```

## 3. ใช้งานใน useEffect หรือ Event Handler

```jsx
import { useAuth } from "../hooks/useAuth";
import { isRegionalManager } from "../utils/roleUtils";

function MyComponent() {
  const { employee } = useAuth();

  const handleSubmit = () => {
    if (isRegionalManager(employee)) {
      // ทำงานพิเศษสำหรับ RM
      console.log("Submitting as Regional Manager");
    } else {
      // ทำงานปกติ
      console.log("Submitting as regular user");
    }
  };

  return (
    <button onClick={handleSubmit}>Submit</button>
  );
}
```

## 4. ใช้งานกับ Protected Route

```jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { hasRole } from "../utils/roleUtils";

function ManagerOnlyPage() {
  const { employee, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  
  if (!hasRole(employee, ["RM", "ZM"])) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div>
      <h1>หน้าสำหรับ Manager เท่านั้น</h1>
    </div>
  );
}
```

## 5. แสดงข้อมูล Role และ Region ใน UI

```jsx
import { useAuth } from "../hooks/useAuth";
import { getRoleName, getRegionName } from "../utils/roleUtils";

function UserProfile() {
  const { employee } = useAuth();

  return (
    <div className="user-profile">
      <h2>{employee?.name}</h2>
      <p>รหัสพนักงาน: {employee?.id}</p>
      <p>สาขา: {employee?.branchId}</p>
      <p>ตำแหน่ง: {getRoleName(employee?.role)}</p>
      <p>ภูมิภาค: {getRegionName(employee?.region)}</p>
    </div>
  );
}
```

## ข้อมูล Role และ Region

### Roles
- `RM` - Regional Manager (ผู้จัดการภูมิภาค)
- `ZM` - Zone Manager (ผู้จัดการโซน)

### Regions
- `N` - ภาคเหนือ
- `S` - ภาคใต้
- `NE` - ภาคตะวันออกเฉียงเหนือ
- `C` - ภาคกลาง
- `BE` - กรุงเทพและปริมณฑล
