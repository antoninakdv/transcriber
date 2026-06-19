function formatTs(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function TranscriptionView({ result }) {
  if (!result) return null;

  return (
    <div className="transcription-view">
      <h3>Transcription</h3>
      <div className="transcription-meta">
        Model: {result.model} &middot; Language: {result.language}
      </div>
      <div className="transcription-segments">
        {result.segments.map((seg, i) => (
          <div key={i} className="segment">
            <span className="segment-time">
              [{formatTs(seg.start)} - {formatTs(seg.end)}]
            </span>
            <span className="segment-text">{seg.text}</span>
          </div>
        ))}
      </div>
      <div className="transcription-full">
        <h4>Full Text</h4>
        <p>{result.text}</p>
      </div>
    </div>
  );
}
