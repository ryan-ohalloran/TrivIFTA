# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 14:06:35 2022

@author: jkern
"""

import numpy as np
import pandas as pd
import streamlit as st

def run():
    
    mcheck = 0
    
    filename = 'FilteredVins.csv'
    
    filteredVins = pd.read_csv(filename)
    
    uploaded_file = st.file_uploader("Upload Unfiltered Daily IFTA report")
    if uploaded_file is not None:
        mcheck = 1
        #read xls or xlsx
        dailyVins=pd.read_csv(uploaded_file)
        
    else:
        st.warning("Unfiltered Daily IFTA report")
    
    fvins = filteredVins['VIN']
    
    
    if mcheck == 1:
        filteredDailyVins = dailyVins[dailyVins['vin'].isin(fvins)]
        filteredDailyVins = filteredDailyVins.reset_index()
        printabledf = filteredDailyVins.iloc[:, 1:6]
        
        CSV = printabledf.to_csv().encode('utf-8')
        
        st.dataframe(printabledf)
        st.download_button(label='Download Filtered Dataset',
                                    data=CSV,
                                    file_name= 'Daily_Filtered_IFTA_Report')
    
if __name__ == '__main__':
    run()
