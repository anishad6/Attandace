// Home.js
// import React, { useState } from 'react';
// import Selections from './Selections'; // adjust path if needed
// import './Home.css';

// function Home() {
//   const [rules, setRules] = useState({
//     fullDay: '',
//     halfDayMin: '',
//     halfDayMax: '',
//     nonWorkingDays: '',
//   });

//   return (
//     <div className="home-container">
//       <Selections rules={rules} setRules={setRules} />
//     </div>
//   );
// }

// export default Home;


function Home() {
  
  return (
    <div className="home-container">
      <div className="home-card">
        <h1 className="home-title">📁 Welcome to My App</h1>
        <p className="home-description">Upload your Excel files and get beautifully formatted outputs.</p>
        <a href="/upload">
          <button className="upload-btn">Go to Upload Page</button>
        </a>
      </div>
    </div>
  );
}

export default Home;

