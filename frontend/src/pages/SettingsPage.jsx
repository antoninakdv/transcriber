import { useState, useEffect } from 'react';
import ModelSelector from '../components/ModelSelector';
import { getSettings, updateSettings } from '../api/client';

export default function SettingsPage() {
  const [model, setModel] = useState('base');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSettings().then((s) => {
      setModel(s.model);
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    await updateSettings({ model });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading) return <p>Loading settings...</p>;

  return (
    <div className="page settings-page">
      <h2>Settings</h2>
      <ModelSelector value={model} onChange={setModel} />
      <div className="settings-actions">
        <button className="btn btn-primary" onClick={handleSave}>
          Save Settings
        </button>
        {saved && <span className="save-confirmation">Saved!</span>}
      </div>
      <div className="settings-info">
        <h3>About Models</h3>
        <p>
          Larger models produce more accurate transcriptions but take longer and use more memory.
          The model is downloaded automatically on first use.
        </p>
        <table className="model-info-table">
          <thead>
            <tr><th>Model</th><th>Parameters</th><th>Speed</th><th>Accuracy</th></tr>
          </thead>
          <tbody>
            <tr><td>Tiny</td><td>39M</td><td>Very Fast</td><td>Basic</td></tr>
            <tr><td>Base</td><td>74M</td><td>Fast</td><td>Good</td></tr>
            <tr><td>Small</td><td>244M</td><td>Moderate</td><td>Better</td></tr>
            <tr><td>Medium</td><td>769M</td><td>Slow</td><td>High</td></tr>
            <tr><td>Large</td><td>1550M</td><td>Very Slow</td><td>Best</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
