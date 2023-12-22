from ifta import *
from ftplib import FTP
import streamlit as st
from datetime import datetime, timedelta
from geotab import MyGeotabAPI, GeotabFTP
import pandas as pd
import io

def main():
    st.title("IFTA Webapp")
    st.write("Transform GeoTab data into IFTA-compliant data.")

    tab1, tab2 = st.tabs(["Manual Document Upload", "Geotab API Data Retrieval"])

    with tab1:
        process_manual_upload()

    with tab2:
        process_geotab_api_data()

def process_manual_upload():
    # functionality for manual document upload
    input_files = st.file_uploader('Select Excel files', type=['xlsx', 'xls'], accept_multiple_files=True)

    if not input_files:
        st.warning('Please upload at least one Excel file.')
        return

    for i, input_file in enumerate(input_files):
        st.write(f"### File: {input_file.name}")
        file_date = st.date_input(f'Select a date for file {i + 1}', key=f'date_{i}')
        fuel_tax_processor = FuelTaxProcessor(input_file.read(), data_type='bytes')
        vin_data_collection = fuel_tax_processor.process_data()
        df = vin_data_collection.to_dataframe()
        st.dataframe(df)
        st.download_button(label=f'Download Filtered Dataset ({input_file.name})', 
                           data=df.to_csv(), 
                           file_name=f"Ohalloran_{file_date.year}_{file_date.month:02d}_{file_date.day:02d}.csv")

def process_geotab_api_data():
    # Code for Geotab API data retrieval
    my_geotab_api = MyGeotabAPI(username=st.secrets.MYGEOTAB_USERNAME, 
                                password=st.secrets.MYGEOTAB_PASSWORD, 
                                database=st.secrets.MYGEOTAB_DATABASE)
    
    date_picker_range = st.date_input("Select date range", value=(datetime.now().date(), datetime.now().date()), key="date_range")

    go_button = st.button("Go")

    if go_button and len(date_picker_range) == 2:
        if date_picker_range[0] > date_picker_range[1]:
            st.warning("Please select a valid date range.")
            return
        # if only selecting one day, add one day to the end date to capture that full day
        elif date_picker_range[0] == date_picker_range[1]:
            date_picker_range[1] = date_picker_range[0] + timedelta(days=1)

        for single_date in daterange(date_picker_range[0], date_picker_range[1]):
            from_date = datetime.combine(single_date, datetime.min.time())
            to_date = datetime.combine(single_date + timedelta(days=1), datetime.min.time())
            geotab_vin_data_collection = my_geotab_api.to_vin_data_collection(from_date, to_date)
            df = geotab_vin_data_collection.to_dataframe()
            st.dataframe(df)
            file_name = f"Ohalloran_{to_date.year}_{to_date.month:02d}_{to_date.day:02d}.csv"
            # add a streamlit button to send the data to the FTP server
            send_to_ftp_button = st.button(f"Send ({file_name}) to FTP")
            if send_to_ftp_button:
                send_to_ftp(df, file_name)
            
    elif go_button:
        st.warning("Please select a valid date range.")
        

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def send_to_ftp(data: pd.DataFrame, filename: str) -> None:
    ftp = GeotabFTP(host=st.secrets.FTP_HOST)
    ftp.login(username=st.secrets.FTP_USERNAME, password=st.secrets.FTP_KEY)
    data_csv = data.to_csv(index=False).encode('utf-8')
    try:
        ftp.storbinary(f'STOR {filename}', io.BytesIO(data_csv))
    except Exception as e:
        st.error(e)
    # if successfull, show a success message
    else:
        st.success(f"Successfully sent {filename} to FTP server🔥")

if __name__ == '__main__':
    main()
