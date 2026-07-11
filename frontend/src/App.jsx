import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import NavBar from './components/NavBar.jsx';
import AnalysisPanel from './components/AnalysisPanel.jsx';

const MODES = {
  brainstorming: {
    label: 'Brainstorming',
    title: 'Brainstorming mode',
    howItWorks:
      'The assistant matches your problem against algorithmic patterns in the knowledge base — two pointers, sliding window, DP, graphs, and more — and helps you choose a viable approach.',
    howToUse:
      'Paste the problem statement on the right, describe what you have tried, and ask which technique fits. Code Lock stays on: you will get strategy and questions, not implementation.',
  },
  complexity: {
    label: 'Complexity',
    title: 'Complexity analysis mode',
    howItWorks:
      'The assistant focuses only on asymptotic analysis: time and space complexity, dominant operations, and TLE risk against typical contest limits (~10⁸ ops/s in C++, ~10⁶–10⁷ in Python).',
    howToUse:
      'Describe your approach in plain language or paste your code. Mention the constraint on N and ask whether the solution will pass. AST metadata highlights loop nesting, recursion, and estimated complexity.',
  },
  hint: {
    label: 'Rubber duck',
    title: 'Rubber duck mode',
    howItWorks:
      'The assistant inspects your code structure (Tree-sitter AST) and compares it with similar solved problems to spot logic bugs: off-by-one errors, overflow, wrong edge cases, or a mismatched algorithm.',
    howToUse:
      'Paste your broken code on the right, describe what fails (WA on large tests, TLE, RE), and ask what might be wrong. You get guiding questions and hints — not a patched solution — unless you unlock code.',
  },
};

// root app
export default function App() {
  const [mode, setMode] = useState('brainstorming');
  const [unlocked, setUnlocked] = useState(false);
  const [taskContext, setTaskContext] = useState('');
  const [code, setCode] = useState('');
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [lastMeta, setLastMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const activeMode = MODES[mode];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // send chat message
  async function send() {
    const q = query.trim();
    if (!q || loading) return;
    const userMsg = { role: 'user', content: q };
    setMessages((m) => [...m, userMsg]);
    setQuery('');
    setLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_query: q,
          user_code: code,
          task_context: taskContext,
          current_mode: mode,
          code_unlocked: unlocked,
          history: messages.slice(-10).map(({ role, content }) => ({ role, content })),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages((m) => [...m, { role: 'assistant', content: data.response }]);
      setLastMeta({ retrieved: data.retrieved, analysis: data.code_analysis });
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: `Backend connection error: ${err.message}. Is the FastAPI server running on port 8000?`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <NavBar
        modes={MODES}
        mode={mode}
        setMode={setMode}
        unlocked={unlocked}
        setUnlocked={setUnlocked}
      />

      <div className="statusline">
        <span className={`statusline-lock ${unlocked ? 'open' : ''}`}>
          <span className="lock-dot" />
          {unlocked ? 'Code unlocked' : 'Code Lock active'}
        </span>
      </div>

      <main className="workspace">
        <section className="chat-column">
          <div className="mode-guide">
            <h2 className="mode-guide-title">{activeMode.title}</h2>
            <div className="mode-guide-grid">
              <div className="mode-guide-block">
                <div className="mode-guide-label">How it works</div>
                <p>{activeMode.howItWorks}</p>
              </div>
              <div className="mode-guide-block">
                <div className="mode-guide-label">How to use</div>
                <p>{activeMode.howToUse}</p>
              </div>
            </div>
          </div>

          <div className="chat">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="msg-role">{m.role === 'user' ? 'You' : 'Copilot'}</div>
                <div className="msg-body">
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                </div>
              </div>
            ))}
            {loading && (
              <div className="msg assistant">
                <div className="msg-role">Copilot</div>
                <div className="msg-body typing">Analyzing…</div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="composer">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Ask a question… (Enter = send, Shift+Enter = new line)"
              rows={2}
            />
            <button className="btn-send" onClick={send} disabled={loading || !query.trim()}>
              Send
            </button>
          </div>
        </section>

        <aside className="context-column">
          <label className="field">
            <span>Problem statement</span>
            <textarea
              value={taskContext}
              onChange={(e) => setTaskContext(e.target.value)}
              placeholder="Paste the problem, constraints on N, time limits…"
              rows={5}
            />
          </label>
          <label className="field grow">
            <span>Your code</span>
            <textarea
              className="code-editor"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder={'def solve():\n    ...'}
              spellCheck={false}
            />
          </label>
          <AnalysisPanel meta={lastMeta} />
        </aside>
      </main>
    </div>
  );
}
