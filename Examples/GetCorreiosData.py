# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 14:12:38 2020

@author: P_267274
"""

import numpy as np
import pandas as pd
import os
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
import pickle
import matplotlib.pyplot as plt
import datetime


def main(SCOPES,SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    # else:
    #     print('Name, Major:')
        # for row in values:
        #     # Print columns A and E, which correspond to indices 0 and 4.
        #     print('%s, %s' % (row, row))
            
    return values




def Create_Service(client_secret_file, api_service_name, api_version, *scopes):
    global service
    SCOPES = [scope for scope in scopes[0]]
    #print(SCOPES)
    
    cred = None

    if os.path.exists('token_write.pickle'):
        with open('token_write.pickle', 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            cred = flow.run_local_server()

        with open('token_write.pickle', 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(api_service_name, api_version, credentials=cred)
        print(api_service_name, 'service created successfully')
        return service
    except Exception as e:
        print(e)
        #return None
        
        
        
        
        
def getSheetsData(SAMPLE_SPREADSHEET_ID, dict_sheets):
    
    "Scrap data from a given spreadsheet link and tab"
    
    # Opening JSON file 
    f = open('credentials.json') 
      
    # returns JSON object as a dictionary 
    credentials = json.load(f)
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    #GET DATA FROM ORIGINAL GOOGLE SHEET
    # https://docs.google.com/spreadsheets/d/153R3WpTCWLFOomh5QO5zlr012X6iFEeeC2CKrpfSps0/edit?usp=sharing


    # here enter the id of your google sheet
    # SAMPLE_SPREADSHEET_ID= '153R3WpTCWLFOomh5QO5zlr012X6iFEeeC2CKrpfSps0'
    # SAMPLE_RANGE_NAME = "'Consolidado - Máscara'!A1:AA1000"
    
    
    # If modifying these scopes, delete the file token.pickle.
    dict_dfs={}    
    for key, value in dict_sheets.items():
        print (key, value)
        
        SAMPLE_RANGE_NAME = value        
        values=main(SCOPES,SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)  
        
        if ['Untitled Spreadsheet'] in values:     
            values.remove(['Untitled Spreadsheet'])
        df=pd.DataFrame(values[1:], columns=values[0])
        if '' in df.columns:
            df=df.drop('',axis=1)
        # eixo5_dfs.update(key=df)

        dict_dfs[key]=df   

         
    return dict_dfs
        
    print('Sheet successfully Updated')
    
    
def set_scraped_dfs(dicts_df):
    
    df_correios = dicts_df['Correios'].copy()

    df_correios[df_correios.columns[1:len(df_correios.columns)]]=df_correios[df_correios.columns[1:len(df_correios.columns)]].replace(to_replace=[',|\$'], value='', regex=True).astype(float)/1000000
    df_correios['Data']=pd.to_datetime('31/12/'+df_correios['Ano'], format="%d/%m/%Y")
    df_correios['ROI']=df_correios['Lucro Líquido']/abs(df_correios['PL'])


    df_amazon= dicts_df['Amazon'].copy()    
    df_amazon[['Lucro Líquido', 'PL']] = df_amazon[['Lucro Líquido', 'PL']].replace(to_replace=['|\$|B'], value='', regex=True).replace(to_replace=[''], value=np.nan, regex=True).astype(float)*1000000000/1000000
    df_amazon['ROI']=df_amazon['ROI'].replace(to_replace=['\%'], value='', regex=True).astype(float)/100
    df_amazon['PL']=np.where(df_amazon['PL'].isnull(),df_amazon['Lucro Líquido']/df_amazon['ROI'], df_amazon['PL'] )


    df_amazon['ROI2']=df_amazon['Lucro Líquido']/df_amazon['PL']
    # df_amazon['diff']=df_amazon['ROI2']-df_amazon['ROI']
    
    df_amazon['Data']=pd.to_datetime(df_amazon['Data'])    
    df_amazon = df_amazon[df_amazon['Data'].dt.strftime('%m')=='12']
    df_amazon.columns = [col  + '_AMZ' for col in df_amazon.columns.to_list()]
    
    df_amazon['Ano'] = df_amazon['Data_AMZ'].dt.strftime('%Y')
    
    
    df_fedex= dicts_df['FEDEX'].copy()
    df_fedex[['Lucro Líquido', 'PL']] = df_fedex[['Lucro Líquido', 'PL']].replace(to_replace=['|\$|B'], value='', regex=True).replace(to_replace=[''], value=np.nan, regex=True).astype(float)*1000000000/1000000
    df_fedex['ROI']=df_fedex['ROI'].replace(to_replace=['\%'], value='', regex=True).astype(float)/100


    df_fedex['ROI2']=df_fedex['Lucro Líquido']/df_fedex['PL']
    # df_fedex['diff']=df_fedex['ROI2']-df_fedex['ROI']
    
    df_fedex['Data']=pd.to_datetime(df_fedex['Data'])    
    df_fedex = df_fedex[df_fedex['Data'].dt.strftime('%m')=='11']    
    df_fedex.columns = [col  + '_FDX' for col in df_fedex.columns.to_list()]

    df_fedex['Ano'] = df_fedex['Data_FDX'].dt.strftime('%Y')
    
    
    df_magalu= dicts_df['Magalu'].copy()
    df_magalu[['Lucro Líquido', 'PL']] = df_magalu[['Lucro Líquido', 'PL']].replace(to_replace=['\.'], value='', regex=True).astype(float)/1000
    df_magalu['ROI']=df_magalu['Lucro Líquido']/abs(df_magalu['PL'])
    df_magalu['Data']=pd.to_datetime(df_magalu['Data'], format='%d/%m/%Y')    
    df_magalu = df_magalu[df_magalu['Data'].dt.strftime('%m')=='12']    
    df_magalu.columns = [col  + '_MGL' for col in df_magalu.columns.to_list()]

    df_magalu['Ano'] = df_magalu['Data_MGL'].dt.strftime('%Y')


    df_dolar=pd.read_csv("C:/Users/P_267274/Desktop/Trabalho/USD_BRL Dados Históricos.csv", header=0, sep=',')    #### NESTA PLANILHA LEGISLATURA.CSV ESTÃO AS DATAS DE INÍCIO E FIM DA LEGISLATURA
    df_dolar=df_dolar[['Data', 'Último']]
    df_dolar['Data']=pd.to_datetime(df_dolar['Data'], format='%d.%m.%Y')
    df_dolar['Ano']=df_dolar['Data'].dt.strftime('%Y')
    df_dolar['Último']=df_dolar['Último'].replace(to_replace=[','], value='.', regex=True).astype(float)

    df_dolar=df_dolar.sort_values('Data')
    
    df_dolary = pd.DataFrame()
    for year in df_dolar.Ano.drop_duplicates().to_list():
        df_filter = df_dolar[df_dolar['Ano']==year].sort_values('Data')
        df_dolary=df_dolary.append(df_filter.tail(1))
    df_dolary.columns = ['Data_DLR', 'USD', 'Ano']
    
    
    return df_correios, df_amazon,df_fedex, df_magalu, df_dolary
    

def plot_IndFinanceiros(df_correios):
    
    plt.figure(figsize=(10,7))

    plt.title('Indicadores Financeiros - Correios')
    # plt.subtitle('Correios')
    plt.plot(df_correios['Data'], df_correios['PL'], label='PL')
    plt.plot(df_correios['Data'], df_correios['Ativo Total'], label='Ativo')
    plt.plot(df_correios['Data'], df_correios['Passivo Total'], label='Passivo')
    plt.plot(df_correios['Data'], df_correios['Lucro Líquido'], label='Lucro Líquido')
    
    plt.plot(df_correios['Data'], [0]*len(df_correios), '--', color='black')
    plt.legend(loc='best', #bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    
    plt.ylabel('(em R$ milhões)')
    plt.savefig('Indicadores Financeiros - Correios.png', bbox_inches='tight') 

    plt.show()
    
    
    return ('Plot Feito')



def plot_LLprojection(df_correios):
    
    df_ll = df_correios[['Ano','Data', 'Lucro Líquido']]

    df_pct =df_ll.set_index('Data')['Lucro Líquido'].pct_change().to_frame().reset_index().rename(columns={'Lucro Líquido':'PCT'})
    df_ll = pd.merge(df_ll, df_pct, how='left', on=['Data'])
    
    
    df_ll_aux = pd.DataFrame({'Data' : [datetime.date(2020, 12, 31), datetime.date(2021, 12, 31)],
                              'Lucro Líquido': [df_ll.iloc[len(df_ll)-1]['Lucro Líquido'].item()*(1+df_ll.iloc[len(df_ll)-1]['PCT'].item()),
                                                df_ll.iloc[len(df_ll)-1]['Lucro Líquido'].item()*(1+df_ll.iloc[len(df_ll)-1]['PCT'].item())**2]})
    
    df_ll = df_ll.append(df_ll_aux)
    df_ll['Data']=pd.to_datetime(df_ll['Data'])
    df_ll['Ano']=df_ll['Data'].dt.strftime('%Y')
    
    
    
    df_ll['LL2'] = np.where(df_ll['Ano'].isin(['2020','2021']),df_ll['Lucro Líquido'],np.nan)
    df_ll['LL2'] = np.where(df_ll['Ano'].isin(['2019']),df_ll['Lucro Líquido'],df_ll['LL2'])
    
    df_ll['LL3'] = np.where(df_ll['Ano'].isin(['2020','2021']),df_ll['Lucro Líquido']-31,np.nan)
    df_ll['LL3'] = np.where(df_ll['Ano'].isin(['2019']),df_ll['Lucro Líquido'],df_ll['LL3'])
    
    
    df_ll_filter = df_ll[df_ll['Ano'].isin(['2018','2019','2020','2021'])]
    df_ll_filter['Lucro Líquido'] = np.where(df_ll_filter['Ano'].isin(['2019','2018', '']),df_ll_filter['Lucro Líquido'],np.nan)
    
    
    
    #PLOT
    plt.figure(figsize=(10,7))
    plt.title('Projeção Lucro Líquido Correios Correios')
    
    plt.plot(df_ll_filter['Data'], df_ll_filter['Lucro Líquido'], label='Lucro Líquido', color='blue',)
    plt.plot(df_ll_filter['Data'], df_ll_filter['LL2'], label='Projeção s/ aumento',linestyle= '--', color='blue')
    plt.plot(df_ll_filter['Data'], df_ll_filter['LL3'], label='Projeção c/ aumento', linestyle='--', color='red')
    
    plt.plot([datetime.datetime.strptime('2019-12-31', '%Y-%m-%d')]*4,[0,50,100,160] , linestyle='--', color='black')
    
    plt.legend(loc='best', #bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
    
    plt.ylabel('(em R$ milhões)')
    plt.savefig('Projeção Lucro Líquido.png', bbox_inches='tight') 

    plt.show()
    
    
    print(df_ll_filter['LL2']/df_ll_filter['LL3']-1)

    return ('Plot Feito')



def plot_ROI(df_merged_filter):
        
    plt.figure(figsize=(10,7))

    plt.title('ROI Comparação')
    # plt.subtitle('Correios')
    plt.plot(df_merged_filter['Data'], df_merged_filter['ROI'], label='Correios')
    # plt.plot(df_merged_filter['Data'], df_merged_filter['ROI2_AMZ'], label='AMAZON')
    # plt.plot(df_merged_filter['Data'], df_merged_filter['ROI2_FDX'], label='FEDEX')
    plt.plot(df_merged_filter['Data'], df_merged_filter['ROI_MGL'], label='MAGALU')

    
    plt.plot(df_merged_filter['Data'], [0]*len(df_merged_filter), '--', color='black')
    plt.legend(loc='best', #bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    
    plt.ylabel('(Lucro Líquido / Patrimônio Líquido)')
    # plt.savefig('Indicadores Financeiros - Correios.png', bbox_inches='tight') 

    plt.show()
    
    return ('Plot Feito')



def plot_LL(df_merged_filter):
        
    plt.figure(figsize=(10,7))

    plt.title('Lucro Líquido')
    # plt.subtitle('Correios')
    plt.plot(df_merged_filter['Data'], df_merged_filter['Lucro Líquido'], label='Correios')
    # plt.plot(df_merged_filter['Data'], df_merged_filter['Lucro Líquido_AMZ'], label='AMAZON')
    plt.plot(df_merged_filter['Data'], df_merged_filter['Lucro Líquido_FDX'], label='FEDEX')
    plt.plot(df_merged_filter['Data'], df_merged_filter['Lucro Líquido_MGL'], label='MAGALU')

    
    plt.plot(df_merged_filter['Data'], [0]*len(df_merged_filter), '--', color='black')
    plt.legend(loc='best', #bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    
    plt.ylabel('(em R$ milhões)')
    plt.savefig('Comparação Lucro Líquido.png', bbox_inches='tight') 

    plt.show()
    
    return ('Plot Feito')


if __name__=='__main__':

    mypath='C:/Users/P_267274/Desktop/Trabalho/Correios'
    os.chdir(mypath)

    # https://docs.google.com/spreadsheets/d/1C2EJgq4KLkItuiDmDltBmvGYZ4aN-6iRBwoTxI0SjLs/edit?usp=sharing

    SAMPLE_SPREADSHEET_ID= '1C2EJgq4KLkItuiDmDltBmvGYZ4aN-6iRBwoTxI0SjLs'
    dict_sheets = {
                    'Correios': "Correios",
                    'FEDEX': "FEDEX",
                    'Amazon': "Amazon",
                    'Magalu':'Magalu'

                    }

    dicts_df = getSheetsData(SAMPLE_SPREADSHEET_ID, dict_sheets)
    
    
    df_correios, df_amazon,df_fedex, df_magalu, df_dolary = set_scraped_dfs(dicts_df)


    df_merged = pd.merge(df_correios,df_amazon, how='left', on='Ano')
    df_merged = pd.merge(df_merged,df_fedex, how='left', on='Ano')
    df_merged = pd.merge(df_merged,df_magalu, how='left', on='Ano')
    df_merged = pd.merge(df_merged,df_dolary, how='left', on='Ano')


    df_merged_filter = df_merged.dropna(subset=['Data_MGL'])
    df_merged_filter=df_merged_filter[df_merged_filter['Ano'].isin(['2013','2014','2015', '2016', '2017', '2018', '2019'])]

    df_merged_filter['Lucro Líquido_AMZ'] = df_merged_filter['Lucro Líquido_AMZ'] *  df_merged_filter['USD']
    df_merged_filter['PL_AMZ'] = df_merged_filter['PL_AMZ'] *  df_merged_filter['USD']
    df_merged_filter['Lucro Líquido_FDX'] = df_merged_filter['Lucro Líquido_FDX'] *  df_merged_filter['USD']
    df_merged_filter['PL_FDX'] = df_merged_filter['PL_FDX'] *  df_merged_filter['USD']

    plot_LLprojection(df_correios)
    plot_IndFinanceiros(df_correios)
    plot_ROI(df_merged_filter)
    plot_LL(df_merged_filter)




