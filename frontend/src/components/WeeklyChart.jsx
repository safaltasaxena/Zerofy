/**
 * WeeklyChart.jsx — Recharts LineChart of the past 7 days of CO2 trend.
 *
 * ACCESSIBILITY.md §8: role="img" + aria-label on chart wrapper.
 * X axis dates formatted as short day names (Mon, Tue, etc.).
 * Empty state if trend is an empty array.
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function formatDay(dateStr) {
  const d = new Date(dateStr)
  return DAY_NAMES[d.getDay()]
}

function SkeletonChart() {
  return (
    <div className="animate-pulse bg-white rounded-xl p-4">
      <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
      <div className="h-32 bg-gray-200 rounded" />
    </div>
  )
}

export default function WeeklyChart({ trend, isLoading }) {
  if (isLoading) return <SkeletonChart />

  if (!trend || trend.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 text-center text-gray-400 text-sm">
        No weekly data yet — keep logging daily to see your trend!
      </div>
    )
  }

  const chartData = trend.slice(0, 7).map((point) => ({
    day: formatDay(point.date),
    co2: point.daily_co2_kg,
  }))

  const ariaLabel = `Weekly CO2 trend for the past ${chartData.length} day${chartData.length === 1 ? '' : 's'}`

  return (
    <div role="img" aria-label={ariaLabel} className="bg-white rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Weekly Trend</h3>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="day"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#6b7280' }}
            unit=" kg"
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value) => [`${Number(value).toFixed(2)} kg CO₂`, 'Daily CO₂']}
          />
          <Line
            type="monotone"
            dataKey="co2"
            stroke="#16a34a"
            strokeWidth={2}
            dot={{ fill: '#16a34a', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
