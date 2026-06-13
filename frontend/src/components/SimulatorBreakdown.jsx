import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = {
  transport:   '#3b82f6',
  diet:        '#22c55e',
  electricity: '#f59e0b',
  lpg:         '#ef4444',
}

const CATEGORY_LABELS = {
  transport:   'Transport',
  diet:        'Diet',
  electricity: 'Electricity',
  lpg:         'LPG',
}

function buildChartData(breakdown) {
  return Object.entries(COLORS).map(([key, color]) => ({
    name:  CATEGORY_LABELS[key],
    value: breakdown?.[key] ?? 0,
    color,
  }))
}

function buildAriaLabel(breakdown) {
  if (!breakdown) return 'Simulator breakdown chart loading'
  const { transport, diet, electricity, lpg, total } = breakdown
  return (
    `Simulated CO2 breakdown: Transport ${transport} kg, ` +
    `Diet ${diet} kg, Electricity ${electricity} kg, ` +
    `LPG ${lpg} kg. Total ${total} kg per day.`
  )
}

const renderLabel = ({ name, value }) => `${name}: ${value} kg`

export default function SimulatorBreakdown({ breakdown, isLoading }) {
  const chartData = buildChartData(breakdown)
  const allZero   = chartData.every((d) => d.value === 0)
  const ariaLabel = buildAriaLabel(breakdown)

  if (isLoading) {
    return (
      <div role="img" aria-label="Loading simulator chart" className="h-48 flex items-center justify-center text-gray-400 text-sm">
        Calculating…
      </div>
    )
  }

  if (allZero) {
    return (
      <div role="img" aria-label="No data to display" className="h-48 flex items-center justify-center text-gray-400 text-sm border border-dashed border-gray-300 rounded-xl">
        Move a slider to see your simulated impact
      </div>
    )
  }

  return (
    <div role="img" aria-label={ariaLabel} className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={renderLabel}
            labelLine={false}
          >
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => `${v} kg`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
