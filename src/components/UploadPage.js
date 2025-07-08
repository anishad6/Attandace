import React, { useState } from 'react';
import './UploadPage.css';

function UploadPage({ setShowUpload }) {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (!file) {
      alert('Please select a file before uploading.');
      return;
    }
    // TODO: Add API call or logic to upload file
    console.log('Uploading:', file.name);
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <button className="back-btn" onClick={() => setShowUpload(false)}>← Back</button>
        <h2>📊 Upload Attendance Excel or CSV</h2>
        <p>Select a file and click upload.</p>
        <form className="upload-form" onSubmit={(e) => { e.preventDefault(); handleUpload(); }}>
          <input type="file" onChange={handleFileChange} />
          <button type="submit" className="upload-btn">📤 Upload</button>
        </form>
      </div>
    </div>
  );
}

export default UploadPage;
