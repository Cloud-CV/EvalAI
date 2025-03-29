import React, { useState } from 'react';
import './ReactApp.css'; // Import the CSS file for styling
import ebayLogo from '../images/organizations/ebay.png'; // Import the image

function ReactApp() {
  const [showMore, setShowMore] = useState(false);
  const tags = ['Hiring', 'eBay', 'Internship 2025', 'LLMs', 'NLP'];
  const displayedTags = showMore ? tags : tags.slice(0, 3); // Show only 3 tags by default

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
        {displayedTags.map((tag, index) => (
          <span key={index} className="tag">{tag}</span>
        ))}
      </div>
      {tags.length > 3 && (
        <button className="show-more-button" onClick={() => setShowMore(!showMore)}>
          {showMore ? 'Show Less' : 'Show More'}
        </button>
      )}
      <div className="card-details">
        <p className="card-organizer">Organized by <strong>eBay ML Challenge</strong></p>
        <p className="card-date">Starts on <strong>May 1, 2024 12:30:00 PM IST</strong></p>
        <p className="card-date">Ends on <strong>May 10, 2024 12:30:00 PM IST</strong></p>
      </div>
      <button className="card-button">View Details</button>
    </div>
  );
}

export default ReactApp;