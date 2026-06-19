import { useState } from 'react';
import { getAudioUrl, deleteFile, exportDocx, getTranscriptionResult } from '../api/client';
import { useTranscription } from '../hooks/useTranscription';
import ProgressBar from './ProgressBar';
import TranscriptionView from './TranscriptionView';

export default function FileList({ files, onRefresh, currentModel }) {
  const [selectedId, setSelectedId] = useState(null);
  const [transcriptionResult, setTranscriptionResult] = useState(null);
  const [playingId, setPlayingId] = useState(null);
  const { status, progress, error, transcribe, reset } = useTranscription();
  const [transcribingId, setTranscribingId] = useState(null);

  const handleTranscribe = (fileId) => {
    setTranscribingId(fileId);
    setSelectedId(fileId);
    setTranscriptionResult(null);
    reset();
    transcribe(fileId, currentModel, async () => {
      const result = await getTranscriptionResult(fileId);
      setTranscriptionResult(result);
      onRefresh?.();
    });
  };

  const handleView = async (fileId) => {
    setSelectedId(fileId);
    setTranscribingId(null);
    reset();
    try {
      const result = await getTranscriptionResult(fileId);
      setTranscriptionResult(result);
    } catch {
      setTranscriptionResult(null);
    }
  };

  const handleDelete = async (fileId) => {
    if (!confirm('Delete this file?')) return;
    await deleteFile(fileId);
    if (selectedId === fileId) {
      setSelectedId(null);
      setTranscriptionResult(null);
    }
    onRefresh?.();
  };

  const handleExport = async (fileId) => {
    try {
      await exportDocx(fileId);
    } catch {
      alert('Export failed. Make sure the file has been transcribed first.');
    }
  };

  if (!files.length) {
    return <p className="empty-state">No files yet. Upload or record something to get started.</p>;
  }

  return (
    <div className="file-list-container">
      <div className="file-list">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Size</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id} className={selectedId === f.id ? 'selected' : ''}>
                <td className="file-name" onClick={() => f.has_transcription && handleView(f.id)}>
                  {f.name}
                </td>
                <td>{f.type}</td>
                <td>{(f.size / 1024).toFixed(1)} KB</td>
                <td>
                  <span className={`badge ${f.has_transcription ? 'badge-done' : 'badge-pending'}`}>
                    {f.has_transcription ? 'Transcribed' : 'Not transcribed'}
                  </span>
                </td>
                <td className="actions">
                  <button
                    className="btn btn-sm"
                    onClick={() => {
                      const audio = new Audio(getAudioUrl(f.id));
                      setPlayingId(f.id);
                      audio.play();
                      audio.onended = () => setPlayingId(null);
                    }}
                  >
                    {playingId === f.id ? 'Playing...' : 'Play'}
                  </button>
                  {!f.has_transcription && (
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleTranscribe(f.id)}
                      disabled={transcribingId === f.id && status === 'processing'}
                    >
                      Transcribe
                    </button>
                  )}
                  {f.has_transcription && (
                    <>
                      <button className="btn btn-sm" onClick={() => handleView(f.id)}>
                        View
                      </button>
                      <button className="btn btn-sm btn-primary" onClick={() => handleExport(f.id)}>
                        Export DOCX
                      </button>
                    </>
                  )}
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(f.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {transcribingId && selectedId === transcribingId && status && status !== 'completed' && (
        <div className="transcription-progress">
          <ProgressBar progress={progress} status={status} />
          {error && <p className="error-text">Error: {error}</p>}
        </div>
      )}

      {transcriptionResult && selectedId && (
        <TranscriptionView result={transcriptionResult} />
      )}
    </div>
  );
}
