import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

export default function QRScanner({ onBack }) {
  const scannerRef = useRef(null);
  const [error, setError] = useState('');
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const scanner = new Html5Qrcode('apex-qr-reader');
    scannerRef.current = scanner;
    let mounted = true;

    scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      decoded => {
        if (!mounted) return;
        let target = decoded;
        try {
          const url = new URL(decoded);
          if (url.pathname.includes('/scan/')) target = url.pathname.split('/scan/')[1];
        } catch {}
        scanner.stop().catch(() => {});
        window.location.href = target.startsWith('http') ? target : `/scan/${target}`;
      },
      () => {}
    ).then(() => mounted && setRunning(true))
     .catch(() => mounted && setError('Camera access was blocked. Please allow camera access and try again.'));

    return () => {
      mounted = false;
      scanner.stop().catch(() => {});
      scanner.clear().catch(() => {});
    };
  }, []);

  return (
    <div style={{maxWidth:'700px',margin:'2rem auto',padding:'1rem'}}>
      <button className="btn btn-secondary btn-sm" onClick={onBack}>Back</button>
      <h1 style={{color:'#ff5500'}}>Scan Asset QR</h1>
      <p style={{color:'#aaa'}}>Point your camera at an APEX asset QR code.</p>
      {error && <div style={{padding:'1rem',color:'#ef4444',background:'rgba(239,68,68,.12)',marginBottom:'1rem'}}>{error}</div>}
      <div id="apex-qr-reader" style={{width:'100%',maxWidth:'500px',margin:'1rem auto',background:'#000',borderRadius:'8px',overflow:'hidden'}} />
      {running && <p style={{textAlign:'center',color:'#22c55e'}}>Camera ready - scan a QR code.</p>}
    </div>
  );
}
