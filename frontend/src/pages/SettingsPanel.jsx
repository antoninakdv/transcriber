import { useState, useEffect, useCallback } from 'react';
import ModelSelector from '../components/ModelSelector';
import {
  getSettings,
  updateSettings,
  saveMistralKey,
  deleteMistralKey,
  testMistralConnection,
} from '../api/client';

const SOURCE_LABEL = {
  environment: 'from environment / .env',
  session: 'entered this session',
  keychain: 'remembered on this device',
};

export default function SettingsPanel() {
  const [model, setModel] = useState('base');
  const [engine, setEngine] = useState('whisper');
  const [mistral, setMistral] = useState({ configured: false, source: null, hint: null });
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  // Mistral API-key field state.
  const [keyInput, setKeyInput] = useState('');
  const [remember, setRemember] = useState(false);
  const [keyBusy, setKeyBusy] = useState(false);
  const [keyMsg, setKeyMsg] = useState(null);
  const [testResult, setTestResult] = useState(null);

  const refresh = useCallback(async () => {
    const s = await getSettings();
    setModel(s.model);
    setEngine(s.transcription_engine || 'whisper');
    setMistral(s.mistral || { configured: false });
    setLoading(false);
  }, []);

  useEffect(() => {
    (async () => { await refresh(); })();
  }, [refresh]);

  const handleSaveSettings = async () => {
    const s = await updateSettings({ model, transcription_engine: engine });
    if (s.mistral) setMistral(s.mistral);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleSaveKey = async () => {
    if (!keyInput.trim()) return;
    setKeyBusy(true);
    setKeyMsg(null);
    setTestResult(null);
    try {
      const status = await saveMistralKey(keyInput.trim(), remember);
      setMistral(status);
      setKeyInput('');
      setKeyMsg(remember ? 'Key saved and remembered on this device.' : 'Key saved for this session.');
    } catch (err) {
      setKeyMsg('Failed to save key: ' + (err.response?.data?.detail || err.message));
    } finally {
      setKeyBusy(false);
    }
  };

  const handleClearKey = async () => {
    setKeyBusy(true);
    setKeyMsg(null);
    setTestResult(null);
    try {
      const status = await deleteMistralKey();
      setMistral(status);
      if (!status.configured && engine === 'voxtral') setEngine('whisper');
      setKeyMsg('Key removed.');
    } finally {
      setKeyBusy(false);
    }
  };

  const handleTest = async () => {
    setKeyBusy(true);
    setTestResult(null);
    try {
      setTestResult(await testMistralConnection());
    } catch (err) {
      setTestResult({ ok: false, message: err.message });
    } finally {
      setKeyBusy(false);
    }
  };

  if (loading) return <p>Loading settings...</p>;

  return (
    <div className="settings-panel-content">
      <h2>Settings</h2>

      {/* Mistral connection status + secure key entry */}
      <div className="settings-section">
        <h3>Mistral API</h3>
        <p className={`mistral-status ${mistral.configured ? 'mistral-status--ok' : 'mistral-status--off'}`}>
          {mistral.configured
            ? `Mistral connected — key ••••${mistral.hint} (${SOURCE_LABEL[mistral.source] || 'set'})`
            : 'No key — Whisper only, refinement disabled.'}
        </p>

        <label htmlFor="mistral-key">Mistral API key</label>
        <input
          id="mistral-key"
          type="password"
          autoComplete="off"
          placeholder={mistral.configured ? 'Enter a new key to replace the current one' : 'Paste your Mistral API key'}
          value={keyInput}
          onChange={(e) => setKeyInput(e.target.value)}
          disabled={keyBusy}
        />
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            disabled={keyBusy}
          />
          Remember on this device (stored in the OS keychain)
        </label>

        <div className="settings-actions">
          <button className="btn btn-primary" onClick={handleSaveKey} disabled={keyBusy || !keyInput.trim()}>
            Save Key
          </button>
          <button className="btn" onClick={handleTest} disabled={keyBusy || !mistral.configured}>
            Test Connection
          </button>
          {mistral.configured && (
            <button className="btn btn-danger" onClick={handleClearKey} disabled={keyBusy}>
              Clear Key
            </button>
          )}
        </div>
        {keyMsg && <p className="settings-note">{keyMsg}</p>}
        {testResult && (
          <p className={testResult.ok ? 'mistral-status--ok' : 'mistral-status--off'}>
            {testResult.message}
          </p>
        )}
        <p className="settings-note">
          A <code>MISTRAL_API_KEY</code> in your environment / <code>.env</code> takes precedence. The key is
          held in memory (or the OS keychain) only — never written to a file or returned to the browser.
        </p>
      </div>

      {/* Transcription engine: local Whisper (default) vs cloud Voxtral */}
      <div className="settings-section">
        <h3>Transcription Engine</h3>
        <label className="radio-row">
          <input
            type="radio"
            name="engine"
            value="whisper"
            checked={engine === 'whisper'}
            onChange={() => setEngine('whisper')}
          />
          Local (Whisper) — offline, private, default
        </label>
        <label className={`radio-row ${mistral.configured ? '' : 'radio-row--disabled'}`}>
          <input
            type="radio"
            name="engine"
            value="voxtral"
            checked={engine === 'voxtral'}
            onChange={() => setEngine('voxtral')}
            disabled={!mistral.configured}
          />
          Mistral (Voxtral, cloud) — needs an API key
        </label>
        {!mistral.configured && (
          <p className="settings-note">Add a Mistral API key above to enable Voxtral.</p>
        )}
        {engine === 'voxtral' && (
          <p className="settings-note settings-note--warn">
            Audio will be uploaded to Mistral's API for transcription.
          </p>
        )}
      </div>

      <ModelSelector value={model} onChange={setModel} />

      <div className="settings-actions">
        <button className="btn btn-primary" onClick={handleSaveSettings}>
          Save
        </button>
        {saved && <span className="save-confirmation">Saved!</span>}
      </div>

      <div className="settings-info">
        <h3>Whisper Models</h3>
        <p>
          Larger models are more accurate but slower. Downloaded automatically on first use.
          (Applies to the local Whisper engine only.)
        </p>
        <table className="model-info-table">
          <thead>
            <tr><th>Model</th><th>Params</th><th>Speed</th><th>Quality</th></tr>
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
