import { useState, useEffect, useCallback } from 'react';
import FileDropZone from '../components/FileDropZone';
import FileList from '../components/FileList';
import AudioRecorder from '../components/AudioRecorder';
import { listFiles, getSettings } from '../api/client';

export default function HomePage() {
  const [files, setFiles] = useState([]);
  const [model, setModel] = useState('base');
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [fileData, settings] = await Promise.all([listFiles(), getSettings()]);
      setFiles(fileData);
      setModel(settings.model);
    } catch {
      console.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="page">
      <div className="top-controls">
        <FileDropZone onUploaded={refresh} />
        <AudioRecorder onRecorded={refresh} />
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <FileList files={files} onRefresh={refresh} currentModel={model} />
      )}
    </div>
  );
}
