import { useState } from 'react';
import RefinementPanel from './RefinementPanel';
import { exportRefinedDocx, updateTranscription } from '../api/client';

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

  if (!result) return null;

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
          Model: {result.model} &middot; Language: {result.language}
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

      <div className="transcription-segments">
        {displayedResult.segments?.map((seg, i) => (
          <div key={i} className="segment">
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
