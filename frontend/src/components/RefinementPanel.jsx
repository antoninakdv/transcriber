import { useState, useEffect } from 'react';
import { useRefinement } from '../hooks/useRefinement';

export default function RefinementPanel({ fileId, onRefined }) {
  const { modes, available, loading, error, loadModes, refine } = useRefinement();
  const [selectedMode, setSelectedMode] = useState(null);
  const [customInstruction, setCustomInstruction] = useState('');
  const [refining, setRefining] = useState(false);
  const [refineError, setRefineError] = useState(null);

  // Load modes on mount
  useEffect(() => {
    loadModes();
  }, [loadModes]);

  const handleRefine = async () => {
    if (!selectedMode) return;
    
    setRefining(true);
    setRefineError(null);
    
    try {
      const result = await refine(fileId, selectedMode, 
        selectedMode === 'custom' ? customInstruction : null);
      
      if (result && result.success) {
        onRefined?.(result);
      } else {
        setRefineError(result?.error || 'Refinement failed');
      }
    } catch (err) {
      setRefineError(err.message || 'Refinement failed');
    } finally {
      setRefining(false);
    }
  };

  const handleModeChange = (e) => {
    const mode = e.target.value;
    setSelectedMode(mode);
    // Reset custom instruction if switching away from custom mode
    if (mode !== 'custom') {
      setCustomInstruction('');
    }
  };

  if (!modes && loading) {
    return <div className="refinement-panel">Loading refinement modes...</div>;
  }

  if (!available) {
    return (
      <div className="refinement-panel refinement-unavailable">
        <h4>Mistral Refinement Unavailable</h4>
        <p>To enable advanced refinement features, please set your Mistral API key.</p>
        <p><small>Add it in <strong>Settings</strong>, or set <code>MISTRAL_API_KEY</code> in your environment / .env file.</small></p>
      </div>
    );
  }

  if (error) {
    return <div className="refinement-panel refinement-error">{error}</div>;
  }

  return (
    <div className="refinement-panel">
      <h4>Refine with Mistral</h4>
      
      <div className="refinement-controls">
        <select 
          value={selectedMode || ''} 
          onChange={handleModeChange}
          disabled={refining || loading}
          className="refinement-mode-select"
        >
          <option value="">Select refinement mode...</option>
          {modes && Object.entries(modes).map(([modeId, modeInfo]) => (
            <option key={modeId} value={modeId}>
              {modeInfo.name} - {modeInfo.description}
            </option>
          ))}
        </select>

        {selectedMode === 'custom' && (
          <div className="custom-instruction">
            <label htmlFor="custom-instruction">Custom Instruction:</label>
            <textarea
              id="custom-instruction"
              value={customInstruction}
              onChange={(e) => setCustomInstruction(e.target.value)}
              placeholder="Enter your custom instruction for processing the transcript..."
              rows={3}
              disabled={refining}
            />
          </div>
        )}

        {selectedMode && (
          <button 
            className="btn btn-primary btn-refine"
            onClick={handleRefine}
            disabled={refining || (!customInstruction && selectedMode === 'custom')}
          >
            {refining ? 'Refining...' : 'Refine Transcript'}
          </button>
        )}
      </div>

      {refineError && (
        <div className="refine-error">{refineError}</div>
      )}

      {modes && selectedMode && (
        <div className="refinement-info">
          <small>
            {modes[selectedMode].model} model, temperature: {modes[selectedMode].temperature}
          </small>
        </div>
      )}
    </div>
  );
}