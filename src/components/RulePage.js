// import React, { useState } from 'react';
// import axios from 'axios';
// import './RulePage.css';

// function RulePage({ rules, setRules }) {
//   const [loading, setLoading] = useState(false);

//   const handleRuleChange = (e) => {
//     const { name, value } = e.target;
//     setRules((prev) => ({
//       ...prev,
//       [name]: value === '' ? '' : Number(value),
//     }));
//   };

//   const handleSaveRules = async () => {
//     setLoading(true);
//      await axios.post('https://atandace.onrender.com/app/save-rules/', rules);

//       alert('✅ Rules saved to server!');
//       window.location.href = '/upload'; 
//     // try {
//     //   await axios.post('http://localhost:8000/app/save-rules/', rules);

//     //   alert('✅ Rules saved to server!');
//     //   window.location.href = 'http://localhost:3000/upload';
//     } catch (err) {
//       console.error('❌ Failed to save rules:', err);
//       alert('❌ Failed to save rules. Please check if the backend is running.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="rule-card">
//       <h2 className="rule-title">🛠️ Attendance Rules</h2>

//       <div className="rule-inputs">
//         <label>
//           Full Day Hours:
//           <input
//             type="number"
//             name="fullDay"
//             value={rules.fullDay}
//             onChange={handleRuleChange}
//             min="0"
//             required
//           />
//         </label>

//         <label>
//           Half Day Min Hours:
//           <input
//             type="number"
//             name="halfDayMin"
//             value={rules.halfDayMin}
//             onChange={handleRuleChange}
//             min="0"
//             required
//           />
//         </label>

//         <label>
//           Half Day Max Hours:
//           <input
//             type="number"
//             name="halfDayMax"
//             value={rules.halfDayMax}
//             onChange={handleRuleChange}
//             min="0"
//             required
//           />
//         </label>
//       </div>

//       <div className="button-group">
//         <button
//           className="save-btn"
//           onClick={handleSaveRules}
//           disabled={loading}
//         >
//           {loading ? 'Saving...' : '💾 Save Rules'}
//         </button>

//         <button
//           className="back-btn"
//           onClick={() => (window.location.href = '/')}
//         >
//           🔙 Back to Upload Page
//         </button>
//       </div>
//     </div>
//   );
// }

// export default RulePage;

// --------------------------------------
import React, { useState } from 'react';
import axios from 'axios';
import './RulePage.css';

function RulePage({ rules = {}, setRules }) {
  const [loading, setLoading] = useState(false);

  const safeNumber = (val) => val === undefined || val === null ? '' : val;

  const handleRuleChange = (e) => {
    const { name, value } = e.target;
    setRules((prev) => ({
      ...prev,
      [name]: value === '' ? '' : Number(value),
    }));
  };

  const handleSaveRules = async () => {
    setLoading(true);
    try {
      await axios.post('http://localhost:8000/app/save-rules/', rules);
      alert('✅ Rules saved to server!');
      window.location.href = 'http://localhost:3000/upload';
    } catch (err) {
      console.error('❌ Failed to save rules:', err);
      alert('❌ Failed to save rules. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rule-card">
      <h2 className="rule-title">🛠️ Attendance Rules</h2>

      <div className="rule-inputs">
        <label>Full Day Hours:</label>
        <input
          type="number"
          name="fullDay"
          value={safeNumber(rules.fullDay)}
          onChange={handleRuleChange}
          min="0"
          required
        />
      </div>

      <div className="rule-inputs">
        <label>Half Day Min Hours:</label>
        <input
          type="number"
          name="halfDayMin"
          value={safeNumber(rules.halfDayMin)}
          onChange={handleRuleChange}
          min="0"
          required
        />
      </div>

      <div className="rule-inputs">
        <label>Half Day Max Hours:</label>
        <input
          type="number"
          name="halfDayMax"
          value={safeNumber(rules.halfDayMax)}
          onChange={handleRuleChange}
          min="0"
          required
        />
      </div>

      <div className="rule-inputs">
        <label>Only check-in / check-out</label>
        <input
          type="checkbox"
          checked={!!rules.onlyCheckInOut}
          onChange={e => setRules({ ...rules, onlyCheckInOut: e.target.checked })}
        />
      </div>

      <div className="rule-inputs">
        <label>Add extra full days</label>
        <input
          type="checkbox"
          checked={!!rules.addExtraFullDays}
          onChange={e => setRules({ ...rules, addExtraFullDays: e.target.checked })}
        />
      </div>

      <div className="button-group">
        <button
          className="save-btn"
          onClick={handleSaveRules}
          disabled={loading}
        >
          {loading ? 'Saving...' : '💾 Save Rules'}
        </button>

        <button
          className="back-btn"
          onClick={() => (window.location.href = '/')}
        >
          🔙 Back to Upload Page
        </button>
      </div>
    </div>
  );
}

export default RulePage;


