// QueryBilling.js
import React, {useState } from "react";
import getBillingData from "../services/BillingService";

function QueryBilling() {

    const startMonth = 1;
    const startYear = 2023;

    const [month, setMonth] = useState(startMonth);
    const [year, setYear] = useState(startYear);
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [dataLoaded, setDataLoaded] = useState(false);


    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        try {
            let response = await getBillingData(month, year);
            let data = JSON.parse(response);
            setData(data);
        }
        catch (error) {
            console.error(error);
        }
        finally
        {
            setLoading(false);
            setDataLoaded(true);
        }
    }
    
    return (
        <div>
          <form onSubmit={handleSubmit}>
            <label htmlFor="month">Month</label>
            <select id="month" name="month" value={month} onChange={(e) => setMonth(e.target.value)}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                <option key={month} value={month}>{month}</option>
              ))}
            </select>
            <label htmlFor="year">Year</label>
            <select id="year" name="year" value={year} onChange={(e) => setYear(e.target.value)}>
              {Array.from({ length: new Date().getFullYear() - startYear + 1 }, (_, i) => startYear + i).map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
            <button type="submit">Submit</button>
          </form>
          <div>
            {loading && <p>Loading...</p>}
            {dataLoaded && Object.keys(data).length > 0 && (
              <ul>
                {Object.keys(data).map((key) => (
                  <li key={key}>{data[key].company_name}: ${data[key].total_cost}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      );
}

export default QueryBilling
