import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { saveRecording } from '../api/client';
import { useState } from 'react';

function formatTime(seconds) {
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  return `${m}:${s}`;
}

export default function AudioRecorder({ onRecorded }) {
  const { isRecording, duration, audioBlob, startRecording, stopRecording } = useAudioRecorder();
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!audioBlob) return;
    setSaving(true);
    try {
      const name = `recording_${new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-')}.webm`;
      await saveRecording(audioBlob, name);
      onRecorded?.();
    } catch (err) {
      alert('Save failed: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="recorder">
      {isRecording ? (
        <>
          <span className="recorder-dot" />
          <span className="recorder-time">{formatTime(duration)}</span>
          <button className="btn btn-danger" onClick={stopRecording}>
            Stop
          </button>
        </>
      ) : (
        <button className="btn btn-record" onClick={startRecording}>
          Record Audio
        </button>
      )}
      {audioBlob && !isRecording && (
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Recording'}
        </button>
      )}
    </div>
  );
}
