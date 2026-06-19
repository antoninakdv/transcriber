import { useState, useRef, useCallback } from 'react';
import { startTranscription, getJobStatus } from '../api/client';

export function useTranscription() {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const transcribe = useCallback(async (fileId, model, onComplete) => {
    setStatus('starting');
    setProgress(0);
    setError(null);

    try {
      const { job_id } = await startTranscription(fileId, model);
      setStatus('processing');

      intervalRef.current = setInterval(async () => {
        try {
          const job = await getJobStatus(job_id);
          setProgress(job.progress);
          setStatus(job.status);

          if (job.status === 'completed') {
            clearInterval(intervalRef.current);
            onComplete?.();
          } else if (job.status === 'error') {
            clearInterval(intervalRef.current);
            setError(job.error);
          }
        } catch {
          clearInterval(intervalRef.current);
          setError('Lost connection to server');
          setStatus('error');
        }
      }, 2000);
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }, []);

  const reset = useCallback(() => {
    clearInterval(intervalRef.current);
    setStatus(null);
    setProgress(0);
    setError(null);
  }, []);

  return { status, progress, error, transcribe, reset };
}
