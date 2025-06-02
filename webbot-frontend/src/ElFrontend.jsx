// El-achtige frontend met press-and-hold audio-opname, sessiegeheugen en bedrijfs-URL input
import React, { useState, useRef, useEffect } from 'react';

export default function ElFrontend() {
  const [status, setStatus] = useState('idle'); // idle, listening, thinking, speaking
  const [companyUrl, setCompanyUrl] = useState('');
  const mediaRecorderRef = useRef(null);
  const chunks = useRef([]);
  const audioRef = useRef(null);
  const sessionId = useRef(null);

  useEffect(() => {
    sessionId.current = crypto.randomUUID();
  }, []);

  async function handleUrlSubmit(e) {
    e.preventDefault();
    if (!companyUrl.trim()) return;

    const normalizedUrl = companyUrl.startsWith('http') ? companyUrl : `https://${companyUrl}`;

    await fetch('https://concierge-webbot-hildo-docker.onrender.com/upload_url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: normalizedUrl, session_id: sessionId.current })
    });

    setCompanyUrl('');
  }

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    chunks.current = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.current.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks.current, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('file', blob, 'input.webm');
      formData.append('session_id', sessionId.current);

      setStatus('thinking');

      const response = await fetch('https://concierge-webbot-hildo-docker.onrender.com/ask', {
        method: 'POST',
        body: formData,
      });

      const { audio_url } = await response.json();

      setStatus('speaking');

      if (audioRef.current) {
        audioRef.current.src = audio_url;
        audioRef.current.load(); // 👈 dwingt reload van nieuwe bron
        audioRef.current.onended = () => setStatus('idle');
        audioRef.current.play().catch((err) => {
          console.warn("Autoplay geblokkeerd:", err);
        });
      }
    };

    mediaRecorder.start();
    setStatus('listening');
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }

  function getStatusText() {
    switch (status) {
      case 'listening': return '🎤 Ik luister...';
      case 'thinking': return '💭 Even denken...';
      case 'speaking': return '🔊 Eva spreekt...';
      default: return 'Houd de knop ingedrukt om te spreken';
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem', fontFamily: 'sans-serif' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Spreek met Eva</h2>

      <form onSubmit={handleUrlSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder="Voer een bedrijfs-URL in..."
          value={companyUrl}
          onChange={(e) => setCompanyUrl(e.target.value)}
          style={{ padding: '0.5rem', width: '280px', fontSize: '1rem' }}
        />
        <button type="submit" style={{ padding: '0.5rem 1rem' }}>📎 Voeg toe</button>
      </form>

      <button
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={status !== 'idle' && status !== 'listening'}
        style={{
          width: '120px',
          height: '120px',
          borderRadius: '50%',
          fontSize: '1.5rem',
          backgroundColor: status === 'idle' || status === 'listening' ? '#4CAF50' : '#aaa',
          color: 'white',
          border: 'none',
          marginBottom: '1rem',
          cursor: status === 'idle' || status === 'listening' ? 'pointer' : 'not-allowed'
        }}
      >
        🎤
      </button>

      <div style={{ marginBottom: '1rem' }}>{getStatusText()}</div>

      <audio ref={audioRef} controls style={{ display: 'none' }}>
        <source src={audioRef.current?.src} type="audio/mpeg" />
      </audio>
    </div>
  );
}
