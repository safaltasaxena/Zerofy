import { useSimulator, buildLogMessage } from '../hooks/useSimulator'
import { useEffect } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COMMUTE_OPTIONS = [
  { value: 'petrol_car',         label: 'Petrol Car' },
  { value: 'diesel_car',         label: 'Diesel Car' },
  { value: 'petrol_two_wheeler', label: 'Petrol Two Wheeler' },
  { value: 'electric_vehicle',   label: 'Electric Vehicle' },
  { value: 'auto_rickshaw',      label: 'Auto Rickshaw' },
  { value: 'bus',                label: 'Bus' },
  { value: 'metro',              label: 'Metro' },
  { value: 'walking',            label: 'Walking' },
  { value: 'cycling',            label: 'Cycling' },
]

const DIET_OPTIONS = [
  { value: 'vegan',            label: 'Vegan' },
  { value: 'vegetarian',       label: 'Vegetarian' },
  { value: 'eggetarian',       label: 'Eggetarian' },
  { value: 'non_vegetarian',   label: 'Non-Vegetarian' },
]

/**
 * SimulatorSection — What-if habit slider panel.
 *
 * Props:
 *   profile          — current user profile (sets slider defaults)
 *   onLogChanges     — called with NLP message when user clicks "Log these changes"
 *   onSimulatorChange — called with the current simulator breakdown whenever sliders change.
 *                       Dashboard uses this to pass breakdown to ScoreBreakdown for the outer ring.
 */
