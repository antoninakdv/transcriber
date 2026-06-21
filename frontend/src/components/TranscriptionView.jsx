import { useState, useRef } from 'react';
import RefinementPanel from './RefinementPanel';
import { exportRefinedDocx, updateTranscription, getAudioUrl } from '../api/client';

// The engine that produced a transcript. Uses the recorded `engine` field; for
// legacy transcripts saved before it existed, derives it from the model id.
function engineLabel(result) {
  const engine = result.engine
    || (String(result.model || '').toLowerCase().startsWith('voxtral') ? 'voxtral' : 'whisper');
  return engine === 'voxtral' ? 'Mistral (Voxtral)' : 'Local (Whisper)';
}

function formatTs(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function TranscriptionView({ result, fileId, onUpdated }) {
  const [refinedResult, setRefinedResult] = useState(null);
  const [showOriginal, setShowOriginal] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);

  // One shared <audio> element drives every segment snippet (seek + play + auto-stop).
  const audioRef = useRef(null);
  const segmentEndRef = useRef(null); // end time (s) of the segment currently playing
  const [playingSegment, setPlayingSegment] = useState(null);

  if (!result) return null;

  const handlePlaySegment = (index, seg) => {
    const audio = audioRef.current;
    if (!audio) return;
    // Clicking the segment that is currently playing pauses it.
    if (playingSegment === index) {
      audio.pause();
      segmentEndRef.current = null;
      setPlayingSegment(null);
      return;
    }
    // Start or replay this segment: ALWAYS re-seek to its start, remember its end.
    // (After auto-pause playingSegment is null, so a replay also lands here.)
    segmentEndRef.current = seg.end;
    audio.currentTime = seg.start;
    const started = audio.play();
    if (started?.catch) started.catch(() => {}); // ignore interrupted-play rejections
    setPlayingSegment(index);
  };

  // Single React-managed timeupdate handler (no manual add/removeEventListener,
  // so no stacked listeners): pause exactly at the active segment's end and clear
  // the playing state so the next click on that segment is a fresh start.
  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (segmentEndRef.current != null && audio.currentTime >= segmentEndRef.current) {
      audio.pause();
      segmentEndRef.current = null;
      setPlayingSegment(null);
    }
  };

  const handleAudioEnded = () => {
    segmentEndRef.current = null;
    setPlayingSegment(null);
  };

  const handleRefined = (refineResult) => {
    setRefinedResult(refineResult);
    setShowOriginal(false);
  };

  const handleEdit = () => {
    setDraft(result.text);
    setEditing(true);
  };

  const handleCancelEdit = () => setEditing(false);

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      const updated = await updateTranscription(fileId, draft);
      onUpdated?.(updated); // lift the saved transcript so view + downstream stay in sync
      setEditing(false);
    } catch (err) {
      alert('Failed to save transcript: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleExportRefined = async () => {
    if (!refinedResult || !fileId) return;
    setExporting(true);
    try {
      await exportRefinedDocx(fileId, refinedResult.refined_text, refinedResult.mode);
    } catch (err) {
      alert('Failed to export refined transcript: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  const displayedResult = showOriginal ? result : refinedResult;
  const displayText = showOriginal ? result.text : (refinedResult?.refined_text || result.text);

  return (
    <div className="transcription-view">
      <div className="transcription-header">
        <h3>{showOriginal ? 'Transcription' : 'Refined Transcript'}</h3>
        <div className="transcription-meta">
          Engine: {engineLabel(result)} &middot; Model: {result.model} &middot; Language: {result.language}
          {refinedResult && (
            <span> &middot; Refined with: {refinedResult.mode}</span>
          )}
        </div>
      </div>

      {/* Refinement Panel */}
      {fileId && (
        <RefinementPanel 
          fileId={fileId} 
          originalText={result.text}
          onRefined={handleRefined}
          currentModel={result.model}
        />
      )}

      {/* Toggle between original and refined */}
      {refinedResult && (
        <div className="transcription-toggle">
          <button 
            className={`btn btn-sm ${showOriginal ? 'btn-active' : ''}`}
            onClick={() => setShowOriginal(true)}
          >
            Original
          </button>
          <button 
            className={`btn btn-sm ${!showOriginal ? 'btn-active' : ''}`}
            onClick={() => setShowOriginal(false)}
          >
            Refined
          </button>
        </div>
      )}

      {/* Shared audio element for per-segment snippet playback (reuses the file's audio URL). */}
      {fileId && (
        <audio
          ref={audioRef}
          src={getAudioUrl(fileId)}
          preload="metadata"
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleAudioEnded}
        />
      )}

      <div className="transcription-segments">
        {displayedResult.segments?.map((seg, i) => (
          <div key={i} className={`segment ${playingSegment === i ? 'segment--playing' : ''}`}>
            <button
              className="segment-play"
              onClick={() => handlePlaySegment(i, seg)}
              aria-label={playingSegment === i ? 'Stop segment' : 'Play segment'}
              title={playingSegment === i ? 'Stop' : 'Play this segment'}
            >
              {playingSegment === i ? '❚❚' : '▶'}
            </button>
            <span className="segment-time">
              [{formatTs(seg.start)} - {formatTs(seg.end)}]
            </span>
            <span className="segment-text">{seg.text}</span>
          </div>
        ))}
      </div>
      
      <div className="transcription-full">
        <div className="transcription-full-header">
          <h4>Full Text{showOriginal && result.edited ? ' (edited)' : ''}</h4>
          {showOriginal && fileId && !editing && (
            <button className="btn btn-sm" onClick={handleEdit}>Edit</button>
          )}
        </div>

        {showOriginal && editing ? (
          <div className="transcript-edit">
            <textarea
              className="transcript-edit-area"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={12}
              disabled={saving}
            />
            <div className="settings-actions">
              <button className="btn btn-sm btn-primary" onClick={handleSaveEdit} disabled={saving}>
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button className="btn btn-sm" onClick={handleCancelEdit} disabled={saving}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="transcription-text-content">
            {!showOriginal && refinedResult?.metadata?.output_format === 'json' ? (
              <pre className="transcription-json">{displayText}</pre>
            ) : (
              <p>{displayText}</p>
            )}
          </div>
        )}

        {refinedResult && !showOriginal && (
          <div className="refined-actions">
            <button 
              className="btn btn-sm btn-primary"
              onClick={handleExportRefined}
              disabled={exporting}
            >
              {exporting ? 'Exporting...' : 'Export Refined DOCX'}
            </button>
            <div className="refined-meta">
              <small>
                Model used: {refinedResult.metadata?.model_used || 'unknown'}
                {refinedResult.metadata?.temperature_used && 
                  `, Temperature: ${refinedResult.metadata.temperature_used}`}
              </small>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
