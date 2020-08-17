#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 11:56:04 2020

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

import sklearn
from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
# from sklearn.metrics import accuracy_score
from sklearn.metrics import r2_score

from sklearn.model_selection import GridSearchCV
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_moons

from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso
from sklearn.linear_model import LassoCV
from sklearn.linear_model import Lars    
from sklearn.linear_model import LassoLars
from sklearn.linear_model import LassoLarsCV
from sklearn.linear_model import Ridge
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import ElasticNetCV

from sklearn.tree import DecisionTreeRegressor

from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import BaggingRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import  KNeighborsRegressor
from sklearn.svm import LinearSVR


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





def filter_dfs(df_fidc, df_rating, ipeaseries_dict, month_forescast, mode,remove_rentsub, remove_taxvar):
    
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
    df_fidc_agg = df_fidc_senior.merge(df_rating_final,how='left',on='CNPJ_FUNDO')
    
    fidcs_df = df_fidc_agg[~pd.isnull(df_fidc_agg['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
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
    fidcs_df_final=fidcs_df_final[~fidcs_df_final['TAB_X_VL_RENTAB_MES_SUB'].isna()]
    fidcs_df_final = fidcs_df_final.drop(['CNPJ_ADMIN','ADMIN'], axis=1)                 #REMOVER COLUNAS IRRELEVANTES COM NA
    
    

    
    #CRIAR DUMMIES IMPORTANTES
    fidcs_df_final['Ano'] = fidcs_df_final['Data'].dt.year
    fidcs_df_final['Mes'] = fidcs_df_final['Data'].dt.month
    fidcs_df_final['Ano_Rating'] = fidcs_df_final['Data Rating'].dt.year.fillna(0)
    fidcs_df_final['Mes_Rating'] = fidcs_df_final['Data Rating'].dt.month.fillna(0)
    
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

    #Create year of rating  dummies    
    fidcs_df_final['d_ar2013'] = np.where(fidcs_df_final['Ano_Rating']==2013,1,0)
    fidcs_df_final['d_ar2014'] = np.where(fidcs_df_final['Ano_Rating']==2014,1,0)
    fidcs_df_final['d_ar2015'] = np.where(fidcs_df_final['Ano_Rating']==2015,1,0)
    fidcs_df_final['d_ar2016'] = np.where(fidcs_df_final['Ano_Rating']==2016,1,0)
    fidcs_df_final['d_ar2017'] = np.where(fidcs_df_final['Ano_Rating']==2017,1,0)
    fidcs_df_final['d_ar2018'] = np.where(fidcs_df_final['Ano_Rating']==2018,1,0)
    fidcs_df_final['d_ar2019'] = np.where(fidcs_df_final['Ano_Rating']==2019,1,0)
    fidcs_df_final['d_ar2020'] = np.where(fidcs_df_final['Ano_Rating']==2020,1,0)
    fidcs_df_final['d_ar2021'] = np.where(fidcs_df_final['Ano_Rating']==2021,1,0)
    fidcs_df_final['d_arNA'] = np.where(fidcs_df_final['Ano_Rating']==0,1,0)


    #Create month of rating dummies
    fidcs_df_final['d_mr1'] = np.where(fidcs_df_final['Mes_Rating']==1,1,0)
    fidcs_df_final['d_mr2'] = np.where(fidcs_df_final['Mes_Rating']==2,1,0)
    fidcs_df_final['d_mr3'] = np.where(fidcs_df_final['Mes_Rating']==3,1,0)
    fidcs_df_final['d_mr4'] = np.where(fidcs_df_final['Mes_Rating']==4,1,0)
    fidcs_df_final['d_mr5'] = np.where(fidcs_df_final['Mes_Rating']==5,1,0)
    fidcs_df_final['d_mr6'] = np.where(fidcs_df_final['Mes_Rating']==6,1,0)
    fidcs_df_final['d_mr7'] = np.where(fidcs_df_final['Mes_Rating']==7,1,0)
    fidcs_df_final['d_mr8'] = np.where(fidcs_df_final['Mes_Rating']==8,1,0)
    fidcs_df_final['d_mr9'] = np.where(fidcs_df_final['Mes_Rating']==9,1,0)
    fidcs_df_final['d_mr10'] = np.where(fidcs_df_final['Mes_Rating']==10,1,0)
    fidcs_df_final['d_mr11'] = np.where(fidcs_df_final['Mes_Rating']==11,1,0)
    fidcs_df_final['d_mr12'] = np.where(fidcs_df_final['Mes_Rating']==12,1,0)    
    fidcs_df_final['d_mrNA'] = np.where(fidcs_df_final['Mes_Rating']==0,1,0)    

    
    #Create rating dummies
    fidcs_df_final['d_AAA'] = np.where(fidcs_df_final['Rating_AUX']=='AAA',1,0)
    fidcs_df_final['d_AAma'] = np.where(fidcs_df_final['Rating_AUX']=='AA+',1,0)
    fidcs_df_final['d_AA'] = np.where(fidcs_df_final['Rating_AUX']=='AA',1,0)
    fidcs_df_final['d_AAme'] = np.where(fidcs_df_final['Rating_AUX']=='AA-',1,0)
    fidcs_df_final['d_Ama'] = np.where(fidcs_df_final['Rating_AUX']=='A+',1,0)
    fidcs_df_final['d_A'] = np.where(fidcs_df_final['Rating_AUX']=='A',1,0)
    fidcs_df_final['d_Ame'] = np.where(fidcs_df_final['Rating_AUX']=='A-',1,0)
    fidcs_df_final['d_BBBma'] = np.where(fidcs_df_final['Rating_AUX']=='BBB+',1,0)
    fidcs_df_final['d_BBB'] = np.where(fidcs_df_final['Rating_AUX']=='BBB',1,0)
    fidcs_df_final['d_BBBme'] = np.where(fidcs_df_final['Rating_AUX']=='BBB-',1,0)
    fidcs_df_final['d_BBma'] = np.where(fidcs_df_final['Rating_AUX']=='BB+',1,0)
    fidcs_df_final['d_BB'] = np.where(fidcs_df_final['Rating_AUX']=='BB',1,0)
    fidcs_df_final['d_BBme'] = np.where(fidcs_df_final['Rating_AUX']=='BB-',1,0)
    fidcs_df_final['d_Bma'] = np.where(fidcs_df_final['Rating_AUX']=='B+',1,0)
    fidcs_df_final['d_B'] = np.where(fidcs_df_final['Rating_AUX']=='B',1,0)
    fidcs_df_final['d_Bme'] = np.where(fidcs_df_final['Rating_AUX']=='B-',1,0)
    fidcs_df_final['d_CCC'] = np.where(fidcs_df_final['Rating_AUX']=='CCC',1,0)
    fidcs_df_final['d_CC'] = np.where(fidcs_df_final['Rating_AUX']=='CC',1,0)
    fidcs_df_final['d_C'] = np.where(fidcs_df_final['Rating_AUX']=='C',1,0)
    fidcs_df_final['d_D'] = np.where(fidcs_df_final['Rating_AUX']=='D',1,0)

    #Create rating dummies
    fidcs_df_final['d_FITCH'] = np.where(fidcs_df_final['Agencia']=='FITCH',1,0)
    fidcs_df_final['d_SP'] = np.where(fidcs_df_final['Agencia']=='SP',1,0)
    fidcs_df_final['d_MOODY'] = np.where(fidcs_df_final['Agencia']=='MOODY',1,0)
    fidcs_df_final['d_AUSTIN'] = np.where(fidcs_df_final['Agencia']=='AUSTIN',1,0)
    fidcs_df_final['d_LIBERIUM'] = np.where(fidcs_df_final['Agencia']=='LIBERIUM',1,0)
    fidcs_df_final['d_SR'] = np.where(fidcs_df_final['Agencia']=='SR',1,0)
    fidcs_df_final['d_INTERNACIONAL'] = np.where(fidcs_df_final['Agencia'].isin(['FITCH','SP','MOODY']),1,0)



    ########FILTRAR NAN NA BASE PRINCIPAL
    na_col = fidcs_df_final.isna().sum(axis=0).to_frame().reset_index()
    
    #retirar colunas com mais de 1% na
    fidcs_df_final = fidcs_df_final[na_col[na_col[0]<0.01*len(fidcs_df_final)]['index'].to_list()]  
    
    
    if mode=='past' or mode=='present':
    
        #ADICONAR VARIAVEIS ECONOMICAS
        todas_series_ativas = ipea.metadata()
        todas_series_mensais_ativas = todas_series_ativas[(todas_series_ativas['SERIES STATUS']=='A')&(todas_series_ativas['FREQUENCY']=='Mensal')]
        todas_series_trim_ativas = todas_series_ativas[(todas_series_ativas['SERIES STATUS']=='A')&(todas_series_ativas['FREQUENCY']=='Trimestral')]
    
        for serie in ipeaseries_dict.keys():
                      
            print('Coletando a Série ',serie)
            
            serie_df = ipea.timeseries(serie)    
            
            serie_df['data']=pd.to_datetime(serie_df['DATE'],utc=True).apply(lambda d: d.replace(hour=0, minute=0, second=0,tzinfo=None))  
            serie_df=serie_df.drop_duplicates()     
            serie_df=serie_df.rename(columns={serie_df.columns[-2]:serie })
            serie_df=serie_df.iloc[:,[-2,-1]]
             
            fidcs_df_final = pd.merge(fidcs_df_final, serie_df, left_on='Data', right_on='data', how='left')
            fidcs_df_final = fidcs_df_final.drop('data', axis=1)
        
         #REMOVER COLUNAS COM MUITOS NANS 
        na_col_ipea = fidcs_df_final.isna().sum(axis=0).to_frame().reset_index()
        
        fidcs_df_final = fidcs_df_final[na_col_ipea[na_col_ipea[0]<0.05*len(fidcs_df_final)]['index'].to_list()]  


    #REMOVE OUTLIERS
    print('Removendo outliers da base')
    fidcs_df_final_aux =  fidcs_df_final[((fidcs_df_final['TAB_X_VL_RENTAB_MES']<np.percentile(fidcs_df_final['TAB_X_VL_RENTAB_MES'], 99.9)) & 
                                          (fidcs_df_final['TAB_X_VL_RENTAB_MES']>np.percentile(fidcs_df_final['TAB_X_VL_RENTAB_MES'], 0.05)))]
    sns.boxplot(x="Ano", y="TAB_X_VL_RENTAB_MES", data=fidcs_df_final_aux)
    plt.savefig('Rentabilidade Média por Ano.png', bbox_inches='tight')     
    plt.show()


    df_quant = fidcs_df_final.groupby("Ano")["TAB_X_VL_RENTAB_MES"].quantile([0.055, 0.98]).unstack(level=1)
    fidcs_df_final = fidcs_df_final.loc[((df_quant.loc[fidcs_df_final['Ano'], 0.055] < fidcs_df_final['TAB_X_VL_RENTAB_MES'].values) & 
                                         (fidcs_df_final['TAB_X_VL_RENTAB_MES'].values < df_quant.loc[fidcs_df_final['Ano'], 0.98])).values]
                                         
    sns.boxplot(x="Ano", y="TAB_X_VL_RENTAB_MES", data=fidcs_df_final)
    plt.savefig('Rentabilidade Média por Ano - Filtrada.png', bbox_inches='tight') 

    plt.show()
                                    
    # #CREATE Y VARIABLE
    
    fidcs_df_final['Y']=(((1+fidcs_df_final['TAB_X_VL_RENTAB_MES']/100)**(12))-1)*100
    

    #SE FOSSEMOS TIRAR O BENCHMARK DA TAXA CHEIA
    # if spread=='IPCA':
    #     fidcs_df_final['Y']=((((1+fidcs_df_final['TAB_X_VL_RENTAB_MES']/100)/(1+fidcs_df_final['PRECOS12_IPCAG12']/100))**(12))-1)*100
    # else:
    #     fidcs_df_final['Y']=((((1+fidcs_df_final['TAB_X_VL_RENTAB_MES']/100)/(1+fidcs_df_final['BM12_TJOVER12']/100))**(12))-1)*100
    
    fidcs_df_final=fidcs_df_final.sort_values(by=['CNPJ_FUNDO','Data', 'TAB_X_CLASSE_SERIE'])
  
    if mode=='past':
        df_merged=pd.DataFrame()
        for cnpj in fidcs_df_final['CNPJ_FUNDO'].unique():
            
            df_filter1 =  fidcs_df_final[fidcs_df_final['CNPJ_FUNDO']==cnpj]
            # print(df_filter1['TAB_X_CLASSE_SERIE'].unique())
            for serie in df_filter1['TAB_X_CLASSE_SERIE'].unique():
                        
                df_filter2 =  df_filter1[df_filter1['TAB_X_CLASSE_SERIE']==serie]
                
                if len(df_filter2)>=month_forescast:
    
                    df_y = df_filter2[['Y','Data']].rename(columns={'Data':'Data_Y'})
                    df_X = df_filter2.drop(['Y'], axis=1).shift(month_forescast).rename(columns={'Data':'Data_X'})
                    df_merged_aux = pd.concat([df_y, df_X], axis=1).dropna(subset=['CNPJ_FUNDO'])
                    
                    df_merged = df_merged.append(df_merged_aux) 
        df_merged['days_diff']=(df_merged['Data_Y']-df_merged['Data_X']) / np.timedelta64(1, 'D')
        df_merged=df_merged[(df_merged['days_diff']<=400) & (df_merged['days_diff']>=300)]  
    else:
        # df_merged=fidcs_df_final.drop(['TAB_X_VL_RENTAB_MES','TAB_X_PR_DESEMP_ESPERADO'],axis=1)                         
        df_merged=fidcs_df_final.drop(['TAB_X_VL_RENTAB_MES'],axis=1)                         


    #remover rentabilidade das cotas subordinadas para previsao 
    if remove_rentsub:
        df_merged=df_merged.drop('TAB_X_VL_RENTAB_MES_SUB', axis=1)
        
    #remover variaveis de taxa de compra e venda do modelo (TAB IX)
    if remove_taxvar:
        
        cols_of_interest=[column for column in df_merged.columns if '_IX_' not in column]
        df_merged = df_merged[cols_of_interest]
                
  
    #RETIRAR NAS DA BASE PRINCIPAL
    na_col2 = df_merged.isna().sum(axis=0).to_frame().reset_index().sort_values(by=0, ascending=False)
    print('NAs na base agregada', na_col2.iloc[0][0])    
    
    df_merged=df_merged.dropna()

    if df_merged.isna().sum(axis=0).to_frame().reset_index()[0].unique().item()==0:
        print('Base sem NANs')
      

    na_col2 = fidcs_df_final.isna().sum(axis=0).to_frame().reset_index().sort_values(by=0, ascending=False)
    print('NAs na base agregada', na_col2.iloc[0][0])    
    
    df_merged=df_merged.dropna()


    print('Bases Filtradas com sucesso!')

    return df_merged






def model_df(df_merged):
    
   
    #DIVIDE TEST AND TRAIN
    # train, test= train_test_split(df_merged, train_size=train_size, test_size=(1-train_size))
          

    lf_metrics_df = pd.DataFrame() 
    lasso_metrics_df = pd.DataFrame() 
    lars_metrics_df = pd.DataFrame()
    lassolars_metrics_df = pd.DataFrame()
    ridge_metrics_df = pd.DataFrame()
    elasticnet_metrics_df = pd.DataFrame()
    randomforest_metrics_df = pd.DataFrame()
    adaboosting_metrics_df = pd.DataFrame()
    bagging_metrics_df = pd.DataFrame()
    gbm_metrics_df = pd.DataFrame()
    knn_metrics_df = pd.DataFrame()
    svm_metrics_df = pd.DataFrame()


    # coef_df = pd.DataFrame() 
    
    lr_dict={'OLS':{},
             'LASSO':{},
             'LARS':{},
             'LASSOLARS':{},
             'RIDGE':{},
             'EN':{},
             'RF':{},
             'ADB':{},
             'BAG':{},
             'GBM':{},
             'KNN':{},
             'SVM':{}}
   
    
      
    #CROSS VALIDATION FOR BEST TEST AND TRAIN MODELS
    rkf = sklearn.model_selection.RepeatedKFold(n_splits=3, n_repeats=3, random_state=100)
    for number, (train_index, test_index) in enumerate(rkf.split(df_merged)):
        print('#########################', number)
        print(train_index[0:5])
        
        train, test = df_merged.iloc[train_index], df_merged.iloc[test_index]        
        
        #REMOVE NON NUMERICAL VARIABLES
        X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
        X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)
      
        Y_train = train['Y'].to_frame()
        Y_test = test['Y'].to_frame()
    
         #KEEP IMPORTANT VARIABLES
         
        if 'Data_Y' in df_merged.columns:
            train_var = train[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data_Y', 'Data_X', 'Rating', 'Y']]
            test_var = test[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data_Y', 'Data_X', 'Rating', 'Y']]
        else:
            train_var = train[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data', 'Rating', 'Y']]
            test_var = test[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data', 'Rating', 'Y']]
            



       #  ################ OLS #############
       #  print('CALCULAR OLS')
       #  print('#########################', number)

       #  model = LinearRegression()
       #  model_fit = model.fit(X_train, Y_train)
        
       #  # train_var['Y'] = list(Y_train.Y)
       #  train_var['Pred_OLS'] = [item[0] for item in model_fit.predict(X_train)]
     
       #  # test_var['Y'] = list(Y_test.Y)
       #  test_var['Pred_OLS'] = [item[0] for item in model_fit.predict(X_test)]
     
       #  lf_metrics_dfs_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_OLS),
       #                                    'R2_test':   r2_score(Y_test.Y, test_var.Pred_OLS),
       #                                    'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_OLS),
       #                                    'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_OLS),
       #                                    'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_OLS),
       #                                    'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_OLS)},
       #                                   index=[str(number)])
    
       #  lf_metrics_df = lf_metrics_df.append(lf_metrics_dfs_aux)
        
       #  lr_dict['OLS'].update({number:{}})
       #  lr_dict['OLS'][number].update({'train_index':train_index,'test_index':test_index })
        
        
       #  ############## LASSO #############
       #  print('CALCULAR LASSO')
       #  param_grid = {'alpha': [1e-15, 1e-10, 1e-5, 1e-2,1e-1, 1, 5, 10]}
       #  lasso_grid = GridSearchCV(Lasso(copy_X=True, fit_intercept=True, max_iter=1000, positive=False, normalize=True),
       #                            param_grid, cv=5).fit(X_train, Y_train)
        
       #  alpha = lasso_grid.best_estimator_.alpha
       #  print('Melhor alpha foi ', alpha)

       #  model = Lasso(copy_X=True, fit_intercept=True, max_iter=1000, positive=False, normalize=True, alpha=alpha)
       #  model_fit = model.fit(X_train, Y_train)

        

       #  # train_var['Y'] = list(Y_train.Y)
       #  train_var['Pred_LASSO'] = [item for item in model_fit.predict(X_train)]
     
       #  # test_var['Y'] = list(Y_test.Y)
       #  test_var['Pred_LASSO'] = [item for item in model_fit.predict(X_test)]
     
       #  lasso_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_LASSO),
       #                                    'R2_test':  r2_score(Y_test.Y, test_var.Pred_LASSO),
       #                                    'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_LASSO),
       #                                    'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_LASSO),
       #                                    'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_LASSO),
       #                                    'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_LASSO)},
       #                                   index=[str(number)])
    
       #  lasso_metrics_df = lasso_metrics_df.append(lasso_metrics_df_aux)
        
       #  lr_dict['LASSO'].update({number:{}})
       #  lr_dict['LASSO'][number].update({'train_index':train_index,'test_index':test_index })


       #  ############## LARS ###########
       #  print('CALCULAR LARS')
       #  print('#########################', number)
       #  param_grid = {'eps': [1e-15, 1e-10, 1e-5, 1e-2,1e-1, 1, 5, 10, 20],
       #                'n_nonzero_coefs':[1,10,50,100,300, 380]}
       #  lars_grid = GridSearchCV(Lars(fit_intercept=True, verbose=True, normalize=True,
       #                                copy_X=True, fit_path=True),
       #                            param_grid, cv=5).fit(X_train, Y_train)
        
       #  eps = lars_grid.best_estimator_.eps
       #  nzero = lars_grid.best_estimator_.n_nonzero_coefs
       #  print('Melhor eps foi ', eps)

       #  model =Lars(fit_intercept=True, verbose=True, normalize=True,
       #              copy_X=True, fit_path=True, eps=eps, n_nonzero_coefs=nzero)
       #  model_fit = model.fit(X_train, Y_train)

       #  # train_var['Y'] = list(Y_train.Y)
       #  train_var['Pred_LARS'] = [item for item in model_fit.predict(X_train)]
     
       #  # test_var['Y'] = list(Y_test.Y)
       #  test_var['Pred_LARS'] = [item for item in model_fit.predict(X_test)]
     
       #  lars_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_LARS),
       #                                    'R2_test':  r2_score(Y_test.Y, test_var.Pred_LARS),
       #                                    'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_LARS),
       #                                    'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_LARS),
       #                                    'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_LARS),
       #                                    'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_LARS)},
       #                                   index=[str(number)])
    
       #  lars_metrics_df = lars_metrics_df.append(lars_metrics_df_aux)
        
       #  lr_dict['LARS'].update({number:{}})
       #  lr_dict['LARS'][number].update({'train_index':train_index,'test_index':test_index })




       # ############## LASSO LARS ###########
       #  print('CALCULAR LASSO LARS')
       #  param_grid = {'eps': [1e-20, 1e-15, 1e-8,1e-3,1,5,10,20],
       #                'alpha':[1e-10,1e-8,1e-2,1,2,5,10]}
       #  lassolars_grid = GridSearchCV(LassoLars(fit_intercept=True, verbose=False, normalize=True, 
       #                                     max_iter=500, copy_X=True,fit_path=True, positive=False),
       #                            param_grid, cv=5).fit(X_train, Y_train)
        
       #  eps = lassolars_grid.best_estimator_.eps
       #  alpha = lassolars_grid.best_estimator_.alpha
       #  print('Melhor eps  e alpha foram ', eps, alpha)

       #  model = LassoLars(fit_intercept=True, verbose=False, normalize=True, 
       #                    max_iter=500, copy_X=True,fit_path=True, positive=False,
       #                    alpha=alpha, eps=eps)
       #  model_fit = model.fit(X_train, Y_train)

       #  # train_var['Y'] = list(Y_train.Y)
       #  train_var['Pred_LASSOLARS'] = [item for item in model_fit.predict(X_train)]
     
       #  # test_var['Y'] = list(Y_test.Y)
       #  test_var['Pred_LASSOLARS'] = [item for item in model_fit.predict(X_test)]
     
       #  lassolars_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_LASSOLARS),
       #                                        'R2_test':  r2_score(Y_test.Y, test_var.Pred_LASSOLARS),
       #                                        'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_LASSOLARS),
       #                                        'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_LASSOLARS),
       #                                        'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_LASSOLARS),
       #                                        'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_LASSOLARS)},
       #                                       index=[str(number)])
        
       #  lassolars_metrics_df = lassolars_metrics_df.append(lassolars_metrics_df_aux)
        
       #  lr_dict['LASSOLARS'].update({number:{}})
       #  lr_dict['LASSOLARS'][number].update({'train_index':train_index,'test_index':test_index })

         
       #  ############## RIDGE ###########
       #  print('CALCULAR RIDGE')
       #  print('#########################', number)

       #  param_grid = {'alpha':[1e-15, 1e-10, 1e-8, 1e-5, 1e-3,1e-2,1e-1, 1, 5, 10,20,50,100,200]}
       #  ridge_grid = GridSearchCV(Ridge(fit_intercept=True, normalize=True, copy_X=True, 
       #                                  max_iter=None, tol=0.001, random_state=None),
       #                            param_grid, cv=5).fit(X_train, Y_train)
        
       #  alpha = ridge_grid.best_estimator_.alpha
       #  print('Melhor alpha foi ', alpha)

       #  model = Ridge(fit_intercept=True, normalize=True, copy_X=True, 
       #               max_iter=None, tol=0.001, random_state=None,
       #               alpha=alpha)
       #  model_fit = model.fit(X_train, Y_train)

       #  # train_var['Y'] = list(Y_train.Y)
       #  train_var['Pred_RIDGE'] = [item for item in model_fit.predict(X_train)]
     
       #  # test_var['Y'] = list(Y_test.Y)
       #  test_var['Pred_RIDGE'] = [item for item in model_fit.predict(X_test)]
     
       #  ridge_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_RIDGE),
       #                                        'R2_test':  r2_score(Y_test.Y, test_var.Pred_RIDGE),
       #                                        'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_RIDGE),
       #                                        'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_RIDGE),
       #                                        'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_RIDGE),
       #                                        'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_RIDGE)},
       #                                       index=[str(number)])
        
       #  ridge_metrics_df = ridge_metrics_df.append(ridge_metrics_df_aux)
        
       #  lr_dict['RIDGE'].update({number:{}})
       #  lr_dict['RIDGE'][number].update({'train_index':train_index,'test_index':test_index })


 

       #  ############## ELASTIC NET ###########
       #  print('CALCULAR ELASTICNET')
       #  param_grid = {'alpha':[1e-15,1e-10, 1e-5,1e-2, 1, 5,20],
       #               'l1_ratio':[0.01,0.25,0.5,0.75,0.99]}
       #  en_grid = GridSearchCV(ElasticNet(fit_intercept=True, normalize=True, 
       #                                    precompute=False, max_iter=500, copy_X=True, tol=0.0001, 
       #                                    warm_start=False, positive=False, random_state=None),
       #                            param_grid, cv=5).fit(X_train, Y_train)
        
       #  alpha = en_grid.best_estimator_.alpha
       #  ratio = en_grid.best_estimator_.l1_ratio
       #  print('Melhor alpha e ratio foram ', alpha, ratio)

       #  model = ElasticNet(fit_intercept=True, normalize=True, 
       #                     precompute=False, max_iter=1000, copy_X=True, tol=0.0001, 
       #                     warm_start=False, positive=False, random_state=None,
       #                     alpha=alpha, l1_ratio=ratio)
       #  model_fit = model.fit(X_train, Y_train)

       #  # train_var['Y'] = list(Y_train.Y)
       #  train_var['Pred_EN'] = [item for item in model_fit.predict(X_train)]
     
       #  # test_var['Y'] = list(Y_test.Y)
       #  test_var['Pred_EN'] = [item for item in model_fit.predict(X_test)]
     
       #  elasticnet_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_EN),
       #                                        'R2_test':  r2_score(Y_test.Y, test_var.Pred_EN),
       #                                        'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_EN),
       #                                        'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_EN),
       #                                        'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_EN),
       #                                        'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_EN)},
       #                                       index=[str(number)])
        
       #  elasticnet_metrics_df = elasticnet_metrics_df.append(elasticnet_metrics_df_aux)
        
       #  lr_dict['EN'].update({number:{}})
       #  lr_dict['EN'][number].update({'train_index':train_index,'test_index':test_index })
        
        
        
        #  ############## RANDOM FOREST   ###########
        # print('CALCULAR RANDOMFOREST')
        
        # RandomForestRegressor().get_params()
        # param_grid = {'bootstrap': [True],
        #              'n_estimators': [10, 200, 500, 1000]}
    
        
        # rf_grid = GridSearchCV(RandomForestRegressor(oob_score=False, random_state=None, 
        #                         verbose=True, warm_start=False),
        #                        param_grid, cv=5).fit(X_train, Y_train)
   
        
        # bootstrap = rf_grid.best_estimator_.bootstrap
        # # max_features = rf_grid.best_estimator_.max_features
        # n_estimators = rf_grid.best_estimator_.n_estimators

        # print('Melhor Estimadores , bootstrap, maxfeatforam ', n_estimators, bootstrap)

        # model = RandomForestRegressor(oob_score=False, random_state=None, 
        #                         verbose=True, warm_start=False,
        #                         bootstrap=bootstrap, n_estimators=n_estimators)
        # model_fit = model.fit(X_train, Y_train)

        # # train_var['Y'] = list(Y_train.Y)
        # train_var['Pred_RF'] = [item for item in model_fit.predict(X_train)]
     
        # # test_var['Y'] = list(Y_test.Y)
        # test_var['Pred_RF'] = [item for item in model_fit.predict(X_test)]
     
        # randomforest_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_RF),
        #                                       'R2_test':  r2_score(Y_test.Y, test_var.Pred_RF),
        #                                       'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_RF),
        #                                       'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_RF),
        #                                       'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_RF),
        #                                       'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_RF)},
        #                                      index=[str(number)])
        
        # randomforest_metrics_df = randomforest_metrics_df.append(randomforest_metrics_df_aux)
        
        # lr_dict['RF'].update({number:{}})
        # lr_dict['RF'][number].update({'train_index':train_index,'test_index':test_index })
        
        
        # ############## BAGGING ###########
        # print('CALCULAR BAGGING')
        
        # param_grid = {'bootstrap': [True],
        #              'n_estimators': [10, 200, 500, 1000]}
  

        # bagging_grid = GridSearchCV(BaggingRegressor(verbose=True),
        #                        param_grid, cv=5).fit(X_train, Y_train)
   
        # n_estimators = bagging_grid.best_estimator_.n_estimators
        # bootstrap = bagging_grid.best_estimator_.bootstrap

        # print('Melhor Estimadores , max_features, bootstrap ', n_estimators, bootstrap)

        # model = BaggingRegressor(verbose=True, n_estimators=n_estimators, bootstrap=bootstrap)
        

        # model_fit = model.fit(X_train, Y_train)
     
        # # train_var['Y'] = list(Y_train.Y)
        # train_var['Pred_BAG'] = [item for item in model_fit.predict(X_train)]
     
        # # test_var['Y'] = list(Y_test.Y)
        # test_var['Pred_BAG'] = [item for item in model_fit.predict(X_test)]
     
        # bagging_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_BAG),
        #                                       'R2_test':  r2_score(Y_test.Y, test_var.Pred_BAG),
        #                                       'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_BAG),
        #                                       'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_BAG),
        #                                       'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_BAG),
        #                                       'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_BAG)},
        #                                      index=[str(number)])
        
        # bagging_metrics_df = bagging_metrics_df.append(bagging_metrics_df_aux)
        
        # lr_dict['BAG'].update({number:{}})
        # lr_dict['BAG'][number].update({'train_index':train_index,'test_index':test_index })

        
        
        
        
        ############## ADABOOSTING ###########
        print('CALCULAR ADABOOSTING')
        print('#########################', number)

    
        param_grid = {'learning_rate': [0.01,0.05,0.1,1],
                     'n_estimators': [10, 200, 500]}       
    
        adb_grid = GridSearchCV(AdaBoostRegressor(base_estimator=None, random_state=None),
                               param_grid, cv=5, verbose=True).fit(X_train, Y_train)
   
  
        n_estimators = adb_grid.best_estimator_.n_estimators
        learning_rate = adb_grid.best_estimator_.learning_rate
        # loss = adb_grid.best_estimator_.loss

        print('Melhor Estimadores , learning_rate ', n_estimators, learning_rate)

        model = AdaBoostRegressor(base_estimator=None, random_state=None,
                                  n_estimators=n_estimators, learning_rate=learning_rate)

        model_fit = model.fit(X_train, Y_train)

        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_ADB'] = [item for item in model_fit.predict(X_train)]
     
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_ADB'] = [item for item in model_fit.predict(X_test)]
     
        adaboosting_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_ADB),
                                              'R2_test':  r2_score(Y_test.Y, test_var.Pred_ADB),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_ADB),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_ADB),
                                              'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_ADB),
                                              'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_ADB)},
                                             index=[str(number)])
        
        adaboosting_metrics_df = adaboosting_metrics_df.append(adaboosting_metrics_df_aux)
        
        lr_dict['ADB'].update({number:{}})
        lr_dict['ADB'][number].update({'train_index':train_index,'test_index':test_index })
    

    



        ############## GBM ###########
        print('CALCULAR GBM')
        print('#########################', number)

        
        param_grid = {'n_estimators': [10, 200, 500]}
  

        gbm_grid = GridSearchCV(GradientBoostingRegressor(verbose=True),
                               param_grid, cv=5).fit(X_train, Y_train)
   
        n_estimators = gbm_grid.best_estimator_.n_estimators

        print('Melhor Estimadores', n_estimators)

        model = GradientBoostingRegressor(verbose=True, n_estimators=n_estimators)
        model_fit = model.fit(X_train, Y_train)

        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_GBM'] = [item for item in model_fit.predict(X_train)]
     
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_GBM'] = [item for item in model_fit.predict(X_test)]
     
        gbm_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_GBM),
                                              'R2_test':  r2_score(Y_test.Y, test_var.Pred_GBM),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_GBM),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_GBM),
                                              'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_GBM),
                                              'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_GBM)},
                                             index=[str(number)])
        
        gbm_metrics_df = gbm_metrics_df.append(gbm_metrics_df_aux)
        
        lr_dict['GBM'].update({number:{}})
        lr_dict['GBM'][number].update({'train_index':train_index,'test_index':test_index })


        ############## KNN ###########
        print('CALCULAR KNN')

        param_grid= {'n_neighbors': [2,3,4,5,6],
                     'weights': ['uniform','distance']}
        knn_grid = GridSearchCV(KNeighborsRegressor(),
                               param_grid, cv=5).fit(X_train, Y_train)
   
        n_neighbors = knn_grid.best_estimator_.n_neighbors
        weights = knn_grid.best_estimator_.weights

        print('Melhor Estimadores', n_neighbors, weights)


        model = KNeighborsRegressor(n_neighbors=n_neighbors, weights=weights)
        model_fit = model.fit(X_train, Y_train)

        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_KNN'] = [item for item in model_fit.predict(X_train)]
     
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_KNN'] = [item for item in model_fit.predict(X_test)]
     
        knn_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_KNN),
                                              'R2_test':  r2_score(Y_test.Y, test_var.Pred_KNN),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_KNN),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_KNN),
                                              'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_KNN),
                                              'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_KNN)},
                                             index=[str(number)])
        
        knn_metrics_df = knn_metrics_df.append(knn_metrics_df_aux)
        
        lr_dict['KNN'].update({number:{}})
        lr_dict['KNN'][number].update({'train_index':train_index,'test_index':test_index })



        ############## SVM ###########
        print('CALCULAR SVM')
        
        param_grid = { 'epsilon': [1e-5, 1e-3, 0.01, 0.1, 0.5, 0.9, 1],
                       'C': [1, 10, 100, 1000]}

        svm_grid = GridSearchCV(LinearSVR(fit_intercept=True, random_state=None),
                               param_grid, cv=5).fit(X_train, Y_train)
   
        epsilon = svm_grid.best_estimator_.epsilon
        C = svm_grid.best_estimator_.C

        print('Melhor Estimadores', epsilon, C)


        model = LinearSVR(fit_intercept=True, verbose=True, random_state=None, max_iter=500, epsilon=epsilon, C=C)
        model_fit = model.fit(X_train, Y_train)

        # train_var['Y'] = list(Y_train.Y)
        train_var['Pred_SVM'] = [item for item in model_fit.predict(X_train)]
     
        # test_var['Y'] = list(Y_test.Y)
        test_var['Pred_SVM'] = [item for item in model_fit.predict(X_test)]
     
        svm_metrics_df_aux = pd.DataFrame({'R2_train': r2_score(Y_train.Y, train_var.Pred_SVM),
                                              'R2_test':  r2_score(Y_test.Y, test_var.Pred_SVM),
                                              'MSE_train': mean_squared_error(Y_train.Y, train_var.Pred_SVM),
                                              'MSE_test':  mean_squared_error(Y_test.Y, test_var.Pred_SVM),
                                              'MAE_train': mean_absolute_error(Y_train.Y, train_var.Pred_SVM),
                                              'MAE_test':  mean_absolute_error(Y_test.Y, test_var.Pred_SVM)},
                                             index=[str(number)])
        
        svm_metrics_df = svm_metrics_df.append(svm_metrics_df_aux)
        
        lr_dict['SVM'].update({number:{}})
        lr_dict['SVM'][number].update({'train_index':train_index,'test_index':test_index })
        
      
    lf_metrics_aux = lf_metrics_df.loc[lf_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    lf_metrics_aux['Model'] = 'OLS'

    lasso_metrics_df_aux = lasso_metrics_df.loc[lasso_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    lasso_metrics_df_aux['Model'] = 'LASSO'

    lars_metrics_df_aux = lars_metrics_df.loc[lars_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    lars_metrics_df_aux['Model'] = 'LARS'

    lassolars_metrics_df_aux = lassolars_metrics_df.loc[lassolars_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    lassolars_metrics_df_aux['Model'] = 'LASSO LARS'

    ridge_metrics_df_aux = ridge_metrics_df.loc[ridge_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    ridge_metrics_df_aux['Model'] = 'RIDGE'

    elasticnet_metrics_df_aux = elasticnet_metrics_df.loc[elasticnet_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    elasticnet_metrics_df_aux['Model'] = 'ELASTIC NET'

    randomforest_metrics_df_aux = randomforest_metrics_df.loc[randomforest_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    randomforest_metrics_df_aux['Model'] = 'RF'
    
    adaboosting_metrics_df_aux = adaboosting_metrics_df.loc[adaboosting_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    adaboosting_metrics_df_aux['Model'] = 'ADABOOSTING'    

    bagging_metrics_df_aux = bagging_metrics_df.loc[bagging_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    bagging_metrics_df_aux['Model'] = 'BAGGING'
       
    gbm_metrics_df_aux = gbm_metrics_df.loc[gbm_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    gbm_metrics_df_aux['Model'] = 'GBM'

    knn_metrics_df_aux = knn_metrics_df.loc[knn_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    knn_metrics_df_aux['Model'] = 'KNN'
    
    svm_metrics_df_aux = svm_metrics_df.loc[svm_metrics_df[['MSE_test']].idxmin().item()].to_frame().transpose()
    svm_metrics_df_aux['Model'] = 'SVM'    

 
    model_metrics = pd.DataFrame() 
    model_metrics = model_metrics.append(lf_metrics_aux)
    model_metrics = model_metrics.append(lasso_metrics_df_aux)
    model_metrics = model_metrics.append(lars_metrics_df_aux)
    model_metrics = model_metrics.append(lassolars_metrics_df_aux)
    model_metrics = model_metrics.append(ridge_metrics_df_aux)
    model_metrics = model_metrics.append(elasticnet_metrics_df_aux)
    model_metrics = model_metrics.append(randomforest_metrics_df_aux)
    model_metrics = model_metrics.append(adaboosting_metrics_df_aux)
    model_metrics = model_metrics.append(bagging_metrics_df_aux)
    model_metrics = model_metrics.append(adaboosting_metrics_df_aux)
    model_metrics = model_metrics.append(gbm_metrics_df_aux)
    model_metrics = model_metrics.append(knn_metrics_df_aux)
    model_metrics = model_metrics.append(svm_metrics_df_aux)

    model_choosen = model_metrics[model_metrics['MSE_test']==model_metrics['MSE_test'].min()]['Model'].item()

    if model_choosen=='OLS':
        
        model_metrics_df = lf_metrics_df    
        
    if model_choosen=='LASSO':
        
        model_metrics_df = lasso_metrics_df  
        
    if model_choosen=='LARS':
        
        model_metrics_df = lars_metrics_df    
        
    if model_choosen=='LASSO LARS':
        
        model_metrics_df = lassolars_metrics_df  

    if model_choosen=='RIDGE':
        
        model_metrics_df = ridge_metrics_df  

    if model_choosen=='ELASTIC NET':
        
        model_metrics_df = elasticnet_metrics_df  
        
    if model_choosen=='RF':
        
        model_metrics_df = randomforest_metrics_df  
        
    if model_choosen=='ADABOOSTING':
        
        model_metrics_df = adaboosting_metrics_df   
        
    if model_choosen=='BAGGING':
        
        model_metrics_df = bagging_metrics_df    
        
    if model_choosen=='GBM':
        
        model_metrics_df = gbm_metrics_df 

    if model_choosen=='SVM':
        
        model_metrics_df = svm_metrics_df 

    if model_choosen=='KNN':
        
        model_metrics_df = knn_metrics_df          
        
 


    return model_choosen, model_metrics_df, lr_dict




def run_model(df_merged, model_choosen, model_metrics_df, lr_dict, test_run):



    #REMOVE NON NUMERICAL VARIABLES
    df_X = df_merged.select_dtypes(include=['float64']).drop('Y', axis=1)
    df_y = df_merged[['Y']]

     #KEEP IMPORTANT VARIABLES
    if 'Data_Y' in df_merged.columns:
        df_model = df_merged[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data_Y', 'Data_X', 'Rating', 'Y']]

    else:
        df_model = df_merged[['DENOM_SOCIAL','CNPJ_FUNDO','TAB_X_CLASSE_SERIE','TAB_X_CLASSE_SERIE_AUX', 'Data', 'Rating', 'Y']]


    coef_df=pd.DataFrame({'name':df_X.columns})

    
    if model_choosen=='OLS':
     
    
            model = LinearRegression()
            model_fit = model.fit(df_X, df_y)           
            
     
    if model_choosen=='LASSO':
        
            train = df_merged.iloc[lr_dict['LASSO'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['LASSO'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
            
            param_grid = {'alpha': [1e-15, 1e-10, 1e-5, 1e-2,1e-1, 1, 5, 10]}
            lasso_grid = GridSearchCV(Lasso(copy_X=True, fit_intercept=True, max_iter=1000, positive=False, normalize=True),
                                  param_grid, cv=5).fit(X_train, Y_train)
        
            alpha = lasso_grid.best_estimator_.alpha
            print('Melhor alpha foi ', alpha)
        
    
    
            model = Lasso(copy_X=True, fit_intercept=True, max_iter=1000, positive=False, normalize=True, alpha=alpha)
            model_fit = model.fit(df_X, df_y)
            
            coef_df['coef_lasso']=model_fit.coef_            
            
        
    if model_choosen=='LARS':
    
            train = df_merged.iloc[lr_dict['LARS'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['LARS'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
            
            param_grid = {'eps': [1e-15, 1e-10, 1e-5, 1e-2,1e-1, 1, 5, 10, 20],
                          'n_nonzero_coefs':[1,10,50,100,300, 380]}
            lars_grid = GridSearchCV(Lars(fit_intercept=True, verbose=True, normalize=True,
                                          copy_X=True, fit_path=True),
                                      param_grid, cv=5).fit(X_train, Y_train)
            
            eps = lars_grid.best_estimator_.eps
            nzero = lars_grid.best_estimator_.n_nonzero_coefs
            print('Melhor eps foi ', eps)
    
            
     
            model = Lars(fit_intercept=True, verbose=True, normalize=True,
                         copy_X=True, fit_path=True, eps=eps, n_nonzero_coefs=nzero)        
            model_fit = model.fit(df_X, df_y)
                
            coef_df['coef_lars']=model_fit.coef_
        
        
    if model_choosen=='LASSO LARS':
    
            train = df_merged.iloc[lr_dict['LASSOLARS'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['LASSOLARS'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
            
            param_grid = {'eps': [1e-20, 1e-15, 1e-8,1e-3,1,5,10,20],
                          'alpha':[1e-10,1e-8,1e-2,1,2,5,10]}
            lassolars_grid = GridSearchCV(LassoLars(fit_intercept=True, verbose=False, normalize=True, 
                                                    max_iter=500, copy_X=True,fit_path=True, positive=False),
                                          param_grid, cv=5).fit(X_train, Y_train)
        
            eps = lassolars_grid.best_estimator_.eps
            alpha = lassolars_grid.best_estimator_.alpha
            print('Melhor eps  e alpha foram ', eps, alpha)
        
            
     
            model = LassoLars(fit_intercept=True, verbose=False, normalize=True, 
                              max_iter=500, copy_X=True,fit_path=True, positive=False,
                              alpha=alpha, eps=eps)
            model_fit = model.fit(df_X, df_y)
            coef_df['coef_lassolars']=model_fit.coef_

    
        
    if model_choosen=='RIDGE':
    
            train = df_merged.iloc[lr_dict['RIDGE'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['RIDGE'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
            
            
            param_grid = {'alpha':[1e-15, 1e-10, 1e-8, 1e-5, 1e-3,1e-2,1e-1, 1, 5, 10,20,50,100,200]}
            ridge_grid = GridSearchCV(Ridge(fit_intercept=True, normalize=True, copy_X=True, 
                                            max_iter=None, tol=0.001, random_state=None),
                                      param_grid, cv=5).fit(X_train, Y_train)
        
            alpha = ridge_grid.best_estimator_.alpha
            print('Melhor alpha foi ', alpha)
        
         
    
            model = Ridge(fit_intercept=True, normalize=True, copy_X=True, 
                     max_iter=None, tol=0.001, random_state=None,
                     alpha=alpha)
            model_fit = model.fit(df_X, df_y)
            coef_df['coef_ridgelars']=model_fit.coef_[0]
   

        
    if model_choosen=='ELASTIC NET':
        
            train = df_merged.iloc[lr_dict['EN'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['EN'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
            
            
            param_grid = {'alpha':[1e-15,1e-10, 1e-5,1e-2, 1, 5,20],
                     'l1_ratio':[0.01,0.25,0.5,0.75,0.99]}
            en_grid = GridSearchCV(ElasticNet(fit_intercept=True, normalize=True, 
                                              precompute=False, max_iter=500, copy_X=True, tol=0.0001, 
                                              warm_start=False, positive=False, random_state=None),
                                   param_grid, cv=5).fit(X_train, Y_train)
        
            alpha = en_grid.best_estimator_.alpha
            ratio = en_grid.best_estimator_.l1_ratio
            print('Melhor alpha e ratio foram ', alpha, ratio)
    
    
            model = ElasticNet(fit_intercept=True, normalize=True, 
                               precompute=False, max_iter=1000, copy_X=True, tol=0.0001, 
                               warm_start=False, positive=False, random_state=None,
                               alpha=alpha, l1_ratio=ratio)
            model_fit = model.fit(df_X, df_y)
            coef_df['coef_en']=model_fit.coef_


    if model_choosen=='BAGGING':
        
        if test_run:
        
            train = df_merged.iloc[lr_dict['BAG'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['BAG'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
                        
            param_grid = {'bootstrap': [True, False],
                         'n_estimators': [10, 200, 500, 1000]}
      
            bagging_grid = GridSearchCV(BaggingRegressor(verbose=True),
                                        param_grid, cv=5).fit(X_train, Y_train)
       
            n_estimators = bagging_grid.best_estimator_.n_estimators
            bootstrap = bagging_grid.best_estimator_.bootstrap
            
            
        else:
            n_estimators = model_metrics_df['ESTIMADORES'].item()
            bootstrap = model_metrics_df['BOOTSTRAP'].item()
            
             

        model = BaggingRegressor(verbose=True, n_estimators=n_estimators, bootstrap=bootstrap)
        model_fit = model.fit(df_X, df_y)
            
    if model_choosen=='RF':
        
        if test_run:
            
        
            train = df_merged.iloc[lr_dict['RF'][int(model_metrics_df[['MSE_test']].idxmin().item())]['train_index']]
            test = df_merged.iloc[lr_dict['RF'][int(model_metrics_df[['MSE_test']].idxmin().item())]['test_index']]
            
            #REMOVE NON NUMERICAL VARIABLES
            X_train = train.select_dtypes(include=['float64']).drop('Y', axis=1)
            X_test = test.select_dtypes(include=['float64']).drop('Y', axis=1)   
              
            Y_train = train['Y'].to_frame()
            Y_test = test['Y'].to_frame()
                        
            param_grid = {'bootstrap': [True, False],
                         'n_estimators': [10, 200, 500, 1000]}
        
            
            rf_grid = GridSearchCV(RandomForestRegressor(oob_score=False, random_state=None, 
                                    verbose=True, warm_start=False),
                                   param_grid, cv=5).fit(X_train, Y_train)
       
            
            bootstrap = rf_grid.best_estimator_.bootstrap
            # max_features = rf_grid.best_estimator_.max_features
            n_estimators = rf_grid.best_estimator_.n_estimators
            
            
        else:
            n_estimators = model_metrics_df['ESTIMADORES'].item()
            bootstrap = model_metrics_df['BOOTSTRAP'].item()        
            

        print('Melhor Estimadores , max_features, bootstrap ', n_estimators, bootstrap)
   
        
        model = RandomForestRegressor(oob_score=False, random_state=None, 
                                      verbose=True, warm_start=False,
                                      bootstrap=bootstrap, n_estimators=n_estimators)  
        model_fit = model.fit(df_X, df_y)



    df_model['Pred_Y'] = [item for item in model_fit.predict(df_X)]
    
    #APPEND DF MODEL WITH X VARIABLES
    df_model = pd.merge(df_model, df_X, left_index=True, right_index=True)

    final_model_metrics = pd.DataFrame({'R2': r2_score(df_y.Y, df_model.Pred_Y),
                                         'MSE': mean_squared_error(df_y.Y, df_model.Pred_Y),
                                         'MAE': mean_absolute_error(df_y.Y, df_model.Pred_Y),
                                         'MODEL': 'BAGGING',
                                         'ESTIMADORES':n_estimators,
                                         'BOOTSTRAP': bootstrap},       
                                        index=['BAGGING'])
    
    print ('Erro na base teste eh', final_model_metrics['MSE'])
        
    return df_model, final_model_metrics, model_fit



def save_results(df_model, final_model_metrics, mode):
    
    
    import matplotlib.pyplot as plt
    import statsmodels.api as sm

    if mode=='past':

        fig=plt.figure()
        ax=fig.add_axes([0,0,1,1])
        ax.scatter(df_model['TAB_X_VL_RENTAB_MES'], df_model['Y'], color='r', label='Y', alpha=0.4)
        ax.scatter(df_model['TAB_X_VL_RENTAB_MES'], df_model['Pred_Y'], color='b', label='Previsão', alpha=0.4)
        ax.set_xlabel('Rentabilidade Nominal Mensal Anualizada (t-1)')
        ax.set_ylabel('Rentabilidade Nominal Mensal (t)')
        ax.set_title('Rentabilidade Prevista FIDCs')
        plt.xlim(-0.1,2.8)
        ax.legend(loc='best')
        fig.savefig('./Dados CVM/Modelagem/ Rent pred vs passada - '+mode+'.png',bbox_inches='tight')     
        plt.show()
            

    
    m, b = np.polyfit(df_model['Y'], df_model['Pred_Y'], 1)

    fig=plt.figure(tight_layout=True)
    ax=fig.add_axes([0,0,1,1])
    ax.scatter(df_model['Y'], df_model['Pred_Y'], alpha=0.4)
    ax.set_xlabel('Y')
    ax.set_ylabel('Previsão')
    ax.set_title('Rentabilidade Observada vs Prevista')

    ax.plot(df_model['Y'], m*df_model['Y'] + b, color='r', alpha=0.5)
    # fig.tight_layout()    
    fig.savefig('./Dados CVM/Modelagem/Rentabilidade obs vs prevista - '+mode+'.png',bbox_inches='tight')     
    plt.show()
        

    writer = pd.ExcelWriter(r'./Dados CVM/Modelagem/Modelagem - '+mode+'.xlsx')
    df_model.to_excel(writer, sheet_name='Dados e Previsão', index=False)
    final_model_metrics.to_excel(writer, sheet_name='Metricas', index=False)
    writer.save()
    
    
    return ('Modelo salvo com sucesso!')




#####################
#CONFERIR AS VARIAVEIS PARA VER SE TIRO ALGUMA
#####################


if __name__=='__main__':
    
    #os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Plots')
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')
    df_fidc, df_rating= open_dfs()

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
    
    # spread='IPCA'
    # spread='DI'
    
    month_forescast = 12
    
    # mode='present'           #Utiliza dados financeiros de hoje para prever rentabilidade hoje
    # mode='present2'          #Utiliza dados financeiros de hoje para prever rentabilidade hoje (remove variaveis economicas)
    # mode='present3'          #Utiliza dados financeiros de hoje para prever rentabilidade hoje (remove variaveis economias e de rent sub)
    mode='present4'          #Utiliza dados financeiros de hoje para prever rentabilidade hoje (remove variaveis economias, de rent sub e de taxas mensais praticadas)

    # mode='past'                #Utiliza dados de month_forecats meses atras para prever rentabilidade hoje
    
    
    remove_rentsub = True      #remove cotas rentabilidade das cotas subordinadas das variavesis explicativas
    # remove_rentsub = False       #Nao remove cotas rentabilidade das cotas subordinadas das variavesis explicativas
 
    remove_taxvar = True      #remove variaveis de taxas de negociacao no mes como variavel explicativa
    # remove_taxvar = False       #nao remove variaveis de taxas de negociacao no mes como variavel explicativa
    
 
    df_merged = filter_dfs(df_fidc, df_rating, ipeaseries_dict, month_forescast, mode, remove_rentsub, remove_taxvar)
    
    # test_run=True  #True: precisa rodar o modelo todo de novo (demora horas)// 
    # test_run=False #False: Ja pega o ultimo modelo que teve melhor performance e seus parametros
    
    # if test_run==True:
    #     model_choosen, model_metrics_df, lr_dict = model_df(df_merged)
    # else:
    #     os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')
    #     model_metrics_df = pd.read_excel('./Dados CVM/Modelagem/Modelagem.xlsx', sheet_name='Metricas')
    #     model_choosen = model_metrics_df['MODEL'].item()
        
    # df_model, final_model_metrics, model_fit = run_model(df_merged, model_choosen, model_metrics_df, lr_dict,test_run)
    
    # save_results(df_model, final_model_metrics, mode)   
    


 