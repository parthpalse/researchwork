import React from 'react';
import ReactDOM from 'react-dom/client';
import { Root } from './Root';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);

// Installable app (PWA): only in production builds, so dev hot-reload is not cached
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}
