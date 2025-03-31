import React from 'react';
import './ReactApp.css'; // Import the CSS file for styling
import ebayLogo from '../images/organizations/ebay.png'; // Import the image

function ReactApp() {
  const tags = ['Hiring', 'LLMs', 'eCommerce', 'Internship 2025', 'NLP']; // Ensure all tags are included

  return (
    <div className="card">
      <div className="logo-box">
        <div className="card-header">
          <img src={ebayLogo} alt="eBay Logo" className="card-logo-small" />
          <h2 className="card-title">
            <span className="title-highlight">eBay</span> 2024 University Machine Learning Competition
          </h2>
        </div>
        <img src={ebayLogo} alt="eBay Logo" className="card-logo-large" />
      </div>
      <div className="card-tags">
        {tags.map((tag, index) => (
          <span key={index} className="tag">{tag}</span>
        ))}
      </div>
      <div className="card-details">
        <p className="card-organizer">Organized by <strong>eBay ML Challenge</strong></p>
        <p className="card-date">Starts on <strong>May 1, 2024 12:00:00 AM PST (GMT -7:00)</strong></p>
      </div>
      <button className="card-button">View Details</button>
    </div>
  );
}

export default ReactApp;