/**
 * OnboardingForm.jsx — JSX-only onboarding page.
 *
 * All logic lives in useOnboardingForm.js.
 * This file: imports, sub-components, and the main return — nothing else.
 * CODING_STANDARDS.md §2: Tailwind only, no logic in JSX, props destructured.
 */

import { useOnboardingForm } from '../hooks/useOnboardingForm'

// ── Shared class strings ──────────────────────────────────────────────────────

const INPUT_CLS =
  'w-full px-3 py-2 text-base text-gray-800 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 min-h-[44px] bg-white'
const LABEL_CLS = 'block text-sm font-medium text-gray-700 mb-1'
const ERROR_CLS = 'text-sm text-red-700 mt-1'
const FIELD_CLS = 'flex flex-col gap-0.5'

// ── Reusable sub-components ───────────────────────────────────────────────────

function FieldError({ id, message }) {
  if (!message) return null
  return <p id={id} role="alert" className={ERROR_CLS}>{message}</p>
}

function TextInput({ id, label, value, onChange, onBlur, error, ...rest }) {
  const errId = `${id}-error`
  return (
    <div className={FIELD_CLS}>
      <label htmlFor={id} className={LABEL_CLS}>{label}</label>
      <input
        id={id} name={id} value={value}
        onChange={onChange} onBlur={onBlur}
        aria-describedby={error ? errId : undefined}
        aria-invalid={Boolean(error)}
        className={INPUT_CLS}
        {...rest}
      />
      <FieldError id={errId} message={error} />
    </div>
  )
}

function SelectInput({ id, label, value, onChange, onBlur, error, options }) {
  const errId = `${id}-error`
  return (
    <div className={FIELD_CLS}>
      <label htmlFor={id} className={LABEL_CLS}>{label}</label>
      <select
        id={id} name={id} value={value}
        onChange={onChange} onBlur={onBlur}
        aria-describedby={error ? errId : undefined}
        aria-invalid={Boolean(error)}
        className={INPUT_CLS}
      >
        {options.map(({ value: v, label: l }) => (
          <option key={v} value={v} disabled={v === ''}>{l}</option>
        ))}
      </select>
      <FieldError id={errId} message={error} />
    </div>
  )
}

// ── Select options ─────────────────────────────────────────────────────────────

const COMMUTE_OPTIONS = [
  { value: '', label: 'Select how you get around' },
  { value: 'petrol_car', label: 'Petrol Car' },
  { value: 'diesel_car', label: 'Diesel Car' },
  { value: 'petrol_two_wheeler', label: 'Petrol Two-Wheeler' },
  { value: 'electric_vehicle', label: 'Electric Vehicle' },
  { value: 'auto_rickshaw', label: 'Auto-Rickshaw' },
  { value: 'bus', label: 'Bus' },
  { value: 'metro', label: 'Metro / Local Train' },
  { value: 'walking', label: 'Walking' },
  { value: 'cycling', label: 'Cycling' },
]

const DIET_OPTIONS = [
  { value: '', label: 'Select your diet type' },
  { value: 'non_vegetarian', label: 'Non-Vegetarian' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'eggetarian', label: 'Eggetarian' },
  { value: 'vegan', label: 'Vegan' },
]

const PERSONA_OPTIONS = [
  { value: '', label: 'Describe yourself' },
  { value: 'student', label: 'Student' },
  { value: 'professional', label: 'Working Professional' },
  { value: 'family', label: 'Family / Parent' },
  { value: 'teenager', label: 'Teenager' },
  { value: 'senior', label: 'Senior / Retired' },
]

// ── Main component ────────────────────────────────────────────────────────────

