import { useState, useCallback } from 'react';
import { getRefinementModes, checkRefinementAvailable, refineTranscript } from '../api/client';

export function useRefinement() {
  const [modes, setModes] = useState(null);
  const [available, setAvailable] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadModes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [modesData, availability] = await Promise.all([
        getRefinementModes(),
        checkRefinementAvailable()
      ]);
      setModes(modesData);
      setAvailable(availability.available);
    } catch (err) {
      setError(err.message || 'Failed to load refinement modes');
      setModes({});
      setAvailable(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const refine = useCallback(async (fileId, mode, customInstruction = null) => {
    setLoading(true);
    setError(null);
    try {
      const result = await refineTranscript(fileId, mode, customInstruction);
      if (!result.success) {
        setError(result.error || 'Refinement failed');
        return null;
      }
      return result;
    } catch (err) {
      setError(err.message || 'Refinement failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { 
    modes, 
    available, 
    loading, 
    error, 
    loadModes, 
    refine 
  };
}