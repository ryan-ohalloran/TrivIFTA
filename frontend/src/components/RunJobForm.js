import React, { useState } from 'react';
import axios from 'axios';
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import Papa from 'papaparse';
import './RunJobForm.css';
import ReactDOM from 'react-dom';
import API_BASE_URL from '../config';

function RunJobForm() {

  const [date, setDate] = useState(null);
  const [options, setOptions] = useState({
    remove_unchanged: false,
    send_email: false,
    save_to_db: true, // Default to true
    send_to_ftp: false,
  });
  const [loading, setLoading] = useState(false);
  const [csvData, setCsvData] = useState(null);
  const [csvString, setCsvString] = useState(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  

  const handleChange = (event) => {
    setOptions({ ...options, [event.target.name]: event.target.checked });
  };

  const parseCSVData = (csvString) => {
    return new Promise((resolve, reject) => {
      Papa.parse(csvString, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          resolve(results.data);
          setDataLoaded(true);
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
  
    try {
      const formattedDate = date.toISOString().split('T')[0];
      const runJobUrl = new URL('api/run-job/', API_BASE_URL).toString();
      console.log(runJobUrl);
  
      // Get the CSRF token from the cookies
      const csrftoken = getCookie('csrftoken');
  
      // Include the CSRF token in the headers of your request
      const response = await axios.post(runJobUrl, { date: formattedDate, ...options }, {
        headers: {
          'X-CSRFToken': csrftoken
        }
      });
  
      const csvString = JSON.parse(response.data).text; // Extract CSV string from API response
      setCsvString(csvString);
  
      if (csvString) {
        const parsedData = await parseCSVData(csvString);
        setCsvData(parsedData);
      } else {
        throw new Error("CSV data is undefined or empty");
      }
    } catch (error) {
      console.error('There was an error!', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Function to get a cookie by name
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const PopperContainer = ({ children }) => {
    return ReactDOM.createPortal(
      children,
      document.body
    );
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([csvString], {type: 'text/csv'});
    element.href = URL.createObjectURL(file);
    element.download = `Ohalloran_${date.getFullYear()}_${("0" + (date.getMonth() + 1)).slice(-2)}_${("0" + date.getDate()).slice(-2)}.csv`;
    document.body.appendChild(element); // Required for this to work in FireFox
    element.click();
  };

  const isDateDisabled = (date) => {
    const threeDaysAgo = new Date();
    const twoYearsAgo = new Date();
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
    twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
    return date < threeDaysAgo && date > twoYearsAgo;
  };

  return (
    <div>
        <form onSubmit={handleSubmit}>
            <div className="date-picker-wrapper">
              <label>
                  Date:
                  <DatePicker 
                  selected={date} 
                  onChange={setDate} 
                  dateFormat="yyyy-MM-dd"
                  filterDate={isDateDisabled}
                  popperContainer={PopperContainer}
                  className="date-picker"
                  />
              </label>
            </div>
            <div className="button-group">
            <label className="checkbox-label">
                <input type="checkbox" name="remove_unchanged" checked={options.remove_unchanged} onChange={handleChange} />
                <span>Remove Stationary</span>
            </label>            
            <label className="checkbox-label">
                <input type="checkbox" name="send_email" checked={options.send_email} onChange={handleChange} />
                <span>Send Email</span>
            </label>
            <label className="checkbox-label">
                <input type="checkbox" name="send_to_ftp" checked={options.send_to_ftp} onChange={handleChange} />
                <span>Send to FTP</span>
            </label>
            </div>
            <div className="submit-button-wrapper">
                <button type="submit" className="submit-button">Go</button>
                {loading && <div className="loader"></div>}
            </div>
        </form>
        {dataLoaded && (
            <button className="download-button" onClick={handleDownload}>Download CSV</button>
        )}
        {Array.isArray(csvData) && csvData.length > 0 && (
      <div className="table-wrapper">
        <table className="data-table">
            <thead>
                <tr>
                  {/* Render table headers */}
                  {Object.keys(csvData[0]).map((header, index) => (
                      <th key={index} className="sticky-header">{header}</th>
                  ))}
                </tr>
            </thead>
            <tbody>
                {/* Render table rows */}
                {csvData.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                      {Object.values(row).map((cell, cellIndex) => (
                          <td key={cellIndex}>{cell}</td>
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
export default RunJobForm;
