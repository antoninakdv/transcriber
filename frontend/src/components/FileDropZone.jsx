import { useState, useRef, useEffect, useCallback } from 'react';
import { uploadFile } from '../api/client';

const ACCEPTED = '.ogg,.mp3,.wav,.mp4,.m4a,.webm,.flac,.aac';
const ACCEPTED_TYPES = new Set([
  'audio/ogg', 'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
  'audio/mp4', 'audio/m4a', 'audio/x-m4a', 'audio/webm', 'audio/flac',
  'audio/aac', 'video/mp4', 'video/webm', 'video/ogg',
]);
const ACCEPTED_EXTS = new Set(['.ogg', '.mp3', '.wav', '.mp4', '.m4a', '.webm', '.flac', '.aac']);

function isAudioFile(file) {
  if (ACCEPTED_TYPES.has(file.type)) return true;
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  return ACCEPTED_EXTS.has(ext);
}

export default function FileDropZone({ onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const handleFiles = useCallback(async (files) => {
    const valid = files.filter(isAudioFile);
    if (!valid.length) {
      alert('No supported audio/video files found. Supported: OGG, MP3, WAV, MP4, M4A, WEBM, FLAC, AAC');
      return;
    }
    setUploading(true);
    try {
      for (const file of valid) {
        await uploadFile(file);
      }
      onUploaded?.();
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  }, [onUploaded]);

  useEffect(() => {
    const onPaste = (e) => {
      const files = Array.from(e.clipboardData?.files || []);
      if (files.length) {
        e.preventDefault();
        handleFiles(files);
      }
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [handleFiles]);

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length) handleFiles(files);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  return (
    <div
      className={`drop-zone ${dragging ? 'drop-zone--active' : ''}`}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={() => setDragging(false)}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        multiple
        hidden
        onChange={(e) => handleFiles(Array.from(e.target.files))}
      />
      {uploading ? (
        <p>Uploading...</p>
      ) : (
        <>
          <p className="drop-zone-icon">&#128194;</p>
          <p>Drag & drop audio/video files here</p>
          <p className="drop-zone-hint">or click to browse, or paste (Ctrl+V) &middot; OGG, MP3, WAV, MP4, WEBM</p>
        </>
      )}
    </div>
  );
}
