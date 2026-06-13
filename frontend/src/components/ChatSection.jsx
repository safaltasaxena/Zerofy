import { useState, useRef, useEffect } from 'react'
import { useChatSession } from '../hooks/useChatSession'
import MessageBubble from './MessageBubble'
import ParsePreview from './ParsePreview'
import QuickUpdateForm from './QuickUpdateForm'

export default function ChatSection({ userId, profile, onUpdateConfirmed }) {
  const {
    messages,
    isLoading,
    showPreview,
    previewData,
    showQuickForm,
    prefillData,
    handleSend,
    handleConfirm,
    handleEdit,
    handleQuickSubmit,
  } = useChatSession({ profile, onUpdateConfirmed })

  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, showPreview, showQuickForm])

  const onSubmit = (e) => {
    e?.preventDefault()
    if (!input.trim() || input.length > 500 || isLoading) return
    handleSend(input)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSubmit()
    }
  }

  return (
    <section className="flex flex-col h-[600px] max-h-screen bg-gray-50 border rounded-xl overflow-hidden relative" aria-label="Chat Update">
      <div role="log" aria-live="polite" className="flex-1 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m.text} isBot={m.isBot} />
        ))}
        {showPreview && previewData && (
          <ParsePreview preview={previewData} onConfirm={handleConfirm} onEdit={handleEdit} />
        )}
        {showQuickForm && prefillData && (
          <QuickUpdateForm prefills={prefillData} onSubmit={handleQuickSubmit} isLoading={isLoading} />
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white border-t sticky bottom-0">
        <form onSubmit={onSubmit} className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value.slice(0, 500))}
              onKeyDown={handleKeyDown}
              disabled={isLoading || showPreview || showQuickForm}
              maxLength={500}
              placeholder="Tell me about your day..."
              aria-label="Chat input"
              className="w-full border rounded-xl p-3 min-h-[44px] max-h-32 resize-none disabled:opacity-50 pr-12"
              rows={1}
            />
            <div className="absolute right-2 bottom-2 text-xs text-gray-400">
              {input.length}/500
            </div>
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading || showPreview || showQuickForm}
            aria-label="Send"
            className="bg-green-600 text-white rounded-xl min-h-[44px] min-w-[44px] px-4 font-medium disabled:opacity-50 flex items-center justify-center mb-1 hover:bg-green-700 transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </section>
  )
}
