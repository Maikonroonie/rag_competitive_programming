const UNLOCK_TOOLTIP = {
  locked:
    'Removes Code Lock. The assistant can then generate full reference solutions from the knowledge base. Use only after you have tried solving the problem yourself.',
  unlocked:
    'Re-enables Code Lock. The assistant goes back to hints and natural-language guidance only — no code blocks.',
};

// top navbar
export default function NavBar({ modes, mode, setMode, unlocked, setUnlocked }) {
  return (
    <header className="navbar">
      <div className="nav-left">
        <span className="brand-mark">⟨/⟩</span>
        <span className="brand-name">CP&nbsp;Copilot</span>
      </div>

      <nav className="mode-pill" aria-label="Work mode">
        {Object.entries(modes).map(([key, m]) => (
          <button
            key={key}
            className={`pill-item ${mode === key ? 'active' : ''}`}
            onClick={() => setMode(key)}
          >
            {m.label}
          </button>
        ))}
      </nav>

      <div className="nav-right">
        <div className="tooltip-wrap">
          <button
            className={`btn-unlock ${unlocked ? 'is-open' : ''}`}
            onClick={() => setUnlocked(!unlocked)}
            aria-describedby="unlock-tooltip"
          >
            {unlocked ? 'Lock code' : 'Unlock code'}
          </button>
          <div id="unlock-tooltip" className="tooltip" role="tooltip">
            {unlocked ? UNLOCK_TOOLTIP.unlocked : UNLOCK_TOOLTIP.locked}
          </div>
        </div>
      </div>
    </header>
  );
}
