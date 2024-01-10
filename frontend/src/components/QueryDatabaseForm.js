// QueryDatabaseForm.js
import React, { useState, useEffect } from 'react';
import "react-datepicker/dist/react-datepicker.css";
import './RunJobForm.css';
import API_BASE_URL from '../config';

function QueryDatabaseForm() {
    const startYear = 2023;
    const startMonth = 1;

    const [month, setMonth] = useState(startMonth);
    const [year, setYear] = useState(startYear);
    const [day, setDay] = useState(null);
    const [data, setData] = useState([]);
    const [daysInMonth, setDaysInMonth] = useState([]);
  
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const currentYear = new Date().getFullYear();
    const years = Array.from({ length: currentYear - startYear + 1 }, (_, i) => startYear + i);
  
    // Calculate the number of days in the month when the component is first rendered
    useEffect(() => {
        const days = new Date(year, month, 0).getDate();
        setDaysInMonth(Array.from({ length: days }, (_, i) => i + 1));
    }, [year, month]);

    const handleMonthChange = (event) => {
        setMonth(event.target.value);
        if (year) {
            const days = new Date(year, event.target.value, 0).getDate();
            setDaysInMonth(Array.from({ length: days }, (_, i) => i + 1));
        }
    };
  
    const handleYearChange = (event) => {
        setYear(event.target.value);
        if (month) {
            const days = new Date(event.target.value, month, 0).getDate();
            setDaysInMonth(Array.from({ length: days }, (_, i) => i + 1));
        }
      };
  
    const handleDayClick = async (day) => {
        setDay(day);
        const formattedDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const response = await fetch(new URL(`api/entries/${formattedDate}/`, API_BASE_URL).toString());
        const jsonData = await response.json();
        setData(jsonData);
    };

  const downloadCSV = () => {
        const header = Object.keys(data[0]).join(',');
        const rows = data.map(row => Object.values(row).join(',')).join('\n');
        const csvData = `${header}\n${rows}`;
    
        const formattedDateForFilename = `${year}_${String(month).padStart(2, '0')}_${String(day).padStart(2, '0')}`;
        const blob = new Blob([csvData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Ohalloran_${formattedDateForFilename}.csv`);
        document.body.appendChild(link);
        link.click();
    };

    return (
        <div>
          <form onSubmit={e => e.preventDefault()}>
            <div className="date-picker-wrapper">
              <label>
                Month:
                <select value={month} onChange={handleMonthChange}>
                  {months.map((month, index) => (
                    <option key={month} value={index + 1}>{month}</option>
                  ))}
                </select>
              </label>
              <label>
                Year:
                <select value={year} onChange={handleYearChange}>
                  {years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="day-list-wrapper">
              {daysInMonth.map(day => (
                <button key={day} onClick={() => handleDayClick(day)}>{day}</button>
              ))}
            </div>
            {data.length > 0 ? (
              <div className="submit-button-wrapper">
                <button type="button" className="download-button" onClick={downloadCSV}>Download CSV</button>
              </div>
            ) : (
                <p>Selected Date not in database</p>
            )}
          </form>
          {data.length > 0 && (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                    <tr>
                    {Object.keys(data[0]).filter(key => key !== 'id').map(key => (
                        <th key={key}>{key}</th>
                    ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, index) => (
                    <tr key={index}>
                        {Object.entries(row).map(([key, value]) => key !== 'id' && (
                        <td key={key}>{value}</td>
                        ))}
                    </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      );
}

export default QueryDatabaseForm;