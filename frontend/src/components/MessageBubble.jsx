export default function MessageBubble({ message, isBot }) {
  return (
    <div className={`flex w-full mb-4 ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div 
        className={`max-w-[80%] rounded-xl px-4 py-3 min-h-[44px] flex items-center ${
          isBot ? 'bg-gray-200 text-gray-900 rounded-bl-none' : 'bg-green-600 text-white rounded-br-none'
        }`}
      >
        <p className="whitespace-pre-wrap">{message}</p>
      </div>
    </div>
  )
}
