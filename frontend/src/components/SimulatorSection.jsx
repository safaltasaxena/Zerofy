import { useSimulator, buildLogMessage } from '../hooks/useSimulator'
import SimulatorBreakdown from './SimulatorBreakdown'

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

export default function SimulatorSection({ profile, onLogChanges }) {
  const { sliderState, breakdown, handleSliderChange } = useSimulator({ profile })

  const onSelect  = (field)  => (e) => handleSliderChange(field, e.target.value)
  const onRange   = (field)  => (e) => handleSliderChange(field, Number(e.target.value))
  const onLog     = ()       => onLogChanges(buildLogMessage(sliderState, profile))

  return (
    <section aria-label="Habit Simulator" className="bg-white rounded-xl border p-4 flex flex-col gap-6">
      <h3 className="font-semibold text-gray-900 text-lg">What if I changed my habits?</h3>

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

      <SimulatorBreakdown breakdown={breakdown} isLoading={false} />

      <button
        onClick={onLog}
        className="w-full bg-green-600 text-white rounded-xl min-h-[44px] font-semibold hover:bg-green-700 transition-colors"
      >
        Log these changes
      </button>
    </section>
  )
}
