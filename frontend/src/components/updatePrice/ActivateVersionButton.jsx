import api from "../../services/api";

export default function ActivateVersionButton({ versionId }) {
  const activate = async () => {
    await api.post(`/api/item-update/activate/${versionId}`);
    alert("Activated!");
  };

  return (
    <button
      onClick={activate}
      className="mt-4 px-6 py-2 bg-green-600 text-white rounded"
    >
      ยืนยัน
    </button>
  );
}
