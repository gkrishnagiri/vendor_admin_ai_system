import React, { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import { Send, Trash2, Bot, User, Terminal, Coins, Zap, Clipboard, Copy, Check } from 'lucide-react'
import DynamicForm from './components/DynamicForm'

// ── Token cost table (USD per 1K tokens) ─────────────────────────────────────
// Prices sourced from OpenAI pricing page (gpt-4o-mini defaults)
const MODEL_COSTS = {
  'gpt-4o-mini':      { input: 0.000150, output: 0.000600 },   // per 1K tokens
  'gpt-4o':           { input: 0.002500, output: 0.010000 },
  'gpt-4':            { input: 0.030000, output: 0.060000 },
  'gpt-4-turbo':      { input: 0.010000, output: 0.030000 },
  'gpt-3.5-turbo':    { input: 0.000500, output: 0.001500 },
}
const DEFAULT_COST = { input: 0.000150, output: 0.000600 }

function calcCost(usage, model = '') {
  const rate = MODEL_COSTS[model] || DEFAULT_COST
  const inputCost  = (usage.prompt_tokens     || 0) / 1000 * rate.input
  const outputCost = (usage.completion_tokens || 0) / 1000 * rate.output
  return inputCost + outputCost
}

function fmtCost(usd) {
  if (usd === 0) return '$0.000000'
  if (usd < 0.000001) return `<$0.000001`
  return `$${usd.toFixed(6)}`
}

function fmtNum(n) {
  return n == null ? '—' : n.toLocaleString()
}

// ── Minimal markdown renderer ─────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return null
  const lines = text.split('\n')
  const elements = []
  let listItems = []
  let listType = null

  const flushList = (key) => {
    if (listItems.length === 0) return
    const Tag = listType === 'ol' ? 'ol' : 'ul'
    elements.push(
      <Tag key={`list-${key}`} style={{ paddingLeft: '1.4em', margin: '6px 0' }}>
        {listItems.map((li, i) => <li key={i}>{inlineFormat(li)}</li>)}
      </Tag>
    )
    listItems = []
    listType = null
  }

  lines.forEach((line, i) => {
    const olMatch = line.match(/^(\d+)\.\s+(.+)/)
    const ulMatch = line.match(/^[-*]\s+(.+)/)
    if (olMatch) {
      if (listType !== 'ol') { flushList(i); listType = 'ol' }
      listItems.push(olMatch[2])
    } else if (ulMatch) {
      if (listType !== 'ul') { flushList(i); listType = 'ul' }
      listItems.push(ulMatch[1])
    } else {
      flushList(i)
      if (line.trim() === '') {
        elements.push(<br key={i} />)
      } else if (line.startsWith('### ')) {
        elements.push(<h4 key={i} style={{ fontWeight: 600, margin: '10px 0 4px' }}>{line.slice(4)}</h4>)
      } else if (line.startsWith('## ')) {
        elements.push(<h3 key={i} style={{ fontWeight: 700, margin: '12px 0 4px' }}>{line.slice(3)}</h3>)
      } else if (line.startsWith('# ')) {
        elements.push(<h2 key={i} style={{ fontWeight: 700, margin: '14px 0 6px' }}>{line.slice(2)}</h2>)
      } else {
        elements.push(<p key={i} style={{ margin: '4px 0' }}>{inlineFormat(line)}</p>)
      }
    }
  })
  flushList('end')
  return elements
}

function inlineFormat(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={i} style={{ background: 'rgba(0,0,0,0.08)', borderRadius: 3, padding: '1px 4px', fontFamily: 'monospace', fontSize: '0.9em' }}>{part.slice(1, -1)}</code>
    return part
  })
}

