# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 14:06:35 2022

@author: jkern
"""

import numpy as np
import pandas as pd

def run():
    filename = 'FilteredVins.csv'
    
    filteredVins = pd.read_csv(filename)
    
    uploaded_filem = st.file_uploader("Upload Unfiltered Daily IFTA report")
    if uploaded_filem is not None:
        mcheck = 1
        #read xls or xlsx
        dailyVins=pd.read_csv(uploaded_filem)
        
    else:
        st.warning("Unfiltered Daily IFTA report")
    
    fvins = filteredVins['VIN']
    
    filteredDailyVins = dailyVins[dailyVins['vin'].isin(fvins)]
    
    if mcheck == 1:
        
        st.dataframe(temp)
        st.download_button(label='Download Filtered Dataset',
                                    data=filteredDailyVins,
                                    file_name= 'Daily_Filtered_IFTA_Report')
    
if __name__ == '__main__':
    run()
