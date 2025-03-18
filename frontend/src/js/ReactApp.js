import React from 'react';
import './ReactApp.css'; // Import the CSS file for styling
import ebayLogo from '../images/organizations/ebay.png'; // Import the image

function ReactApp() {
  return (
    <div className="card">
      <div className="card-header">
        <img src={ebayLogo} alt="eBay Logo" className="card-logo-small" />
        <h2 className="card-title">
          <span className="title-highlight">eBay 2025</span> University Machine Learning Competition
        </h2>
      </div>
      <div className="card-main">
        <div className="logo-box">
          <img src={ebayLogo} alt="eBay Logo" className="card-logo-large" />
        </div>
      </div>
      <div className="card-tags">
        <span className="tag">Hiring</span>
        <span className="tag">eBay</span>
        <span className="tag">Internship 2025</span>
        <span className="tag">LLMs</span>
        <span className="tag">NLP</span>
      </div>
      <div className="card-details">
        <p className="card-organizer">Organized by <strong>eBay ML Challenge</strong></p>
        <p className="card-date">Starts on <strong>May 1, 2025 12:30:00 PM IST</strong></p>
        <p className="card-date">Ends on <strong>May 10, 2025 12:30:00 PM IST</strong></p>
      </div>
      <button className="card-button">View Details</button>
    </div>
  );
}

export default ReactApp;