# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 13:35:47 2023

@author: jkern
"""

import numpy as np
import pandas as pd
import os
import math
import streamlit as st
#import base64
#import zipfile
import io


def readData(string, x):
    devicedf = pd.read_csv(string, skiprows=3)
    if x == 0:
        devicedf = getFactorize(devicedf)

    return devicedf



def getFactorize(df):
    df = df.loc[:, ['Serial Number', 'Database','Customer', 'VIN', 
                                'Bill Days', 'Quantity', 'Unit Cost', 'Cost', 'Billing Info']]
    
    ##if db is OH, then db = cust
    df.loc[df['Database'] == 'o_halloran', 'Database'] = df['Customer']
    
    df['Database'] = np.where((df['Database'] == 'landmark') & 
                              (df['Customer'] == 'Total Polish Solutions (Brian Diffin  Knoxvilee  Tennessee)'), 
                              'Total Polish Solutions', df['Database'])

    df.loc[df['Database'] == 'ls', 'Database'] = 'John LeJune'
    df.loc[df['Database'] == 't_b', 'Database'] = 'Ted Parker'
    
    df = df[df['Database'].notna()]
    df['id'] = df['Database'].factorize()[0]
    df['check'] = 0
    return df


def editProductPrice(df, ic):
    if ic == 0:
        df['Unit Cost'] = np.where(df['Unit Cost'] == 19, 32, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 14, 25, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 16, 27, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 18, 27, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 14.12, 32, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 15.4, 32, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 6, 15, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 7, 15, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 9, 20, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 22.85, 32, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 13, 20, df['Unit Cost'])
        df['Unit Cost'] = np.where(df['Unit Cost'] == 5, 7, df['Unit Cost'])
    
    return df


def setQuantity(d, m, y):
    days = getPrevMonDays(m, y)
    for i in range(len(d)):
        for x in range(len(d[i])):
            if d[i]['Serial Number'][x][:2] == 'G7' and d[i]['check'][x] == 0 and d[i]['Bill Days'][x] < days:
                z = 0
                while z < 1:
                    for y in range(len(d[i])):
                        if d[i]['Serial Number'][y][:2] == 'G9' and d[i]['check'][y] == 0 and d[i]['Bill Days'][y] == days:
                            z = 1
                            d[i].at[y, 'Bill Days'] = days - d[i]['Bill Days'][x]
                            d[i].at[y, 'check'] = 1
                            d[i].at[x, 'check'] = 1
                            break
                    z = 1
        d[i]['Quantity'] = d[i]['Bill Days'] / days
        d[i] = setCost(d[i])
    
    return d



def setCost(df):
    df['Cost'] = df['Unit Cost'] * df['Quantity']
    return df


def sourceWriteCsv(df1, df2, df3):
    
    df1 = df1[['Serial Number', 'VIN', 'Billing Info']]
    df1 = df1.rename(columns={'VIN': 'Plan Name'})
    df1['Plan Name'] = df1['Billing Info'].str.split('[').str[0]
    df1['Billing Info'] = df1['Billing Info'].str.split('[').str[1]
    df1['Billing Info'] = df1['Billing Info'].str[:-2]
    try:
        df1['Billing Info'] = df1['Billing Info'].astype(float) / 100.
    except ValueError:
        print(df1['Billing Info'])
        
    df2 = df2[['Serial Number', 'VIN', 'Billing Info']]
    df2 = df2.rename(columns={'VIN': 'Plan Name'})
    df2['Plan Name'] = df2['Billing Info'].str.split('[').str[0]
    df2['Billing Info'] = df2['Billing Info'].str.split('[').str[1]
    df2['Billing Info'] = df2['Billing Info'].str[:-2]
    try:
        df2['Billing Info'] = df2['Billing Info'].astype(float) / 100.
    except ValueError:
        print(df2['Billing Info'])
        
    df3 = df3[['Serial Number', 'VIN', 'Billing Info']]
    df3 = df3.rename(columns={'VIN': 'Plan Name'})
    df3['Plan Name'] = df3['Billing Info'].str.split('[').str[0]
    df3['Billing Info'] = df3['Billing Info'].str.split('[').str[1]
    df3['Billing Info'] = df3['Billing Info'].str[:-2]
    try:
        df3['Billing Info'] = df3['Billing Info'].astype(float) / 100.
    except ValueError:
        print(df3['Billing Info'])
    
    df = combineSourcewell(df1, df2, df3)
    fdf = df[['Serial Number', 'Plan Name', 'Billing Info', 'Months Billed']]
    
    return fdf


def removeMidMonthChanges(df):
    
    df.drop_duplicates(subset=['Serial Number'], keep='last', inplace=True, ignore_index=True)
    return df


def combineSourcewell(df1, df2, df3):
    
    df1 = removeMidMonthChanges(df1)
    df2 = removeMidMonthChanges(df2)
    df3 = removeMidMonthChanges(df3)

    
    df1SN = df1['Serial Number'].tolist()
    df2SN = df2['Serial Number'].tolist()
    df3SN = df3['Serial Number'].tolist()
    
    allSNs = df1SN + df2SN + df3SN
    uniqueSN = set(allSNs)
    uniquelist = list(uniqueSN)
    
    df = pd.DataFrame()
    df['Serial Number'] = uniquelist
    #st.write(len(df))
    df['Plan Name'] = ''
    df['Billing Info'] = ''
    #st.write('writing new columns')
    df['Months Billed'] = 0
    df['original'] = 1
    
    df = sourceone(df, df1)
    df = sourcetwo(df, df2)
    df = sourcethree(df, df3)
    
    
    return df


def sourceone(df, df1):
    
    for i in range(len(df)):
        for j in range(len(df1)):
            if df['Serial Number'][i] == df1['Serial Number'][j]:
                df['Months Billed'][i] += 1
                df['Plan Name'][i] = df1['Plan Name'][j]
                df['Billing Info'][i] = df1['Billing Info'][j]
                df['original'][i] = 1
    
    
    return df


def sourcetwo(df, df2):
    
    for i in range(len(df)):
        checker = 0
        for j in range(len(df2)):
            if checker == 0:
                if df['Serial Number'][i] == df2['Serial Number'][j] and df['original'][i] == 1:
                    if df['Billing Info'][i] == df2['Billing Info'][j]:
                        df['Months Billed'][i] += 1
                    else:
                        df['original'][i] = 0
                        sn = df['Serial Number'][i]
                        pn = df2['Plan Name'][j]
                        bi = df2['Billing Info'][j]
                        
                        
                        templine = {'Serial Number': sn, 'Plan Name': pn, 'Billing Info': bi, 'Months Billed': 1, 'original': 1}
                        df = df.append(templine, ignore_index = True)
                        checker = 1
    
    return df


def sourcethree(df, df3):
    
    for i in range(len(df)):
        checker = 0
        for j in range(len(df3)):
            if checker == 0:
                if df['Serial Number'][i] == df3['Serial Number'][j] and df['original'][i] == 1:
                    if df['Billing Info'][i] == df3['Billing Info'][j]:
                        df['Months Billed'][i] += 1
                    else:
                        df['original'][i] = 0
                        sn = df['Serial Number'][i]
                        pn = df3['Plan Name'][j]
                        bi = df3['Billing Info'][j]
                        df['Plan Name'][i] = df3['Plan Name'][j]
                        df['Billing Info'][i] = df3['Billing Info'][j]
                        
                        templine = {'Serial Number': sn, 'Plan Name': pn, 'Billing Info': bi, 'Months Billed': 1, 'original': 1}
                        df = df.append(templine, ignore_index = True)
                        checker = 1
    
    return df


def writeToCsv(d, lng, i, sourcewell):
    
    idx = i
    file = d[idx]['Database'].iloc[0]
    file += '.csv'
        
    df = d[idx]
    if sourcewell:
        if file[:-4] == 'cityofgrimes':
            df = df[['Serial Number', 'VIN', 'Billing Info']]
            df = df.rename(columns={'VIN': 'Plan Name'})
            df['Plan Name'] = df['Billing Info'].str.split('[').str[0]
            df['Billing Info'] = df['Billing Info'].str.split('[').str[1]
            df['Billing Info'] = df['Billing Info'].str[:-2]
            try:
                df['Billing Info'] = df['Billing Info'].astype(float) / 100.
            except ValueError:
                print(df['Billing Info'])
            #df['Billing Info'] = (df['Billing Info'].str[:2] + '.' + df['Billing Info'][-2:])
        
    else:
        df = df[['Serial Number', 'VIN', 'Bill Days', 'Quantity', 'Unit Cost', 'Cost']]
    df.index = np.arange(1, len(df) + 1)
    return df, file
        
    
    
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    
    return df.to_csv().encode("utf-8")

    
def getYear(y):
    if y < 2022 | y > 2999:
        y = 0
    return y
    

def getPrevMonDays(m, y):
    m = m.lower()
    days = 0
    if m == 'jan':
        days = 31
    elif m == 'feb':
        days = 31
    elif m == 'mar':
        days = 28
        if y % 4 == 0:
            days = 29
    elif m == 'apr':
        days = 31
    elif m == 'may':
        days = 30
    elif m == 'jun':
        days = 31
    elif m == 'jul':
        days = 30
    elif m == 'aug':
        days = 31
    elif m == 'sep':
        days = 31
    elif m == 'oct':
        days = 30
    elif m == 'nov':
        days = 31
    elif m == 'dec':
        days = 30
    else:
        days = 0
    return days


def getMonth(m):
    m = m.lower()
    if m == 'january':
        m = 'Jan'
    elif m == 'february':
        m = 'Feb'
    elif m == 'march':
        m = 'Mar'
    elif m == 'april':
        m = 'Apr'
    elif m == 'may':
        m = 'May'
    elif m == 'june':
        m = 'Jun'
    elif m == 'july':
        m = 'Jul'
    elif m == 'august':
        m = 'Aug'
    elif m == 'september':
        m = 'Sep'
    elif m == 'october':
        m = 'Oct'
    elif m == 'november':
        m = 'Nov'
    elif m == 'december':
        m = 'Dec'
    else:
        m = 'nono'
    return m


def srcwl(l, df):
    
    for i in range(l):
        tdf = df.loc[df['id'] == i]
        tdf = tdf.reset_index(drop=True)
        compname = tdf['Database'].iloc[0]
        
        if compname == 'cityofgrimes':
            return tdf
    return ''
        
    
    
    
    
    
    
    