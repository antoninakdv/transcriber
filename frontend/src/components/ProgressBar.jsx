export default function ProgressBar({ progress, status }) {
  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
      <span className="progress-label">
        {status === 'processing' && `Transcribing... ${progress}%`}
        {status === 'pending' && 'Waiting...'}
        {status === 'starting' && 'Starting...'}
        {status === 'completed' && 'Done!'}
        {status === 'error' && 'Error'}
      </span>
    </div>
  );
}
