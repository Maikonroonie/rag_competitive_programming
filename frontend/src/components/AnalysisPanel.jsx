// ast and rag panel
export default function AnalysisPanel({ meta }) {
  if (!meta) return null;
  const { retrieved = [], analysis } = meta;

  return (
    <div className="analysis-panel">
      {analysis && analysis.language && (
        <div className="panel-block">
          <div className="panel-title">AST analysis (Tree-sitter)</div>
          <ul className="ast-list">
            <li><b>Language:</b> {analysis.language}</li>
            <li><b>Functions:</b> {analysis.functions.join(', ') || '—'}</li>
            <li><b>Loops:</b> {analysis.loop_count} (nesting {analysis.max_loop_nesting})</li>
            <li><b>Recursion:</b> {analysis.recursion ? 'yes' : 'no'}</li>
            <li><b>Est. complexity:</b> {analysis.estimated_complexity}</li>
          </ul>
          {analysis.warnings.length > 0 && (
            <ul className="warnings">
              {analysis.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {retrieved.length > 0 && (
        <div className="panel-block">
          <div className="panel-title">Knowledge base sources</div>
          {retrieved.map((d, i) => (
            <div key={i} className="source-chip" title={d.snippet}>
              <span className={`kind kind-${d.kind}`}>{d.kind}</span>
              <span className="source-title">{d.title}</span>
              <span className="score">{d.score.toFixed(2)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
