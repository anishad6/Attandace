// // src/App.js
// import React from 'react';
// import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import Navbar from './components/Navbar';
// import UploadPage from './components/UploadPage';
// import UploadExcel from './components/UploadExcel';
// import './components/Home.css';


// function Home() {
//   return (
//     <div className="home-container">
//       <div className="home-card">
//         <h1 className="home-title">📁 Welcome to My App</h1>
//         <p className="home-description">Upload your Excel files and get beautifully formatted outputs.</p>
//         <a href="/upload">
//           <button className="upload-btn">Go to Upload Page</button>
//         </a>
//       </div>
//     </div>
//   );
// }

// // export default Home;

// export default function App() {
//   return (
//     <Router>
//       {/* Navbar will always render */}
//       <Navbar />

//       {/* Page content based on route */}
//       <Routes>
//         <Route path="/" element={<Home />} />
//         <Route path="/upload" element={<UploadExcel />} />
//         {/* <Route path="/upload" element={<UploadPage />} /> */}
//       </Routes>
//     </Router>
//   );
// }


// --------------------------------------------

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import UploadExcel from './components/UploadExcel';
import RulePage from './components/RulePage';
import './components/Home.css';
import Home from './components/Home'; 


function App() {
  const [rules, setRules] = useState({
    fullDay: 9,
    halfDayMin: 5,
    halfDayMax: 9,
  });

  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<UploadExcel rules={rules} setRules={setRules} />} />
        <Route path="/rules" element={<RulePage rules={rules} setRules={setRules} />} />
      </Routes>
    </Router>
  );
}

export default App;




