# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 14:06:35 2022

@author: jkern
"""

import numpy as np
import pandas as pd
from datetime import datetime
import streamlit as st
import gcsfs
from ftplib import FTP
import io

ftp = FTP("12.19.168.100")
ftp.login("geotab","46s8hD_tf#A6886R")
ftp.cwd('/')


def run():
    
    mcheck = 0
    
    filename = 'FilteredVins.csv'
    
    filteredVins = pd.read_csv(filename)
    
    # uploaded_file = st.file_uploader("Upload Unfiltered Daily IFTA report")
    # if uploaded_file is not None:
    #     mcheck = 1
    #     #read xls or xlsx
    #     dailyVins=pd.read_csv(uploaded_file)
        
    # else:
    #     st.warning("Unfiltered Daily IFTA report")

    
    dt = datetime.now() 

    year = dt.year
    month = dt.month
    day = dt.day
    day -= 1
    
    if day == 0:
        if month == 1:
            year -= 1
            month = 12
            day = 31
        elif month == 2:
            month -= 1
            day = 31
        elif month == 3:
            month -= 1
            if year % 4 == 0:
                day = 29
            else:
                day = 28
        elif month == 4:
            month -= 1
            day = 31
        elif month == 5:
            month -= 1
            day = 30
        elif month == 6:
            month -= 1
            day = 31
        elif month == 7:
            month -= 1
            day = 30
        elif month == 8:
            month -= 1
            day = 31
        elif month == 9:
            month -= 1
            day = 31
        elif month == 10:
            month -= 1
            day = 30
        elif month == 11:
            month -= 1
            day = 31
        elif month == 12:
            month -= 1
            day = 30
        
        

    daystring = 'Ohalloran_'
    daystring += str(year)
    daystring += '_'
    daystring += str(month)
    daystring += '_'
    daystring += str(day)
    daystring += '.csv'
    
    fvins = filteredVins['VIN']
    
    
    # if mcheck > 1:
    #     filteredDailyVins = dailyVins[dailyVins['VIN'].isin(fvins)]
    #     filteredDailyVins = filteredDailyVins.reset_index()
    #     printabledf = filteredDailyVins.iloc[:, 1:6]
    #     cols = printabledf.columns.tolist()
    #     cols = cols[0:1] + cols[3:5] + cols[1:3]
    #     printabledf = printabledf[cols]
    #     printabledf.set_index('VIN', inplace=True)
        
    #     CSV = printabledf.to_csv().encode('utf-8')
        
    #     st.dataframe(printabledf)
    #     st.download_button(label='Download Filtered Dataset',
    #                                 data=CSV,
    #                                 file_name= daystring)
        
        
    x = 0 
    if x == 0: 
        mcheck = 2
        #read xls or xlsx
        fs = gcsfs.GCSFileSystem(project='my-project')
        autodaystring = 'ifta/Ohalloran/'
        #autodaystring += str(year)
        autodaystring += '2022'
        autodaystring += '_'
        #autodaystring += str(month)
        autodaystring += '12'
        autodaystring += '_'
        #autodaystring += str(day)
        autodaystring += '27'
        autodaystring += '.csv'
        with fs.open(autodaystring) as f:
            dailyVinsauto = pd.read_csv(f)
        
        
        
    if mcheck == 2:
        filteredDailyVinsauto = dailyVinsauto[dailyVinsauto['VIN'].isin(fvins)]
        filteredDailyVinsauto = filteredDailyVinsauto.reset_index()
        printabledfauto = filteredDailyVinsauto.iloc[:, 1:6]
        cols = printabledfauto.columns.tolist()
        cols = cols[0:1] + cols[3:5] + cols[1:3]
        printabledfauto = printabledfauto[cols]
        printabledfauto.set_index('VIN', inplace=True)
        
        
        CSV1 = printabledfauto.to_csv().encode('utf-8')
        
        
        
        buffer = io.BytesIO()
        printabledfauto.to_excel(buffer)
        buffer.seek(0)
        
                
        ftp.storbinary('STOR ' + daystring, buffer)
        #ftp.storbinary('STOR ' + daystring, CSV1)
        #ftp.storlines("STOR " + daystring, buffer)
        
        st.dataframe(printabledfauto)
        st.download_button(label='Download Filtered Dataset',
                                    data=CSV1,
                                    file_name= daystring)
        
    
if __name__ == '__main__':
    run()
