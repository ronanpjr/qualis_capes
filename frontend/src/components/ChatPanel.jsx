import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Olá! Sou seu assistente QUALIS CAPES. Como posso ajudar com a classificação de periódicos hoje?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function sendMessage(e) {
    if (e) e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setLoading(true)

    try {
      const BASE_URL = import.meta.env.VITE_API_URL
      const res = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      })

      if (!res.ok) throw new Error('Erro na comunicação com o assistente')

      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', text: data.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Desculpe, ocorreu um erro ao consultar os dados. Tente novamente mais tarde.', isError: true }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '56px',
          height: '56px',
          borderRadius: '28px',
          background: 'var(--primary-700)',
          color: 'var(--white)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          cursor: 'pointer',
          border: 'none',
          transition: 'transform 0.2s, background 0.2s',
          transform: isOpen ? 'scale(0.9)' : 'scale(1)',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--primary-500)'}
        onMouseLeave={e => e.currentTarget.style.background = 'var(--primary-700)'}
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div style={{
          position: 'fixed',
          bottom: '96px',
          right: '24px',
          width: '380px',
          height: '600px',
          maxHeight: 'calc(100vh - 120px)',
          background: 'var(--white)',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 9998,
          overflow: 'hidden',
          border: '1px solid var(--neutral-200)',
        }}>
          {/* Header */}
          <div style={{
            background: 'var(--primary-100)',
            color: 'var(--primary-900)',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
            borderBottom: '1px solid var(--neutral-200)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '4px',
                background: 'var(--accent)',
              }} />
              <div style={{
                fontFamily: 'var(--font-serif)',
                fontWeight: 600,
                fontSize: '15px',
              }}>
                Assistente IA
              </div>
            </div>
            <div style={{
              fontSize: '10px',
              fontWeight: 600,
              color: 'var(--primary-500)',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
              marginLeft: '16px'
            }}>
              Powered by Gemini
            </div>
          </div>

          {/* Messages Area */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            background: 'var(--primary-50)',
          }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  background: msg.role === 'user' ? 'var(--primary-700)' : 'var(--white)',
                  color: msg.role === 'user' ? 'var(--white)' : (msg.isError ? 'var(--danger)' : 'var(--neutral-900)'),
                  padding: '12px 16px',
                  borderRadius: msg.role === 'user' ? '16px 16px 0 16px' : '16px 16px 16px 0',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--neutral-200)',
                  fontSize: '14px',
                  lineHeight: 1.5,
                }}
              >
                {msg.role === 'assistant' ? (
                  <div className="markdown-body" style={{ fontSize: 'inherit' }}>
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                ) : (
                  msg.text
                )}
              </div>
            ))}

            {loading && (
              <div style={{
                alignSelf: 'flex-start',
                background: 'var(--white)',
                padding: '12px 16px',
                borderRadius: '16px 16px 16px 0',
                border: '1px solid var(--neutral-200)',
                color: 'var(--neutral-400)',
                fontSize: '14px',
              }}>
                <span className="dot-flashing">...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form
            onSubmit={sendMessage}
            style={{
              padding: '16px',
              background: 'var(--white)',
              borderTop: '1px solid var(--neutral-200)',
              display: 'flex',
              gap: '8px',
            }}
          >
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Pergunte sobre estratos e áreas…"
              style={{
                flex: 1,
                border: '1px solid var(--neutral-300)',
                padding: '10px 12px',
                borderRadius: '20px',
                outline: 'none',
              }}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '20px',
                background: input.trim() && !loading ? 'var(--primary-700)' : 'var(--neutral-200)',
                color: 'var(--white)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: 'none',
                cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                transition: 'background 0.2s',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: '2px' }}>
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  )
}
