/**
 * ScoreBreakdown.jsx — Recharts PieChart showing today's CO2 breakdown.
 *
 * ACCESSIBILITY.md §5: pie chart min 200×200px.
 * ACCESSIBILITY.md §8: role="img" + aria-label on chart wrapper, text labels on every slice.
 * ACCESSIBILITY.md §11: slice colours — transport #3b82f6, diet #22c55e, electricity #f59e0b, lpg #ef4444.
 * EDGE-20: all-zero breakdown → empty state, no divide-by-zero.
 *
 * simulatorBreakdown prop: if provided, renders a second outer ring showing what-if scores.
 * Inner ring (r 55-85) = actual today score. Outer ring (r 92-112) = simulator.
 */

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const SLICE_META = [
  { key: 'transport', label: 'Transport', color: '#3b82f6' },
  { key: 'diet', label: 'Diet', color: '#22c55e' },
  { key: 'electricity', label: 'Electricity', color: '#f59e0b' },
  { key: 'lpg', label: 'LPG', color: '#ef4444' },
]

// Lighter tint versions for the simulator outer ring
const SIMULATOR_COLORS = {
  transport: '#93c5fd',   // blue-300
  diet: '#86efac',   // green-300
  electricity: '#fcd34d',   // amber-300
  lpg: '#fca5a5',   // red-300
}

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

export default function ScoreBreakdown({ breakdown, analogy, isLoading, simulatorBreakdown }) {
  if (isLoading) return <SkeletonBreakdown />

  const total = breakdown?.total ?? 0
  const isAllZero = total === 0

  const hasSimulator =
    simulatorBreakdown &&
    Math.abs(simulatorBreakdown.total) > 0.01

  if (isAllZero && !hasSimulator) {
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

  // Ensure inner pie has a structure even when actual data is 0 but simulator is active
  const displayChartData = chartData.length > 0
    ? chartData
    : [{ name: 'No data', value: 0.001, color: '#f3f4f6' }]

  // Build simulator outer ring data (only shown when simulatorBreakdown differs significantly from breakdown)
  const isSimulatorDiff =
    simulatorBreakdown &&
    Math.abs(simulatorBreakdown.total - total) > 0.01

  const simChartData = isSimulatorDiff
    ? SLICE_META.map(({ key, label }) => ({
      name: `Sim: ${label}`,
      key,
      value: simulatorBreakdown[key] ?? 0,
      color: SIMULATOR_COLORS[key],
    })).filter((d) => d.value > 0)
    : []

  const simTotal = isSimulatorDiff ? (simulatorBreakdown.total ?? 0) : null
  const simDelta = simTotal !== null ? (simTotal - total).toFixed(2) : null

  const ariaLabel =
    `Today's carbon breakdown: Transport ${breakdown.transport}kg, ` +
    `Diet ${breakdown.diet}kg, Electricity ${breakdown.electricity}kg, LPG ${breakdown.lpg}kg`

  const chartHeight = 240

  return (
    <div className="bg-white rounded-xl p-4">
      {hasSimulator && (
        <div className="flex items-center justify-center gap-4 mb-2 text-xs">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-gray-600">Actual</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-300" />
            <span className="text-gray-600">What-if</span>
          </span>
          {simDelta !== null && (
            <span className={`font-semibold ${parseFloat(simDelta) < 0 ? 'text-green-600' : 'text-red-500'}`}>
              {parseFloat(simDelta) < 0 ? `▼ ${Math.abs(simDelta)} kg saved` : `▲ +${simDelta} kg more`}
            </span>
          )}
        </div>
      )}
      <div role="img" aria-label={ariaLabel} className="relative">
        <ResponsiveContainer width="100%" height={chartHeight}>
          <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            {/* Inner ring — actual today score */}
            <Pie
              data={displayChartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              dataKey="value"
              label={hasSimulator ? false : PieLabel}
              labelLine={false}
            >
              {chartData.map((entry) => (
                <Cell key={entry.key} fill={entry.color} />
              ))}
            </Pie>

            {/* Outer ring — simulator what-if (only when simulator is active) */}
            {hasSimulator && simChartData.length > 0 && (
              <Pie
                data={simChartData}
                cx="50%"
                cy="50%"
                innerRadius={92}
                outerRadius={112}
                dataKey="value"
                label={false}
                labelLine={false}
              >
                {simChartData.map((entry) => (
                  <Cell key={entry.key} fill={entry.color} />
                ))}
              </Pie>
            )}

            <Tooltip
              formatter={(value, name) => [`${Number(value).toFixed(2)} kg CO₂`, name]}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Centre total — shows actual score in inner ring centre */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <p
              aria-label={`Today's carbon score: ${total.toFixed(2)} kg CO₂`}
              className="text-4xl font-bold text-gray-800 leading-none"
            >
              {total.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500 mt-1">kg CO₂</p>
            {hasSimulator && simTotal !== null && (
              <p className="text-xs text-blue-400 mt-0.5">→ {simTotal.toFixed(2)} if changed</p>
            )}
          </div>
        </div>
      </div>

      {analogy && (
        <p className="text-sm text-gray-600 text-center mt-3 px-2 leading-relaxed">{analogy}</p>
      )}
    </div>
  )
}

