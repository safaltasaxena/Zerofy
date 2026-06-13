import { useState } from 'react'

export default function QuickUpdateForm({ prefills, onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    commute_mode: prefills?.commute_mode || '',
    avg_daily_km: prefills?.avg_daily_km ?? '',
    ac_hours_per_day: prefills?.ac_hours_per_day ?? '',
    diet_type: prefills?.diet_type || ''
  })
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    
    const km = Number(formData.avg_daily_km)
    const ac = Number(formData.ac_hours_per_day)

    if (!formData.commute_mode) return setError("Please select your main way of getting around")
    if (km < 0) return setError("Distance can't be negative")
    if (km > 500) return setError("Enter a distance between 0 and 500 km")
    if (ac > 24) return setError("AC hours can't be more than 24 in a day")
    if (!formData.diet_type) return setError("Please select the option that best describes how you eat")

    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Quick Update Form" className="bg-white p-4 rounded-xl border shadow-sm my-4 space-y-4">
      <h3 className="font-semibold text-gray-900 text-lg">Quick Update</h3>
      {error && <div role="alert" className="text-red-600 text-sm font-medium">{error}</div>}
      
      <div className="flex flex-col gap-1">
        <label htmlFor="commute_mode" className="text-sm font-medium text-gray-700">Commute Mode</label>
        <select id="commute_mode" name="commute_mode" value={formData.commute_mode} onChange={handleChange} className="border rounded-lg p-2 min-h-[44px]">
          <option value="">Select mode...</option>
          <option value="petrol_car">Petrol Car</option>
          <option value="diesel_car">Diesel Car</option>
          <option value="petrol_two_wheeler">Petrol Two Wheeler</option>
          <option value="electric_vehicle">Electric Vehicle</option>
          <option value="auto_rickshaw">Auto Rickshaw</option>
          <option value="bus">Bus</option>
          <option value="metro">Metro</option>
          <option value="walking">Walking</option>
          <option value="cycling">Cycling</option>
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="avg_daily_km" className="text-sm font-medium text-gray-700">Distance (km)</label>
        <input type="number" id="avg_daily_km" name="avg_daily_km" value={formData.avg_daily_km} onChange={handleChange} className="border rounded-lg p-2 min-h-[44px]" />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="ac_hours_per_day" className="text-sm font-medium text-gray-700">AC Hours</label>
        <input type="number" id="ac_hours_per_day" name="ac_hours_per_day" value={formData.ac_hours_per_day} onChange={handleChange} className="border rounded-lg p-2 min-h-[44px]" />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="diet_type" className="text-sm font-medium text-gray-700">Diet</label>
        <select id="diet_type" name="diet_type" value={formData.diet_type} onChange={handleChange} className="border rounded-lg p-2 min-h-[44px]">
          <option value="">Select diet...</option>
          <option value="vegan">Vegan</option>
          <option value="vegetarian">Vegetarian</option>
          <option value="eggetarian">Eggetarian</option>
          <option value="non_vegetarian">Non-Vegetarian</option>
        </select>
      </div>

      <button type="submit" disabled={isLoading} aria-busy={isLoading} className="w-full bg-green-600 text-white rounded-lg min-h-[44px] font-medium hover:bg-green-700 transition-colors disabled:opacity-50">
        {isLoading ? 'Updating...' : 'Update my habits'}
      </button>
    </form>
  )
}
