# import all functions and classes from filter.py
from filter import *

from ftplib import FTP
import streamlit as st

def main():
    st.title("IFTA Webapp")
    st.write("Transform GeoTab data into IFTA-compliant data.")

    # get input excel files from user
    input_files = st.file_uploader('Select Excel files', type=['xlsx', 'xls'], accept_multiple_files=True)

    if not input_files:
        st.warning('Please upload at least one Excel file.')
        return

    for i, input_file in enumerate(input_files):
        st.write(f"### File: {input_file.name}")

        # Display date selector for each file
        file_date = st.date_input(f'Select a date for file {i + 1}', key=f'date_{i}')
        
        # Process input file as bytes
        fuel_tax_processor = FuelTaxProcessor(input_file.read(), data_type='bytes')
        vin_data_collection = fuel_tax_processor.process_data()

        # Get dataframe object from VinDataCollection object
        df = vin_data_collection.to_dataframe()

        # Display dataframe preview
        st.dataframe(df)

        # Download button for each file
        st.download_button(label=f'Download Filtered Dataset ({input_file.name})', 
                            data=df.to_csv(), 
                            file_name=f"Ohalloran_{file_date.year}_{file_date.month:02d}_{file_date.day:02d}.csv")

    # Download button for all files
    # if st.button("Download All"):
    #     for input_file in input_files:
    #         # Process input file as bytes
    #         fuel_tax_processor = FuelTaxProcessor(input_file.read(), data_type='bytes')
    #         vin_data_collection = fuel_tax_processor.process_data()

    #         # Get dataframe object from VinDataCollection object
    #         df = vin_data_collection.to_dataframe()

    #         # Download individual dataframe
    #         st.download_button(label=f'Download Filtered Dataset ({input_file.name})', 
    #                             data=df.to_csv(), 
    #                             file_name=f"Ohalloran_{dt.year}_{dt.month:02d}_{dt.day:02d}_{input_file.name}.csv")

if __name__ == '__main__':
    main()