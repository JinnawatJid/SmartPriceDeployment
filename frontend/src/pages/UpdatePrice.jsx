import React, { useState, useEffect } from "react";
import api from "../services/api";

import UploadPriceExcel from "../components/updatePrice/UploadPriceExcel";
import PricePreviewTable from "../components/updatePrice/PricePreviewTable";
import ActivateVersionButton from "../components/updatePrice/ActivateVersionButton";

export default function UpdatePrice() {
  const [version, setVersion] = useState(null);
  const [rows, setRows] = useState([]);

  useEffect(() => {
    if (!version) return;
    api.get(`/api/item-update/preview/${version.version_id}`)
       .then(res => setRows(res.data));
  }, [version]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Update Price (Manager)</h1>

      <UploadPriceExcel onUploaded={setVersion} />

      {rows.length > 0 && (
        <>
          <ActivateVersionButton versionId={version.version_id} />
          <PricePreviewTable rows={rows} />
        </>
      )}
    </div>
  );
}
