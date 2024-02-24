// Query the billing endpoint for all billing data and transform it to JSON
// import API_BASE_URL from '../config';
import getCookie from './GetCookie';
import axios from 'axios';

function getBillingData(month, year) {

    let cookie = getCookie('csrftoken');
    let url = new URL('http://127.0.0.1:8000/api/bills/').toString();

    return axios.post(url, {
        month: month,
        year: year
    }, {
        headers: {
            'X-CSRFToken': cookie
        }
    })
        .then(response => response.data)
        .catch(error => console.error(error));

}

export default getBillingData;