export default function OnboardingForm() {
  const {
    fields, errors, networkError, isLoading,
    honeypot, setHoneypot,
    handleChange, handleBlur, handleSubmit,
  } = useOnboardingForm()

  const buttonText = isLoading ? 'Saving...' : 'Save my habits'

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-start px-4 py-8">
      <main id="main-content" className="w-full max-w-lg" tabIndex="-1">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800">
            Let's get your carbon baseline 🌿
          </h1>
          <p className="text-base text-gray-500 mt-1">
            Takes 2 minutes — we only ask what we need
          </p>
        </header>

        <div aria-live="assertive" aria-atomic="true" className="mb-4">
          {networkError && (
            <div role="alert" className="px-4 py-3 bg-red-50 border border-red-300 rounded-lg text-sm text-red-700">
              {networkError}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-6">
          <input
            type="text" name="website" value={honeypot}
            onChange={(e) => setHoneypot(e.target.value)}
            tabIndex="-1" aria-hidden="true" autoComplete="off"
            aria-label="Website"
            className="sr-only"
          />

          <fieldset className="flex flex-col gap-4 border-0 p-0 m-0">
            <legend className="text-base font-semibold text-gray-700 mb-2">About you</legend>
            <TextInput id="name"    label="Your name" value={fields.name}    onChange={handleChange} onBlur={handleBlur} error={errors.name}    type="text"   maxLength={100} autoComplete="given-name" />
            <TextInput id="state"   label="State"     value={fields.state}   onChange={handleChange} onBlur={handleBlur} error={errors.state}   type="text"   maxLength={50}  autoComplete="address-level1" />
            <TextInput id="city"    label="City"      value={fields.city}    onChange={handleChange} onBlur={handleBlur} error={errors.city}    type="text"   maxLength={50}  autoComplete="address-level2" />
            <SelectInput id="persona" label="I'm a..." value={fields.persona} onChange={handleChange} onBlur={handleBlur} error={errors.persona} options={PERSONA_OPTIONS} />
          </fieldset>

          <fieldset className="flex flex-col gap-4 border-0 p-0 m-0">
            <legend className="text-base font-semibold text-gray-700 mb-2">How you get around</legend>
            <SelectInput id="commute_mode" label="Main way of getting around" value={fields.commute_mode} onChange={handleChange} onBlur={handleBlur} error={errors.commute_mode} options={COMMUTE_OPTIONS} />
            <TextInput id="avg_daily_km" label="Average daily distance (km)" value={fields.avg_daily_km} onChange={handleChange} onBlur={handleBlur} error={errors.avg_daily_km} type="number" min={0} max={500} step={0.1} />
          </fieldset>

          <fieldset className="flex flex-col gap-4 border-0 p-0 m-0">
            <legend className="text-base font-semibold text-gray-700 mb-2">Home energy use</legend>
            <TextInput id="ac_hours_per_day"          label="AC hours per day"                value={fields.ac_hours_per_day}          onChange={handleChange} onBlur={handleBlur} error={errors.ac_hours_per_day}          type="number" min={0} max={24}    step={0.5} />
            <TextInput id="monthly_electricity_units" label="Monthly electricity units (kWh)" value={fields.monthly_electricity_units} onChange={handleChange} onBlur={handleBlur} error={errors.monthly_electricity_units} type="number" min={0} max={10000} step={1} />
            <TextInput id="lpg_cylinders_per_month"   label="LPG cylinders per month"         value={fields.lpg_cylinders_per_month}   onChange={handleChange} onBlur={handleBlur} error={errors.lpg_cylinders_per_month}   type="number" min={0} max={10}    step={0.5} />
          </fieldset>

          <fieldset className="flex flex-col gap-4 border-0 p-0 m-0">
            <legend className="text-base font-semibold text-gray-700 mb-2">What you eat</legend>
            <SelectInput id="diet_type" label="Diet type" value={fields.diet_type} onChange={handleChange} onBlur={handleBlur} error={errors.diet_type} options={DIET_OPTIONS} />
          </fieldset>

          <button
            type="submit" disabled={isLoading} aria-busy={isLoading}
            className="w-full py-3 px-6 text-base font-semibold text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 rounded-xl min-h-[44px] transition-colors duration-200"
          >
            {buttonText}
          </button>
        </form>
      </main>
    </div>
  )
}
