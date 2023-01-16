# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 13:35:48 2023

@author: jkern
"""

from BillingFuns import *

mcheck = 0
internalcheck = 0
sw = False

srcwell = st.radio(
    "Monthly Billing or Sourcewell Quarterly?",
    ('Billing', 'Internal Billing', 'Sourcewell Quarterly Sales Report'))

if srcwell == 'Sourcewell Quarterly Sales Report':
    internalcheck = 0
    sw = True
else:
    internalcheck = 0
    sw = False
    
if srcwell == 'Internal Billing':
    sw = False
    internalcheck = 1
    

if not sw:
    uploaded_filem = st.file_uploader("Upload Monthly Billing CSV")
    if uploaded_filem is not None:
        mcheck = 1
        #read xls or xlsx
        monthlydf=pd.read_csv(uploaded_filem, skiprows=3)
        monthlydf = getFactorize(monthlydf)
        
    else:
        st.warning("Monthly Bill From Geotab")




    ### Enter Year, and Month name
    year = 0
    month = ''
    
    yearcheck = 0
    moncheck = 'nono'
    while yearcheck == 0:
        year = st.text_input('Year', '2023')
        #year = input("Please type the year we are billing: ")
        try:
            year = int(year)
            yearcheck = getYear(year)
        except ValueError:
            print("Please enter a number.\n")
    
            
    while moncheck == 'nono':
        month = st.text_input('Month (The one it currently is - this will affect bill days)', 'February')
        #month = input("Please type the month we are billing: ")
        moncheck = getMonth(month)
        
    month = moncheck
    year = yearcheck

# ---------------------------------------------------------------------------


    if mcheck == 1:
        # Set our unit prices
        monthlydf = editProductPrice(monthlydf, internalcheck)
        
        
        ## Edit cost
        monthlydf = setCost(monthlydf)
        
        
        ## Get the number of companies to bill this month
        lng = len(monthlydf['Database'].unique())
        
        
        ## Create Database for each company (These will turn into excel spreadsheets)
        d = {}
        for i in range(lng):
            tdf = monthlydf.loc[monthlydf['id'] == i]
            tdf = tdf.reset_index(drop=True)
            d[i] = tdf
    
    
        ## Deals with termination of GO7 Devices and alters the billing days accordingly
        d = setQuantity(d, month, year)

    
    #zipObj = zipfile.ZipFile("MonthlyBillBreakdown.zip", "w")




        for i in range(lng):
            
            # Write each company billing to a separate excel spreadsheet
            compname = d[i]['Database'].iloc[0]
            
            # if sw:
            #     if compname == 'cityofgrimes':
            #         tempdf, tempfile = writeToCsv(d, lng, i, sw)
            #         dbname = tempfile[:-4]
                    
            #         CSV = convert_df(tempdf, tempfile)
            #         st.download_button(label=dbname,
            #                                     data=CSV,
            #                                     file_name= tempfile)
            
            tempdf, tempfile = writeToCsv(d, lng, i, sw)
            x = sum(tempdf['Cost'])
            sx = str(round(x, 2))
            dbname = tempfile[:-4]
            st.write(dbname + " Monthly total: " + sx)
                
            CSV = convert_df(tempdf)
            st.download_button(label=dbname,
                               data=CSV,
                               file_name= tempfile)
 
       
## This is the case for sourcewell
else:
    uploaded_file1 = st.file_uploader("Upload 1st Monthly Billing CSV")
    if uploaded_file1 is not None:
        #read xls or xlsx
        monthlydf1=pd.read_csv(uploaded_file1, skiprows=3)
        monthlydf1 = getFactorize(monthlydf1)
    else:
        st.warning("Monthly Bill From Geotab")
        
    uploaded_file2 = st.file_uploader("Upload 2nd Monthly Billing CSV")
    if uploaded_file2 is not None:
        #read xls or xlsx
        monthlydf2 = pd.read_csv(uploaded_file2, skiprows=3)
        monthlydf2 = getFactorize(monthlydf2)
    else:
        st.warning("Monthly Bill From Geotab")
        
    uploaded_file3 = st.file_uploader("Upload 3rd Monthly Billing CSV")
    if uploaded_file3 is not None and uploaded_file2 is not None and uploaded_file1 is not None:
        mcheck = 2
        #read xls or xlsx
        monthlydf3 = pd.read_csv(uploaded_file3, skiprows=3)
        monthlydf3 = getFactorize(monthlydf3)
    else:
        st.warning("Monthly Bill From Geotab")
        
    if mcheck == 2:

        lng1 = len(monthlydf1['Database'].unique())
        lng2 = len(monthlydf2['Database'].unique())
        lng3 = len(monthlydf3['Database'].unique())
        
        grim1 = srcwl(lng1, monthlydf1)
        grim2 = srcwl(lng2, monthlydf2)
        grim3 = srcwl(lng3, monthlydf3)
        
        st.write('Getting Sent to combiner')
        grimtot = sourceWriteCsv(grim1, grim2, grim3)
        CSV = convert_df(grimtot)
        st.write('HAS BEEN CONVERTED TO CSV')
        st.download_button(label='Grimes Sourcewell Download',
                           data=CSV,
                           file_name='GeotabSourcewellQuarterlyFiling.csv')

        # for i in range(lng1):
            
        #     # Write each company billing to a separate excel spreadsheet
        #     compname = d[i]['Database'].iloc[0]
            
        #     if compname == 'cityofgrimes':
        #         tempdf, tempfile = writeToCsv(d, lng, i, sw)
        #         dbname = tempfile[:-4]
                
        #         CSV = convert_df(tempdf)
        #         st.download_button(label=dbname,
        #                            data=CSV,
        #                            file_name= tempfile)
            
        #     tempdf, tempfile = writeToCsv(d, lng, i, sw)
        #     x = sum(tempdf['Cost'])
        #     sx = str(round(x, 2))
        #     dbname = tempfile[:-4]
        #     st.write(dbname + " Monthly total: " + sx)
                
        #     CSV = convert_df(tempdf, tempfile)
        #     st.download_button(label=dbname,
        #                        data=CSV,
        #                        file_name= tempfile)
        
        # compname1 = monthlydf1['Database'].iloc[0]
        # st.write('this is the compname: ' + compname1)

        








