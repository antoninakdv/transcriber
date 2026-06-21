import { useState, useRef, useCallback } from 'react';
import { startTranscription, getJobStatus } from '../api/client';

export function useTranscription() {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  // Whisper transcription is CPU-bound and runs in a single backend thread, so
  // the server can briefly fail to answer a status poll while it is busy. Tolerate
  // a few consecutive misses before declaring the connection lost — otherwise one
  // transient blip ends a job that is actually still running and completes fine.
  const MAX_CONSECUTIVE_FAILURES = 6; // ~12s of silence at the 2s poll interval

  const transcribe = useCallback(async (fileId, model, onComplete) => {
    setStatus('starting');
    setProgress(0);
    setError(null);

    try {
      const { job_id } = await startTranscription(fileId, model);
      setStatus('processing');

      let failures = 0;
      intervalRef.current = setInterval(async () => {
        try {
          const job = await getJobStatus(job_id);
          failures = 0;
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
          failures += 1;
          if (failures >= MAX_CONSECUTIVE_FAILURES) {
            clearInterval(intervalRef.current);
            setError('Lost connection to server');
            setStatus('error');
          }
          // Otherwise keep polling — the server is likely just busy transcribing.
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
