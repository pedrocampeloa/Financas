#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 13:41:23 2020

@author: pedrocampelo
"""

import os
import pandas as pd
# import datetime as dt
import numpy as np
import datetime as dt



os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')


def set_fidcs_df(FIDC_date_list, df_fidc_old):
    
    """"
    Nessa funcao eu appendo os dataframes pelo site da CVM
    O Site disponibiliza cerca de 16 tabelas, indicadas no index list (algumas entraram depois de algum periodo)
    É preciso conecta-las da forma correta: primeira parte é agregada por fundo e segunda por cotas
    É agregado uma tabela agregando as tabelas por fundo (fidc_df1), e outra pelas cotas (fidc_X) e depois agrego as duas (fidc_df_agg_aux)
    
    fidc_df1: Na primeira agrego horizontalmente por CNPJ, Nome e Data
    fidc_X: Na primeira agreg horizontalmente opor CNPJ, Nome, Cota e Data
    fidc_df_agg_aux: Agora é preciso appendar verticalmente as bases com as Datas diferentes
    
    Por fim, abro a ultima base de FIDCS (df_fidc_old) e atualizo as novas informacoes de forma automatica     
    """
    
    FIDC_index_list=["I", "II","III","IV","V","VI","VII","IX","X_1_1","X_5","X_7","X_1","X_2","X_3","X_4","X_6"]
    fidc_dict={}
    fidc_df_agg=pd.DataFrame()
    
    for FIDC_date in FIDC_date_list:
        
        FIDC_year=FIDC_date[0:4]
        FIDC_month=FIDC_date[4:len(FIDC_date)]
        fidc_dict[FIDC_date]={}
              
        
        for FIDC_index in FIDC_index_list:
            
            #ANTES DE 2017 O INFORME NAO ERA MENSAL, E SIM ANUAL (SINALIZAR CAMINHOS DIFERENTES)
            if int(FIDC_year)<2017:
                file_name = "Dados CVM/"+FIDC_year+"/inf_mensal_fidc_"+FIDC_year+"/inf_mensal_fidc_tab_"+FIDC_index+"_"+FIDC_year+".csv"
            else:
                file_name = "Dados CVM/"+FIDC_year+ "/"+FIDC_date+"/inf_mensal_fidc_"+FIDC_date+"/inf_mensal_fidc_tab_"+FIDC_index+"_"+FIDC_date+".csv"
                
              
            print(FIDC_date, FIDC_index)
            
            if os.path.isfile(file_name):
                
                fidc_df=pd.read_csv(file_name, encoding="ISO-8859-1", sep=';')
     
                
                #print(fidc_df.columns[0:5]) 
                
                # if  'TAB_X_CLASSE_SERIE' in fidc_df.columns:
                    #print(fidc_df['TAB_X_CLASSE_SERIE'].unique().tolist())
                
                if FIDC_index=='I':
                    
                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    columns_strings = ['CNPJ_ADMIN','ADMIN','CONDOM', 'FUNDO_EXCLUSIVO', 'COTST_INTERESSE']
                    
                    columns1 = columns_groupby + columns_numeric
                    columns2 = columns_groupby + columns_strings
    
                    fidc_df_aux1 = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()        
                    fidc_df_aux2 = fidc_df[columns2].fillna('').groupby(columns_groupby + ['CONDOM', 'FUNDO_EXCLUSIVO', 'COTST_INTERESSE']).sum().reset_index()
                    
                    fidc_df = fidc_df_aux1.merge(fidc_df_aux2,how='left',on=['DENOM_SOCIAL','CNPJ_FUNDO','DT_COMPTC'])[columns_groupby + columns_strings + columns_numeric]       
                    
                    fidc_df1=fidc_df
            
                
                elif FIDC_index in ["II","III","IV","V","VI","VII","IX", "X_1_1", "X_5", "X_7"]:

                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    
                    columns1 = columns_groupby + columns_numeric
    
                    fidc_df = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()        
                    
                    fidc_df1 = pd.merge(fidc_df1, fidc_df, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC'], how='left')                
                    fidc_dict[FIDC_date].update({'AGG':fidc_df1})
                    
                elif FIDC_index=='X_1':               
                    
                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    
                    columns1 = columns_groupby + columns_numeric
    
                    fidc_df = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()        
                    fidc_x1 = fidc_df

                    
                elif FIDC_index=='X_2': 
                    
                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    
                    columns1 = columns_groupby + columns_numeric
    
                    fidc_df = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()     
                    fidc_x2 = fidc_df
                    
                elif FIDC_index=='X_3':
                    
                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    
                    columns1 = columns_groupby + columns_numeric
    
                    fidc_df = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()     
                    fidc_x3 = fidc_df
                    
                    fidc_x3['TAB_X_CLASSE_SERIE'] = fidc_x3['TAB_X_CLASSE_SERIE'].replace(to_replace=['Classe Sénior'], value='Sênior', regex=True)
                    fidc_x1x3 = pd.merge(fidc_x3,fidc_x1, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'], how='left')
    
                    fidc_dict[FIDC_date].update({'X1X3':fidc_x1x3})
                    
                    FIDC_date_aux = dt.datetime.strptime(FIDC_year+'-'+FIDC_month+'-01', '%Y-%m-%d')
                    
                    #ANTES DE 10/2019, AS COTAS SENIORES DAS TABELAS X1 E X3 NAO VINHA COM O NUMERO DA COTA SENIOR (SENIOR1) E FICA IMPOSSÍVEL DA CHAVE SER IGUAL PARA O MERGE COM AS TABELAS X2 E X4
                    if FIDC_date_aux<=dt.datetime.strptime('2019-10-01', '%Y-%m-%d'):

                        fidc_x1x3['TAB_X_CLASSE_SERIE'] = fidc_x1x3['TAB_X_CLASSE_SERIE'].replace(to_replace=['Sênior'], value='Sênior 1', regex=True)
                    
                elif FIDC_index=='X_4':
                    
                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE','TAB_X_TP_OPER']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    
                    columns1 = columns_groupby + columns_numeric
    
                    fidc_df2 = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()     
                    
                    fidc_x4_vl = fidc_df.pivot_table('TAB_X_VL_TOTAL', 
                             ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'],
                             'TAB_X_TP_OPER')
    
                    fidc_x4_vl=fidc_x4_vl.rename(columns={'Amortizações':'TAB_X_VL_TOTAL_AMORT',
                                                         'Captações no Mês':'TAB_X_VL_TOTAL_CAPT', 
                                                         'Resgates Solicitados':'TAB_X_VL_TOTAL_RESGSOL',
                                                         'Resgates no Mês':'TAB_X_VL_TOTAL_RESG'})
                                
                    fidc_x4_qt = fidc_df.pivot_table('TAB_X_QT_COTA', 
                                             ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'],
                                             'TAB_X_TP_OPER')
                    
                    fidc_x4_qt=fidc_x4_qt.rename(columns={'Amortizações':'TAB_X_QT_TOTAL_AMORT',
                                                         'Captações no Mês':'TAB_X_QT_TOTAL_CAPT', 
                                                         'Resgates Solicitados':'TAB_X_QT_TOTAL_RESGSOL',
                                                         'Resgates no Mês':'TAB_X_QT_TOTAL_RESG'})
                                    
                    fidc_x4 = pd.merge(fidc_x4_vl, fidc_x4_qt, left_index=True, right_index=True).reset_index()
                    
                    fidc_x2x4 = pd.merge(fidc_x2, fidc_x4, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'], how='left')
                    fidc_x2x4['TAB_X_CLASSE_SERIE'] = fidc_x2x4['TAB_X_CLASSE_SERIE'].replace(to_replace=['Série'], value='Sênior', regex=True)
    
                    fidc_dict[FIDC_date].update({'X2X4':fidc_x2x4})
                     
                    if int(FIDC_year)<2017:
                        file_name_aux = "Dados CVM/"+FIDC_year+"/inf_mensal_fidc_"+FIDC_year+"/inf_mensal_fidc_tab_X_6_"+FIDC_year+".csv"
                    else:
                        file_name_aux = "Dados CVM/"+FIDC_year+ "/"+FIDC_date+"/inf_mensal_fidc_"+FIDC_date+"/inf_mensal_fidc_tab_X_6_"+FIDC_date+".csv"
      
                    if not os.path.isfile(file_name_aux):
                        print('Nao tem X6')
           
                        #X1X3 appenda o X2X4
                        fidc_X = pd.merge(fidc_x1x3, fidc_x2x4, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'], how='left')
                        fidc_df_agg_aux = pd.merge(fidc_X, fidc_df1, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC'], how='left')
                        fidc_df_agg_aux = fidc_df_agg_aux.drop_duplicates()

                        # print('TAB_X_VL_LIQUIDEZ_180' in fidc_df_agg_aux.columns)
 
                        fidc_dict[FIDC_date].update({'X':fidc_df_agg_aux})
    
                elif FIDC_index=='X_6':

                    print('Tem X6')
                    
                    columns_groupby = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE']
                    columns_numeric = fidc_df.select_dtypes(include=['float64','int64']).columns.to_list()
                    
                    columns1 = columns_groupby + columns_numeric
    
                    fidc_df = fidc_df[columns1].groupby(columns_groupby).mean().reset_index()     

                    fidc_x6 = fidc_df
                    fidc_x6['TAB_X_CLASSE_SERIE'] = fidc_x6['TAB_X_CLASSE_SERIE'].replace(to_replace=['Senior'], value='Sênior', regex=True)
                    fidc_x1x3x6 = pd.merge(fidc_x1x3,fidc_x6, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'], how='left')

                    fidc_dict[FIDC_date].update({'X1X3X6':fidc_x1x3x6})
    
                    #X1X3X6 appenda o X2X4
                    fidc_X = pd.merge(fidc_x1x3x6, fidc_x2x4, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC','TAB_X_CLASSE_SERIE'], how='left')
                    fidc_df_agg_aux = pd.merge(fidc_X, fidc_df1, on=['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC'], how='left')
                    fidc_df_agg_aux = fidc_df_agg_aux.drop_duplicates()

                    # print('TAB_X_VL_LIQUIDEZ_180' in fidc_df_agg_aux.columns)
                    
                    #fidc_dict[FIDC_date] = fidc_df_agg_aux
                    fidc_dict[FIDC_date].update({'X':fidc_df_agg_aux})
                    
          
        print('Appendando', FIDC_date)    
        fidc_df_agg=fidc_df_agg.append(fidc_df_agg_aux)
        #print('TAB_X_VL_LIQUIDEZ_180' in fidc_df_agg.columns)
           
        fidc_df_agg['Data'] = fidc_df_agg['DT_COMPTC'].apply(lambda x: x[:8]+'01')
        #fidc_df_agg['DT_COMPTC'] = pd.to_datetime(fidc_df_agg['DT_COMPTC'])
        #fidc_df_agg['Data'] = pd.to_datetime(fidc_df_agg['Data'])
    
        fidc_df_agg['TAB_X_CLASSE_SERIE_AUX']=np.where(fidc_df_agg['TAB_X_CLASSE_SERIE'].str.contains('Sênior'), 'Senior', fidc_df_agg['TAB_X_CLASSE_SERIE'])
      
    fidc_df_agg['DT_COMPTC'] = pd.to_datetime(fidc_df_agg['DT_COMPTC'])
    fidc_df_agg['Data'] = pd.to_datetime(fidc_df_agg['Data'])
      
    fidc_df_agg['d_CONDOM']=np.where(fidc_df_agg['CONDOM']=='ABERTO', 1, 0)
    fidc_df_agg['d_FUNDO_EXCLUSIVO']=np.where(fidc_df_agg['FUNDO_EXCLUSIVO']=='S', 1, 0)
    fidc_df_agg['d_COTST_INTERESSE']=np.where(fidc_df_agg['COTST_INTERESSE']=='S', 1, 0)
    
    print('Abrindo e arrumando base da CVM')
    df_fidc_old = df_fidc_old[df_fidc_old['DT_COMPTC'].isin(list(set(df_fidc_old['DT_COMPTC'].unique())-set(fidc_df_agg['DT_COMPTC'].unique())))]
    
    df_fidc_final = fidc_df_agg.append(df_fidc_old)
    df_fidc_final['TAB_X_CLASSE_SERIE_AUX']=np.where(df_fidc_final['TAB_X_CLASSE_SERIE'].str.contains('Subordinada'), 'Subordinada', df_fidc_final['TAB_X_CLASSE_SERIE'])
    
    print('Dados arrumados com sucesso!')
    return df_fidc_final,fidc_dict




def save_dfs(df_fidc_final):
    
    print('Salvando DFs')
    
    df_fidc_final.to_pickle(r'./Dados CVM/Dados FIDCS.pkl')
       
    writer = pd.ExcelWriter(r'./Dados CVM/Dados FIDCS.xlsx')
    df_fidc_final.to_excel(writer, sheet_name='FIDCs', index=False)
    writer.save()
    
    # writer = pd.ExcelWriter(r'./Dados CVM/Dados FIDCS.csv')
    # df_fidc_final.to_excel(writer, sheet_name='FIDCs', index=False)
    # writer.save() 
    
    return ('DFs salvos com sucesso!')




if __name__=='__main__':
    
  
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')
    
    df_fidc_old = pd.read_pickle(r'./Dados CVM/Dados FIDCS.pkl')
    FIDC_date_list=["201301","201401","201501","201601",
                    "201701","201702","201703","201704","201705","201706",
                    "201707","201708","201709","201710","201711","201712",
                    "201801","201802","201803","201804","201805","201806",
                    "201807","201808","201809","201810","201811","201812",
                    "201901","201902","201903","201904","201905","201906",
                    "201907","201908","201909","201910","201911","201912",
                    "202001","202002","202003","202004","202005","202006"]

    df_fidc_final, fidc_dict = set_fidcs_df(FIDC_date_list, df_fidc_old)
    save_dfs(df_fidc_final)




        