// ── Token / Cost meta pill shown beneath each bubble ─────────────────────────
function TokenMeta({ usage, model, label, accent }) {
  if (!usage || !usage.total_tokens) return null
  const cost = calcCost(usage, model)
  return (
    <div className={`token-meta ${accent ? 'accent' : ''}`} title={label}>
      <span className="token-meta-chip">
        <Zap size={10} />
        {label === 'request' && <span>{fmtNum(usage.prompt_tokens)} in</span>}
        {label === 'response' && (
          <>
            <span>{fmtNum(usage.prompt_tokens)} in</span>
            <span className="token-sep">+</span>
            <span>{fmtNum(usage.completion_tokens)} out</span>
            <span className="token-sep">=</span>
            <span>{fmtNum(usage.total_tokens)} total</span>
          </>
        )}
      </span>
      <span className="token-meta-chip cost">
        <Coins size={10} />
        {fmtCost(cost)}
      </span>
    </div>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button className="copy-btn" onClick={handleCopy} title="Copy to clipboard">
      {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
    </button>
  )
}

export default function ChatPanel() {
  // { role, content, sources, status, usage, model }
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [debugLines, setDebugLines] = useState([])
  const [showDebug, setShowDebug] = useState(true)
  const [splitPct, setSplitPct]   = useState(65)
  const [llmModel, setLlmModel]   = useState('gpt-4o-mini')

  // Conversation-level token accumulators
  const [convUsage, setConvUsage] = useState({ prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 })
  const [convCost,  setConvCost]  = useState(0)

  // Track the most-recent exchange's usage/cost for the header bar
  const [lastUsage, setLastUsage] = useState(null)
  const [lastCost,  setLastCost]  = useState(null)

  const chatEndRef   = useRef(null)
  const debugEndRef  = useRef(null)
  const containerRef = useRef(null)
  const dragging     = useRef(false)

  // Fetch settings on mount
  useEffect(() => {
    axios.get('/api/settings')
      .then(res => {
        const val = res.data?.show_debug_panel
        if (val !== undefined) setShowDebug(val === 'true' || val === true)
        if (res.data?.llm_model) setLlmModel(res.data.llm_model)
      })
      .catch(() => {})
  }, [])

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])
  useEffect(() => { debugEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [debugLines])

  // Divider drag
  const onMouseDown = useCallback((e) => { e.preventDefault(); dragging.current = true }, [])
  const onMouseMove = useCallback((e) => {
    if (!dragging.current || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const pct = ((e.clientX - rect.left) / rect.width) * 100
    setSplitPct(Math.min(85, Math.max(25, pct)))
  }, [])
  const onMouseUp = useCallback(() => { dragging.current = false }, [])

  useEffect(() => {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [onMouseMove, onMouseUp])

  // ── Send message ────────────────────────────────────────────────────────────
  const sendMessage = async (overrideText = null, hidden = false) => {
    const text = typeof overrideText === 'string' ? overrideText.trim() : input.trim()
    if (!text || loading) return

    // Snapshot of input tokens for the user bubble (estimated as prompt = all tokens sent)
    if (!hidden) {
      const userMsg = { role: 'user', content: text }
      setMessages(prev => [...prev, userMsg])
    }
    setInput('')
    setLoading(true)

    const history = messages.map(m => ({ role: m.role, content: m.content }))

    try {
      setDebugLines(prev => [...prev, `── Query: ${text} ──`])

      const res = await fetch('/api/v2/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, history })
      })

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)

      const reader  = res.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop()

        for (const chunk of chunks) {
          if (chunk.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(chunk.substring(6))

              if (parsed.type === 'log') {
                if (parsed.content && parsed.content.trim() !== '') {
                  const splitLines = parsed.content.split('\n').filter(l => l.trim().length > 0)
                  setDebugLines(prev => [...prev, ...splitLines])
                }

              } else if (parsed.type === 'result') {
                const data = parsed.payload
                const safeData = { ...data }
                const planData = safeData.plan // preserve before delete
                delete safeData.debug_log
                delete safeData.plan
                delete safeData.execution

                const answerText = data.answer || (data.status === 'NO_CONTEXT'
                  ? "I couldn't find relevant information for your query in the knowledge base."
                  : JSON.stringify(safeData))

                const usage = data.usage || {}

                // Update user bubble with the input token count (prompt_tokens from response)
                setMessages(prev => {
                  const arr = [...prev]
                  // Find the last user message and attach request usage
                  for (let i = arr.length - 1; i >= 0; i--) {
                    if (arr[i].role === 'user') {
                      arr[i] = { ...arr[i], usage: { prompt_tokens: usage.prompt_tokens || 0 }, model: llmModel }
                      break
                    }
                  }
                  return arr
                })

                // Push assistant bubble with full usage
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: answerText,
                  sources: data.sources || [],
                  status: data.status,
                  form_schema: data.form_schema,
                  plan: planData || data.plan,
                  usage,
                  model: llmModel
                }])

                // Update last exchange stats
                const cost = calcCost(usage, llmModel)
                setLastUsage(usage)
                setLastCost(cost)

                // Accumulate conversation totals
                setConvUsage(prev => ({
                  prompt_tokens:     (prev.prompt_tokens     || 0) + (usage.prompt_tokens     || 0),
                  completion_tokens: (prev.completion_tokens || 0) + (usage.completion_tokens || 0),
                  total_tokens:      (prev.total_tokens      || 0) + (usage.total_tokens      || 0),
                }))
                setConvCost(prev => prev + cost)

              } else if (parsed.type === 'error') {
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: `Error: ${parsed.error}`,
                  status: 'ERROR'
                }])
              }
            } catch(e) {
              console.error('Failed to parse SSE JSON', e)
            }
          }
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}`,
        status: 'ERROR'
      }])
      setDebugLines(prev => [...prev, `[ERROR] ${err.message}`, ''])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(null) }
  }

  const clearChat = () => {
    setMessages([])
    setDebugLines([])
    setConvUsage({ prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 })
    setConvCost(0)
    setLastUsage(null)
    setLastCost(null)
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="chat-page">
      {/* Header */}
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Bot size={22} color="var(--accent)" />
          <span className="page-title" style={{ marginBottom: 0, fontSize: '1.4rem' }}>AI Agent Chat</span>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {messages.filter(m => m.role === 'assistant').length} response(s)
          </span>
          <button className="btn btn-danger" style={{ padding: '8px 14px', fontSize: '0.85rem' }} onClick={clearChat}>
            <Trash2 size={14} /> Clear
          </button>
        </div>
      </div>

      {/* Token / Cost status bar */}
      {(lastUsage || convUsage.total_tokens > 0) && (
        <div className="token-status-bar">
          {/* Last request+response */}
          {lastUsage && (
            <div className="token-status-group">
              <span className="token-status-label">Last exchange</span>
              <span className="token-status-chip">
                <Zap size={11} />
                {fmtNum(lastUsage.prompt_tokens)} in
                <span className="token-sep">+</span>
                {fmtNum(lastUsage.completion_tokens)} out
                <span className="token-sep">=</span>
                <strong>{fmtNum(lastUsage.total_tokens)}</strong> tokens
              </span>
              <span className="token-status-chip cost">
                <Coins size={11} />
                {fmtCost(lastCost)}
              </span>
            </div>
          )}
          <div className="token-status-divider" />
          {/* Conversation total */}
          <div className="token-status-group">
            <span className="token-status-label">Conversation total</span>
            <span className="token-status-chip">
              <Zap size={11} />
              {fmtNum(convUsage.prompt_tokens)} in
              <span className="token-sep">+</span>
              {fmtNum(convUsage.completion_tokens)} out
              <span className="token-sep">=</span>
              <strong>{fmtNum(convUsage.total_tokens)}</strong> tokens
            </span>
            <span className="token-status-chip cost">
              <Coins size={11} />
              <strong>{fmtCost(convCost)}</strong>
            </span>
          </div>
        </div>
      )}

      {/* Split pane container */}
      <div className="chat-split-container" ref={containerRef}>

        {/* ── Left: Chat pane ── */}
        <div className="chat-pane" style={{ width: showDebug ? `${splitPct}%` : '100%' }}>
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <Bot size={48} color="var(--accent)" opacity={0.4} />
                <p>Ask anything about your knowledge base.</p>
                <p style={{ fontSize: '0.85rem', opacity: 0.6 }}>e.g. "How do I add a new vendor?" or "What are the steps to approve a purchase order?"</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-bubble-row ${msg.role}`}>
                <div className="chat-avatar">
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className="chat-bubble-wrapper">
                  <div className={`chat-bubble ${msg.role}`}>
                    <div style={{ position: 'absolute', top: 5, right: 5, zIndex: 10 }}>
                      <CopyButton text={msg.content} />
                    </div>
                    {msg.role === 'user'
                      ? msg.content
                      : (
                        <div className="chat-answer">
                          {renderMarkdown(msg.content)}
                          {msg.status === 'CLARIFICATION_REQUIRED' && msg.form_schema && (
                            <DynamicForm 
                              schema={msg.form_schema} 
                              onSubmit={(data) => {
                                const formText = Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(', ');
                                // Send only the extracted key-value pairs; history gives the LLM full context
                                sendMessage(formText);
                              }}
                              onClear={() => setInput('')}
                            />
                          )}
                          {msg.status === 'PLAN_APPROVAL_REQUIRED' && msg.plan && (
                            <div style={{ marginTop: 15, background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 6, padding: '12px 16px' }}>
                              <h4 style={{ margin: '0 0 10px', color: 'var(--accent)' }}>Proposed Action Plan</h4>
                              <div style={{ fontSize: '0.9em', marginBottom: 15, color: 'var(--text-main)' }}>
                                {renderMarkdown(msg.plan)}
                              </div>
                              <div style={{ display: 'flex', gap: 10 }}>
                                <button className="btn btn-primary" onClick={() => {
                                  const lastUserQuery = messages.filter(m => m.role === 'user').pop().content;
                                  sendMessage(`/execute-approved-plan ${lastUserQuery}`, true);
                                }}>Approve & Execute</button>
                                <button className="btn" style={{ background: 'var(--border)', color: 'var(--text-main)' }} onClick={() => {
                                  sendMessage('Cancel execution');
                                }}>Cancel</button>
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    }
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="chat-sources">
                        Sources: {[...new Set(msg.sources)].map((s, i) => (
                          <span key={i} className="badge" style={{ marginLeft: 4 }}>{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  {/* Per-message token metadata */}
                  {msg.usage && msg.role === 'user' && (
                    <div className="token-meta user-meta">
                      <span className="token-meta-chip">
                        <Zap size={10} />
                        <span>{fmtNum(msg.usage.prompt_tokens)} input tokens</span>
                      </span>
                    </div>
                  )}
                  {msg.usage && msg.role === 'assistant' && (
                    <div className="token-meta assistant-meta">
                      <span className="token-meta-chip">
                        <Zap size={10} />
                        <span>{fmtNum(msg.usage.prompt_tokens)} in</span>
                        <span className="token-sep">+</span>
                        <span>{fmtNum(msg.usage.completion_tokens)} out</span>
                        <span className="token-sep">=</span>
                        <span>{fmtNum(msg.usage.total_tokens)} tokens</span>
                      </span>
                      <span className="token-meta-chip cost">
                        <Coins size={10} />
                        {fmtCost(calcCost(msg.usage, msg.model))}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble-row assistant">
                <div className="chat-avatar"><Bot size={16} /></div>
                <div className="chat-bubble assistant">
                  <div className="typing-indicator">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input-bar">
            <textarea
              className="chat-textarea"
              rows={1}
              placeholder="Type your question... (Enter to send, Shift+Enter for newline)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button 
              className="btn" 
              style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', padding: '0 8px' }}
              onClick={async () => {
                const text = await navigator.clipboard.readText();
                setInput(prev => prev + text);
              }}
              title="Paste from clipboard"
            >
              <Clipboard size={18} />
            </button>
            <button className="btn chat-send-btn" onClick={sendMessage} disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </div>
        </div>

        {/* ── Draggable divider ── */}
        {showDebug && (
          <div className="chat-divider" onMouseDown={onMouseDown}>
            <div className="chat-divider-handle" />
          </div>
        )}

        {/* ── Right: Debug pane ── */}
        {showDebug && (
          <div className="debug-pane" style={{ width: `${100 - splitPct}%` }}>
            <div className="debug-header">
              <Terminal size={14} />
              <span>Debug / Print Output</span>
              {debugLines.length > 0 && (
                <button
                  onClick={() => setDebugLines([])}
                  style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#6b7', cursor: 'pointer', fontSize: '0.75rem' }}
                >
                  Clear
                </button>
              )}
            </div>
            <div className="debug-log">
              {debugLines.length === 0
                ? <span style={{ opacity: 0.4 }}>No debug output yet...</span>
                : debugLines.map((line, i) => (
                  <div key={i} className={`debug-line ${line.startsWith('[ERROR]') ? 'error' : line.startsWith('──') ? 'separator' : ''}`}>
                    {line || '\u00A0'}
                  </div>
                ))
              }
              <div ref={debugEndRef} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
