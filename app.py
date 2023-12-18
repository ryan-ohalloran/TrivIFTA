# import all functions and classes from filter.py
from filter import *

from ftplib import FTP
import streamlit as st

def main():
    st.title("IFTA Webapp")
    st.write("Transform GeoTab data into IFTA-compliant data.")

    # Get calendar day selection from user
    dt = st.date_input('Select a calendar day')

    # get download file name using date and make sure month and day are 2 digits
    output_file_name = f"Ohalloran_{dt.year}_{dt.month:02d}_{dt.day:02d}.csv"

    # get input excel file from user
    input_file = st.file_uploader('Select an Excel file', type=['xlsx', 'xls'])
    if not input_file:
        st.warning('Please upload an Excel file.')
        return
    
    # Process input file as bytes
    vin_data_collection = process_data(input_file, data_type='bytes')

    # Get dataframe object from VinDataCollection object
    df = vin_data_collection.to_dataframe()

    # Display dataframe preview
    st.dataframe(df)
    st.download_button(label='Download Filtered Dataset', 
                                data=df.to_csv(), 
                                file_name=output_file_name)

if __name__ == '__main__':
    main()