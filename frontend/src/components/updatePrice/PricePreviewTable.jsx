export default function PricePreviewTable({ rows }) {
  return (
    <table className="w-full mt-4 border">
      <thead>
        <tr className="grid grid-cols-7 bg-gray-100 ">
          <th className="col-span-3 text-start">SKU</th>
          <th>R1</th>
          <th>→</th>
          <th>New R1</th>
          <th>Alt Name</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className="border-t grid grid-cols-7">
            <td className="col-span-3">{r.sku}</td>
            <td className="text-center">{r.old_R1}</td>
            <td className="text-center">→</td>
            <td className="text-blue-600 text-center">{r.new_R1}</td>
            <td className="text-center">{r.new_alternate_name}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
