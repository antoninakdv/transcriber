import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/files/upload', form);
  return data;
}

export async function saveRecording(blob, filename = 'recording.webm') {
  const form = new FormData();
  form.append('file', blob, filename);
  const { data } = await api.post('/files/recording', form);
  return data;
}

export async function listFiles() {
  const { data } = await api.get('/files');
  return data;
}

export async function deleteFile(fileId) {
  await api.delete(`/files/${fileId}`);
}

export function getAudioUrl(fileId) {
  return `http://localhost:8000/api/files/${fileId}/audio`;
}

export async function startTranscription(fileId, model = '') {
  const params = model ? { model } : {};
  const { data } = await api.post(`/transcribe/${fileId}`, null, { params });
  return data;
}

export async function getJobStatus(jobId) {
  const { data } = await api.get(`/transcribe/${jobId}/status`);
  return data;
}

export async function getTranscriptionResult(fileId) {
  const { data } = await api.get(`/transcribe/${fileId}/result`);
  return data;
}

export async function exportDocx(fileId, refinedMode = null) {
  const params = refinedMode ? { refined_mode: refinedMode } : {};
  const response = await api.post(`/export/docx/${fileId}`, null, {
    params,
    responseType: 'blob',
  });
  const url = URL.createObjectURL(response.data);
  const filename = response.headers['content-disposition']
    ?.match(/filename="?(.+)"?/)?.[1] || 'transcription.docx';
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportRefinedDocx(fileId, refinedText, refinedMode) {
  const response = await api.post(`/export/docx/refined/${fileId}`, {
    refined_text: refinedText,
    refined_mode: refinedMode
  }, {
    responseType: 'blob',
  });
  const url = URL.createObjectURL(response.data);
  const filename = response.headers['content-disposition']
    ?.match(/filename="?(.+)"?/)?.[1] || `${refinedMode}_refined.docx`;
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function getSettings() {
  const { data } = await api.get('/settings');
  return data;
}

export async function updateSettings(settings) {
  const { data } = await api.put('/settings', settings);
  return data;
}

// Mistral Refinement API
export async function getRefinementModes() {
  const { data } = await api.get('/refine/modes');
  return data;
}

export async function checkRefinementAvailable() {
  const { data } = await api.get('/refine/available');
  return data;
}

export async function refineTranscript(fileId, mode, customInstruction = null) {
  const { data } = await api.post(`/refine/${fileId}`, {
    mode,
    custom_instruction: customInstruction
  });
  return data;
}

export async function refineText(text, mode, customInstruction = null) {
  const { data } = await api.post('/refine/text', {
    text,
    mode,
    custom_instruction: customInstruction
  });
  return data;
}
