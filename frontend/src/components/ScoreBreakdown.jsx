/**
 * ScoreBreakdown.jsx — Recharts PieChart showing today's CO2 breakdown.
 *
 * ACCESSIBILITY.md §5: pie chart min 200×200px.
 * ACCESSIBILITY.md §8: role="img" + aria-label on chart wrapper, text labels on every slice.
 * ACCESSIBILITY.md §11: slice colours — transport #3b82f6, diet #22c55e, electricity #f59e0b, lpg #ef4444.
 * EDGE-20: all-zero breakdown → empty state, no divide-by-zero.
 */

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const SLICE_META = [
  { key: 'transport',   label: 'Transport',   color: '#3b82f6' },
  { key: 'diet',        label: 'Diet',         color: '#22c55e' },
  { key: 'electricity', label: 'Electricity',  color: '#f59e0b' },
  { key: 'lpg',         label: 'LPG',          color: '#ef4444' },
]

// SVG presentation attributes are not inline styles — fill/fontSize are valid here.
function PieLabel({ cx, cy, midAngle, outerRadius, percent, value }) {
  const RADIAN = Math.PI / 180
  const radius = outerRadius + 28
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)
  if (percent < 0.04) return null   // Skip label if slice is too small to read
  return (
    <text x={x} y={y} textAnchor="middle" dominantBaseline="central" fontSize={10} fill="#374151">
      {`${Number(value).toFixed(1)}kg ${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

function SkeletonBreakdown() {
  return (
    <div className="animate-pulse bg-white rounded-xl p-6 flex flex-col items-center gap-4">
      <div className="w-48 h-48 bg-gray-200 rounded-full" />
      <div className="h-3 bg-gray-200 rounded w-3/4" />
    </div>
  )
}

export default function ScoreBreakdown({ breakdown, analogy, isLoading }) {
  if (isLoading) return <SkeletonBreakdown />

  const total = breakdown?.total ?? 0
  const isAllZero = total === 0

  if (isAllZero) {
    return (
      <div className="bg-white rounded-xl p-6 text-center">
        <p className="text-4xl font-bold text-gray-800 mb-1">0.00</p>
        <p className="text-sm text-gray-500 mb-4">kg CO₂ today</p>
        <p className="text-green-700 font-medium text-sm">
          🌱 Zero emissions logged yet — log your habits to see your score!
        </p>
      </div>
    )
  }

  const chartData = SLICE_META
    .map(({ key, label, color }) => ({ name: label, key, value: breakdown[key] ?? 0, color }))
    .filter((d) => d.value > 0)

  const ariaLabel =
    `Today's carbon breakdown: Transport ${breakdown.transport}kg, ` +
    `Diet ${breakdown.diet}kg, Electricity ${breakdown.electricity}kg, LPG ${breakdown.lpg}kg`

  return (
    <div className="bg-white rounded-xl p-4">
      <div role="img" aria-label={ariaLabel} className="relative">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              dataKey="value"
              label={PieLabel}
              labelLine={false}
            >
              {chartData.map((entry) => (
                <Cell key={entry.key} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [`${Number(value).toFixed(2)} kg CO₂`, name]}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Centre total — Tailwind absolute over chart, no inline style */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <p
              aria-label={`Today's carbon score: ${total.toFixed(2)} kg CO₂`}
              className="text-4xl font-bold text-gray-800 leading-none"
            >
              {total.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500 mt-1">kg CO₂</p>
          </div>
        </div>
      </div>

      {analogy && (
        <p className="text-sm text-gray-600 text-center mt-3 px-2 leading-relaxed">{analogy}</p>
      )}
    </div>
  )
}
