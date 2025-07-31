import './UploadExcel.css';
import React, { useState } from 'react';
import axios from 'axios';


function UploadExcel() {
  const [file, setFile] = useState(null);
  const [salaryFile, setSalaryFile] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [salaryUploadMsg, setSalaryUploadMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [resultUrl, setResultUrl] = useState(null);
  const [salaryData, setSalaryData] = useState([]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setErrorMsg('');
    setSuccessMsg('');
    setResultUrl(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const isValidExtension = allowedExtensions.some(ext =>
      selectedFile.name.toLowerCase().endsWith(ext)
    );

    if (!isValidExtension) {
      setErrorMsg('❌ Invalid format. Please upload a .xlsx, .xls, or .csv file.');
      setFile(null);
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setErrorMsg('❌ File size must be less than 5MB.');
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleSalaryFileChange = (e) => {
  const file = e.target.files[0];
  const formData = new FormData();
  formData.append("file", file);

    // const file = e.target.files[0];
    setSalaryUploadMsg('');
    if (!file) return;

    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const isValid = allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValid) {
      setSalaryUploadMsg('❌ Invalid file format. Only .xlsx, .xls, .csv allowed.');
      return;
    }

    setSalaryFile(file);
  };

  const handleUpload = async () => {
  if (!file) {
    setErrorMsg('⚠️ Please select a file before uploading.');
    return;
  }

  const formData = new FormData();
  formData.append('file', file); // or 'attendance_file' depending on backend expectation

  setLoading(true);
  setErrorMsg('');
  setSuccessMsg('');
  setResultUrl(null);

  try {
    // const response = await axios.post(
    //   'http://localhost:8000/app/upload-excel/',
    const response = await axios.post(
        'https://atandace.onrender.com/app/upload-excel/',
      formData,
      { responseType: 'blob' }
    );

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const downloadUrl = window.URL.createObjectURL(blob);
    setResultUrl(downloadUrl);

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = file.name.replace(/\.[^/.]+$/, '') + '_Processed.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);

        // Summary file request with proper FormData
    const summaryFormData = new FormData();
    summaryFormData.append('attendance_file', file);

    // const summaryRes = await axios.post(
    //   'http://localhost:8000/app/generate-summary/',
    const summaryRes = await axios.post(
      'https://atandace.onrender.com/app/generate-summary/', 

      summaryFormData,
      { responseType: 'blob' }
    );


    // // Summary file request
    // const summaryRes = await axios.post('http://localhost:8000/app/generate-summary/', {
    //   responseType: 'blob',
    // });

    const summaryBlob = new Blob([summaryRes.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const summaryUrl = window.URL.createObjectURL(summaryBlob);
    const summaryLink = document.createElement('a');
    summaryLink.href = summaryUrl;
    summaryLink.download = 'Attendance_Summary_Report.xlsx';
    document.body.appendChild(summaryLink);
    summaryLink.click();
    document.body.removeChild(summaryLink);
    window.URL.revokeObjectURL(summaryUrl);

    setSuccessMsg('✅ File processed and summary downloaded.');
    setFile(null);
  } catch (error) {
    console.error('Upload error:', error);

    if (error.response && error.response.data) {
      const errData = error.response.data;

      // ✅ Check if it's a Blob before using FileReader
      if (errData instanceof Blob) {
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const json = JSON.parse(reader.result);
            setErrorMsg(`❌ ${json.error || 'Upload failed.'}`);
          } catch {
            setErrorMsg('❌ Upload failed. Server returned invalid error format.');
          }
        };
        reader.readAsText(errData);
      } else if (typeof errData === 'object') {
        // Direct JSON
        setErrorMsg(`❌ ${errData.error || 'Upload failed.'}`);
      } else {
        setErrorMsg('❌ Upload failed. Unexpected error format.');
      }
    } else {
      setErrorMsg('❌ Server error. Please try again.');
    }
  } finally {
    setLoading(false);
  }
};

const handleSalaryUpload = async () => {
  if (!salaryFile) {
    setSalaryUploadMsg('⚠️ Please select a salary file.');
    return;
  }

  const formData = new FormData();
  formData.append('file', salaryFile);

  try {
    // const res = await axios.post('http://localhost:8000/app/upload-salary/', formData, {
    const res = await axios.post('https://atandace.onrender.com/app/upload-salary/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    setSalaryUploadMsg('✅ Salary file uploaded successfully.');
    setSalaryFile(null);
    setSalaryData(res.data.data); // ✅ Save result to state

  } catch (err) {
    console.error("❌ Upload error:", err.response?.data || err.message);
    setSalaryUploadMsg(`❌ Error: ${err.response?.data?.error || 'Upload failed'}`);
  }
};


// const handleSalaryUpload = async () => {
//   if (!salaryFile) {
//     setSalaryUploadMsg('⚠️ Please select a salary file.');
//     return;
//   }

//   // ✅ Create form data
//   const formData = new FormData();
//   formData.append('file', salaryFile);  // Key must match backend: request.FILES["file"]

//   try {
//     // ✅ Make API call to backend
//     const res = await axios.post('http://localhost:8000/app/upload-salary/', formData, {
//       headers: {
//         'Content-Type': 'multipart/form-data',
//       },
//     });

//     console.log('✅ Response:', res.data);
//     setSalaryUploadMsg('✅ Salary file uploaded successfully.');
//     setSalaryFile(null);  // clear file input after upload

//     // Optionally do something with res.data.data
//     // like showing in a table

//   } catch (err) {
//     console.error("❌ Upload error:", err.response?.data || err.message);
//     setSalaryUploadMsg(`❌ Error: ${err.response?.data?.error || 'Upload failed'}`);
//   }
// };

  // const handleSalaryUpload = async () => {
  //   if (!salaryFile) {
  //     setSalaryUploadMsg('⚠️ Please select a salary file.');
  //     return;
  //   }

  //   const formData = new FormData();
  //   formData.append('file', salaryFile);

  //   try {
  //     const res = await axios.post('http://localhost:8000/app/upload-salary/', formData);
  //     // const res = await axios.post('https://atandace.onrender.com/app/upload-salary/', formData);

  //     setSalaryUploadMsg('✅ Salary file uploaded successfully.');
  //     setSalaryFile(null);
  //   } catch (err) {
  //     setSalaryUploadMsg('❌ Error uploading salary file.');
  //   }
  // };

  const handleViewResult = () => {
    if (resultUrl) {
      window.open(resultUrl, '_blank');
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
       <button
          className="rule-btn"
          onClick={() => window.location.href = '/rules'}
        >
          ⚙️ Configure Attendance Rules
        </button>
        <h2>📊 Upload Attendance Excel or CSV</h2>

        <input
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={handleFileChange}
          disabled={loading}
        />

        {file && (
          <p className="file-info">
            📁 <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
          </p>
        )}

        <button onClick={handleUpload} disabled={loading || !file}>
          {loading ? '⏳ Uploading...' : '📤 Upload & Generate Summary'}
        </button>

        {resultUrl && (
          <button className="view-result-btn" onClick={handleViewResult}>
            👀 View Transposed Excel
          </button>
        )}

        {errorMsg && <p className="error-text">{errorMsg}</p>}
        {successMsg && <p className="success-text">{successMsg}</p>}

        <hr style={{ margin: '30px 0', border: '1px solid #e2e8f0' }} />

        <h2>💼 Upload Salary Excel or CSV</h2>

        <input
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={handleSalaryFileChange}
          disabled={loading}
        />

        {salaryFile && (
          <p className="file-info">
            📁 <strong>{salaryFile.name}</strong> ({(salaryFile.size / 1024).toFixed(1)} KB)
          </p>
        )}

        <button onClick={handleSalaryUpload} disabled={!salaryFile}>
          📤 Upload Salary File
        </button>

        {salaryUploadMsg && (
          <p className={salaryUploadMsg.startsWith('✅') ? 'success-text' : 'error-text'}>
            {salaryUploadMsg}
          </p>
        )}

        {salaryData.length > 0 && (
  <div>
    <h3>📊 Calculated Salary Details:</h3>
    <table border="1" cellPadding="5">
      <thead>
        <tr>
          {Object.keys(salaryData[0]).map((key) => (
            <th key={key}>{key}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {salaryData.map((row, i) => (
          <tr key={i}>
            {Object.values(row).map((val, j) => (
              <td key={j}>{val}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)}

      </div>
    </div>
  );
}

export default UploadExcel;





// import './UploadExcel.css';
// import React, { useState } from 'react';
// import axios from 'axios';

// function UploadExcel() {
//   const [file, setFile] = useState(null);
//   const [errorMsg, setErrorMsg] = useState('');
//   const [successMsg, setSuccessMsg] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [resultUrl, setResultUrl] = useState(null); // ✅ for viewing result

//   const handleFileChange = (e) => {
//     const selectedFile = e.target.files[0];
//     setErrorMsg('');
//     setSuccessMsg('');
//     setResultUrl(null); // ✅ clear previous result

//     if (!selectedFile) {
//       setFile(null);
//       return;
//     }

//     const allowedExtensions = ['.xlsx', '.xls', '.csv'];
//     const isValidExtension = allowedExtensions.some(ext =>
//       selectedFile.name.toLowerCase().endsWith(ext)
//     );

//     if (!isValidExtension) {
//       setErrorMsg('❌ Invalid format. Please upload a .xlsx, .xls, or .csv file.');
//       setFile(null);
//       return;
//     }

//     if (selectedFile.size > 5 * 1024 * 1024) {
//       setErrorMsg('❌ File size must be less than 5MB.');
//       setFile(null);
//       return;
//     }

//     setFile(selectedFile);
//   };

//   const handleUpload = async () => {
//     if (!file) {
//       setErrorMsg('⚠️ Please select a file before uploading.');
//       return;
//     }

//     const formData = new FormData();
//     formData.append('file', file);

//     setLoading(true);
//     setErrorMsg('');
//     setSuccessMsg('');
//     setResultUrl(null); // ✅ clear previous result

//     try {
//       const response = await axios.post(
//         'http://localhost:8000/app/upload-excel/',
//         formData,
//         { responseType: 'blob' }
//       );

//       const blob = new Blob([response.data], {
//         type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
//       });

//       const downloadUrl = window.URL.createObjectURL(blob);

//       // ✅ Save for later viewing
//       setResultUrl(downloadUrl);

//       // Auto download
//       const link = document.createElement('a');
//       link.href = downloadUrl;
//       link.download = file.name.replace(/\.[^/.]+$/, "") + '_Processed.xlsx';
//       document.body.appendChild(link);
//       link.click();
//       document.body.removeChild(link);
//       window.URL.revokeObjectURL(downloadUrl);

//       setSuccessMsg('✅ File processed and downloaded successfully.');
//       setFile(null);
//     } catch (error) {
//       console.error('Upload error:', error);
//       if (error.response && error.response.data) {
//         const reader = new FileReader();
//         reader.onload = () => {
//           try {
//             const errData = JSON.parse(reader.result);
//             setErrorMsg(`❌ ${errData.error || 'Upload failed.'}`);
//           } catch {
//             setErrorMsg('❌ Upload failed. Server returned invalid error format.');
//           }
//         };
//         reader.readAsText(error.response.data);
//       } else {
//         setErrorMsg('❌ Server error. Please try again.');
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleViewResult = () => {
//     if (resultUrl) {
//       window.open(resultUrl, '_blank');
//     }
//   };

//   return (
//     <div className="upload-container">
//       <h2>📊 Upload Attendance Excel or CSV</h2>

//       <input
//         type="file"
//         accept=".xlsx,.xls,.csv"
//         onChange={handleFileChange}
//         disabled={loading}
//       />

//       {file && (
//         <p className="file-info">
//           📁 <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
//         </p>
//       )}

//       <button onClick={handleUpload} disabled={loading || !file}>
//         {loading ? '⏳ Uploading...' : '📤 Upload'}
//       </button>

//       {/* ✅ View result button */}
//       {resultUrl && (
//         <button className="view-result-btn" onClick={handleViewResult}>
//           👀 View Result
//         </button>
//       )}

//       {errorMsg && <p className="error-text">{errorMsg}</p>}
//       {successMsg && <p className="success-text">{successMsg}</p>}
//     </div>
//   );
// }

// export default UploadExcel;



// ----------------------------------------------------------------------------

// this one i had used previous 

// import './UploadExcel.css';
// import React, { useState } from 'react';
// import axios from 'axios';

// function UploadExcel() {
//   const [file, setFile] = useState(null);
//   const [salaryFile, setSalaryFile] = useState(null);
//   const [errorMsg, setErrorMsg] = useState('');
//   const [successMsg, setSuccessMsg] = useState('');
//   const [salaryUploadMsg, setSalaryUploadMsg] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [resultUrl, setResultUrl] = useState(null);

//   const handleFileChange = (e) => {
//     const selectedFile = e.target.files[0];
//     setErrorMsg('');
//     setSuccessMsg('');
//     setResultUrl(null);

//     if (!selectedFile) {
//       setFile(null);
//       return;
//     }

//     const allowedExtensions = ['.xlsx', '.xls', '.csv'];
//     const isValidExtension = allowedExtensions.some(ext =>
//       selectedFile.name.toLowerCase().endsWith(ext)
//     );

//     if (!isValidExtension) {
//       setErrorMsg('❌ Invalid format. Please upload a .xlsx, .xls, or .csv file.');
//       setFile(null);
//       return;
//     }

//     if (selectedFile.size > 5 * 1024 * 1024) {
//       setErrorMsg('❌ File size must be less than 5MB.');
//       setFile(null);
//       return;
//     }

//     setFile(selectedFile);
//   };

//   const handleSalaryFileChange = (e) => {
//     const file = e.target.files[0];
//     setSalaryUploadMsg('');
//     if (!file) return;

//     const allowedExtensions = ['.xlsx', '.xls', '.csv'];
//     const isValid = allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

//     if (!isValid) {
//       setSalaryUploadMsg('❌ Invalid file format. Only .xlsx, .xls, .csv allowed.');
//       return;
//     }

//     setSalaryFile(file);
//   };

//   const handleUpload = async () => {
//     if (!file) {
//       setErrorMsg('⚠️ Please select a file before uploading.');
//       return;
//     }

//     const formData = new FormData();
//     formData.append('file', file);

//     setLoading(true);
//     setErrorMsg('');
//     setSuccessMsg('');
//     setResultUrl(null);

//     try {
//       const response = await axios.post(
//         'https://atandace.onrender.com/app/upload-excel/',
//         // 'http://localhost:8000/app/upload-excel/',
//         formData,
//         { responseType: 'blob' }
//       );

//       const blob = new Blob([response.data], {
//         type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
//       });

//       const downloadUrl = window.URL.createObjectURL(blob);
//       setResultUrl(downloadUrl);

//       const link = document.createElement('a');
//       link.href = downloadUrl;
//       link.download = file.name.replace(/\.[^/.]+$/, '') + '_Processed.xlsx';
//       document.body.appendChild(link);
//       link.click();
//       document.body.removeChild(link);
//       window.URL.revokeObjectURL(downloadUrl);

//       // const summaryRes = await axios.get('http://localhost:8000/app/generate-summary/', {
//       const summaryRes = await axios.get('https://atandace.onrender.com/app/generate-summary/', {

//         responseType: 'blob',
//       });

//       const summaryBlob = new Blob([summaryRes.data], {
//         type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
//       });

//       const summaryUrl = window.URL.createObjectURL(summaryBlob);
//       const summaryLink = document.createElement('a');
//       summaryLink.href = summaryUrl;
//       summaryLink.download = 'Attendance_Summary_Report.xlsx';
//       document.body.appendChild(summaryLink);
//       summaryLink.click();
//       document.body.removeChild(summaryLink);
//       window.URL.revokeObjectURL(summaryUrl);

//       setSuccessMsg('✅ File processed and summary downloaded.');
//       setFile(null);
//     } catch (error) {
//       console.error('Upload error:', error);
//       if (error.response && error.response.data) {
//         const reader = new FileReader();
//         reader.onload = () => {
//           try {
//             const errData = JSON.parse(reader.result);
//             setErrorMsg(`❌ ${errData.error || 'Upload failed.'}`);
//           } catch {
//             setErrorMsg('❌ Upload failed. Server returned invalid error format.');
//           }
//         };
//         reader.readAsText(error.response.data);
//       } else {
//         setErrorMsg('❌ Server error. Please try again.');
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleSalaryUpload = async () => {
//     if (!salaryFile) {
//       setSalaryUploadMsg('⚠️ Please select a salary file.');
//       return;
//     }

//     const formData = new FormData();
//     formData.append('file', salaryFile);

//     try {
//       // const res = await axios.post('http://localhost:8000/app/upload-salary/', formData);
//       const res = await axios.post('https://atandace.onrender.com/app/upload-salary/', formData);

//       setSalaryUploadMsg('✅ Salary file uploaded successfully.');
//       setSalaryFile(null);
//     } catch (err) {
//       setSalaryUploadMsg('❌ Error uploading salary file.');
//     }
//   };

//   const handleViewResult = () => {
//     if (resultUrl) {
//       window.open(resultUrl, '_blank');
//     }
//   };

//   return (
//     <div className="upload-container">
//       <div className="upload-card">
//         <h2>📊 Upload Attendance Excel or CSV</h2>

//         <input
//           type="file"
//           accept=".xlsx,.xls,.csv"
//           onChange={handleFileChange}
//           disabled={loading}
//         />

//         {file && (
//           <p className="file-info">
//             📁 <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
//           </p>
//         )}

//         <button onClick={handleUpload} disabled={loading || !file}>
//           {loading ? '⏳ Uploading...' : '📤 Upload & Generate Summary'}
//         </button>

//         {resultUrl && (
//           <button className="view-result-btn" onClick={handleViewResult}>
//             👀 View Transposed Excel
//           </button>
//         )}

//         {errorMsg && <p className="error-text">{errorMsg}</p>}
//         {successMsg && <p className="success-text">{successMsg}</p>}

//         <hr style={{ margin: '30px 0', border: '1px solid #e2e8f0' }} />

//         <h2>💼 Upload Salary Excel or CSV</h2>

//         <input
//           type="file"
//           accept=".xlsx,.xls,.csv"
//           onChange={handleSalaryFileChange}
//           disabled={loading}
//         />

//         {salaryFile && (
//           <p className="file-info">
//             📁 <strong>{salaryFile.name}</strong> ({(salaryFile.size / 1024).toFixed(1)} KB)
//           </p>
//         )}

//         <button onClick={handleSalaryUpload} disabled={!salaryFile}>
//           📤 Upload Salary File
//         </button>

//         {salaryUploadMsg && (
//           <p className={salaryUploadMsg.startsWith('✅') ? 'success-text' : 'error-text'}>
//             {salaryUploadMsg}
//           </p>
//         )}
//       </div>
//     </div>
//   );
// }

// export default UploadExcel;



// -----------------------------------------------------------------------------------
// Akash code start from here 

// import './UploadExcel.css';
// import React, { useState } from 'react';
// import axios from 'axios';

// function UploadExcel() {
//   const [file, setFile] = useState(null);
//   const [errorMsg, setErrorMsg] = useState('');
//   const [successMsg, setSuccessMsg] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [showUpload, setShowUpload] = useState(false);
//   const [resultData, setResultData] = useState(null); // For result section

//   // Simple Navbar component
//   const Navbar = () => (
//     <nav
//       style={{
//         width: '100%',
//         background: 'linear-gradient(90deg,rgb(253, 253, 253) 0%,rgb(147, 157, 178) 100%)',
//         color: '#fff',
//         padding: '18px 32px',
//         fontSize: '1.25rem',
//         fontWeight: 700,
//         letterSpacing: '1px',
//         boxShadow: '0 2px 8px rgba(59,130,246,0.08)',
//         position: 'fixed',
//         top: 0,
//         left: 0,
//         zIndex: 2000,
//         display: 'flex',
//         alignItems: 'center',
//         gap: '16px'
//       }}
//     >
//       <img
//         src="/logo123.png"
//         alt="Logo"
//         style={{
//           height: '32px',
//           width: '120px',
//           marginRight: '12px',
//           borderRadius: '6px',
//           background: '#fff'
//         }}
//       />
//     </nav>
//   );

//   const handleFileChange = (e) => {
//     const selectedFile = e.target.files[0];
//     setErrorMsg('');
//     setSuccessMsg('');
//     setResultData(null);

//     if (!selectedFile) {
//       setFile(null);
//       return;
//     }

//     const allowedExtensions = ['.xlsx', '.xls', '.csv'];
//     const isValidExtension = allowedExtensions.some(ext =>
//       selectedFile.name.toLowerCase().endsWith(ext)
//     );

//     if (!isValidExtension) {
//       setErrorMsg('❌ Invalid format. Please upload a .xlsx, .xls, or .csv file.');
//       setFile(null);
//       return;
//     }

//     if (selectedFile.size > 5 * 1024 * 1024) {
//       setErrorMsg('❌ File size must be less than 5MB.');
//       setFile(null);
//       return;
//     }

//     setFile(selectedFile);
//   };

//   const handleUpload = async () => {
//     if (!file) {
//       setErrorMsg('⚠️ Please select a file before uploading.');
//       return;
//     }

//     const formData = new FormData();
//     formData.append('file', file);

//     setLoading(true);
//     setErrorMsg('');
//     setSuccessMsg('');
//     setResultData(null);

//     try {
//       // Expecting backend to return JSON result and file as blob
//       const response = await axios.post(
//         'http://localhost:8000/app/upload-excel/',
//         formData,
//         { responseType: 'blob' }
//       );

//       // Try to extract result section from response headers (if backend supports it)
//       let resultSection = null;
//       if (response.headers['x-result-section']) {
//         try {
//           resultSection = JSON.parse(response.headers['x-result-section']);
//         } catch {
//           resultSection = null;
//         }
//       }

//       // Download file as before
//       const blob = new Blob([response.data], {
//         type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
//       });

//       const downloadUrl = window.URL.createObjectURL(blob);
//       const link = document.createElement('a');
//       link.href = downloadUrl;
//       link.download = file.name.replace(/\.[^/.]+$/, "") + '_Processed.xlsx';
//       document.body.appendChild(link);
//       link.click();
//       document.body.removeChild(link);
//       window.URL.revokeObjectURL(downloadUrl);

//       setSuccessMsg('✅ File processed and downloaded successfully.');

//       // If backend supports, show result section
//       if (resultSection) {
//         setResultData(resultSection);
//       } else {
//         // Try to parse result from blob if it's a JSON (for demo/fallback)
//         if (blob.type === "application/json") {
//           const text = await blob.text();
//           try {
//             setResultData(JSON.parse(text));
//           } catch {
//             setResultData(null);
//           }
//         }
//       }

//       setFile(null);
//     } catch (error) {
//       console.error('Upload error:', error);
//       if (error.response && error.response.data) {
//         const reader = new FileReader();
//         reader.onload = () => {
//           try {
//             const errData = JSON.parse(reader.result);
//             setErrorMsg(`❌ ${errData.error || 'Upload failed.'}`);
//           } catch {
//             setErrorMsg('❌ Upload failed. Server returned invalid error format.');
//           }
//         };
//         reader.readAsText(error.response.data);
//       } else {
//         setErrorMsg('❌ Server error. Please try again.');
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleCardClick = () => {
//     setShowUpload(true);
//   };

//   if (!showUpload) {
//     return (
//       <>
//         <Navbar />
//         <div
//           style={{
//             position: 'fixed',
//             top: 90,
//             left: 40,
//             zIndex: 1000,
//             background: 'transparent',
//             minHeight: 0,
//             minWidth: 0,
//             display: 'flex',
//             justifyContent: 'flex-start',
//             alignItems: 'flex-start'
//           }}
//         >
//           <button
//             onClick={handleCardClick}
//             style={{
//               border: 'none',
//               background: 'white',
//               borderRadius: '14px',
//               boxShadow: '0 4px 16px rgba(54, 187, 199, 0.13)',
//               padding: '40px 80px', // Bigger card button
//               cursor: 'pointer',
//               transition: 'box-shadow 0.2s, transform 0.2s',
//               display: 'flex',
//               flexDirection: 'column',
//               alignItems: 'center',
//               gap: '20px',
//               fontFamily: 'inherit',
//             }}
//             onMouseOver={e => {
//               e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.18)';
//               e.currentTarget.style.transform = 'translateY(-2px) scale(1.08)';
//             }}
//             onMouseOut={e => {
//               e.currentTarget.style.boxShadow = '0 4px 16px rgba(54, 187, 199, 0.13)';
//               e.currentTarget.style.transform = 'none';
//             }}
//           >
//             <div style={{ textAlign: 'center' }}>
//               <h3 style={{ margin: 0, fontSize: '1.5rem', color: '#3b82f6', fontWeight: 700 }}>📊 Upload</h3>
//               <p style={{ margin: 0, color: '#555', fontSize: '1.2rem' }}>
//                 Excel/CSV
//               </p>
//             </div>
//           </button>
//         </div>
//       </>
//     );
//   }

//   return (
//     <>
//       <Navbar />
//       <div
//         className="upload-container"
//         style={{
//           minHeight: '100vh',
//           background: 'linear-gradient(135deg, #f8fafc 0%, #e0e7ef 100%)',
//           display: 'flex',
//           flexDirection: 'column',
//           alignItems: 'center',
//           justifyContent: 'center',
//           padding: '40px 0'
//         }}
//       >
//         <div
//           style={{
//             background: 'white',
//             borderRadius: '18px',
//             boxShadow: '0 4px 24px rgba(134, 209, 228, 0.79)',
//             padding: '40px 65px',
//             minWidth: '340px',
//             maxWidth: '95vw',
//             display: 'flex',
//             flexDirection: 'column',
//             alignItems: 'center',
//             gap: '18px',
//             position: 'relative'
//           }}
//         >
//           <button
//             onClick={() => setShowUpload(false)}
//             style={{
//               position: 'absolute',
//               top: 16,
//               left: 16,
//               background: 'transparent',
//               border: 'none',
//               color: '#3b82f6',
//               fontSize: '1.2rem',
//               fontWeight: 600,
//               cursor: 'pointer',
//               display: 'flex',
//               alignItems: 'center',
//               gap: '4px'
//             }}
//           >
//             <span style={{ fontSize: '1.2rem' }}>←</span> Back
//           </button>
//           <h2 style={{ color: '#3b82f6', marginBottom: '10px', fontWeight: 700, fontSize: '2rem' }}>
//             📊 Upload Attendance Excel or CSV
//           </h2>

//           <input
//             type="file"
//             accept=".xlsx,.xls,.csv"
//             onChange={handleFileChange}
//             disabled={loading}
//             style={{
//               margin: '12px 0',
//               padding: '8px',
//               borderRadius: '8px',
//               border: '1px solid #d1d5db',
//               background: '#f9fafb',
//               fontSize: '1rem',
//               width: '100%'
//             }}
//           />

//           {file && (
//             <p style={{
//               color: '#2563eb',
//               background: '#f1f5fd',
//               borderRadius: '8px',
//               padding: '8px 16px',
//               fontWeight: 500,
//               margin: 0
//             }}>
//               📁 <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
//             </p>
//           )}

//           <button
//             onClick={handleUpload}
//             disabled={loading || !file}
//             style={{
//               background: loading || !file ? '#dbeafe' : 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)',
//               color: loading || !file ? '#94a3b8' : '#fff',
//               border: 'none',
//               borderRadius: '8px',
//               padding: '12px 32px',
//               fontSize: '1.1rem',
//               fontWeight: 600,
//               cursor: loading || !file ? 'not-allowed' : 'pointer',
//               boxShadow: '0 2px 8px rgba(59,130,246,0.08)',
//               transition: 'background 0.2s, color 0.2s'
//             }}
//           >
//             {loading ? '⏳ Uploading...' : '📤 Upload'}
//           </button>

//           {errorMsg && <p style={{
//             color: '#dc2626',
//             background: '#fee2e2',
//             borderRadius: '8px',
//             padding: '8px 16px',
//             fontWeight: 500,
//             margin: 0
//           }}>{errorMsg}</p>}
//           {successMsg && <p style={{
//             color: '#16a34a',
//             background: '#dcfce7',
//             borderRadius: '8px',
//             padding: '8px 16px',
//             fontWeight: 500,
//             margin: 0
//           }}>{successMsg}</p>}

//           {/* Result Section */}
//           {resultData && (
//             <div
//               style={{
//                 marginTop: '24px',
//                 width: '100%',
//                 background: '#f9fafb',
//                 borderRadius: '10px',
//                 padding: '18px 12px',
//                 boxShadow: '0 2px 8px rgba(59,130,246,0.06)',
//                 color: '#222'
//               }}
//             >
//               <h4 style={{ margin: '0 0 10px 0', color: '#2563eb' }}>Result Section</h4>
//               <pre style={{
//                 whiteSpace: 'pre-wrap',
//                 wordBreak: 'break-word',
//                 fontSize: '1rem',
//                 background: 'transparent',
//                 margin: 0
//               }}>
//                 {JSON.stringify(resultData, null, 2)}
//               </pre>
//             </div>
//           )}
//         </div>
//       </div>
//     </>
//   );
// }

// export default UploadExcel;





