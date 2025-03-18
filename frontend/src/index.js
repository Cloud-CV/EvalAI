import React from 'react';
import ReactDOM from 'react-dom/client';
import './css/index.css'; // Ensure this path is correct
import App from './js/ReactApp';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);