import React from 'react';
import ReactDOM from 'react-dom/client';
import './css/index.css'; // Ensure this path is correct
import ReactApp from './js/ReactApp';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ReactApp />
  </React.StrictMode>
);