export default function SimulatorSection({ profile, onLogChanges, onSimulatorChange }) {
  const { sliderState, breakdown, isLoading, handleSliderChange } = useSimulator({ profile })

  const onSelect  = (field)  => (e) => handleSliderChange(field, e.target.value)
  const onRange   = (field)  => (e) => handleSliderChange(field, Number(e.target.value))
  const onLog     = ()       => onLogChanges(buildLogMessage(sliderState, profile))

  // Emit simulator breakdown upward whenever it changes so Dashboard
  // can pass it to ScoreBreakdown for the outer ring display.
  useEffect(() => {
    if (onSimulatorChange) {
      onSimulatorChange(breakdown)
    }
  }, [breakdown, onSimulatorChange])

  return (
    <section aria-label="Habit Simulator" className="bg-white rounded-xl border p-4 flex flex-col gap-6">
      <h3 className="font-semibold text-gray-900 text-lg">What if I changed my habits?</h3>
      <p className="text-xs text-gray-500 -mt-4">
        Move the sliders to see a second ring appear on the score chart above ↑
      </p>

      {/* Commute mode */}
      <div className="flex flex-col gap-1">
        <label htmlFor="sim-commute-mode" className="text-sm font-medium text-gray-700">Commute Mode</label>
        <select
          id="sim-commute-mode"
          value={sliderState.commute_mode}
          onChange={onSelect('commute_mode')}
          className="border rounded-lg p-2 min-h-[44px]"
        >
          {COMMUTE_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {/* Daily km */}
      <div className="flex flex-col gap-1">
        <label htmlFor="sim-avg-daily-km" className="text-sm font-medium text-gray-700">
          Daily Distance — {sliderState.avg_daily_km} km
        </label>
        <input
          id="sim-avg-daily-km"
          type="range"
          min={0}
          max={500}
          step={1}
          value={sliderState.avg_daily_km}
          onChange={onRange('avg_daily_km')}
          aria-label={`Daily commute distance, currently ${sliderState.avg_daily_km} km`}
          className="w-full accent-green-600"
        />
        <div className="flex justify-between text-xs text-gray-400"><span>0</span><span>500 km</span></div>
      </div>

      {/* Diet type */}
      <div className="flex flex-col gap-1">
        <label htmlFor="sim-diet-type" className="text-sm font-medium text-gray-700">Diet</label>
        <select
          id="sim-diet-type"
          value={sliderState.diet_type}
          onChange={onSelect('diet_type')}
          className="border rounded-lg p-2 min-h-[44px]"
        >
          {DIET_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {/* AC hours */}
      <div className="flex flex-col gap-1">
        <label htmlFor="sim-ac-hours" className="text-sm font-medium text-gray-700">
          AC Hours per Day — {sliderState.ac_hours_per_day} h
        </label>
        <input
          id="sim-ac-hours"
          type="range"
          min={0}
          max={24}
          step={0.5}
          value={sliderState.ac_hours_per_day}
          onChange={onRange('ac_hours_per_day')}
          aria-label={`AC hours per day, currently ${sliderState.ac_hours_per_day} hours`}
          className="w-full accent-green-600"
        />
        <div className="flex justify-between text-xs text-gray-400"><span>0</span><span>24 h</span></div>
      </div>

      {/* LPG cylinders */}
      <div className="flex flex-col gap-1">
        <label htmlFor="sim-lpg" className="text-sm font-medium text-gray-700">
          LPG Cylinders per Month — {sliderState.lpg_cylinders_per_month}
        </label>
        <input
          id="sim-lpg"
          type="range"
          min={0}
          max={10}
          step={0.1}
          value={sliderState.lpg_cylinders_per_month}
          onChange={onRange('lpg_cylinders_per_month')}
          aria-label={`LPG cylinders per month, currently ${sliderState.lpg_cylinders_per_month}`}
          className="w-full accent-green-600"
        />
        <div className="flex justify-between text-xs text-gray-400"><span>0</span><span>10</span></div>
      </div>

      {/* Simulated total */}
      <div className="bg-gray-50 rounded-xl p-3 text-center border border-gray-100">
        <p className="text-xs text-gray-400 mb-1">Simulated daily CO₂</p>
        <p className={`text-2xl font-bold ${
          breakdown.total < (profile?.baseline_daily_co2_kg ?? breakdown.total)
            ? 'text-green-600' : 'text-gray-800'
        }`}>
          {breakdown.total.toFixed(2)} <span className="text-sm font-normal text-gray-500">kg</span>
        </p>
        {profile?.baseline_daily_co2_kg != null && (
          <p className="text-xs text-gray-500 mt-1">
            {(breakdown.total - profile.baseline_daily_co2_kg) < 0
              ? `🌱 ${Math.abs((breakdown.total - profile.baseline_daily_co2_kg).toFixed(2))} kg less than your baseline`
              : `${((breakdown.total - profile.baseline_daily_co2_kg).toFixed(2))} kg more than your baseline`
            }
          </p>
        )}
      </div>

      {/* Simulated breakdown pie chart */}
      <div
        role="img"
        aria-label={`Simulated CO2 breakdown: Transport ${breakdown.transport.toFixed(2)}kg, Diet ${breakdown.diet.toFixed(2)}kg, Electricity ${breakdown.electricity.toFixed(2)}kg, LPG ${breakdown.lpg.toFixed(2)}kg`}
        className="w-full h-48 relative"
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={[
                { name: 'Transport', value: breakdown.transport, color: '#3b82f6' },
                { name: 'Diet', value: breakdown.diet, color: '#22c55e' },
                { name: 'Electricity', value: breakdown.electricity, color: '#f59e0b' },
                { name: 'LPG', value: breakdown.lpg, color: '#ef4444' },
              ].filter(d => d.value > 0)}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={75}
              dataKey="value"
            >
              {[
                { key: 'transport', color: '#3b82f6' },
                { key: 'diet', color: '#22c55e' },
                { key: 'electricity', color: '#f59e0b' },
                { key: 'lpg', color: '#ef4444' },
              ].filter(cell => breakdown[cell.key] > 0).map((cell) => (
                <Cell key={cell.key} fill={cell.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${Number(value).toFixed(2)} kg`} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <button
        onClick={onLog}
        className="w-full bg-green-600 text-white rounded-xl min-h-[44px] font-semibold hover:bg-green-700 transition-colors"
      >
        Log these changes
      </button>
    </section>
  )
}
