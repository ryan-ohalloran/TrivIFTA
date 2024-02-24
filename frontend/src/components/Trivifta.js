import React, { useState } from 'react';
import RunJobForm from './RunJobForm';
import QueryDatabaseForm from './QueryDatabaseForm';

function Trivifta() {

    const [activeTab, setActiveTab] = useState('run-job-form');
    
    return (
        <div className="Trivifta">
        <header>
            <h1 className='header-title'>IFTA Compliance Service</h1>
            <nav className='nav-bar'>
            <ul className="nav-tabs">
                <li className={activeTab === 'run-job-form' ? 'nav-tab active' : 'nav-tab'} onClick={() => setActiveTab('run-job-form')}><a href="#run-job-form">Run Report</a></li>
                <li className={activeTab === 'query-database-form' ? 'nav-tab active' : 'nav-tab'} onClick={() => setActiveTab('query-database-form')}><a href="#query-database-form">View Report Database</a></li>
            </ul>
            </nav>
        </header>
        {activeTab === 'run-job-form' && <RunJobForm />}
        {activeTab === 'query-database-form' && <QueryDatabaseForm />} {/* Display the new component when the second tab is active */}
        </div>
    );

}

export default Trivifta;