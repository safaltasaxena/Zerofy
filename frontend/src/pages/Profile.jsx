import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProfile, getGamification } from '../utils/api'
import BadgeShelf from '../components/BadgeShelf'

export default function Profile() {
  const [profileData, setProfileData] = useState(null)
  const [gamificationData, setGamificationData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const navigate = useNavigate()
  const userId = localStorage.getItem('zerofy_user_id')

  useEffect(() => {
    async function fetchProfileAndGamification() {
      try {
        setLoading(true)
        setError(null)
        // Parallel API calls using Promise.all per budget (PROF-04)
        const [profile, gamification] = await Promise.all([
          getProfile(),
          getGamification(userId),
        ])
        setProfileData(profile)
        setGamificationData(gamification)
      } catch (err) {
        setError(err.message || 'Could not load profile data.')
      } finally {
        setLoading(false)
      }
    }

    fetchProfileAndGamification()
  }, [userId])

  const handleUpdateClick = () => {
    navigate('/onboarding')
  }

  // Pre-calculate readable labels to avoid logic in JSX return
  const name = profileData?.name || 'User'
  const locationText = profileData?.city && profileData?.state
    ? `${profileData.city}, ${profileData.state}`
    : profileData?.state || profileData?.city || 'No location set'
  
  const commuteText = profileData?.commute_mode
    ? `${profileData.commute_mode.replace('_', ' ')} (${profileData.avg_daily_km || 0} km/day)`
    : 'Not set'
  const dietText = profileData?.diet_type || 'Not set'
  const acText = profileData?.ac_hours_per_day !== undefined
    ? `${profileData.ac_hours_per_day} hrs/day`
    : 'Not set'
  const lpgText = profileData?.lpg_cylinders_per_month !== undefined
    ? `${profileData.lpg_cylinders_per_month} cylinders/month`
    : 'Not set'

  const streak = gamificationData?.log_streak || 0
  const points = gamificationData?.awareness_score || 0
  const badges = gamificationData?.badges || []

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6" aria-busy="true">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">My Profile</h1>
        <div className="text-gray-500 animate-pulse">Loading profile details...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">My Profile</h1>
        <div className="text-red-600 bg-red-50 px-4 py-3 rounded-xl border border-red-150 max-w-md text-center" role="alert">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-50 p-6">
      <div className="w-full max-w-md flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
          <button
            type="button"
            className="px-4 py-2 text-sm font-semibold bg-green-600 hover:bg-green-700 text-white rounded-xl shadow-sm min-h-[44px] transition-colors"
            onClick={handleUpdateClick}
          >
            Update my habits
          </button>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-150 flex flex-col gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{name}</h2>
            <p className="text-sm text-gray-500 font-medium">{locationText}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 border-y border-gray-100 py-4">
            <div className="flex flex-col">
              <span className="text-xs text-gray-400 font-bold uppercase tracking-wider">Streak</span>
              <span className="text-xl font-extrabold text-orange-600">🔥 {streak} days</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-400 font-bold uppercase tracking-wider">Points</span>
              <span className="text-xl font-extrabold text-green-700">🏆 {points} pts</span>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Current Habits</h3>
            <ul className="flex flex-col gap-2 text-sm text-gray-700">
              <li className="flex justify-between py-1 border-b border-gray-50">
                <span className="font-medium">Commute:</span>
                <span className="text-gray-900 capitalize">{commuteText}</span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-50">
                <span className="font-medium">Diet Type:</span>
                <span className="text-gray-900 capitalize">{dietText}</span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-50">
                <span className="font-medium">AC Usage:</span>
                <span className="text-gray-900">{acText}</span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-50">
                <span className="font-medium">LPG Usage:</span>
                <span className="text-gray-900">{lpgText}</span>
              </li>
            </ul>
          </div>

          <div className="flex flex-col gap-3 pt-2">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Badges Earned</h3>
            <BadgeShelf badges={badges} />
          </div>
        </div>
      </div>
    </div>
  )
}
