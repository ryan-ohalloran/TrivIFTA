// App.js
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Trivifta from './components/Trivifta.js';
import QueryBilling from './components/QueryBilling.js';

function App() {
  return (
    <Router>
      <div className="App">
        <nav>
          <ul>
            <li>
              <Link to="/trivifta">IFTA Compliance</Link>
            </li>
            <li>
              <Link to="/querybilling">Billing</Link>
            </li>
          </ul>
        </nav>
        <Routes>
          <Route path="/trivifta" element={<Trivifta />} />
          <Route path="/querybilling" element={<QueryBilling />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;