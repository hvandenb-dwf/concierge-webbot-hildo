import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import ElFrontend from './ElFrontend.jsx';  // ✅ verander deze regel

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ElFrontend />  // ✅ en deze
  </StrictMode>,
);
