export default function ParsePreview({ preview, onConfirm, onEdit }) {
  const { category, change, quantity, unit } = preview || {}
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') onConfirm()
  }

  return (
    <div role="region" aria-label="Update Preview" className="bg-white border rounded-xl p-4 shadow-sm my-4">
      <div className="font-medium text-gray-800 mb-3 text-lg">
        {category} → {change} | {quantity} {unit}
      </div>
      <div className="flex gap-3">
        <button
          onClick={onConfirm}
          onKeyDown={handleKeyDown}
          aria-label={`Confirm: ${change} ${quantity} ${unit}`}
          className="flex-1 bg-green-600 text-white min-h-[44px] rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center"
        >
          Confirm ✅
        </button>
        <button
          onClick={onEdit}
          aria-label="Edit this update"
          className="flex-1 bg-gray-100 text-gray-800 min-h-[44px] rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center"
        >
          Edit ✏️
        </button>
      </div>
    </div>
  )
}
