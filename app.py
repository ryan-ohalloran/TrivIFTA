from filter import *
from ftplib import FTP
import streamlit as st
from datetime import datetime, timedelta
from geotab import MyGeotabAPI

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
        for single_date in daterange(date_picker_range[0], date_picker_range[1]):
            from_date = datetime.combine(single_date, datetime.min.time())
            to_date = datetime.combine(single_date + timedelta(days=1), datetime.min.time())
            geotab_vin_data_collection = my_geotab_api.to_vin_data_collection(from_date, to_date)
            df = geotab_vin_data_collection.to_dataframe()
            st.dataframe(df)
            st.download_button(label=f'Download Filtered Dataset ({to_date.date()})', 
                            data=df.to_csv(), 
                            file_name=f"Geotab_{to_date.year}_{to_date.month:02d}_{to_date.day:02d}.csv")
    elif go_button:
        st.warning("Please select a valid date range.")
        

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

if __name__ == '__main__':
    main()
