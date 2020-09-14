#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 01:05:06 2020

@author: pedrocampelo
"""


import time
import os
import pandas as pd
import datetime as dt
import numpy as np
import regex as re
import sys
import ipeadatapy as ipea
import seaborn as sns
import matplotlib.pyplot as plt
import math


import sklearn

from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
# from sklearn.metrics import accuracy_score
from sklearn.metrics import r2_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

from sklearn.model_selection import GridSearchCV
from sklearn.calibration import CalibratedClassifierCV
from sklearn.datasets import make_moons

from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.naive_bayes import ComplementNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import BaggingClassifier


def open_dfs():
    
    ############################################ OPENING AND SETTING DATABASES ####################################

    # df_fidc = pd.read_excel('Dados FIDCs 2.xlsx')
    # df_fidc.to_pickle("Dados FIDCS.pkl")
    
    
    print('Abrindo e arrumando base da CVM')
    df_fidc = pd.read_pickle(r'./Dados CVM/Dados FIDCS.pkl')
    
    
    
    
   
    print('Abrindo e arrumando base de ratings')
    df_rating = pd.read_excel('./Rating/Rating FIDCs - 2020.xlsx')
    
    print('Bases Abertas com sucesso!')
    
    return df_fidc, df_rating





def filter_dfs(df_fidc, df_rating):
    
    print('Filtrando DF FIDC da CVM')
    #FILTER FIDC DF
    #df_fidc['TAB_X_CLASSE_SERIE_AUX'].unique()   
    df_fidc['TAB_X_CLASSE_SERIE_AUX'] = np.where(df_fidc['TAB_X_CLASSE_SERIE'].str.contains('Sénior|Sênior|Série'),'Senior','Subordinada')
    df_fidc_senior = df_fidc[df_fidc['TAB_X_CLASSE_SERIE_AUX']=='Senior'] 
    
      
    print('Filtrando DF RATING')

    #FILTER RATING DF
     
    df_rating_filter1 = df_rating[df_rating['Tipo Cota']=='Senior']                                                                        #FILTRO 1 (COTA SENIOR)
    #df_rating_filter=df_rating_filter[df_rating_filter['Rating'].str.contains('AA|AAA|A\\+')] 
    df_rating_filter2=df_rating_filter1[~pd.isnull(df_rating_filter1['CNPJ'])]                                                               #FILTRO 2 (CNPJ VAZIOS)
    df_rating_filter2["Data"] = pd.to_datetime(df_rating_filter1['Data'], errors='coerce')
    df_rating_filter2["Data Vencimento"] = pd.to_datetime(df_rating_filter2['Data Vencimento'], errors='coerce')
    df_rating_filter2["Data Rating Antigo"] = pd.to_datetime(df_rating_filter2['Data Rating Antigo'], errors='coerce')
    df_rating_filter2["Data Vencimento Antigo"] = pd.to_datetime(df_rating_filter2['Data Vencimento Antigo'], errors='coerce')
    
    df_rating_filter2['Rating_AUX'] = df_rating_filter2['Rating'].replace(to_replace=['\(.*\)|\.|sf|br| '], value='', regex=True)
    df_rating_filter2['Rating_AUX']=df_rating_filter2['Rating_AUX'].apply(str.upper)
  
    df_rating_filter3=df_rating_filter2[~(df_rating_filter2['Rating_AUX'].str.contains('ENCERRADO|RETIRADO|NR'))]                            #FILTRO 3 (COTAS ENCERRADAS E S/ RATING)
    df_rating_filter3=df_rating_filter3[~(df_rating_filter3['Rating_AUX']=='')]                                                              #FILTRO 3
        
    
    print('Verificando a chave das duas bases')
    cnpj_fidc_list = df_fidc_senior['CNPJ_FUNDO'].unique().tolist()
    cnpj_rating_list = df_rating_filter3['CNPJ'].unique().tolist()
       
    
    intersect_list = set(cnpj_fidc_list).intersection(set(cnpj_rating_list))
    # fidc_list = set(cnpj_fidc_list) - set(cnpj_rating_list)
    rating_list = set(cnpj_rating_list) - set(cnpj_fidc_list)

    # a=df_rating_filter3[df_rating_filter3['CNPJ'].isin(list(rating_list))]  

    df_rating_filter4=df_rating_filter3[~df_rating_filter3['CNPJ'].isin(list(rating_list))]  #FILTRO 4 (COTAS QUE NAO ESTAO NA BASE DA CVM)
                                        
 
    if len(intersect_list)/len(cnpj_rating_list)>0.85:
        print('Maioria dos FIDCs com Rating estao na base da CVM')
    else:
        print('Muitos FIDCs avaliados nao estao na lista da CVM!!!!')
        sys.exit()
    
    print('Distinguindo os ratings pela Data de availiacao mais proxima')
    df_rating_final=pd.DataFrame()
    for cnpj in df_rating_filter4['CNPJ'].unique().tolist():
        df_aux=df_rating_filter4[df_rating_filter4['CNPJ']==cnpj]
        if len(df_aux['Rating'].unique())>1:
            # print('Retirar rating antigos')
            df_aux=df_aux[df_aux['Data']==max(df_aux['Data'].tolist())]

        df_aux=df_aux[0:1]
        df_aux=df_aux[['CNPJ','ISIN','Rating','Rating_AUX','Data', 'Data Vencimento','Rating Antigo', 
                       'Data Rating Antigo', 'Data Vencimento Antigo','Agencia']]
        df_rating_final=df_rating_final.append(df_aux)                              #FILTRO 5 (NOTAS DUPLICADAS)
        
        
    df_rating_final = df_rating_final.rename(columns={'CNPJ':'CNPJ_FUNDO', 'Data':'Data Rating'})      
              
 
    
    #PEGAR A- PRA CIMA
    # df_rating_final = df_rating_append[df_rating_append['Rating_AUX'].isin(['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A','A-',])]
    
    print('Agregando as duas bases')
    fidcs_df = df_fidc_senior.merge(df_rating_final,how='left',on='CNPJ_FUNDO')
    
    # fidcs_df = fidcs_df[~pd.isnull(fidcs_df['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    #fidcs_wrating= df_fidc_agg[pd.isnull(df_fidc_agg['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    
    
    
    fidcs_df['TAB_X_CLASSE_SERIE'] = fidcs_df['TAB_X_CLASSE_SERIE'].replace(to_replace=['Classe Sénior|Sênior'], value='Série', regex=True)
    fidcs_df = fidcs_df.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])
    

    
    df_fidc_sub = df_fidc[df_fidc['TAB_X_CLASSE_SERIE_AUX']=='Subordinada'] 
    df_fidc_sub = df_fidc_sub[df_fidc_sub['CNPJ_FUNDO'].isin(fidcs_df['CNPJ_FUNDO'].unique())]
    df_fidc_sub= df_fidc_sub[['DENOM_SOCIAL','CNPJ_FUNDO','Data',
                             'TAB_X_QT_COTA','TAB_X_VL_COTA','TAB_X_VL_RENTAB_MES','TAB_X_NR_COTST',
                             'TAB_X_VL_TOTAL_AMORT','TAB_X_VL_TOTAL_CAPT','TAB_X_VL_TOTAL_RESGSOL','TAB_X_VL_TOTAL_RESG',
                             'TAB_X_QT_TOTAL_AMORT','TAB_X_QT_TOTAL_CAPT','TAB_X_QT_TOTAL_RESGSOL','TAB_X_QT_TOTAL_RESG'
                             ]]
    
    #FILTRAR NAN NA BASE SUB
    na_col_sub = df_fidc_sub.isna().sum(axis=0).to_frame().reset_index()
    
    #retirar colunas com mais de 1.5% na
    df_fidc_sub=df_fidc_sub[na_col_sub[na_col_sub[0]<0.015*len(df_fidc_sub)]['index'].to_list()]  

    na_col_sub2 = df_fidc_sub.isna().sum(axis=0).to_frame().reset_index()
    if len(na_col_sub2[na_col_sub2[0]>0][0].unique())==1:
        
        #Verificar se o numero de linhas com NA é o mesmo
        #Se for, pode escolher arbitrariamente qualquer coluna, retirar os NANs que provavelmente 
        
        df_fidc_sub = df_fidc_sub[~df_fidc_sub[na_col_sub2[na_col_sub2[0]>0]['index'].unique()[1]].isna()]
    else:
        print("Verficar colunas com NAS Diferentes!")
        
    if len(df_fidc_sub.isna().sum(axis=0).to_frame().reset_index()[0].unique())==1 & df_fidc_sub.isna().sum(axis=0).to_frame().reset_index()[0].unique().item()==0:
        print('Base sem NANs')


    df_fidc_sub = df_fidc_sub.groupby(['DENOM_SOCIAL','CNPJ_FUNDO','Data']).mean() 
       
    df_fidc_sub.columns = [column + '_SUB' for column in df_fidc_sub.columns.tolist()]
    df_fidc_sub = df_fidc_sub.reset_index()
    
    
    #MERGE COM AS RENTS SUBORDINADAS
    fidcs_df_final = fidcs_df.merge(df_fidc_sub,how='left',on=['DENOM_SOCIAL','CNPJ_FUNDO','Data'])
    # fidcs_df_final=fidcs_df_final[~fidcs_df_final['TAB_X_VL_RENTAB_MES_SUB'].isna()]
    fidcs_df_final = fidcs_df_final.drop(['CNPJ_ADMIN','ADMIN'], axis=1)                 #REMOVER COLUNAS IRRELEVANTES COM NA
    
    

    
    #CRIAR DUMMIES IMPORTANTES
    fidcs_df_final['Ano'] = fidcs_df_final['Data'].dt.year
    fidcs_df_final['Mes'] = fidcs_df_final['Data'].dt.month
    # fidcs_df_final['Ano_Rating'] = fidcs_df_final['Data Rating'].dt.year.fillna(0)
    # fidcs_df_final['Mes_Rating'] = fidcs_df_final['Data Rating'].dt.month.fillna(0)
    
    #Create year dummies 
    fidcs_df_final['d_a2013'] = np.where(fidcs_df_final['Ano']==2013,1,0)
    fidcs_df_final['d_a2014'] = np.where(fidcs_df_final['Ano']==2014,1,0)
    fidcs_df_final['d_a2015'] = np.where(fidcs_df_final['Ano']==2015,1,0)
    fidcs_df_final['d_a2016'] = np.where(fidcs_df_final['Ano']==2016,1,0)
    fidcs_df_final['d_a2017'] = np.where(fidcs_df_final['Ano']==2017,1,0)
    fidcs_df_final['d_a2018'] = np.where(fidcs_df_final['Ano']==2018,1,0)
    fidcs_df_final['d_a2019'] = np.where(fidcs_df_final['Ano']==2019,1,0)
    fidcs_df_final['d_a2020'] = np.where(fidcs_df_final['Ano']==2020,1,0)
    fidcs_df_final['d_a2021'] = np.where(fidcs_df_final['Ano']==2021,1,0)

    #Create month dummies
    fidcs_df_final['d_m1'] = np.where(fidcs_df_final['Mes']==1,1,0)
    fidcs_df_final['d_m2'] = np.where(fidcs_df_final['Mes']==2,1,0)
    fidcs_df_final['d_m3'] = np.where(fidcs_df_final['Mes']==3,1,0)
    fidcs_df_final['d_m4'] = np.where(fidcs_df_final['Mes']==4,1,0)
    fidcs_df_final['d_m5'] = np.where(fidcs_df_final['Mes']==5,1,0)
    fidcs_df_final['d_m6'] = np.where(fidcs_df_final['Mes']==6,1,0)
    fidcs_df_final['d_m7'] = np.where(fidcs_df_final['Mes']==7,1,0)
    fidcs_df_final['d_m8'] = np.where(fidcs_df_final['Mes']==8,1,0)
    fidcs_df_final['d_m9'] = np.where(fidcs_df_final['Mes']==9,1,0)
    fidcs_df_final['d_m10'] = np.where(fidcs_df_final['Mes']==10,1,0)
    fidcs_df_final['d_m11'] = np.where(fidcs_df_final['Mes']==11,1,0)
    fidcs_df_final['d_m12'] = np.where(fidcs_df_final['Mes']==12,1,0)    

    return fidcs_df_final



def check_solis_fidcs(df_merged):
    #check fidcs with default

    fidcs_default = df_merged[df_merged['DENOM_SOCIAL'].str.contains('ARCTURUS|BELLATRIX|BONSUCESSO|ODEBRECHT|LAVORO II|LEGO|MARTINS|ODYSSEY|ORION|PREVIMIL|SILVERADO|TRENDBANK')]
    fidcs_default_filtered = fidcs_default#[cols_of_intenterest]
        
    return fidcs_default_filtered


def set_defaults_df(df_merged, month_forescast, ipeaseries_dict):


    #FILTER FIDCS IN DEFAULT
    fidc_filter = pd.DataFrame({})
    last_date = df_merged.sort_values('Data')['Data'].unique()[-2]
    

    for cnpj in df_merged['CNPJ_FUNDO'].unique():
        print('CNPJ ', cnpj)
        
        fidc_filter_aux2 = df_merged[df_merged['CNPJ_FUNDO']==cnpj]
        
        for serie in fidc_filter_aux2['TAB_X_CLASSE_SERIE'].unique():
                # print('Serie', serie)
          
                fidc_filter_aux = fidc_filter_aux2[fidc_filter_aux2['TAB_X_CLASSE_SERIE']==serie].sort_values('Data')
    
                #CONDITIONS FOR DEFAULT :
                    #1) ANO < ULTIMO ANO DA BASE
                    #2) RENT <0  (ULTIMA LINHA)
                    #2) PL <0.05  (ULTIMA LINHA)
                    #2) RENTSUB <0.0  (ULTIMA LINHA)  
                
                date = fidc_filter_aux['Data'].to_list()[-1]
                rent = fidc_filter_aux['TAB_X_VL_RENTAB_MES'].tail(1).item()
                pl = fidc_filter_aux['TAB_IV_A_VL_PL'].tail(1).item()
                rent_sub = fidc_filter_aux['TAB_X_VL_RENTAB_MES_SUB'].tail(1).item()
               
                if (date < last_date) and (rent<=0) and (pl<=0.05) and ((rent_sub<=0.0) or (math.isnan(rent_sub))):
                    fidc_filter_aux['default']=1
                else:
                    fidc_filter_aux['default']=0
                    
                    
                fidc_filter = fidc_filter.append(fidc_filter_aux)     
                
    fidcs_ndefault=fidc_filter[fidc_filter['default']==0]#[cols_of_intenterest]
    fidcs_ndefault['Y']=0
    fidcs_default=fidc_filter[fidc_filter['default']==1]#[cols_of_intenterest]
    
    #SET Y VARIABLE TO FIND WHAT MONTH DEFAULT WAS 
    fidc_filter = pd.DataFrame({})
    for cnpj in fidcs_default['CNPJ_FUNDO'].unique():
        print('CNPJ ', cnpj)
        
        fidc_filter_aux2 = fidcs_default[fidcs_default['CNPJ_FUNDO']==cnpj]
        
        for serie in fidc_filter_aux2['TAB_X_CLASSE_SERIE'].unique():
                print('Serie', serie)
     
                fidc_filter_aux = fidc_filter_aux2[fidc_filter_aux2['TAB_X_CLASSE_SERIE']==serie].sort_values('Data').reset_index()
    
                default_list = []
                for row in range(len(fidc_filter_aux.index),0,-1):
                    # print(row-1)
    
                    if fidc_filter_aux.iloc[row-1,:]['TAB_IV_A_VL_PL']<=.05:
                        # print(fidc_filter_aux.iloc[row-1,:]['Data'])
                        default_list.append(row-1)
                        
                    else:
                        break
                    
                if len(default_list)<5:
                    num = default_list[-1]-1 #or len(fidc_filter_aux)-1-len(default_list)
                    
                    default_list.append(num)
    
                fidc_filter_aux['Y'] = np.where(fidc_filter_aux.index.isin(default_list), 1, 0)                  
                fidc_filter = fidc_filter.append(fidc_filter_aux)     
        
        
    #MERGE DEFAULT AND NOT DEFAULT DFs
    fidcs_default = fidc_filter   

    
    fidcs_merged = fidcs_ndefault.append(fidcs_default)
    fidcs_merged=fidcs_merged.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])
    
    fidcs_merged = fidcs_merged.drop('index', axis=1)
    
    

    df_merged2=pd.DataFrame()
    for cnpj in fidcs_merged['CNPJ_FUNDO'].unique():
        
        df_filter1 =  fidcs_merged[fidcs_merged['CNPJ_FUNDO']==cnpj]
        # print(df_filter1['TAB_X_CLASSE_SERIE'].unique())
        for serie in df_filter1['TAB_X_CLASSE_SERIE'].unique():
                    
            df_filter2 =  df_filter1[df_filter1['TAB_X_CLASSE_SERIE']==serie]
            
            if len(df_filter2)>=month_forescast:

                df_y = df_filter2[['Y','Data']].rename(columns={'Data':'Data_Y'})
                df_X = df_filter2.drop(['Y'], axis=1).shift(month_forescast).rename(columns={'Data':'Data_X'})
                df_merged_aux = pd.concat([df_y, df_X], axis=1).dropna(subset=['CNPJ_FUNDO'])
                
                df_merged2 = df_merged2.append(df_merged_aux) 
    df_merged2['days_diff']=(df_merged2['Data_Y']-df_merged2['Data_X']) / np.timedelta64(1, 'D')


    # a = df_merged2[['CNPJ_FUNDO', 'DENOM_SOCIAL','Data_Y','Data_X','days_diff','default','Y','TAB_X_VL_RENTAB_MES', 'TAB_X_VL_RENTAB_MES_SUB', 'TAB_IV_A_VL_PL']]
    
    
    condition = [df_merged2['Mes'].isin([1,2,3]),df_merged2['Mes'].isin([4,5,6]),
                 df_merged2['Mes'].isin([7,8,9]) ,df_merged2['Mes'].isin([10,11,12])]
    choise = ['1T', '2T', '3T', '4T']                  
    df_merged2['Trim']=np.select(condition, choise, default= '')


    for column in ['TAB_X_VL_RENTAB_MES_SUB', 'TAB_X_VL_COTA_SUB','TAB_X_QT_COTA_SUB']:

         mask1 = df_merged2[column].shift() > 0.0
         mask2 = ((df_merged2[column].shift() < 0.0) & (df_merged2[column] > df_merged2[column].shift()))
         mask3 = ((df_merged2[column].shift() < 0.0) & (df_merged2[column] < df_merged2[column].shift()))
         
         
         if column == 'TAB_X_VL_RENTAB_MES_SUB':
             column_name = 'rent_ratio'
         
         elif column == 'TAB_X_VL_COTA_SUB':
             column_name = 'vlcota_ratio'                
         
         else: 
             column_name = 'qtcota_ratio'
 
         
         df_merged2[column_name] = np.select([mask1, mask2, mask3],
                                         [df_merged2[column].pct_change(), abs(df_merged2[column].pct_change()),
                                          -df_merged2[column].pct_change()],
                                         0)

    fidcs_ndefault = df_merged2[
        ((df_merged2['default']==0) & ((df_merged2['days_diff']<=(month_forescast+2)*31) & (df_merged2['days_diff']>=(month_forescast-2)*30)))  #DP DE 2 MESES PARA DIFERENCAS DE DATAS EM CASO DE NAO DEFAULT
        ]


    #FILTRAR NAN NA BASE NAO-DEFAULT
    na_col_ndefault= fidcs_ndefault.isna().sum(axis=0).to_frame().reset_index()
    
    #retirar colunas com mais de 15% na
    fidcs_ndefault=fidcs_ndefault[na_col_ndefault[na_col_ndefault[0]<0.15*len(fidcs_ndefault)]['index'].to_list()].dropna()


    #REMOVE OUTLIERS
    print('Removendo outliers da base')
    fidcs_ndefault_aux =  fidcs_ndefault[((fidcs_ndefault['TAB_X_VL_RENTAB_MES']<np.percentile(fidcs_ndefault['TAB_X_VL_RENTAB_MES'], 99.9)) & 
                                          (fidcs_ndefault['TAB_X_VL_RENTAB_MES']>np.percentile(fidcs_ndefault['TAB_X_VL_RENTAB_MES'], 0.05)))]
    sns.boxplot(x="Ano", y="TAB_X_VL_RENTAB_MES", data=fidcs_ndefault_aux)
    # plt.savefig('Rentabilidade Média por Ano.png', bbox_inches='tight')     
    plt.show()


    df_quant = fidcs_ndefault.groupby("Ano")["TAB_X_VL_RENTAB_MES"].quantile([0.045, 0.985]).unstack(level=1)
    fidcs_ndefault = fidcs_ndefault.loc[((df_quant.loc[fidcs_ndefault['Ano'], 0.045] < fidcs_ndefault['TAB_X_VL_RENTAB_MES'].values) & 
                                         (fidcs_ndefault['TAB_X_VL_RENTAB_MES'].values < df_quant.loc[fidcs_ndefault['Ano'], 0.985])).values]
                                         
    sns.boxplot(x="Ano", y="TAB_X_VL_RENTAB_MES", data=fidcs_ndefault)
    plt.savefig('Rentabilidade Média por Ano - Filtrada.png', bbox_inches='tight') 

    plt.show()



    #Retirar dados com dados com datas muito espacadas
    fidcs_default=df_merged2[
        ((df_merged2['default']==1) & ((df_merged2['days_diff']<=(month_forescast+30)*31) & (df_merged2['days_diff']!=0)))                        #MAIS FLEXIVEL NA DIFERENCA DE DATAS
        ][fidcs_ndefault.columns.to_list()]


    #FILTRAR NAN NA BASE DEFAULT
    na_col_default= fidcs_default.isna().sum(axis=0).to_frame().reset_index()


    df_merged3=pd.DataFrame()
    for cnpj in fidcs_default['CNPJ_FUNDO'].unique():
        
        df_filter1 =  fidcs_default[fidcs_default['CNPJ_FUNDO']==cnpj]
        # print(df_filter1['TAB_X_CLASSE_SERIE'].unique())
        for serie in df_filter1['TAB_X_CLASSE_SERIE'].unique():
                    
            df_filter2 = df_filter1[df_filter1['TAB_X_CLASSE_SERIE']==serie]
            
            
            # df_filter2 = df_filter2[['CNPJ_FUNDO', 'DENOM_SOCIAL','Data_Y','Data_X','Mes','Ano','Trim','Y','TAB_X_VL_RENTAB_MES', 'TAB_X_VL_RENTAB_MES_SUB', 'TAB_IV_A_VL_PL', 'TAB_X_VL_COTA_SUB','TAB_X_QT_COTA_SUB']]
            
                
            
            df_aux = df_filter2#[['CNPJ_FUNDO', 'DENOM_SOCIAL','Data_Y','Data_X','Ano', 'Trim','TAB_X_VL_RENTAB_MES_SUB', 'TAB_X_VL_COTA_SUB','TAB_X_QT_COTA_SUB']]            
            df_aux=df_aux.reset_index().drop('index',axis=1)
            
            
            if math.isnan(df_aux.iloc[0,:]['TAB_X_VL_RENTAB_MES_SUB']):
                df_aux['TAB_X_VL_RENTAB_MES_SUB'] = np.where(df_aux.index==0, 0, df_aux['TAB_X_VL_RENTAB_MES_SUB'])
                
                # df_aux.loc[df_aux.index==0, 'TAB_X_VL_RENTAB_MES_SUB']=0

            if math.isnan(df_aux.iloc[0,:]['TAB_X_VL_COTA_SUB']):
                df_aux['TAB_X_VL_COTA_SUB'] = np.where(df_aux.index==0, 0, df_aux['TAB_X_VL_COTA_SUB'])  
                # df_aux.loc[df_aux.index==0, 'TAB_X_VL_COTA_SUB']=0

            if math.isnan(df_aux.iloc[0,:]['TAB_X_QT_COTA_SUB']):
                df_aux['TAB_X_QT_COTA_SUB'] = np.where(df_aux.index==0, 0, df_aux['TAB_X_QT_COTA_SUB']) 
                # df_aux.loc[df_aux.index==0, 'TAB_X_QT_COTA_SUB']=0

                    
            df_ratio_grouped = df_aux[['Ano', 'Trim','rent_ratio',
                                       'vlcota_ratio','qtcota_ratio']].groupby(['Ano', 'Trim']).mean().rename(columns={'rent_ratio':'ratio_rent_mean',
                                                                                                                       'vlcota_ratio':'ratio_vlcota_mean',
                                                                                                                       'qtcota_ratio':'ratio_qtcota_mean'})               
            df_aux = df_aux.merge(df_ratio_grouped,how='left', on=['Ano', 'Trim'])
            
            
            df_aux['rent_ratio_aux']=df_aux[['rent_ratio','ratio_rent_mean']].min(axis = 1) 
            df_aux['rent_ratio_aux']=np.where(df_aux['rent_ratio_aux']>0.25,0.25,df_aux['rent_ratio_aux'])
            df_aux['rent_ratio_aux']=np.where(df_aux['rent_ratio_aux']<-0.4,-0.4,df_aux['rent_ratio_aux'])
            
            df_aux['vlcota_ratio_aux']=df_aux[['rent_ratio','ratio_vlcota_mean']].min(axis = 1) 
            df_aux['vlcota_ratio_aux']=np.where(df_aux['vlcota_ratio_aux']>0.25,0.24,df_aux['vlcota_ratio_aux'])
            df_aux['vlcota_ratio_aux']=np.where(df_aux['vlcota_ratio_aux']<-0.4,-0.4,df_aux['vlcota_ratio_aux'])
            
            df_aux['qtcota_ratio_aux']=df_aux[['rent_ratio','ratio_qtcota_mean']].min(axis = 1) 
            df_aux['qtcota_ratio_aux']=np.where(df_aux['qtcota_ratio_aux']>0.25,0.25,df_aux['qtcota_ratio_aux'])
            df_aux['qtcota_ratio_aux']=np.where(df_aux['qtcota_ratio_aux']<-0.4,-0.4,df_aux['qtcota_ratio_aux'])

            rent = []
            # rent2 = []
            vlcota = []
            # vlcota2 = []
            qtcota = []
            # qtcota2 = []
           
            for row in range(len(df_aux)):
                # print(row)
                
                if df_aux.iloc[row,:]['rent_ratio_aux']!=0:
                    rent_ratio = df_aux.iloc[row,:]['rent_ratio_aux']
                # if df_aux.iloc[row,:]['ratio_rent_mean']!=0:
                    # rent2_ratio = df_aux.iloc[row,:]['ratio_rent_mean']
                if df_aux.iloc[row,:]['vlcota_ratio_aux']!=0:
                    vlcota_ratio = df_aux.iloc[row,:]['vlcota_ratio_aux']
                # if df_aux.iloc[row,:]['ratio_vlcota_mean']!=0:
                    # vlcota2_ratio = df_aux.iloc[row,:]['ratio_vlcota_mean']
                if df_aux.iloc[row,:]['qtcota_ratio_aux']!=0:
                    qtcota_ratio = df_aux.iloc[row,:]['qtcota_ratio_aux']
                # if df_aux.iloc[row,:]['ratio_qtcota_mean']!=0:
                    # qtcota2_ratio = df_aux.iloc[row,:]['ratio_qtcota_mean']

                                  
                if math.isnan(df_aux.iloc[row,:]['TAB_X_VL_RENTAB_MES_SUB']):
                    
                    if rent[row-1]<0 and rent_ratio<=0:
                        rent.append(rent[row-1]*(1+(abs(rent_ratio))))
                        # rent2.append(rent2[row-1]*abs((1+(rent2_ratio))))                          
                        
                    else:
                        
                        rent.append(rent[row-1]*(1+(rent_ratio)))
                        # rent2.append(rent2[row-1]*(1+(rent2_ratio)))
                else:
                    
                    rent.append(df_aux.iloc[row,:]['TAB_X_VL_RENTAB_MES_SUB'])
                    # rent2.append(df_aux.iloc[row,:]['TAB_X_VL_RENTAB_MES_SUB'])
                    
                if math.isnan(df_aux.iloc[row,:]['TAB_X_VL_COTA_SUB']):
                    
                    if vlcota[row-1]<0 and vlcota_ratio<=0:
                        vlcota.append(rent[row-1]*(1+abs(vlcota_ratio)))
                        # vlcota2.append(rent2[row-1]*abs((1+(vlcota2_ratio))))                          
                        
                    else:
                        
                        vlcota.append(vlcota[row-1]*(1+(vlcota_ratio)))
                        # vlcota2.append(vlcota2[row-1]*(1+(vlcota2_ratio)))

                else:
                                            
                    vlcota.append(df_aux.iloc[row,:]['TAB_X_VL_COTA_SUB'])
                    # vlcota2.append(df_aux.iloc[row,:]['TAB_X_VL_COTA_SUB'])
                    
                if math.isnan(df_aux.iloc[row,:]['TAB_X_VL_RENTAB_MES_SUB']):

                    
                    # qtcota.append(qtcota[row-1]*(1+(qtcota_ratio)))

                    if qtcota[row-1]<0 and qtcota_ratio<=0:
                        qtcota.append(rent[row-1]*(1+abs(qtcota_ratio)))
                        # qtcota2.append(rent2[row-1]*abs((1+(qtcota2_ratio))))                          
                        
                    else:
                        
                        qtcota.append(qtcota[row-1]*(1+(qtcota_ratio)))
                        # qtcota2.append(qtcota2[row-1]*(1+(qtcota2_ratio)))
                
                else:
                    
                    qtcota.append(df_aux.iloc[row,:]['TAB_X_QT_COTA_SUB'])
                    # qtcota2.append(df_aux.iloc[row,:]['TAB_X_QT_COTA_SUB'])
 
            df_aux['TAB_X_VL_RENTAB_MES_SUB']=rent 
            df_aux['TAB_X_VL_RENTAB_MES_SUB']=np.where(df_aux['TAB_X_VL_RENTAB_MES_SUB']<-1000,-1000,df_aux['TAB_X_VL_RENTAB_MES_SUB'])

            df_aux['TAB_X_VL_COTA_SUB']=vlcota  
            df_aux['TAB_X_VL_COTA_SUB']=np.where(df_aux['TAB_X_VL_COTA_SUB']<0,0,df_aux['TAB_X_VL_COTA_SUB'])

            df_aux['TAB_X_QT_COTA_SUB']=qtcota  
            df_aux['TAB_X_QT_COTA_SUB']=np.where(df_aux['TAB_X_QT_COTA_SUB']<0,0,df_aux['TAB_X_QT_COTA_SUB'])

            
            df_merged3 = df_merged3.append(df_aux)

    df_merged3 = df_merged3.drop(['rent_ratio_aux','ratio_rent_mean','vlcota_ratio_aux','ratio_vlcota_mean','qtcota_ratio_aux','ratio_qtcota_mean'],axis=1)

    fidcs_merged_final = fidcs_ndefault.append(df_merged3).dropna()
    # na_col = fidcs_merged_final.isna().sum(axis=0).to_frame().reset_index()

    for serie in ipeaseries_dict.keys():
                  
        print('Coletando a Série ',serie)
        
        serie_df = ipea.timeseries(serie)    
        
        serie_df['data']=pd.to_datetime(serie_df['DATE'],utc=True).apply(lambda d: d.replace(hour=0, minute=0, second=0,tzinfo=None))  
        serie_df=serie_df.drop_duplicates()     
        serie_df=serie_df.rename(columns={serie_df.columns[-2]:serie })
        serie_df=serie_df.iloc[:,[-2,-1]]
         
        fidcs_merged_final = pd.merge(fidcs_merged_final, serie_df, left_on='Data_X', right_on='data', how='left')
        fidcs_merged_final = fidcs_merged_final.drop('data', axis=1)
    
     #REMOVER COLUNAS COM MUITOS NANS 
    na_col_ipea = fidcs_merged_final.isna().sum(axis=0).to_frame().reset_index()
    
    fidcs_merged_final = fidcs_merged_final[na_col_ipea[na_col_ipea[0]<0.05*len(fidcs_merged_final)]['index'].to_list()]  
        
    return fidcs_default, fidcs_merged_final
    










def model_fidcs_default(df_merged):
    
    
    
    
    lf_metrics_df = pd.DataFrame() 


    logit_metrics_df = pd.DataFrame() 
    # pca_metrics_df = pd.DataFrame() 
    lda_metrics_df = pd.DataFrame() 
    qda_metrics_df = pd.DataFrame() 
    gbc_metrics_df = pd.DataFrame()
    gnb_metrics_df = pd.DataFrame()
    cnb_metrics_df = pd.DataFrame()
    knn_metrics_df = pd.DataFrame()
    svm_metrics_df = pd.DataFrame()
    randomforest_metrics_df = pd.DataFrame()
    bagging_metrics_df = pd.DataFrame()
    

    # coef_df = pd.DataFrame() 
    
    metrics_dict = {'LOGIT':{},
                    # 'PCA':{},
                    'LDA':{},
                    'QDA':{},
                    'GBC':{},
                    'GNB':{},
                    # 'CNB':{},
                    'KNN':{},
                    'SVM':{},
                    'RF':{},
                    'RF':{},
                    'BAG':{}
                    }

   
    
      
    #CROSS VALIDATION FOR BEST TEST AND TRAIN MODELS
    rkf = sklearn.model_selection.RepeatedKFold(n_splits=3, n_repeats=3, random_state=100)
    for number, (train_index, test_index) in enumerate(rkf.split(df_merged)):
        print('#########################', number)
        print(train_index[0:5])
        
        train, test = df_merged.iloc[train_index], df_merged.iloc[test_index]        
        
        #REMOVE NON NUMERICAL VARIABLES
        X_train = train.select_dtypes(include=['float64','int64']).drop('Y',axis=1)
        X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
      
        Y_train = train['Y'].to_frame()
        Y_test = test['Y'].to_frame()
    
         #KEEP IMPORTANT VARIABLES
         
        if 'Data_Y' in df_merged.columns:
            train_var = train[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data_Y', 'Data_X', 'Y']]
            test_var = test[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data_Y', 'Data_X', 'Y']]
        else:
            train_var = train[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data', 'Y']]
            test_var = test[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data', 'Y']]
            


        ################ LOGIT #############
        print('CALCULAR LOGIT')
        print('#########################', number)
      
        model = LogisticRegression(random_state=0)
        model_fit = model.fit(X_train, Y_train)
        
        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_LOGIT_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_LOGIT'] = np.where(train_var['Pred_LOGIT_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_LOGIT)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_LOGIT_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_LOGIT'] = np.where(test_var['Pred_LOGIT_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_LOGIT)


        
        logit_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_LOGIT),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_LOGIT),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_LOGIT),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_LOGIT),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_LOGIT),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_LOGIT),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        logit_metrics_df = logit_metrics_df.append(logit_metrics_dfs_aux)
        
        metrics_dict['LOGIT'].update({number:{}})
        metrics_dict['LOGIT'][number].update({'train_index':train_index,'test_index':test_index })
  
  
  
        
  
    
        ############## LDA #############
        print('CALCULAR LDA')
        param_grid = {'shrinkage':['auto',None]}
        lda_grid = GridSearchCV(LDA(),param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        shrinkage = lda_grid.best_estimator_.shrinkage
        print('Melhor alpha foi ', shrinkage)
        
        model = LDA(shrinkage=shrinkage)
        model_fit = model.fit(X_train, Y_train)
        
        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_LDA_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_LDA'] = np.where(train_var['Pred_LDA_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_LDA)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_LDA_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_LDA'] = np.where(test_var['Pred_LDA_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_LDA)


        lda_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_LDA),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_LDA),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_LDA),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_LDA),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_LDA),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_LDA),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        lda_metrics_df = lda_metrics_df.append(lda_metrics_dfs_aux)        
        
         
        metrics_dict['LDA'].update({number:{}})
        metrics_dict['LDA'][number].update({'train_index':train_index,'test_index':test_index })
        


        ############## QDA #############
        print('CALCULAR QDA')
        
        model = QDA()
        model_fit = model.fit(X_train, Y_train)
        
        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_QDA_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_QDA'] = np.where(train_var['Pred_QDA_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_QDA)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_QDA_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_QDA'] = np.where(test_var['Pred_QDA_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_QDA)


        qda_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_QDA),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_QDA),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_QDA),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_QDA),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_QDA),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_QDA),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        qda_metrics_df = qda_metrics_df.append(qda_metrics_dfs_aux)                
         
        metrics_dict['QDA'].update({number:{}})
        metrics_dict['QDA'][number].update({'train_index':train_index,'test_index':test_index })




         ############## gbc #############
         print('CALCULAR GBC')
        
         param_grid = {'learning_rate':[0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1],
                       'n_estimators':[10, 200, 500]}
         gbc_grid = GridSearchCV(GradientBoostingClassifier(verbose=True),
                                 param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
         learning_rate = gbc_grid.best_estimator_.shrinkage
         n_estimators = gbc_grid.best_estimator_.shrinkage

         print('Melhor alpha foi ', n_estimators, learning_rate)
        
         model = GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate)
         model_fit = model.fit(X_train, Y_train)
        
         # train_var['Y'] = list(Y_train.Y)
         train_var['Pred_GBC_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
         train_var['Pred_GBC'] = np.where(train_var['Pred_GBC_Prob']>0.5,1,0)

         cm_train = confusion_matrix(Y_train.Y, train_var.Pred_GBC)

        
         # test_var['Y'] = list(Y_test.Y)
         test_var['Pred_GBC_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
         test_var['Pred_GBC'] = np.where(test_var['Pred_GBC_Prob']>0.5,1,0)

         cm_test= confusion_matrix(Y_test.Y, test_var.Pred_GBC)


         gbc_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_GBC),
                                               'R2_test':   r2_score(Y_test.Y, test_var.Pred_GBC),
                                               'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_GBC),
                                               'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_GBC),
                                               'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_GBC),
                                               'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_GBC),
                                               'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                               'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                               'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                               'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                               'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                               'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                               'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                               'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                               index=[str(number)])
        
         gbc_metrics_df = gbc_metrics_df.append(gbc_metrics_dfs_aux)        
        
         
         metrics_dict['GBC'].update({number:{}})
         metrics_dict['GBC'][number].update({'train_index':train_index,'test_index':test_index })



        ############## GNB #############
        print('CALCULAR GNB')
        
        model = GaussianNB()
        model_fit = model.fit(X_train, Y_train)
        
        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_GNB_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_GNB'] = np.where(train_var['Pred_GNB_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_GNB)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_GNB_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_GNB'] = np.where(test_var['Pred_GNB_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_GNB)


        gnb_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_GNB),
                                                'R2_test':   r2_score(Y_test.Y, test_var.Pred_GNB),
                                                'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_GNB),
                                                'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_GNB),
                                                'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_GNB),
                                                'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_GNB),
                                                'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                                'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                                'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                                'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                                'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                                'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                                'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                                'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        gnb_metrics_df = gnb_metrics_df.append(gnb_metrics_dfs_aux)        
        
         
        metrics_dict['GNB'].update({number:{}})
        metrics_dict['GNB'][number].update({'train_index':train_index,'test_index':test_index })






          ############## KNN #############
        print('CALCULAR KNN')
        
        param_grid = {'n_neighbors':[1, 5, 10, 25],
                        'leaf_size':[1, 5, 10, 20,30, 50]}
        knn_grid = GridSearchCV(KNeighborsClassifier(),
                                  param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        n_neighbors = knn_grid.best_estimator_.n_neighbors
        leaf_size = knn_grid.best_estimator_.leaf_size

        print('Melhor alpha foi ',leaf_size,n_neighbors)
        
        model = KNeighborsClassifier(n_neighbors=n_neighbors,leaf_size=leaf_size)
        model_fit = model.fit(X_train, Y_train)
        
        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_KNN_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_KNN'] = np.where(train_var['Pred_KNN_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_KNN)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_KNN_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_KNN'] = np.where(test_var['Pred_KNN_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_KNN)


        knn_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_KNN),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_KNN),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_KNN),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_KNN),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_KNN),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_KNN),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        knn_metrics_df = knn_metrics_df.append(knn_metrics_dfs_aux)        
        
         
        metrics_dict['KNN'].update({number:{}})
        metrics_dict['KNN'][number].update({'train_index':train_index,'test_index':test_index })
        
        
        



        ############## SVM #############
        print('CALCULAR SVM')
        
        param_grid = {'C': [0.1,1, 10, 100], 
                      'gamma': [1,0.1,0.01,0.001],
                      'kernel': ['linear','rbf', 'poly', 'sigmoid']}
        svm_grid = GridSearchCV(SVC(),
                                param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        c = svm_grid.best_estimator_.n_neighbors
        gamma = svm_grid.best_estimator_.leaf_size
        kernel = svm_grid.best_estimator_.leaf_size

        print('Melhor alpha foi ',c,gamma,kernel)
        
        model = SVC(c=c,gamma=gamma,kernel=kernel)
        model_fit = model.fit(X_train, Y_train)
        
        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_SVM_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_SVM'] = np.where(train_var['Pred_SVM_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_SVM)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_SVM_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_SVM'] = np.where(test_var['Pred_SVM_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_SVM)


        svm_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_SVM),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_SVM),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_SVM),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_SVM),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_SVM),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_SVM),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        svm_metrics_df = svm_metrics_df.append(svm_metrics_dfs_aux)        
        
         
        metrics_dict['SVM'].update({number:{}})
        metrics_dict['SVM'][number].update({'train_index':train_index,'test_index':test_index })


        
 
            
            
        ############## RANDOM FOREST   ###########
        print('CALCULAR RANDOMFOREST')
        
        RandomForestClassifier().get_params()
        param_grid = {'bootstrap': [True],
                      'n_estimators': [10, 200, 500, 1000]}
    
        
        rf_grid = GridSearchCV(RandomForestClassifier(oob_score=False, random_state=None, 
                                verbose=True, warm_start=False),
                                param_grid, cv=5).fit(X_train, Y_train)
   
        
        bootstrap = rf_grid.best_estimator_.bootstrap
        # max_features = rf_grid.best_estimator_.max_features
        n_estimators = rf_grid.best_estimator_.n_estimators

        print('Melhor Estimadores , bootstrap, maxfeatforam ', n_estimators, bootstrap)

        model = RandomForestClassifier(oob_score=False, random_state=None, 
                                verbose=True, warm_start=False,
                                bootstrap=bootstrap, n_estimators=n_estimators)
        model_fit = model.fit(X_train, Y_train)

        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_RF_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_RF'] = np.where(train_var['Pred_RF_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_RF)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_RF_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_RF'] = np.where(test_var['Pred_RF_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_RF)


        randomforest_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_RF),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_RF),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_RF),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_RF),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_RF),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_RF),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                              index=[str(number)])
        
        randomforest_metrics_df = randomforest_metrics_df.append(randomforest_metrics_dfs_aux)        
        
         
        metrics_dict['RF'].update({number:{}})
        metrics_dict['RF'][number].update({'train_index':train_index,'test_index':test_index })



        
        
        ############## BAGGING ###########
        print('CALCULAR BAGGING')
        
        param_grid = {'bootstrap': [True],
                      'n_estimators': [10, 200, 500, 1000]}
  

        bagging_grid = GridSearchCV(BaggingClassifier(verbose=True),
                                param_grid, cv=5).fit(X_train, Y_train)
   
        n_estimators = bagging_grid.best_estimator_.n_estimators
        bootstrap = bagging_grid.best_estimator_.bootstrap

        print('Melhor Estimadores , max_features, bootstrap ', n_estimators, bootstrap)

        model = BaggingClassifier(verbose=True, n_estimators=n_estimators, bootstrap=bootstrap)
    
        model_fit = model.fit(X_train, Y_train)
     
        
        train_var['Pred_BAG_Prob'] = pd.DataFrame(model_fit.predict_proba(X_train), index=train_var.index)[1]
        train_var['Pred_BAG'] = np.where(train_var['Pred_BAG_Prob']>0.5,1,0)

        cm_train = confusion_matrix(Y_train.Y, train_var.Pred_BAG)

        
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_BAG_Prob'] = [item[0] for item in model_fit.predict_proba(X_test)]
        test_var['Pred_BAG'] = np.where(test_var['Pred_BAG_Prob']>0.5,1,0)

        cm_test= confusion_matrix(Y_test.Y, test_var.Pred_BAG)


        bagging_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_BAG),
                                              'R2_test':   r2_score(Y_test.Y, test_var.Pred_BAG),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_BAG),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_BAG),
                                              'accuracy_train': accuracy_score(Y_train.Y, train_var.Pred_BAG),
                                              'accuracy_test':  accuracy_score(Y_test.Y, test_var.Pred_BAG),
                                              'default_wrong_train':cm_train[1][0],      #FALSE NEGATIVE TRAIN
                                              'default_correct_train':cm_train[1][1],    #CORRECT DEFAULT TRAIN
                                              'Ndefault_wrong_train':cm_train[0][1],     #FALSE POSITIVE TRAIN
                                              'Ndefault_correct_train':cm_train[0][0],   #CORRECT N DEFAULT TRAIN
                                              'default_wrong_test':cm_test[1][0],        #FALSE NEGATIVE TEST
                                              'default_correct_test':cm_test[1][1],      #CORRECT DEFAULT TEST
                                              'Ndefault_wrong_test':cm_test[0][1],       #FALSE POSITIVE TEST
                                              'Ndefault_correct_test':cm_test[0][0]},     #FALSE POSITIVE TEST    
                                             index=[str(number)])
        
        bagging_metrics_df = bagging_metrics_df.append(bagging_metrics_df_aux)        
        
         
        metrics_dict['BAG'].update({number:{}})
        metrics_dict['BAG'][number].update({'train_index':train_index,'test_index':test_index })
     
        
      
    logit_metrics_df_aux = logit_metrics_df.loc[logit_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    logit_metrics_df_aux['Model'] = 'LOGIT'

    lda_metrics_df_aux = lda_metrics_df.loc[lda_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    lda_metrics_df_aux['Model'] = 'LDA'

    qda_metrics_df_aux = qda_metrics_df.loc[qda_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    qda_metrics_df_aux['Model'] = 'QDA'

    gbc_metrics_df_aux = gbc_metrics_df.loc[gbc_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    gbc_metrics_df_aux['Model'] = 'GBC'

    gnb_metrics_df_aux = gnb_metrics_df.loc[gnb_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    gnb_metrics_df_aux['Model'] = 'GNB'
      
    gbm_metrics_df_aux = gbm_metrics_df.loc[gbm_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    gbm_metrics_df_aux['Model'] = 'GBM'

    knn_metrics_df_aux = knn_metrics_df.loc[knn_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    knn_metrics_df_aux['Model'] = 'KNN'
    
    svm_metrics_df_aux = svm_metrics_df.loc[svm_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    svm_metrics_df_aux['Model'] = 'SVM'    

    randomforest_metrics_df_aux = randomforest_metrics_df.loc[randomforest_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    randomforest_metrics_df_aux['Model'] = 'RF' 
    
    bagging_metrics_df_aux = bagging_metrics_df.loc[bagging_metrics_df[['accuracy_test']].idxmax().item()].to_frame().transpose()
    bagging_metrics_df_aux['Model'] = 'BAG' 

 
    model_metrics = pd.DataFrame() 
    model_metrics = model_metrics.append(logit_metrics_df_aux)
    model_metrics = model_metrics.append(lda_metrics_df_aux)
    model_metrics = model_metrics.append(qda_metrics_df_aux)
    model_metrics = model_metrics.append(gbc_metrics_df_aux)
    model_metrics = model_metrics.append(gnb_metrics_df_aux)
    model_metrics = model_metrics.append(gbm_metrics_df_aux)
    model_metrics = model_metrics.append(knn_metrics_df_aux)
    model_metrics = model_metrics.append(svm_metrics_df_aux)
    model_metrics = model_metrics.append(randomforest_metrics_df_aux)
    model_metrics = model_metrics.append(bagging_metrics_df_aux)
    model_choosen = model_metrics[model_metrics['MSE_test']==model_metrics['MSE_test'].min()]['Model'].item()

    if model_choosen=='LOGIT':
        
        model_metrics_df = logit_metrics_df    
        
    if model_choosen=='LDA':
        
        model_metrics_df = lda_metrics_df  
        
    if model_choosen=='QDA':
        
        model_metrics_df = qda_metrics_df    
        
    if model_choosen=='GBC':
        
        model_metrics_df = gbc_metrics_df  

    if model_choosen=='GNB':
        
        model_metrics_df = gnb_metrics_df  

        
    if model_choosen=='SVM':
        
        model_metrics_df = svm_metrics_df 

    if model_choosen=='KNN':
        
        model_metrics_df = knn_metrics_df          

    if model_choosen=='RF':
        
        model_metrics_df = randomforest_metrics_df  
        
    if model_choosen=='BAGGING':
        
        model_metrics_df = bagging_metrics_df    
        


    return model_choosen, model_metrics_df, metrics_dict
   
    
   
    
   
    
    
def run_model(df_merged, model_choosen, model_metrics_df,metrics_dict ,test_run):



    #REMOVE NON NUMERICAL VARIABLES
    df_X = df_merged.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
    df_y = df_merged[['Y']]

    df_model = df_merged[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data_Y', 'Data_X', 'Y']]


    if model_choosen=='LOGIT':
        
        model = LogisticRegression(random_state=0)
        model_fit = model.fit(df_X, df_y)
        
        
    if model_choosen=='LDA':
        
        train = df_merged.iloc[metrics_dict['LDA'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
        test = df_merged.iloc[metrics_dict['LDA'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]

        #REMOVE NON NUMERICAL VARIABLES
        X_train = train.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
        X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)   
          
        Y_train = train['Y'].to_frame()
        Y_test = test['Y'].to_frame()
        
        param_grid = {'shrinkage':['auto',None]}
        lda_grid = GridSearchCV(LDA(),param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        shrinkage = lda_grid.best_estimator_.shrinkage
        print('Melhor alpha foi ', shrinkage)
        
        model = LDA(shrinkage=shrinkage)
        model_fit = model.fit(df_X, df_y)

        
    if model_choosen=='QDA':
        
        model = QDA()
        model_fit = model.fit(df_X, df_y)
        
    if model_choosen=='GBC':
        
        train = df_merged.iloc[metrics_dict['GBC'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
        test = df_merged.iloc[metrics_dict['GBC'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]

        #REMOVE NON NUMERICAL VARIABLES
        X_train = train.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
        X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)   
          
        Y_train = train['Y'].to_frame()
        Y_test = test['Y'].to_frame()
        
        param_grid = {'learning_rate':[0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1],
                       'n_estimators':[10, 200, 500]}
        gbc_grid = GridSearchCV(GradientBoostingClassifier(verbose=True),
                                 param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        learning_rate = gbc_grid.best_estimator_.shrinkage
        n_estimators = gbc_grid.best_estimator_.shrinkage

        print('Melhor alpha foi ', n_estimators, learning_rate)
        
        model = GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate)
        model_fit = model.fit(df_X, df_y)


    if model_choosen=='GNB':
        

        
        model = GaussianNB()
        model_fit = model.fit(df_X, df_y)       

        
    if model_choosen=='SVM':
        
        train = df_merged.iloc[metrics_dict['SVM'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
        test = df_merged.iloc[metrics_dict['SVM'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]

        #REMOVE NON NUMERICAL VARIABLES
        X_train = train.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
        X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)   
          
        Y_train = train['Y'].to_frame()
        Y_test = test['Y'].to_frame()
        
        param_grid = {'C': [0.1,1, 10, 100], 
                      'gamma': [1,0.1,0.01,0.001],
                      'kernel': ['linear','rbf', 'poly', 'sigmoid']}
        svm_grid = GridSearchCV(SVC(),
                                param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        c = svm_grid.best_estimator_.n_neighbors
        gamma = svm_grid.best_estimator_.leaf_size
        kernel = svm_grid.best_estimator_.leaf_size

        print('Melhor alpha foi ',c,gamma,kernel)
        
        model = SVC(c=c,gamma=gamma,kernel=kernel)
        model_fit = model.fit(df_X, df_y)

        

    if model_choosen=='KNN':
        
        train = df_merged.iloc[metrics_dict['KNN'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
        test = df_merged.iloc[metrics_dict['KNN'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]

        #REMOVE NON NUMERICAL VARIABLES
        X_train = train.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
        X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)   
          
        Y_train = train['Y'].to_frame()
        Y_test = test['Y'].to_frame()
        
        
        param_grid = {'n_neighbors':[1, 5, 10, 25],
                        'leaf_size':[1, 5, 10, 20,30, 50]}
        knn_grid = GridSearchCV(KNeighborsClassifier(),
                                  param_grid=param_grid ,cv=5).fit(X_train, Y_train)
        
        n_neighbors = knn_grid.best_estimator_.n_neighbors
        leaf_size = knn_grid.best_estimator_.leaf_size

        print('Melhor alpha foi ',leaf_size,n_neighbors)
        
        model = KNeighborsClassifier(n_neighbors=n_neighbors,leaf_size=leaf_size)
        model_fit = model.fit(df_X, df_y)



    if model_choosen=='RF':
        
        if test_run:
        
            train = df_merged.iloc[metrics_dict['RF'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[metrics_dict['RF'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
    
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
            
            param_grid = {'bootstrap': [True],
                          'n_estimators': [10, 200, 500, 1000]}
        
            
            rf_grid = GridSearchCV(RandomForestClassifier(oob_score=False, random_state=None, 
                                    verbose=True, warm_start=False),
                                    param_grid, cv=5).fit(X_train, Y_train)
       
            
            bootstrap = rf_grid.best_estimator_.bootstrap
            # max_features = rf_grid.best_estimator_.max_features
            n_estimators = rf_grid.best_estimator_.n_estimators
    
            print('Melhor Estimadores , bootstrap, maxfeatforam ', n_estimators, bootstrap)
            
        else:
            n_estimators = model_metrics_df['ESTIMADORES'].item()
            bootstrap = model_metrics_df['BOOTSTRAP'].item()        
            
            

        model = RandomForestClassifier(oob_score=False, random_state=None, 
                                verbose=True, warm_start=False,
                                bootstrap=bootstrap, n_estimators=n_estimators)
        model_fit = model.fit(df_X, df_y)
        
    if model_choosen=='BAGGING':
        
        
        if test_run:
        
            train = df_merged.iloc[metrics_dict['BAGGING'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[metrics_dict['BAGGING'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
    
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64','int64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64','int64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
    
            param_grid = {'bootstrap': [True],
                          'n_estimators': [10, 200, 500, 1000]}
      
    
            bagging_grid = GridSearchCV(BaggingClassifier(verbose=True),
                                    param_grid, cv=5).fit(X_train, Y_train)
       
            n_estimators = bagging_grid.best_estimator_.n_estimators
            bootstrap = bagging_grid.best_estimator_.bootstrap

    
            print('Melhor Estimadores , bootstrap, maxfeatforam ', n_estimators, bootstrap)
            
        else:
            n_estimators = model_metrics_df['ESTIMADORES'].item()
            bootstrap = model_metrics_df['BOOTSTRAP'].item()  
        

        model = BaggingClassifier(verbose=True, n_estimators=n_estimators, bootstrap=bootstrap)
    
        model_fit = model.fit(df_X, df_y)
     
     
 

    df_model['Pred_Prob_Y'] = pd.DataFrame(model_fit.predict_proba(df_X), index=df_X.index)[1]
    df_model['Pred_Y'] = np.where(df_model['Pred_Prob_Y']>0.5,1,0)
    
    #APPEND DF MODEL WITH X VARIABLES
    df_model = pd.merge(df_model, df_X, left_index=True, right_index=True)
    
    cm = confusion_matrix(df_y.Y, df_model.Pred_Y)


    final_model_metrics = pd.DataFrame({'R2': r2_score(df_y.Y, df_model.Pred_Y),
                                          'MSE': mean_squared_error(df_y.Y, df_model.Pred_Y),
                                          'accuracy': accuracy_score(df_y.Y, df_model.Pred_Y),
                                          'default_wrong':cm[1][0],      #FALSE NEGATIVE TRAIN
                                          'default_correct':cm[1][1],    #CORRECT DEFAULT TRAIN
                                          'Ndefault_wrong':cm[0][1],     #FALSE POSITIVE TRAIN
                                          'Ndefault_correct':cm[0][0],   #CORRECT N DEFAULT TRAIN
                                          'MODEL':model_choosen,
                                          'ESTIMADORES':n_estimators,
                                          'BOOTSTRAP':bootstrap},
                                         index=[str(number)])


    print ('Erro na base teste eh', round(final_model_metrics['MSE'].item(),2))
    
    #try plot RF tree
    # if model_choosen=='RF':
        
    #     print('plot tree')        
    
    #     from sklearn import tree

    #     fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=800)
    #     tree.plot_tree( model_fit.estimators_[5],
    #                    # feature_names = fn, 
    #                    # class_names=cn,
    #                    filled = True)
    #     fig.savefig('rf_individualtree.png')
        
        
    return df_model, final_model_metrics, model_fit


def save_df(file_name,sheet, df):
    
    writer = pd.ExcelWriter(file_name)
    df.to_excel(writer, sheet_name=sheet, index=False)
    writer.save()
    
    return ('DF Salvo com Sucesso!')


if __name__=='__main__':
    
    #os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Plots')
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')
    df_fidc, df_rating= open_dfs()
    df_merged = filter_dfs(df_fidc, df_rating)



    fidcs_default_solis=check_solis_fidcs(df_merged)

    file_name=r'./Dados CVM/FIDCs SOLIS em Defaults.xlsx'
    sheet= 'DEFAULT'
    save_df(file_name,sheet,fidcs_default_solis)
    
    
    month_forescast=6
    ipeaseries_dict={
                
                'ANATEL_SERVMOVFIX':'Telefone - acessos móveis e fixos em serviço',
                'CE_CUTIND': 'UTIL_CAP_INSTAL_IND',
                'MME_CETOT':'Consumo final energia - qde.',
                'ELETRO_CEET':'Consumo - energia elétrica - qde.',
                'ELETRO_CEETT':'Consumo - energia elétrica - tarifa média por MWh.',                
                'SGS12_IBCBR12':'IBCBR',
                'SGS12_IBCBRDESSAZ12':'IBCBR - DESSAZIONALIZADO',    
                'ABRAS12_INV12':'Índice nacional de vendas - variação nominal',
                'ABRAS12_INVR12':'Índice nacional de vendas - variação real',
                'ACSP12_INAD12':'Inadimplência - índice em t-3',
                'ACSP12_INADI12':'Inadimplência - índice em t-4',
                'ACSP12_SCPCC12':'SPC - número de consultas',
                'ACSP12_SCPCRC12':'SPC - número de registros cancelados',
                'ACSP12_SCPCRL12':'SPC - número de registros líquidos',
                'ACSP12_SCPCRR12':'SPC - número de registros recebidos',
                'ACSP12_TELCH12':'Usecheque - número de consultas',
                'FCESP12_IICA12':'Índice de condições econômicas atuais (ICEA)',
                'AGENCIAS':'N Agencias Bancarias',
                'ANBIMA12_IBVRJ12':'IND BOVESPA',
                'APLICACOES':'Aplicacoes Bancarias',
                'BM_M0FN':'M0 - base monetária - fim período',
                'BM_M1FN':'M1 - fim período',
                'BM_CRBBC':'Empréstimos - setor privado - origem: Banco do Brasil',                
                'BM_CRBCC':'Empréstimos - setor privado - origem: bancos comerciais',
                'BM12_CIN12':'Operações de crédito - inadimplência',
                'BM12_CINPF12':'Operações de crédito - inadimplência - pessoa física',                
                'BM12_CINPJ12':'Operações de crédito - inadimplência - pessoa jurídica',
                'BM12_CPCA12':'Operações de crédito - prazo médio da carteira',
                'BM12_CPCAPF12':'Operações de crédito - prazo médio da carteira - pessoa física',                
                'BM12_CPCAPJ12':'Operações de crédito - prazo médio da carteira - pessoa jurídica',
                'BM12_CPCO12':'Operações de crédito - prazo médio das concessões',
                'BM12_CPCOPF12':'Operações de crédito - prazo médio das concessões - pessoa física',                
                'BM12_CPCOPJ12':'Operações de crédito - prazo médio das concessões - pessoa jurídica',
                'BM12_CRDCA12':'Operações de crédito - recursos direcionados - concessões acumuladas',
                'BM12_CRDCAPF12':'Operações de crédito - recursos direcionados - concessões acumuladas - pessoa física',
                'BM12_CRDCAPJ12':'Operações de crédito - recursos direcionados - concessões acumuladas - pessoa jurídica',
                'BM12_CRDIN12':'Operações de crédito - recursos direcionados - inadimplência',
                'BM12_CRDINPF12':'Operações de crédito - recursos direcionados - inadimplência - pessoa física',
                'BM12_CRDINPJ12':'Operações de crédito - recursos direcionados - inadimplência - pessoa jurídica',
                'BM12_CRDPCA12':'Operações de crédito - recursos direcionados - prazo médio da carteira',
                'BM12_CRDPCAPF12':'Operações de crédito - recursos direcionados - prazo médio da carteira - pessoa física',
                'BM12_CRDPCAPJ12':'Operações de crédito - recursos direcionados - prazo médio da carteira - pessoa jurídica',
                'BM12_CRDPCO12':'Operações de crédito - recursos direcionados - prazo médio das concessões',
                'BM12_CRDPCOPF12':'Operações de crédito - recursos direcionados - prazo médio das concessões - pessoa física',
                'BM12_CRDPCOPJ12':'Operações de crédito - recursos direcionados - prazo médio das concessões - pessoa jurídica',
                'BM12_CRDS12':'Operações de crédito - recursos direcionados - saldo',
                'BM12_CRDSD12':'Operações de crédito - recursos direcionados - spread',
                'BM12_CRDSDPF12':'Operações de crédito - recursos direcionados - spread - pessoa física',
                'BM12_CRDSDPJ12':'Operações de crédito - recursos direcionados - spread - pessoa jurídica',
                'BM12_CRDSPF12':'Operações de crédito - recursos direcionados - saldo - pessoa física',
                'BM12_CRDSPJ12':'Operações de crédito - recursos direcionados - saldo - pessoa jurídica',
                'BM12_CRDTJ12':'Operações de crédito - recursos direcionados - taxa de juros',
                'BM12_CRDTJPF12':'Operações de crédito - recursos direcionados - taxa de juros - pessoa física',
                'BM12_CRDTJPJ12':'Operações de crédito - recursos direcionados - taxa de juros - pessoa jurídica',
                'BM12_CRLCA12':'Operações de crédito - recursos livres - concessões acumuladas',
                'BM12_CRLCAPF12':'Operações de crédito - recursos livres - concessões acumuladas - pessoa física',
                'BM12_CRLCAPJ12':'Operações de crédito - recursos livres - concessões acumuladas - pessoa jurídica',
                'BM12_CRLINPF12':'Operações de crédito - recursos livres - inadimplência - pessoa física',
                'BM12_CRLINPJ12':'Operações de crédito - recursos livres - inadimplência - pessoa jurídica',
                'BM12_CRLPCA12':'Operações de crédito - recursos livres - prazo médio da carteira',
                'BM12_CRLPCAPF12':'Operações de crédito - recursos livres - prazo médio da carteira - pessoa física',
                'BM12_CRLPCAPJ12':'Operações de crédito - recursos livres - prazo médio da carteira - pessoa jurídica',
                'BM12_CRLPCO12':'Operações de crédito - recursos livres - prazo médio das concessões',
                'BM12_CRLPCOPF12':'Operações de crédito - recursos livres - prazo médio das concessões - pessoa física',
                'BM12_CRLPCOPJ12':'Operações de crédito - recursos livres - prazo médio das concessões - pessoa jurídica',
                'BM12_CRLS12':'Operações de crédito - recursos livres - saldo',
                'BM12_CRLSD12':'Operações de crédito - recursos livres - spread',
                # 'BM12_CRLSDPF12	':'Operações de crédito - recursos livres - spread - pessoa física',
                'BM12_CRLSDPJ12':'Operações de crédito - recursos livres - spread - pessoa jurídica',
                'BM12_CRLSPF12':'Operações de crédito - recursos livres - saldo - pessoa física',
                'BM12_CRLSPJ12':'Operações de crédito - recursos livres - saldo - pessoa jurídica',
                'BM12_CRLTJ12':'Operações de crédito - recursos livres - taxa de juros',
                'BM12_CRLTJPF12':'Operações de crédito - recursos livres - taxa de juros - pessoa física',
                'BM12_CRLTJPJ12':'Operações de crédito - recursos livres - taxa de juros - pessoa jurídica',
                'BM12_CS12':'Operações de crédito - saldo',
                'BM12_CSD12':'Operações de crédito - spread',
                'BM12_CSDPF12':'Operações de crédito - spread - pessoa física',
                'BM12_CSDPJ12':'Operações de crédito - spread - pessoa jurídica',
                'BM12_CSPF12':'Operações de crédito - saldo - pessoa física',
                'BM12_CSPJ12':'Operações de crédito - saldo - pessoa jurídica',
                'BM12_CTJ12':'Operações de crédito - taxa de juros',
                'BM12_CTJPF12':'Operações de crédito - taxa de juros - pessoa física',
                'BM12_CTJPJ12':'Operações de crédito - taxa de juros - pessoa jurídica',

                'BM12_DEPOUCN12':'M2 - depósitos em poupança - fim período - novo conceito',
                'BM12_DEPOUCNY12':'M2 - depósitos em poupança - fim período - novo conceito',
                'BM12_DEV12':'M1 - depósitos à vista - fim período',
                'BM12_DEVM12':'M1 - depósitos à vista - média',
                'BM12_FCAFIN12':'Fatores condicionantes da base monetária - oper. de redesconto do BC',
                'BM12_FCDEPFIN12':'Fatores condicionantes da base monetária - depósitos de instituições financeiras',
                'BM12_FCODA12':'Fatores condicionantes da base monetária - oper. com derivativos - ajustes',
                'BM12_FCOSE12':'Fatores condicionantes da base monetária - oper. do setor externo',
                'BM12_FCOTPF12':'Fatores condicionantes da base monetária - oper. com títulos públicos federais',
                'BM12_FCOUTC12':'Fatores condicionantes da base monetária - outras contas',
                'BM12_FCPME12':'Fatores condicionantes da base monetária - variação da base monetária - papel-moeda emitido',
                'BM12_FCRB12':'Fatores condicionantes da base monetária - variação da base monetária - reservas bancárias',
                'BM12_FCTN12':'Fatores condicionantes da base monetária - Tesouro Nacional',
                'BM12_FCVARBM12':'Fatores condicionantes da base monetária - variação da base monetária',
                'BM12_FRFCN12':'M3 - quotas de fundos de renda fixa - fim período - novo conceito',
                'BM12_FRFCNY12':'M3 - quotas de fundos de renda fixa - fim período - novo conceito',
                'BM12_M0MN12':'M0 - base monetária - média',
                'BM12_M0N12':'M0 - base monetária - fim período',
                'BM12_M0NY12':'M0 - base monetária - fim período',
                'BM12_M1MN12':'M1 - média',
                'BM12_M1N12':'M1 - fim período',
                'BM12_M1NY12':'M1 - fim período',
                'BM12_M2NCN12':'M2 - fim período - novo conceito',
                'BM12_M2NCNY12':'M2 - fim período - novo conceito',
                'BM12_M3NCN12':'M3 - fim período - novo conceito',
                'BM12_M3NCNY12':'M3 - fim período - novo conceito',
                'BM12_M4NCN12':'M4 - fim período - novo conceito',
                'BM12_M4NCNY12':'M4 - fim período - novo conceito',
                'BM12_OPTFCN12':'M3 - oper. compromissadas com títulos federais - fim período - novo conceito',
                'BM12_OPTFCNY12':'M3 - oper. compromissadas com títulos federais - fim período - novo conceito',
                'BM12_OPTPCN12':'M3 - oper. compromissadas com títulos privados - fim período - novo conceito',
                'BM12_OPTPCNY12':'M3 - oper. compromissadas com títulos privados - fim período - novo conceito',
                'BM12_PME12':'M0 - base monetária - papel-moeda emitido - fim período',
                'BM12_PMEM12':'M0 - base monetária - papel-moeda emitido - média',
                'BM12_PMPP12':'M1 - papel-moeda em poder do público - fim período',
                'BM12_PMPPM12':'M1 - papel-moeda em poder do público - média',
                'BM12_RBM12':'M0 - base monetária - reservas bancárias - média',
                'BM12_REB12':'M0 - base monetária - reservas bancárias - fim período',
                        
                'SCN10_CFGG10':'PIB - consumo final - governo - var. real anual',
                'SCN10_CFGGN10':'PIB - consumo final - governo',
                'SCN10_CTN10':'PIB - consumo final',
                'SCN10_FBKFG10':'PIB - formação bruta de capital fixo - var. real anual',
                'SCN10_FBKFN10':'PIB - formação bruta de capital fixo',
                'SCN10_FBKN10':'PIB - formação bruta de capital',
                
                'MTE12_SALMIN12':'Salário mínimo',
                
                'PAN_PO':'Pessoas ocupadas',
                'PAN_TDESOC':'Taxa de desocupação',
                'IBSIE_QSCAB':'Produção - aço bruto',
                'IBSIE_QSCFG':'Produção - ferro-gusa',
                'IBSIE_QSCL':'Produção - laminados',

                # 'IMPORTACAO':'Importações Brasileiras - (FOB)',
                # 'EXPORTACAO':'Exportações Brasileiras - (FOB)',
                
                'BM_ERC':'Taxa de câmbio - R$ / US$ - comercial - compra - média',
                'BM_ERCF':'Taxa de câmbio - R$ / US$ - comercial - compra - fim período',
                'BM_ERV':'Taxa de câmbio - R$ / US$ - comercial - venda - média',
                'BM_ERVF':'Taxa de câmbio - R$ / US$ - comercial - venda - fim período',
                
                'PRECOS_IPCAG':'Inflação - IPCA',
                'PAN_IPCAG':'Índice de Preços ao Consumidor Ampliado (IPCA)',
                'IGP_IGP':'IGP-DI - geral - índice (ago. 1994 = 100)',
                'IGP_IGPDIG':'Inflação - IGP-DI',
                'IGP_IGPOG':'IGP-OG - geral - índice (ago. 1994 = 100)',
                'IGP_IGPOGG':'Inflação - IGP-OG',
                'IGP_INCCG':'Inflação - INCC-DI',
                'IGP_IPA':'IPA-DI - geral - índice (ago. 1994 = 100)',
                'IGP_IPAA':'IPA-DI - origem - prod. agropecuários - índice (ago. 1994 = 100)',
                'IGP_IPADIG':'Inflação - IPA-DI',
                'IGP_IPAI':'IPA-DI - origem - prod. industriais - índice (ago. 1994 = 100)',
                'IGP_IPCG':'Inflação - IPC-DI (FGV)',
                'PAN_IGPDIG':'Índice Geral de Preços (IGP-DI)',
                'PAN_ERV':'Taxa de câmbio nominal',
                'SGS366_DIASUTEISPAS366':'Dias úteis - indicador',
                'SGS12_NDIASUTEISPAS12':'Número de dias úteis',
        
                'PRECOS12_IPCAG12':'IPCA_MENSAL',
                'PAN12_IPCAG12':'IPCA_MENSAL_ANUALIZADO',
                'PRECOS12_INPCBR12':'INPC_MENSAL',
                'BM12_TJOVER12':'SELIC_MENSAL',
                'PAN12_TJOVER12':'SELIC_MENSAL_ANUALIZADO',
                              
                # 'PAN4_FBKFI90G4':'Investimento real',
                # 'PAN4_FBKFPIBV4':'Taxa de investimento nominal',
                # 'PAN4_PIBPMG4':'PIB real',
                # 'PAN4_PIBPMV4':'PIB nominal',
                # 'PAN4_PO4':'Pessoas ocupadas',
                # 'PAN4_TDESOC4':'Taxa de desocupação',
                
                # 'CNI4_INECCOMPDF4':'Expectativa do consumidor (INEC) - compras de bens de maior valor - Índice de difusão',
                # 'CNI4_INECDESPDF4':'Expectativa do consumidor (INEC) - expectativa de desemprego - Índice de difusão',
                # 'CNI4_INECDF4':'Expectativa do consumidor (INEC) - Índice de difusão',
                # 'CNI4_INECEXPDF4':'Expectativa do consumidor (INEC) - expectativa de Renda própria - Índice de difusão',
                # 'CNI4_INECINFDF4':'Expectativa do consumidor (INEC) - expectativa de inflação - Índice de difusão',
                # 'CNI4_INECINTDF4':'Expectativa do consumidor (INEC) - expectativa de situação financeira - Índice de difusão',
                # 'CNI4_INECPERDF4':'Expectativa do consumidor (INEC) - endividamento - Índice de difusão'
                
                }   
    fidcs_default, fidcs_merged = set_defaults_df(df_merged,month_forescast, ipeaseries_dict)
    
    
    file_name=r'./Dados CVM/FIDCs CVM em Defaults.xlsx'
    sheet = 'DEFAULT'
    # save_df(file_name,sheet, fidcs_default)


    # test_run=True  #True: precisa rodar o modelo todo de novo (demora horas)// 
    test_run=False #False: Ja pega o ultimo modelo que teve melhor performance e seus parametros
    
   
    if test_run==True:
        model_choosen, model_metrics_df, model_metrics = model_fidcs_default(df_merged)
    else:
        os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')
        model_metrics_df = pd.read_excel('./Dados CVM/Modelagem/Modelagem Default.xlsx', sheet_name='Metricas')
        model_choosen = model_metrics_df['MODEL'].item()
        model_metrics={}


    df_model, final_model_metrics, model_fit = run_model(df_merged, model_choosen, model_metrics_df, model_metrics,test_run)
    
    writer = pd.ExcelWriter(r'./Dados CVM/Modelagem/Modelagem Default.xlsx')
    df_model.to_excel(writer, sheet_name='Dados e Previsão', index=False)
    final_model_metrics.to_excel(writer, sheet_name='Metricas', index=False)
    writer.save()


    # cols_of_intenterest = ['CNPJ_FUNDO','DENOM_SOCIAL','DT_COMPTC','Data','Ano','Mes',
    #                         'TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX',
    #                         #'Rating','Rating_AUX','Agencia','Data Rating','Ano_Rating','Mes_Rating','Data Vencimento','Rating Antigo',
    #                         'TAB_X_VL_RENTAB_MES',
    #                         # 'TAB_X_PR_DESEMP_ESPERADO','TAB_X_PR_DESEMP_REAL',
    #                         'TAB_X_NR_COTST','TAB_X_QT_COTA',
    #                         'TAB_X_VL_COTA','TAB_X_QT_COTA_SUB','TAB_X_VL_COTA_SUB','TAB_X_VL_RENTAB_MES_SUB','TAB_I_VL_ATIVO',
    #                         'TAB_I1_VL_DISP','TAB_I2_VL_CARTEIRA','TAB_IV_A_VL_PL','TAB_IV_B_VL_PL_MEDIO',
    #                         # 'TAB_V_A_VL_DIRCRED_PRAZO','TAB_V_B_VL_DIRCRED_INAD','TAB_V_C_VL_DIRCRED_ANTECIPADO',
    #                         # 'TAB_VI_A_VL_DIRCRED_PRAZO','TAB_VI_B_VL_DIRCRED_INAD','TAB_VI_C_VL_DIRCRED_ANTECIPADO'
    #                         ]




# ARCTURUS FIDC NP MULTISSEGMENTO SUBORDINADA
    #RENT == 0 (ULTIMAS MES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMO MES)
    #NA SUB PARA 3 ULTIMOS MESES

# BELLATRIX FIDC SUBORDINADA
    #RENT == 0 (ULTIMAS ANO)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMO ANO)
    #NA SUB PARA ULTIMO ANO

# BONSUCESSO CRÉDITO CONSIGNADO FIDC SUBORDINADA - II (NAO SEI SE QUEBROU))
    #RENT == 0 (ULTIMOS 4 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 4 MESES)
    #RENT E VARIAVEIS SUB 0 (ULTIMOS 4 MESES)

# BONSUCESSO CRÉDITO CONSIGNADO FIDC SUBORDINADA - 
    #RENT == 0 (ULTIMOS 5 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 5 MESES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 5 MESES)
    
    
# FORNECEDORES ODEBRECHT FIDC SUBORDINADA JÚNIOR
    #RENT == 0 (ULTIMOS 7 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 7 MESES)
    #RENT E VARIAVEIS SUB 0 (ULTIMO MES)

# LAVORO II FIDC SUBORDINADA ORDINÁRIA
    #RENT <= 0 (ULTIMOS 10 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL < 0.05 (ULTIMOS 4 MESES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 4 MESES)

# LEGO FIDC SUBORDINADA JÚNIOR LP
    #RENT <= 0 (ULTIMOS 6 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 4 MESES)
    #RENT E VARIAVEIS SUB 0 (ULTIMOS 4 MESES)

# LEGO II FIDC MULTISSETORIAL SUBORDINADA JÚNIOR
    #RENT <= 0 (ULTIMOS 36 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL < 0.05 (ULTIMOS 30 MESES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 4 MESES)

# MARTINS FIDC SUBORDINADA
    #RENT <= 0 (ULTIMOS 6 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL < 0.05 (ULTIMOS 6 MESES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 6 MESES)


# ODYSSEY FIDC MULTISSETORIAL SUBORDINADA LP
    #RENT == 0 (ULTIMOS 2 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 2 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 2 MES)


# ORION FIDC MULTISSETORIAL SUBORDINADA JÚNIOR LP
    #RENT == 0 (ULTIMOS 2 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 2 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 2 MES)


# PREVIMIL FINANCEIRO FIDC SUBORDINADA
    #RENT == 0 (ULTIMOS 7 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 1 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 1 MES)

# SILVERADO FORNECEDORES DO SISTEMA PETROBRAS FIDC MULTISSETORIAL SUBORDINADA JÚNIOR
    #RENT == 0 (ULTIMOS 7 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 1 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 1 MES)

# SILVERADO MAXIMUM FIDC MULTISSETORIAL SUBORDINADA MEZANINO 1
    #RENT == 0 (ULTIMOS 7 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 1 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 1 MES)

# SILVERADO MAXIMUM II FIDC MULTISSETORIAL SUBORDINADA JÚNIOR
    #RENT == 0 (ULTIMOS 7 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 1 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 1 MES)

# SILVERADO TOTVM FICFIDC SUBORDINADA JÚNIOR
    #RENT == 0 (ULTIMOS 10 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 4 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 4 MES)

# TRENDBANK FOMENTO FIDC MULTISSETORIAL SUBORDINADA
    #RENT <= 0 (ULTIMOS 6 MESES)
    #N COTISTA, VL DA COTA, ATIVO, PL = 0 (ULTIMOS 1 MES)
    #RENT E VARIAVEIS SUB NA (ULTIMOS 1 MES)





