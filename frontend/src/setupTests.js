import '@testing-library/jest-dom'

// Polyfill ResizeObserver for JSDOM / ResponsiveContainer compatibility
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
