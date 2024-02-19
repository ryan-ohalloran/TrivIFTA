// QueryBilling.js
import React, {useState } from "react";
import API_BASE_URL from "../config";
import axios from "axios";

function QueryBilling() {

    const startMonth = 1;
    const startYear = 2023;

    const [month, setMonth] = useState(startMonth);
    const [year, setYear] = useState(startYear);
    const [data, setData] = useState([]);

    
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

    const handleSubmit = async (event) => {
        event.preventDefault();

        // Get the CSRF token from the cookies
        const csrftoken = getCookie('csrftoken');

        try {
            const response = await axios.post(new URL('api/bills/', "http://127.0.0.1:8000/").toString(), 
                {month: month, year: year},
                {
                    headers: {
                        'X-CSRFToken': csrftoken
                    }
            });
            setData(response.data);
            console.log(data);
        }
        catch (error) {
            console.error(error);
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
        </div>
    );
}

export default QueryBilling
