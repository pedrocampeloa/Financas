#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 18:20:47 2020

@author: pedrocampelo
"""

import selenium
import time
import os
import pandas as pd
import datetime as dt
import numpy as np
import regex as re
import unidecode
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch
import matplotlib.gridspec as gridspec
import seaborn as sns

import sgs
import ipeadatapy as ipea

import spacy
import keras
import nltk
import sklearn


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
    df_fidc_senior=df_fidc[df_fidc['TAB_X_CLASSE_SERIE_AUX']=='Senior'] 

    
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
    
    df_rating_filter4=df_rating_filter3[~df_rating_filter3['CNPJ'].isin(list(rating_list))]  #FILTRO 4 (COTAS QUE NAO ESTAO NA BASE DA CVM)
                                        

    
    if len(intersect_list)/len(cnpj_rating_list)>0.85:
        print('Maioria dos FIDCs com Rating estao na base da CVM')
    else:
        print('Muitos FIDCs avaliados nao estao na lista da CVM!!!!')
        sys.exit()
    
    print('Distinguindo os ratings pela Data de availiacao mais proxima')
    df_rating_append=pd.DataFrame()
    for cnpj in df_rating_filter4['CNPJ'].unique().tolist():
        df_aux=df_rating_filter4[df_rating_filter4['CNPJ']==cnpj]
        if len(df_aux['Rating'].unique())>1:
            print('Retirar rating antigos')
            df_aux=df_aux[df_aux['Data']==max(df_aux['Data'].tolist())]

        df_aux=df_aux[0:1]
        df_aux=df_aux[['CNPJ','ISIN','Rating','Rating_AUX','Data', 'Data Vencimento','Rating Antigo', 
                       'Data Rating Antigo', 'Data Vencimento Antigo','Agencia']]
        df_rating_append=df_rating_append.append(df_aux)                              #FILTRO 5 (NOTAS DUPLICADAS)
        
        
    df_rating_append = df_rating_append.rename(columns={'CNPJ':'CNPJ_FUNDO', 'Data':'Data Rating'})      
              

  
    #NAO PEGAR AA- NACIONAL
    # df_rating_final = df_rating_append[(df_rating_append['Rating_AUX'].isin(['AAA', 'AA+', 'AA', 'AA-'])&
    #                                      df_rating_append['Agencia'].isin(['FITCH', 'SP', 'MOODYS']))|
    #                                     (df_rating_append['Rating_AUX'].isin(['AAA', 'AA+', 'AA'])&
    #                                      df_rating_append['Agencia'].isin(['AUSTIN', 'LIBERIUM', 'SR']))]

    #PEGAR A- PRA CIMA
    df_rating_final = df_rating_append[df_rating_append['Rating_AUX'].isin(['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A','A-',])]
    
    
    
    print('Bases Filtradas com sucesso!')

    return df_fidc_senior, df_rating_filter4, df_rating_append, df_rating_final



def plot_rating(df_rating, df_rating_filter4, df_rating_append):


    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Plots')

    
    ########################################### #PIE PLOT ####################################3
    
    # 1376 -FILTRO1 >>> 731 - FILTRO2 >>> 631 -  FILTRO3 >>> 622 - FILTRO 4 >>>> 608 - FILTRO 5 >>> 393 - FILTRO 6 >>> 140    

    
    ############################################# SET DATABASE TO PIEPLOT1 ####################################

    #FILTRO 1
    pie_df1=df_rating['Tipo Cota'].value_counts().to_frame()
    pie_df1['Cota']=pie_df1.index
    pie_df1['Explode']=np.where(pie_df1['Cota']=='Senior',0.1,0)
    pie_df1['Label'] = pie_df1['Cota'] + ' - ' + pie_df1['Tipo Cota'].apply(str)
    pie_df1['Label2'] = np.where(pie_df1['Cota']=='Subordinada','',pie_df1['Label'])

    #pie_df1=pie_df1.sort_values(by=['Tipo Cota'], ascending=True)

    pal = sns.diverging_palette(255,130, l=60, n=20, center="dark")
    
    ############################################## PIE PLOT 1 - A #######################################


    #PLOT1
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.pie(pie_df1['Tipo Cota'],  labels =  pie_df1['Cota'], shadow=False, startangle=310, colors=[pal[1],'C1'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.legend(pie_df1['Label'], loc="best")
    plt.title("Filtro da Base Total de  Rating\n" + "Filtro 1 - Cotas Senior")
    
    plt.savefig('Ratings Filtrados 1.png') 
    plt.show()    
    
    ############################################## PIE PLOT 1 - B #######################################

    #PLOT2
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.pie(pie_df1['Tipo Cota'],  labels =  pie_df1['Cota'],shadow=False, startangle=310, colors=[pal[1],'w'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.legend( pie_df1['Label2'], loc="best")
    plt.title("Filtro da Base Total de  Rating\n" + "Filtro 1 - Cotas Senior")

    plt.savefig('Ratings Filtrados 2.png') 
    plt.show()  


    ############################################# SET DATABASE TO PIEPLOT 2  ####################################
    
    pie_df2_aux=pd.DataFrame({'Tipo Cota': [len(df_rating_filter4), pie_df1[pie_df1['Cota']=='Senior']['Tipo Cota'].values[0] - len(df_rating_filter4)],
                                           'Cota':['Seniores Usáveis', 'Seniores Não Usáveis'],
                                           'Explode': [0.1,0]
                                           })


    
    pie_df2 = pie_df1.append(pie_df2_aux).reset_index()
    pie_df2 = pie_df2[~(pie_df2['Cota']=='Senior')]
    
    pie_df2['Label'] = np.where(pie_df2['Cota']=='Subordinada','',pie_df2['Cota'] + ' - ' + pie_df2['Tipo Cota'].apply(str))
    pie_df2['Label2'] = np.where(pie_df2['Cota']=='Seniores Não Usáveis','',pie_df2['Label'])
    
    pie_df2['index']=np.where(pie_df2['Cota']=='Subordinada', 2,pie_df2['index'])
    pie_df2['index']=pd.to_numeric(pie_df2['index'])
    pie_df2=pie_df2.sort_values(by=['index'], ascending=True)

     
    
    ############################################## PIE PLOT 2 - A #######################################

    #PLOT3
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.pie(pie_df2['Tipo Cota'],  labels =  pie_df2['Cota'],shadow=False, startangle=310, colors=[pal[1],'C1', 'w'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.legend(pie_df2['Label'], loc="best")
    plt.title("Filtro da Base Total de  Rating\n" + "Filtro 2 - Cotas Seniores Usáveis")
    
    plt.savefig('Ratings Filtrados 3.png') 
    plt.show()    
    

    ############################################## PIE PLOT 2 -B  #######################################
    
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.pie(pie_df2['Tipo Cota'],  labels =  pie_df2['Cota'],shadow=False, startangle=310, colors=[pal[1],'w', 'w'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.legend( pie_df2['Label2'], loc="best")
    plt.title("Filtro da Base Total de  Rating\n" + "Filtro 2 - Cotas Seniores Usáveis")

    plt.savefig('Ratings Filtrados 4.png') 
    plt.show()
    
    
    ############################################# SET DATABASE TO PIEPLOT 3 ####################################
    
    pie_df3_aux=pd.DataFrame({'Tipo Cota': [len(df_rating_append), pie_df2[pie_df2['Cota']=='Seniores Usáveis']['Tipo Cota'].values[0] - len(df_rating_append)],
                                           'Cota':['Seniores Únicas', 'Seniores Repetidas'],
                                           'Explode': [0.1,0],
                                           'index':[0,1]
                                           })


    
    pie_df3 = pie_df2.append(pie_df3_aux).reset_index()
    pie_df3 = pie_df3[~(pie_df3['Cota']=='Seniores Usáveis')]
    
    pie_df3['Label'] = np.where(pie_df3['Cota'].str.contains('Seniores Não Usáveis|Subordinada'),'',pie_df3['Cota'] + ' - ' + pie_df3['Tipo Cota'].apply(str))
    pie_df3['Label2'] = np.where(pie_df3['Cota']=='Seniores Repetidas','',pie_df3['Label'])
    
    pie_df3['index']=np.where(pie_df3['Cota']=='Seniores Não Usáveis', 2,pie_df3['index'])
    pie_df3['index']=np.where(pie_df3['Cota']=='Subordinada', 3,pie_df3['index'])

    pie_df3['index']=pd.to_numeric(pie_df3['index'])
    pie_df3=pie_df3.sort_values(by=['index'], ascending=True)
        
 
    df_rating_append['AAA']=np.where(df_rating_append['Rating_AUX']=='AAA',1,0)    
    df_rating_append['AA+']=np.where(df_rating_append['Rating_AUX']=='AA+',1,0)    
    df_rating_append['AA']=np.where(df_rating_append['Rating_AUX']=='AA',1,0)    
    df_rating_append['AA-']=np.where(df_rating_append['Rating_AUX']=='AA-',1,0)    
    df_rating_append['A+']=np.where(df_rating_append['Rating_AUX']=='A+',1,0)    
    df_rating_append['A']=np.where(df_rating_append['Rating_AUX']=='A',1,0)    
    df_rating_append['A-']=np.where(df_rating_append['Rating_AUX']=='A-',1,0)    
    df_rating_append['BBB+']=np.where(df_rating_append['Rating_AUX']=='BBB+',1,0)    
    df_rating_append['BBB']=np.where(df_rating_append['Rating_AUX']=='BBB',1,0)    
    df_rating_append['BBB-']=np.where(df_rating_append['Rating_AUX']=='BBB-',1,0)    
    df_rating_append['BB+']=np.where(df_rating_append['Rating_AUX']=='BB+',1,0)    
    df_rating_append['BB']=np.where(df_rating_append['Rating_AUX']=='BB',1,0)    
    df_rating_append['BB-']=np.where(df_rating_append['Rating_AUX']=='BB-',1,0)    
    df_rating_append['B+']=np.where(df_rating_append['Rating_AUX']=='B+',1,0)    
    df_rating_append['B']=np.where(df_rating_append['Rating_AUX']=='B',1,0)    
    df_rating_append['B-']=np.where(df_rating_append['Rating_AUX']=='B-',1,0)    
    df_rating_append['CCC']=np.where(df_rating_append['Rating_AUX']=='CCC',1,0)    
    df_rating_append['CC']=np.where(df_rating_append['Rating_AUX']=='CC',1,0)    
    df_rating_append['C']=np.where(df_rating_append['Rating_AUX']=='C',1,0)    
    df_rating_append['D']=np.where(df_rating_append['Rating_AUX']=='D',1,0)   
    
    df_rating_append['Grupo']='Senior Única'
    
    df_barpie=df_rating_append.groupby(['Grupo'])[['AAA','AA+','AA','AA-','A+','A','A-','BBB+','BBB','BBB-',
                                                            'BB+','BB','BB-','B+','B','B-','CCC','CC','C','D']].sum()

    df_barpie2 = round(100*df_barpie/(len(df_rating_append)),2)
 
    
    ############################################## PIE PLOT 3 - A #######################################

    #PLOT5
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.pie(pie_df3['Tipo Cota'],  labels =  pie_df3['Cota'],shadow=False, startangle=310, colors=[pal[1],'C1','w','w'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.legend(pie_df3['Label'], loc="best")
    plt.title("Filtro da Base Total de  Rating\n" + "Filtro 3 - Retirar Cotas Repetidas")
    
    plt.savefig('Ratings Filtrados 5.png') 
    plt.show()    
    

    ############################################## PIE PLOT 3 - B #######################################

       
    
    #PLOT6
    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    fig.subplots_adjust(wspace=0)
    
    ax1.pie(pie_df3['Tipo Cota'],  labels =  pie_df3['Cota'],shadow=False, startangle=310, colors=[pal[1],'w', 'w', 'w'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.legend( pie_df3['Label2'], loc="lower left")

    bottom=0
    #labels=[]
    # bar chart parameters
    for i in range(1,len(df_barpie.columns)+1):
        #print(df_barpie.columns[-i])
        heightt=df_barpie[df_barpie.columns[-i]].values[0]
        heightt2=df_barpie2[df_barpie2.columns[-i]].values[0]
        #ypos = bottom + ax2.patches[i].get_height() / 2
        ax2.bar(0, df_barpie[df_barpie.columns[-i]].values[0],.2, label=df_barpie.columns[-i], bottom = bottom, color = pal[-i])
        bottom+=heightt
        ypos = bottom + ax2.patches[-i].get_height()/2 - 5
        if i%2==0:
            k=i
        else:
            k=i*(-1)
                
        ax2.text(0.15*(k/i),ypos, "%d%%" % (heightt2), ha='center',color="black")

    #ax2.plot(0, 350, 'o',ms=50 * 2, mec='r', mfc='none', mew=2)

    #ax2.legend(labels[::-1] , loc='best')
    #ax2.legend(labels[], loc='best')
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(reversed(handles), reversed(labels), loc='center right')
    plt.box(False)  
    ax2.axis('off')
    ax2.set_xlim(- 2.5 * .2, 2.5 * .2)
    plt.tight_layout()
  
    # use ConnectionPatch to draw lines between the two plots
    # get the wedge data
    theta1, theta2 = ax1.patches[0].theta1, ax1.patches[0].theta2
    center, r = ax1.patches[0].center, ax1.patches[0].r
    bar_height = sum([item.get_height() for item in ax2.patches])
    
    # draw top connecting line
    x = r * np.cos(np.pi / 180 * theta2) + center[0]
    y = np.sin(np.pi / 180 * theta2) + center[1]
    con = ConnectionPatch(xyA=(- .2 / 2, bar_height), xyB=(x, y),coordsA="data", coordsB="data", axesA=ax2, axesB=ax1)
    con.set_color([0, 0, 0])
    con.set_linewidth(4)
    ax2.add_artist(con)
    
    # draw bottom connecting line
    x = r * np.cos(np.pi / 180 * theta1) + center[0]
    y = np.sin(np.pi / 180 * theta1) + center[1]
    con = ConnectionPatch(xyA=(- .2 / 2, 0), xyB=(x, y), coordsA="data",coordsB="data", axesA=ax2, axesB=ax1)
    con.set_color([0, 0, 0])
    ax2.add_artist(con)
    con.set_linewidth(4)
    
    fig.suptitle("Filtro da Base Total de  Rating\n" + "Filtro 4 - Cotas com Rating Desejáveis", fontsize=16)
    plt.savefig('Ratings Filtrados 6.png') 

    plt.show()
       
    ############################################## PIE PLOT 3 - C #######################################

 
    #PLOT7
    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    fig.subplots_adjust(wspace=0)
    
    ax1.pie(pie_df3['Tipo Cota'],  labels =  pie_df3['Cota'],shadow=False, startangle=310, colors=[pal[1],'w', 'w', 'w'], autopct='%1.1f%%', textprops={'color':"w"})
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.legend( pie_df3['Label2'], loc="lower left")


    bottom=0
    #labels=[]
    # bar chart parameters
    for i in range(1,len(df_barpie.columns)+1):
        #print(df_barpie.columns[-i])
        heightt=df_barpie[df_barpie.columns[-i]].values[0]
        heightt2=df_barpie2[df_barpie2.columns[-i]].values[0]
        #ypos = bottom + ax2.patches[i].get_height() / 2
        ax2.bar(0, df_barpie[df_barpie.columns[-i]].values[0],.2, label=df_barpie.columns[-i], bottom = bottom, color = pal[-i])
        bottom+=heightt
        ypos = bottom + ax2.patches[-i].get_height()/2 - 5
        if i%2==0:
            k=i
        else:
            k=i*(-1)
                
        ax2.text(0.15*(k/i),ypos, "%d%%" % (heightt2), ha='center',color="black")

    ax2.plot(0, 350, 'o',ms=50 * 2, mec='r', mfc='none', mew=2)

    #ax2.legend(labels[::-1] , loc='best')
    #ax2.legend(labels[], loc='best')
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(reversed(handles), reversed(labels), loc='center right')
    plt.box(False)  
    ax2.axis('off')
    ax2.set_xlim(- 2.5 * .2, 2.5 * .2)
    plt.tight_layout()
  
    # use ConnectionPatch to draw lines between the two plots
    # get the wedge data
    theta1, theta2 = ax1.patches[0].theta1, ax1.patches[0].theta2
    center, r = ax1.patches[0].center, ax1.patches[0].r
    bar_height = sum([item.get_height() for item in ax2.patches])
    
    # draw top connecting line
    x = r * np.cos(np.pi / 180 * theta2) + center[0]
    y = np.sin(np.pi / 180 * theta2) + center[1]
    con = ConnectionPatch(xyA=(- .2 / 2, bar_height), xyB=(x, y),coordsA="data", coordsB="data", axesA=ax2, axesB=ax1)
    con.set_color([0, 0, 0])
    con.set_linewidth(4)
    ax2.add_artist(con)
    
    # draw bottom connecting line
    x = r * np.cos(np.pi / 180 * theta1) + center[0]
    y = np.sin(np.pi / 180 * theta1) + center[1]
    con = ConnectionPatch(xyA=(- .2 / 2, 0), xyB=(x, y), coordsA="data",coordsB="data", axesA=ax2, axesB=ax1)
    con.set_color([0, 0, 0])
    ax2.add_artist(con)
    con.set_linewidth(4)
    
    fig.suptitle("Filtro da Base Total de  Rating\n" + "Filtro 4 - Cotas com Rating Desejáveis", fontsize=16)
    plt.savefig('Ratings Filtrados 7.png') 

    plt.show()
 

 

    ############################################# SET DATABASE TO PLOT 0 ####################################
    
    df_rating_append["Data_AUX"] = np.where(df_rating_append["Agencia"]=="SR",df_rating_append["Data Vencimento"],df_rating_append["Data Rating"])    
    df_rating_append["Data_AUX"]=df_rating_append["Data_AUX"].dt.strftime("%Y")
 
    
    df_rating_append["d2020"] = np.where(df_rating_append["Data_AUX"]=="2020", 1,0)
    df_rating_append["d2019"] = np.where(df_rating_append["Data_AUX"]=="2019", 1,0)
    df_rating_append["d2018"] = np.where(df_rating_append["Data_AUX"]=="2018", 1,0)
    df_rating_append["d2017"] = np.where(df_rating_append["Data_AUX"]=="2017", 1,0)
    df_rating_append["d2016"] = np.where(df_rating_append["Data_AUX"]=="2016", 1,0)
    df_rating_append["d2015"] = np.where(df_rating_append["Data_AUX"]=="2015", 1,0)
    df_rating_append["d2014"] = np.where(df_rating_append["Data_AUX"]=="2014", 1,0)
    df_rating_append["d2013"] = np.where(df_rating_append["Data_AUX"]=="2013", 1,0)
    df_rating_append["d2012"] = np.where(df_rating_append["Data_AUX"]=="2012", 1,0)
    df_rating_append["Sem data"] = np.where(pd.isnull(df_rating_append["Data_AUX"]), 1,0)

    df_rating_append["Total_Year"]=df_rating_append["d2012"]+df_rating_append["d2013"]+df_rating_append["d2014"]+df_rating_append["d2015"]+df_rating_append["d2016"] +df_rating_append["d2017"] +df_rating_append["d2018"]+df_rating_append["d2019"]+df_rating_append["d2020"]+df_rating_append["Sem data"]   


    df_rating_agency=df_rating_append.groupby(['Agencia'])[['d2012','d2013','d2014','d2015','d2016','d2017','d2018','d2019','d2020','Sem data', 'Total_Year']].sum()
    df_rating_agency['Agencia']=df_rating_agency.index


    conditions = [
        (df_rating_agency['Agencia']=='FITCH'),
        (df_rating_agency['Agencia']=='MOODY'),
        (df_rating_agency['Agencia']=='SP'),    
        (df_rating_agency['Agencia']=='LIBERIUM'),
        (df_rating_agency['Agencia']=='AUSTIN'),
        (df_rating_agency['Agencia']=='SR')
        ]
    
    choices = [x for x in range(1,7)]
    
    #Ordenar por rating
    df_rating_agency['Rank'] = np.select(conditions, choices, default='')
    df_rating_agency['Rank']=pd.to_numeric(df_rating_agency['Rank'])
    df_rating_agency=df_rating_agency.sort_values(by=['Rank'], ascending=True)



    ############################################ PLOT 0 ####################################3
     
    list2012 = [i+j for i,j in zip(df_rating_agency['Sem data'], df_rating_agency['d2012'])]
    list2013 = [i+j for i,j in zip(list2012, df_rating_agency['d2013'])]
    list2014 = [i+j for i,j in zip(list2013 ,df_rating_agency['d2014'])]
    list2015 = [i+j for i,j in zip(list2014 ,df_rating_agency['d2015'])]
    list2016 = [i+j for i,j in zip(list2015 ,df_rating_agency['d2016'])]
    list2017 = [i+j for i,j in zip(list2016 ,df_rating_agency['d2017'])]
    list2018 = [i+j for i,j in zip(list2017 ,df_rating_agency['d2018'])]
    list2019 = [i+j for i,j in zip(list2018 ,df_rating_agency['d2019'])]
    # list2020 = [i+j for i,j in zip(list2019 ,df_rating_agency['d2020'])]

    # pal = sns.hls_palette(8, l=.3, s=.8)
    # pal = sns.color_palette("Paired")
    # pal = sns.light_palette((210, 90, 60),input="husl")
    # pal = sns.cubehelix_palette(8, start=2, rot=0, dark=0, light=.95, reverse=False)
    pal = sns.diverging_palette(255, 133, l=60, n=10, center="dark")


    print('Fazendo plot 2 sobre No FIDCs avaliados')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.bar([x for x in range(1,7)], df_rating_agency['Sem data'], width=0.5, label='S/ Data', color = pal[0])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2012'], width=0.5, label='2012', bottom = df_rating_agency['Sem data'], color = pal[1])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2013'], width=0.5, label='2013', bottom = list2012, color = pal[2])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2014'], width=0.5, label='2014', bottom = list2013, color = pal[3])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2015'], width=0.5, label='2015', bottom = list2014, color = pal[4])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2016'], width=0.5, label='2016', bottom = list2015, color = pal[5])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2017'], width=0.5, label='2017', bottom = list2016, color = pal[6])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2018'], width=0.5, label='2018', bottom = list2017, color = pal[7])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2019'], width=0.5, label='2019', bottom = list2018, color = pal[8])
    ax.bar([x for x in range(1,7)], df_rating_agency['d2020'], width=0.5, label='2020', bottom = list2019, color = pal[9])
    
    plt.xticks([x for x in range(1,8)],  df_rating_agency['Agencia'])
    
    for i in range(0,len(df_rating_agency)):
        plt.text(i+1-0.05,df_rating_agency['Total_Year'][i]+5, df_rating_agency['Total_Year'][i])


    ax.set_ylabel('Número de Cotas Avaliadas')
    ax.set_title('Cotas Avaliadas por Rating ')
    ax.legend(loc='best')
    plt.box(False)  
    fig.tight_layout()
    
    plt.savefig('Numero de Rating por Agencia e Ano.png') 
    plt.show()

    print('Plot feito!')
    
    
    
    ############################################# SET DATABASE TO PLOT 1 ####################################
    

    df_rating_append['AUSTIN'] = np.where(df_rating_append['Agencia']=='AUSTIN',1,0)
    df_rating_append['LIBERIUM'] = np.where(df_rating_append['Agencia']=='LIBERIUM',1,0)
    df_rating_append['SR'] = np.where(df_rating_append['Agencia']=='SR',1,0)
    df_rating_append['FITCH'] = np.where(df_rating_append['Agencia']=='FITCH',1,0)
    df_rating_append['SP'] = np.where(df_rating_append['Agencia']=='SP',1,0)
    df_rating_append['MOODY'] = np.where(df_rating_append['Agencia']=='MOODY',1,0)

    rating_count_df_aux=df_rating_append.groupby(['Rating_AUX'])[['AUSTIN', 'LIBERIUM', 'SR', 'LIBERIUM', 'FITCH', 'SP', 'MOODY']].sum()
    rating_count_df_aux['Rating']=rating_count_df_aux.index


    rating_count_df=df_rating_append['Rating_AUX'].value_counts().to_frame()
    rating_count_df['Rating']=rating_count_df.index
    rating_count_df = rating_count_df.rename(columns={'Rating_AUX':'N_Rating'})     
    
    
    rating_count_df=rating_count_df.merge(rating_count_df_aux, how='left', on='Rating')

    print (rating_count_df.apply(pd.to_numeric, errors='coerce').sum())
    

    conditions = [
        (rating_count_df['Rating']=='AAA'),
        (rating_count_df['Rating']=='AA+'),
        (rating_count_df['Rating']=='AA'),    
        (rating_count_df['Rating']=='AA-'),
        (rating_count_df['Rating']=='A+'),
        (rating_count_df['Rating']=='A'),
        (rating_count_df['Rating']=='A-'),
        (rating_count_df['Rating']=='BBB+'),
        (rating_count_df['Rating']=='BBB'),
        (rating_count_df['Rating']=='BBB-'),
        (rating_count_df['Rating']=='BB+'), 
        (rating_count_df['Rating']=='BB'),
        (rating_count_df['Rating']=='BB-'),
        (rating_count_df['Rating']=='B+'), 
        (rating_count_df['Rating']=='B'),
        (rating_count_df['Rating']=='B-'),        
        (rating_count_df['Rating']=='CCC'),        
        (rating_count_df['Rating']=='CC'),        
        (rating_count_df['Rating']=='C'),        
        (rating_count_df['Rating']=='D')
        ]
    
    choices = [x for x in range(1,21)]
    
    #Ordenar por rating
    rating_count_df['Rank'] = np.select(conditions, choices, default='black')
    rating_count_df['Rank']=pd.to_numeric(rating_count_df['Rank'])
    rating_count_df=rating_count_df.sort_values(by=['Rank'], ascending=False)
    

    ############################################ PLOT 1 - A ####################################3


    print('Fazendo plot 1 sobre No FIDCs avaliados')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.barh(rating_count_df['Rating'], rating_count_df['N_Rating'])    
    ax.set_xlabel('Número de Cotas Avaliadas')
    ax.set_ylabel('Rating')
    ax.set_title('Cotas Avaliadas por Rating - Geral')
    
    for i, v in enumerate(rating_count_df.N_Rating):
        plt.text(v+0.2, i, str(round(v, 2)), va="center")
        
    #ax.legend(loc='best')
    plt.box(False)  
    
    plt.savefig('Rating FIDCS por cotas - Geral 1.png') 
    plt.show()
    
    print('Plot Feito!')
    
    ############################################ PLOT 1 - B ####################################

    
    print('Fazendo plot 1 sobre No FIDCs avaliados')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.barh(rating_count_df['Rating'], rating_count_df['N_Rating'])   
    ax.plot(3, 17.5, 'o',ms=27 * 2, mec='r', mfc='none', mew=2)
    ax.set_xlabel('Número de Cotas Avaliadas')
    ax.set_ylabel('Rating')
    ax.set_title('Cotas Avaliadas por Rating - Geral')
    
    for i, v in enumerate(rating_count_df.N_Rating):
        plt.text(v+0.2, i, str(round(v, 2)), va="center")
    
    #ax.legend(loc='best')
    plt.box(False)  
    
    plt.savefig('Rating FIDCS por cotas - Geral 2.png') 
    plt.show()
    
    print('Plot Feito!')
    
    
    ############################################# SET DATABASE TO PLOT 2 ####################################

    
    rating_count_df=rating_count_df.sort_values(by=['Rank'], ascending=True)

    df_aux = rating_count_df[['Rating','AUSTIN', 'LIBERIUM', 'SR', 'LIBERIUM','FITCH', 'SP', 'MOODY']]
    df_aux = df_aux.loc[:,~df_aux.columns.duplicated()]
    df_aux['Total']= df_aux['SR']+df_aux['AUSTIN']+ df_aux['LIBERIUM']+ df_aux['SP']+ df_aux['MOODY']+ df_aux['FITCH']
    df_aux=df_aux.reset_index()
  
    list1 = [i+j for i,j in zip(df_aux['SR'], df_aux['AUSTIN'])]
    list2= [i+j for i,j in zip(list1, df_aux['LIBERIUM'])]
    list3 = [i+j for i,j in zip(list2 ,df_aux['SP'])]
    list4 = [i+j for i,j in zip(list3 ,df_aux['MOODY'])]
    #list5= [i+j for i,j in zip(list4 ,df_aux['FITCH'])]
  
    ############################################ PLOT 2 - A ####################################

    print('Fazendo plot 1 sobre No FIDCs avaliados')
      
    pal = sns.color_palette("coolwarm", 6)
    #pal = sns.diverging_palette(255, 20, n=6, center='dark')

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar([x for x in range(len(df_aux))], df_aux['SR'], width=0.5, label='SR', color = pal[0])
    ax.bar([x for x in range(len(df_aux))], df_aux['AUSTIN'], width=0.5, label='Austin', bottom = df_aux['SR'], color = pal[1])
    ax.bar([x for x in range(len(df_aux))], df_aux['LIBERIUM'], width=0.5, label='Liberium', bottom = list1, color = pal[2])
    ax.bar([x for x in range(len(df_aux))], df_aux['SP'], width=0.5, label='SP', bottom = list2, color = pal[3])
    ax.bar([x for x in range(len(df_aux))], df_aux['MOODY'], width=0.5, label='Moodys', bottom = list3, color = pal[4])
    ax.bar([x for x in range(len(df_aux))], df_aux['FITCH'], width=0.5, label='Fitch', bottom = list4, color = pal[5])
    
    plt.xticks([x for x in range(len(df_aux))],  df_aux['Rating'])
      
    for i in range(len(df_aux)):
        plt.text(i-.3,df_aux['Total'][i]+1, df_aux['Total'][i])      
        
    #ax.plot(1.5, 10, 'o',ms=55 * 2, mec='r', mfc='none', mew=2)
 
    ax.set_ylabel('Número de Cotas Avaliadas')
    ax.set_xlabel('Rating')
    ax.set_title('Cotas Avaliadas por Rating')
    plt.xticks(rotation=30)

    ax.legend(loc='best')
    plt.box(False)  
    
    plt.savefig('Rating FIDCS por cotas - Agencias 1.png') 
    plt.show()
    
    
    
    ############################################ PLOT 2 - B ####################################

    
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar([x for x in range(len(df_aux))], df_aux['SR'], width=0.5, label='SR', color = pal[0])
    ax.bar([x for x in range(len(df_aux))], df_aux['AUSTIN'], width=0.5, label='Austin', bottom = df_aux['SR'], color = pal[1])
    ax.bar([x for x in range(len(df_aux))], df_aux['LIBERIUM'], width=0.5, label='Liberium', bottom = list1, color = pal[2])
    ax.bar([x for x in range(len(df_aux))], df_aux['SP'], width=0.5, label='SP', bottom = list2, color = pal[3])
    ax.bar([x for x in range(len(df_aux))], df_aux['MOODY'], width=0.5, label='Moodys', bottom = list3, color = pal[4])
    ax.bar([x for x in range(len(df_aux))], df_aux['FITCH'], width=0.5, label='Fitch', bottom = list4, color = pal[5])
    
    plt.xticks([x for x in range(len(df_aux))],  df_aux['Rating'])
    
    for i in range(0,len(df_aux)):
        plt.text(i-.3,df_aux['Total'][i]+1, df_aux['Total'][i])
        
        
    ax.plot(1.5, 12, 'o',ms=55 * 2, mec='r', mfc='none', mew=2)
 
    ax.set_ylabel('Número de Cotas Avaliadas')
    ax.set_xlabel('Rating')
    ax.set_title('Cotas Avaliadas por Rating')
    plt.xticks(rotation=30)

    ax.legend(loc='best')
    plt.box(False)  
    
    plt.savefig('Rating FIDCS por cotas - Agencias 2.png') 
    plt.show()
    
    print('Plot Feito!')
    
    ############################################# SET DATABASE TO PLOT 3 ####################################
    
    
    conditions = [
        (df_rating_append['Rating_AUX']=='AAA'),
        (df_rating_append['Rating_AUX'].str.contains('AA+|AA-') | (df_rating_append['Rating_AUX']=='AA')),
        (df_rating_append['Rating_AUX'].str.contains('A+|A-')   | (df_rating_append['Rating_AUX']=='A')),
        (df_rating_append['Rating_AUX'].str.contains('BBB')),
        (df_rating_append['Rating_AUX'].str.contains('BB+|BB-') | (df_rating_append['Rating_AUX']=='BB')),
        (df_rating_append['Rating_AUX'].str.contains('B+|B-')   | (df_rating_append['Rating_AUX']=='B')),
        (df_rating_append['Rating_AUX']=='CCC'),
        (df_rating_append['Rating_AUX']=='CC'),
        (df_rating_append['Rating_AUX']=='C'),
        (df_rating_append['Rating_AUX']=='D')
        ]
   
    choices = ['AAA','AA','A','BBB','BB','B','CCC','CC','C','D']
    df_rating_append['Group'] = np.select(conditions, choices)

 
    
    
    df_austin = df_rating_append[df_rating_append['Agencia']=='AUSTIN']
    df_austin = df_austin['Group'].value_counts().to_frame()
    df_austin['Rating'] = df_austin.index
    

    

    
    
    conditions = [
        (df_austin['Rating']=='AAA'),
        (df_austin['Rating']=='AA'),    
        (df_austin['Rating']=='A'),
        (df_austin['Rating']=='BBB'),
        (df_austin['Rating']=='BB'),
        (df_austin['Rating']=='B'),
        (df_austin['Rating']=='CCC'),        
        (df_austin['Rating']=='CC'),        
        (df_austin['Rating']=='C'),        
        (df_austin['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
        #Ordenar por rating
    df_austin['Rank'] = np.select(conditions, choices, default='black')
    df_austin['Rank']=pd.to_numeric(df_austin['Rank'])
    df_austin=df_austin.sort_values(by=['Rank'], ascending=True)
   
    conditions = [
        (df_austin['Rating']=='AAA'),
        (df_austin['Rating']=='AA'),    
        (df_austin['Rating']=='A'),
        (df_austin['Rating']=='BBB'),
        (df_austin['Rating']=='BB'),
        (df_austin['Rating']=='B'),
        (df_austin['Rating']=='CCC'),        
        (df_austin['Rating']=='CC'),        
        (df_austin['Rating']=='C'),        
        (df_austin['Rating']=='D')
        ]
    
    
    pal = sns.diverging_palette(10, 220, sep=80, n=10) 

    pal1 = []
    pal2 = []
    pal3 = []
    
    for i in range(len(pal)):

        pal1.append(pal[i][0])
        pal2.append(pal[i][1])
        pal3.append(pal[i][2])
    
    df_austin['Color1']=pd.to_numeric(np.select(conditions, pal1, default='black'))
    df_austin['Color2']=pd.to_numeric(np.select(conditions, pal2, default='black'))
    df_austin['Color3']=pd.to_numeric(np.select(conditions, pal3, default='black'))
    df_austin['Color'] = df_austin[['Color1', 'Color2', 'Color3']].apply(tuple, axis=1)

 


   
    
    df_liberium = df_rating_append[df_rating_append['Agencia']=='LIBERIUM']
    df_liberium = df_liberium['Group'].value_counts().to_frame()
    df_liberium['Rating'] = df_liberium.index
    
    
    conditions = [
        (df_liberium['Rating']=='AAA'),
        (df_liberium['Rating']=='AA'),    
        (df_liberium['Rating']=='A'),
        (df_liberium['Rating']=='BBB'),
        (df_liberium['Rating']=='BB'),
        (df_liberium['Rating']=='B'),
        (df_liberium['Rating']=='CCC'),        
        (df_liberium['Rating']=='CC'),        
        (df_liberium['Rating']=='C'),        
        (df_liberium['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
    #Ordenar por rating
    df_liberium['Rank'] = np.select(conditions, choices, default='black')
    df_liberium['Rank']=pd.to_numeric(df_liberium['Rank'])
    df_liberium=df_liberium.sort_values(by=['Rank'], ascending=True)  
    
    conditions = [
        (df_liberium['Rating']=='AAA'),
        (df_liberium['Rating']=='AA'),    
        (df_liberium['Rating']=='A'),
        (df_liberium['Rating']=='BBB'),
        (df_liberium['Rating']=='BB'),
        (df_liberium['Rating']=='B'),
        (df_liberium['Rating']=='CCC'),        
        (df_liberium['Rating']=='CC'),        
        (df_liberium['Rating']=='C'),        
        (df_liberium['Rating']=='D')
        ]    
    
    pal = sns.diverging_palette(10, 220, sep=80, n=10) 

    pal1 = []
    pal2 = []
    pal3 = []
    
    for i in range(len(pal)):
        pal1.append(pal[i][0])
        pal2.append(pal[i][1])
        pal3.append(pal[i][2])
     

    
    df_liberium['Color1']=pd.to_numeric(np.select(conditions, pal1, default='black'))
    df_liberium['Color2']=pd.to_numeric(np.select(conditions, pal2, default='black'))
    df_liberium['Color3']=pd.to_numeric(np.select(conditions, pal3, default='black'))
    df_liberium['Color']= df_liberium[['Color1', 'Color2', 'Color3']].apply(tuple, axis=1)


    
    df_sr = df_rating_append[df_rating_append['Agencia']=='SR']
    df_sr = df_sr['Group'].value_counts().to_frame()
    df_sr['Rating'] = df_sr.index
    
    
    conditions = [
        (df_sr['Rating']=='AAA'),
        (df_sr['Rating']=='AA'),    
        (df_sr['Rating']=='A'),
        (df_sr['Rating']=='BBB'),
        (df_sr['Rating']=='BB'),
        (df_sr['Rating']=='B'),
        (df_sr['Rating']=='CCC'),        
        (df_sr['Rating']=='CC'),        
        (df_sr['Rating']=='C'),        
        (df_sr['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
    #Ordenar por rating
    df_sr['Rank'] = np.select(conditions, choices, default='black')
    df_sr['Rank']=pd.to_numeric(df_sr['Rank'])
    df_sr=df_sr.sort_values(by=['Rank'], ascending=True)  
    
    conditions = [
        (df_sr['Rating']=='AAA'),
        (df_sr['Rating']=='AA'),    
        (df_sr['Rating']=='A'),
        (df_sr['Rating']=='BBB'),
        (df_sr['Rating']=='BB'),
        (df_sr['Rating']=='B'),
        (df_sr['Rating']=='CCC'),        
        (df_sr['Rating']=='CC'),        
        (df_sr['Rating']=='C'),        
        (df_sr['Rating']=='D')
        ]    
    
    pal = sns.diverging_palette(10, 220, sep=80, n=10) 

    pal1 = []
    pal2 = []
    pal3 = []
    
    for i in range(len(pal)):
        pal1.append(pal[i][0])
        pal2.append(pal[i][1])
        pal3.append(pal[i][2])
     

    
    df_sr['Color1']=pd.to_numeric(np.select(conditions, pal1, default='black'))
    df_sr['Color2']=pd.to_numeric(np.select(conditions, pal2, default='black'))
    df_sr['Color3']=pd.to_numeric(np.select(conditions, pal3, default='black'))
    df_sr['Color'] = df_sr[['Color1', 'Color2', 'Color3']].apply(tuple, axis=1)

    
    
    
    
    
    df_sp = df_rating_append[df_rating_append['Agencia']=='SP']
    df_sp = df_sp['Group'].value_counts().to_frame()
    df_sp['Rating'] = df_sp.index


    conditions = [
        (df_sp['Rating']=='AAA'),
        (df_sp['Rating']=='AA'),    
        (df_sp['Rating']=='A'),
        (df_sp['Rating']=='BBB'),
        (df_sp['Rating']=='BB'),
        (df_sp['Rating']=='B'),
        (df_sp['Rating']=='CCC'),        
        (df_sp['Rating']=='CC'),        
        (df_sp['Rating']=='C'),        
        (df_sp['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
    #Ordenar por rating
    df_sp['Rank'] = np.select(conditions, choices, default='black')
    df_sp['Rank']=pd.to_numeric(df_sp['Rank'])
    df_sp=df_sp.sort_values(by=['Rank'], ascending=True)  
    
    conditions = [
        (df_sp['Rating']=='AAA'),
        (df_sp['Rating']=='AA'),    
        (df_sp['Rating']=='A'),
        (df_sp['Rating']=='BBB'),
        (df_sp['Rating']=='BB'),
        (df_sp['Rating']=='B'),
        (df_sp['Rating']=='CCC'),        
        (df_sp['Rating']=='CC'),        
        (df_sp['Rating']=='C'),        
        (df_sp['Rating']=='D')
        ]    
    
    pal = sns.diverging_palette(10, 220, sep=80, n=10) 

    pal1 = []
    pal2 = []
    pal3 = []
    
    for i in range(len(pal)):
        pal1.append(pal[i][0])
        pal2.append(pal[i][1])
        pal3.append(pal[i][2])
     

    
    df_sp['Color1']=pd.to_numeric(np.select(conditions, pal1, default='black')) 
    df_sp['Color2']=pd.to_numeric(np.select(conditions, pal2, default='black'))
    df_sp['Color3']=pd.to_numeric(np.select(conditions, pal3, default='black'))
    df_sp['Color'] = df_sp[['Color1', 'Color2', 'Color3']].apply(tuple, axis=1)

    
    
    
    
    df_moody = df_rating_append[df_rating_append['Agencia']=='MOODY']
    df_moody = df_moody['Group'].value_counts().to_frame()
    df_moody['Rating'] = df_moody.index
    
        
    conditions = [
        (df_moody['Rating']=='AAA'),
        (df_moody['Rating']=='AA'),    
        (df_moody['Rating']=='A'),
        (df_moody['Rating']=='BBB'),
        (df_moody['Rating']=='BB'),
        (df_moody['Rating']=='B'),
        (df_moody['Rating']=='CCC'),        
        (df_moody['Rating']=='CC'),        
        (df_moody['Rating']=='C'),        
        (df_moody['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
    #Ordenar por rating
    df_moody['Rank'] = np.select(conditions, choices, default='black')
    df_moody['Rank']=pd.to_numeric(df_moody['Rank'])
    df_moody=df_moody.sort_values(by=['Rank'], ascending=True)  
    
    conditions = [
        (df_moody['Rating']=='AAA'),
        (df_moody['Rating']=='AA'),    
        (df_moody['Rating']=='A'),
        (df_moody['Rating']=='BBB'),
        (df_moody['Rating']=='BB'),
        (df_moody['Rating']=='B'),
        (df_moody['Rating']=='CCC'),        
        (df_moody['Rating']=='CC'),        
        (df_moody['Rating']=='C'),        
        (df_moody['Rating']=='D')
        ]
        
    
    pal = sns.diverging_palette(10, 220, sep=80, n=10) 

    pal1 = []
    pal2 = []
    pal3 = []
    
    for i in range(len(pal)):
        pal1.append(pal[i][0])
        pal2.append(pal[i][1])
        pal3.append(pal[i][2])
     

    
    df_moody['Color1']=pd.to_numeric(np.select(conditions, pal1, default='black'))
    df_moody['Color2']=pd.to_numeric(np.select(conditions, pal2, default='black'))
    df_moody['Color3']=pd.to_numeric(np.select(conditions, pal3, default='black'))
    df_moody['Color'] = df_moody[['Color1', 'Color2', 'Color3']].apply(tuple, axis=1)

    
    
    
    df_fitch = df_rating_append[df_rating_append['Agencia']=='FITCH']
    df_fitch = df_fitch['Group'].value_counts().to_frame()
    df_fitch['Rating'] = df_fitch.index
    
    conditions = [
        (df_fitch['Rating']=='AAA'),
        (df_fitch['Rating']=='AA'),    
        (df_fitch['Rating']=='A'),
        (df_fitch['Rating']=='BBB'),
        (df_fitch['Rating']=='BB'),
        (df_fitch['Rating']=='B'),
        (df_fitch['Rating']=='CCC'),        
        (df_fitch['Rating']=='CC'),        
        (df_fitch['Rating']=='C'),        
        (df_fitch['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
    #Ordenar por rating
    df_fitch['Rank'] = np.select(conditions, choices, default='black')
    df_fitch['Rank']=pd.to_numeric(df_fitch['Rank'])
    df_fitch=df_fitch.sort_values(by=['Rank'], ascending=True)  
    
    conditions = [
        (df_fitch['Rating']=='AAA'),
        (df_fitch['Rating']=='AA'),    
        (df_fitch['Rating']=='A'),
        (df_fitch['Rating']=='BBB'),
        (df_fitch['Rating']=='BB'),
        (df_fitch['Rating']=='B'),
        (df_fitch['Rating']=='CCC'),        
        (df_fitch['Rating']=='CC'),        
        (df_fitch['Rating']=='C'),        
        (df_fitch['Rating']=='D')
        ]    
    
    pal = sns.diverging_palette(10, 220, sep=80, n=10) 

    pal1 = []
    pal2 = []
    pal3 = []
    
    for i in range(len(pal)):
        pal1.append(pal[i][0])
        pal2.append(pal[i][1])
        pal3.append(pal[i][2])
     

    
    df_fitch['Color1']=pd.to_numeric(np.select(conditions, pal1, default='black')) 
    df_fitch['Color2']=pd.to_numeric(np.select(conditions, pal2, default='black'))
    df_fitch['Color3']=pd.to_numeric(np.select(conditions, pal3, default='black'))
    df_fitch['Color']= df_fitch[['Color1', 'Color2', 'Color3']].apply(tuple, axis=1)
    
    
    ############################################ PLOT 3 ####################################3
    
    fig, axs = plt.subplots(3, 2, figsize=(5, 8))  
    
    axs[0, 0].pie(df_fitch['Group'], shadow=True, colors = df_fitch['Color'], labels = df_fitch['Rating'], textprops={'fontsize': 8})
    axs[0, 1].pie(df_sp['Group'], shadow=True, colors = df_sp['Color'], labels = df_sp['Rating'], textprops={'fontsize': 8})
    axs[1, 0].pie(df_moody['Group'], shadow=True, colors = df_moody['Color'], labels = df_moody['Rating'], textprops={'fontsize': 8})
    axs[1, 1].pie(df_liberium['Group'], shadow=True, colors = df_liberium['Color'], labels = df_liberium['Rating'], textprops={'fontsize': 8})
    axs[2, 0].pie(df_austin['Group'], shadow=True, colors = df_austin['Color'], labels = df_austin['Rating'], textprops={'fontsize': 8})
    axs[2,1].pie(df_sr['Group'], shadow=True, colors = df_sr['Color'], labels = df_sr['Rating'], textprops={'fontsize': 8})

    axs[0,0].set_title('Fitch ('+ str(sum(df_fitch.Group))+' cotas)', fontsize=9, fontweight="bold")
    axs[0,1].set_title('SP ('+ str(sum(df_sp.Group))+' cotas)', fontsize=9, fontweight="bold")
    axs[1,0].set_title('Moodys ('+ str(sum(df_moody.Group))+' cotas)', fontsize=9, fontweight="bold")
    axs[1,1].set_title('Liberium ('+ str(sum(df_liberium.Group))+' cotas)', fontsize=9, fontweight="bold")
    axs[2,0].set_title('Austin ('+ str(sum(df_austin.Group))+' cotas)', fontsize=9, fontweight="bold")
    axs[2,1].set_title('SR ('+ str(sum(df_sr.Group))+' cotas)', fontsize=9, fontweight="bold")

    
    fig.suptitle("Ratings por Agência", fontsize=16, fontweight="bold")
    plt.savefig('Rating por Agencia.png') 

    plt.show()
    
    
    
    ############################################# SET DATABASE TO PLOT 4 ####################################
    
    rating_count_df['Freq']=rating_count_df['N_Rating']/len(df_rating_append)
    rating_count_df['Mais']= np.where(rating_count_df['Rating'].str.contains('\+'),rating_count_df['N_Rating'],0)
    rating_count_df['Menos']= np.where(rating_count_df['Rating'].str.contains('\-'),rating_count_df['N_Rating'],0)
    rating_count_df['Normal']= np.where((rating_count_df['Mais']==0)&(rating_count_df['Menos']==0),rating_count_df['N_Rating'],0)


    conditions = [
        (rating_count_df['Rating']=='AAA'),
        (rating_count_df['Rating'].str.contains('AA+|AA-') | (rating_count_df['Rating']=='AA')),
        (rating_count_df['Rating'].str.contains('A+|A-')   | (rating_count_df['Rating']=='A')),
        (rating_count_df['Rating'].str.contains('BBB')),
        (rating_count_df['Rating'].str.contains('BB+|BB-') | (rating_count_df['Rating']=='BB')),
        (rating_count_df['Rating'].str.contains('B+|B-')   | (rating_count_df['Rating']=='B')),
        (rating_count_df['Rating']=='CCC'),
        (rating_count_df['Rating']=='CC'),
        (rating_count_df['Rating']=='C'),
        (rating_count_df['Rating']=='D')
        ]
   
    
    choices = ['AAA','AA','A','BBB','BB','B','CCC','CC','C','D']

    rating_count_df['Group'] = np.select(conditions, choices, default='black')
    rating_count_df = rating_count_df.loc[:,~rating_count_df.columns.duplicated()]
    
    rating_count_df2=rating_count_df.groupby(['Group'])[['Mais', 'Menos', 'Normal']].sum()
    rating_count_df2['Rating']=rating_count_df2.index
    rating_count_df2['N_Rating']=rating_count_df2['Mais']+rating_count_df2['Menos']+rating_count_df2['Normal']
    
    
    conditions = [
        (rating_count_df2['Rating']=='AAA'),
        (rating_count_df2['Rating']=='AA'),    
        (rating_count_df2['Rating']=='A'),
        (rating_count_df2['Rating']=='BBB'),
        (rating_count_df2['Rating']=='BB'),
        (rating_count_df2['Rating']=='B'),
        (rating_count_df2['Rating']=='CCC'),        
        (rating_count_df2['Rating']=='CC'),        
        (rating_count_df2['Rating']=='C'),        
        (rating_count_df2['Rating']=='D')
        ]
    
    choices = [x for x in range(1,11)]
    
    #Ordenar por rating
    rating_count_df2['Rank'] = np.select(conditions, choices, default='black')
    rating_count_df2['Rank']=pd.to_numeric(rating_count_df2['Rank'])
    rating_count_df2=rating_count_df2.sort_values(by=['Rank'])
    
    #rating_count_df2=rating_count_df2.reset_index()
  
  
    #pal = sns.color_palette("Blues")
    #pal = sns.hls_palette(8, l=.3, s=.8)
    pal  = sns.color_palette("hls", 8)


    ############################################ PLOT 4 ####################################3
    print('Fazendo plot 2 sobre No FIDCs avaliados')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.bar(rating_count_df2['Rating'], rating_count_df2['Menos'], width=0.8, label='-', color=pal[0])
    ax.bar(rating_count_df2['Rating'], rating_count_df2['Normal'], bottom=rating_count_df2['Menos'], width=0.8, label=' ', color=pal[3])
    ax.bar(rating_count_df2['Rating'], rating_count_df2['Mais'], bottom=[i+j for i,j in zip(rating_count_df2['Menos'], rating_count_df2['Normal'])],  width=0.8, label='+', color=pal[5])
    
    ax.set_ylabel('Número de Cotas Avaliadas')
    ax.set_title('Cotas Avaliadas por Rating ')
    ax.legend(loc='best')
    plt.box(False)  
    fig.tight_layout()
    
    plt.savefig('Rating FIDCS por cotas - Agregado Rating.png') 
    plt.show()

    print('Plot feito!')

    return 'Plots Feitos!'





def weighted_mean(df, weight_column):
    
    wm = lambda x: np.ma.average(x, weights=df.loc[x.index, weight_column])
    
    return wm






def analyze_fidcs(df_fidc_senior,df_fidc ,df_rating_final, fitler_date0, fitler_date1, fitler_date2):
    
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Plots')
    
   
    
   
    print('Agregando as duas bases')
    df_fidc_agg = df_fidc_senior.merge(df_rating_final,how='left',on='CNPJ_FUNDO')
    
    fidcs_rating = df_fidc_agg[~pd.isnull(df_fidc_agg['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    #fidcs_wrating= df_fidc_agg[pd.isnull(df_fidc_agg['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    
    fidcs_rating['TAB_X_CLASSE_SERIE'] = fidcs_rating['TAB_X_CLASSE_SERIE'].replace(to_replace=['Classe Sénior|Sênior'], value='Série', regex=True)
    fidcs_rating = fidcs_rating.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])
    fidcs_rating=fidcs_rating[~fidcs_rating['DENOM_SOCIAL'].str.contains('FIC')]

    
    #CHECK FORNECEDORES
    fidcs_fornec=fidcs_rating.groupby(['CNPJ_FUNDO','DENOM_SOCIAL']).agg(PL =("TAB_IV_B_VL_PL_MEDIO", "mean"),
                                                                         n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                                         ).reset_index()

    writer = pd.ExcelWriter(r'FIDCs Fornecedores.xlsx')
    fidcs_fornec.to_excel(writer, sheet_name='FIDCs', index=False)
    writer.save() 
  

    print('Agregando com a base de cotas Subordinadas')

    df_fidcs_sub = df_fidc[(df_fidc['CNPJ_FUNDO'].isin(fidcs_rating['CNPJ_FUNDO'].unique().tolist())) & (df_fidc['TAB_X_CLASSE_SERIE_AUX']=='Subordinada')]
    
    df_fidc_agg_sub = df_fidcs_sub.merge(df_rating_final,how='left',on='CNPJ_FUNDO')
    
    fidcs_rating_sub = df_fidc_agg_sub[~pd.isnull(df_fidc_agg_sub['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    fidcs_rating_sub = fidcs_rating_sub.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])

    
    #CHECK COTAS DE FUNDOS 
    
    # fidc_dict={}
    # for cnpj in fidcs_rating['CNPJ_FUNDO'].unique():
    #     df_aux=fidcs_rating[fidcs_rating['CNPJ_FUNDO']==cnpj] 

    #     fidc_dict[cnpj]={}
    #     for serie in df_aux['TAB_X_CLASSE_SERIE'].unique():
            
    #         df_aux2 = df_aux[df_aux['TAB_X_CLASSE_SERIE']==serie][['CNPJ_FUNDO','DENOM_SOCIAL','TAB_X_CLASSE_SERIE','Data','TAB_I1_VL_DISP','TAB_I2_VL_CARTEIRA','TAB_I3_VL_POSICAO_DERIV','TAB_I4_VL_OUTRO_ATIVO' ]]
            
    #         fidc_dict[cnpj].update({serie:df_aux2})
            

    # a=fidc_dict['08.315.045/0001-67']['Série 1']
    # b=fidc_dict['08.315.045/0001-67']['Série 2']


        

    
    ################################### SET DATABASE TO PLOT 1 ###################################
    # VERIFICANTO COMO ESTAO OS ATIVOS  (Ativos estao muito concentrados na Carteira - pouca disp, derivativos, e outros)
    
    
    
    #VERIFICANDO COMO ESTAO OS ATIVOS DA CARTEIRA
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')


    carteira_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_I2A_VL_DIRCRED_RISCO','TAB_I2B_VL_DIRCRED_SEM_RISCO',
                             'TAB_I2C_VL_VLMOB','TAB_I2D_VL_TITPUB_FED','TAB_I2E_VL_CDB','TAB_I2F_VL_OPER_COMPROM','TAB_I2G_VL_OUTRO_RF',
                             'TAB_I2H_VL_COTA_FIDC','TAB_I2I_VL_COTA_FIDC_NP','TAB_I2J_VL_CONTRATO_FUTURO' ,'TAB_IV_B_VL_PL_MEDIO', 'TAB_IV_A_VL_PL']
    
                
    df_carteira = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*carteira_columnlist]].dropna()

    
    
 
    # df_carteira.isna().any()    
    # df_carteira[pd.isnull(df_carteira['TAB_IV_B_VL_PL_MEDIO'])]
    # df_carteira.loc[:, df_carteira.isna().any()]

    df_carteira=df_carteira.groupby(['Data', 'Rating_AUX']).agg(DRr_m =("TAB_I2A_VL_DIRCRED_RISCO", "mean"),
                                                          DRr_wm=("TAB_I2A_VL_DIRCRED_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          DRsr_m =("TAB_I2B_VL_DIRCRED_SEM_RISCO", "mean"),
                                                          DRsr_wm=("TAB_I2B_VL_DIRCRED_SEM_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          VM_m =("TAB_I2C_VL_VLMOB", "mean"),
                                                          VM_wm=("TAB_I2C_VL_VLMOB", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          TPF_m =("TAB_I2D_VL_TITPUB_FED", "mean"),
                                                          TPF_wm=("TAB_I2D_VL_TITPUB_FED", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          CDB_m =("TAB_I2E_VL_CDB", "mean"),
                                                          CDB_wm=("TAB_I2E_VL_CDB", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          OPCM_m =("TAB_I2F_VL_OPER_COMPROM", "mean"),
                                                          OPCM_wm=("TAB_I2F_VL_OPER_COMPROM", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          ORF_m =("TAB_I2G_VL_OUTRO_RF", "mean"),
                                                          ORF_wm=("TAB_I2G_VL_OUTRO_RF", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          COTAFIDC_m =("TAB_I2H_VL_COTA_FIDC", "mean"),
                                                          COTAFIDC_wm=("TAB_I2H_VL_COTA_FIDC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          COTAFIDCNP_m =("TAB_I2I_VL_COTA_FIDC_NP", "mean"),
                                                          COTAFIDCNP_wm=("TAB_I2I_VL_COTA_FIDC_NP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          FUT_m =("TAB_I2J_VL_CONTRATO_FUTURO", "mean"),
                                                          FUT_wm=("TAB_I2J_VL_CONTRATO_FUTURO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                          n=("TAB_I2A_VL_DIRCRED_RISCO",'size')
                                                          ).reset_index()
  
    
    #CHECK WM

    # c = df_carteira   
    # c['X'] = c['TAB_I2A_VL_DIRCRED_RISCO'] * c['TAB_IV_B_VL_PL_MEDIO']
    # c=c.groupby(['Data', 'Rating_AUX'])[['TAB_I2A_VL_DIRCRED_RISCO','X','TAB_IV_B_VL_PL_MEDIO']].sum()
    # c['XX']=c['X']/c['TAB_IV_B_VL_PL_MEDIO']
    
    
    df_carteira[df_carteira.select_dtypes(include=np.number).columns.tolist()]=df_carteira.select_dtypes(include=np.number)/1000000
    df_carteira['n']=df_carteira['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_carteira[df_carteira['Rating_AUX']=='AAA'],
                  'AA+':df_carteira[df_carteira['Rating_AUX']=='AA+'],
                  'AA':df_carteira[df_carteira['Rating_AUX']=='AA'],
                  'AA-':df_carteira[df_carteira['Rating_AUX']=='AA-']}
    
    
 
    
    ################################################# PLOT 1 ###############################################

    #TEST INDIVIDUAL SUBPLOT
    
    # plt.stackplot( df_carteira1['Data'],
    #               df_carteira1['DRr_wm'],  df_carteira1['DRsr_wm'], df_carteira1['VM_wm'],df_carteira1['TPF_wm'],df_carteira1['CDB_wm'],
    #               df_carteira1['OPCM_wm'],df_carteira1['ORF_wm'],df_carteira1['COTAFIDC_wm'],df_carteira1['COTAFIDCNP_wm'],df_carteira1['FUT_wm'],
    #               labels=['DR c/ Risco','DR s/ Risco','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'])
    # plt.legend(loc='upper left')
    
    # plt.set_xlabel('Tempo')
    # plt.set_ylabel('R$ em milhões')
    # plt.set_ylabel('Média da Carteira FIDCS - AAA')
    # plt.set_xticks(rotation=60)
    # plt.show()



            ############# MEDIA PONDERADA ##################
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
        
        ax.stackplot(df_aux['Data'],
              df_aux['DRr_wm'],  df_aux['DRsr_wm'], df_aux['VM_wm'],df_aux['TPF_wm'],df_aux['CDB_wm'],
              df_aux['OPCM_wm'],df_aux['ORF_wm'],df_aux['COTAFIDC_wm'],df_aux['COTAFIDCNP_wm'],df_aux['FUT_wm'], alpha=.6)
            
     
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'], loc='best')
    fig.legend(labels=['DR c/ Risco','DR s/ Risco','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'], loc='center left')

    fig.suptitle("Carteira dos FIDCs por Rating\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Carteira FIDC - Media Ponderada.png') 
    plt.show()
        
  
        ############# MEDIA SIMPLES ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
        
        ax.stackplot(df_aux['Data'],
              df_aux['DRr_m'],  df_aux['DRsr_m'], df_aux['VM_m'],df_aux['TPF_m'],df_aux['CDB_m'],
              df_aux['OPCM_m'],df_aux['ORF_m'],df_aux['COTAFIDC_m'],df_aux['COTAFIDCNP_m'],df_aux['FUT_m'], alpha=.6)
            
     
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'], loc='best')
    fig.legend(labels=['DR c/ Risco','DR s/ Risco','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'], loc='center left')

    fig.suptitle("Carteira dos FIDCs por Rating\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Carteira FIDC - Media Simples.png') 
    plt.show()

    
    ################################### SET DATABASE TO PLOT 2A ###################################
    #EXPLODIR CARTEIRA
    
    # fitler_date0 = np.datetime64('2019-11-01')
    # fitler_date2 = np.datetime64('2020-04-01')


                   
    dr1_columnlist=['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_I2A_VL_DIRCRED_RISCO','TAB_I2A1_VL_CRED_VENC_AD',
                    'TAB_I2A2_VL_CRED_VENC_INAD','TAB_I2A21_VL_TOTAL_PARCELA_INAD','TAB_I2A3_VL_CRED_INAD','TAB_I2A4_VL_CRED_DIRCRED_PERFM',
                    'TAB_I2A5_VL_CRED_VENCIDO_PENDENTE','TAB_I2A6_VL_CRED_EMP_RECUP','TAB_I2A7_VL_CRED_RECEITA_PUBLICA',
                    'TAB_I2A8_VL_CRED_ACAO_JUDIC','TAB_I2A9_VL_CRED_FATOR_RISCO','TAB_I2A10_VL_CRED_DIVERSO','TAB_I2A11_VL_REDUCAO_RECUP', 'TAB_IV_B_VL_PL_MEDIO']
   
                
    df_dr1 = fidcs_rating[(fidcs_rating['Data']>=fitler_date0) & (fidcs_rating['Data']<=fitler_date2)][[*dr1_columnlist]].dropna()
    
    df_dr1['Total']=df_dr1[['TAB_I2A1_VL_CRED_VENC_AD','TAB_I2A2_VL_CRED_VENC_INAD','TAB_I2A3_VL_CRED_INAD','TAB_I2A4_VL_CRED_DIRCRED_PERFM',
                            'TAB_I2A5_VL_CRED_VENCIDO_PENDENTE','TAB_I2A6_VL_CRED_EMP_RECUP','TAB_I2A7_VL_CRED_RECEITA_PUBLICA',
                            'TAB_I2A8_VL_CRED_ACAO_JUDIC','TAB_I2A9_VL_CRED_FATOR_RISCO','TAB_I2A10_VL_CRED_DIVERSO', 'TAB_I2A11_VL_REDUCAO_RECUP']].sum(axis = 1, skipna = True) #- df_dr1['TAB_I2A11_VL_REDUCAO_RECUP']


    # a=df_dr1[['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_I2A_VL_DIRCRED_RISCO','Total']]
    # df_dr1['diff']=df_dr1['Total']- df_dr1['TAB_I2A_VL_DIRCRED_RISCO']
    # df_dr1=df_dr1.round(5)


    df_dr1=df_dr1.groupby(['Data','Rating_AUX']).agg(DRva_m =("TAB_I2A1_VL_CRED_VENC_AD", "mean"),
                                                    DRva_wm=("TAB_I2A1_VL_CRED_VENC_AD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRvi_m =("TAB_I2A2_VL_CRED_VENC_INAD", "mean"),
                                                    DRvi_wm=("TAB_I2A2_VL_CRED_VENC_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRdi_m =("TAB_I2A3_VL_CRED_INAD", "mean"),
                                                    DRdi_wm=("TAB_I2A3_VL_CRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRper_m =("TAB_I2A4_VL_CRED_DIRCRED_PERFM", "mean"),
                                                    DRper_wm=("TAB_I2A4_VL_CRED_DIRCRED_PERFM", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRvp_m =("TAB_I2A5_VL_CRED_VENCIDO_PENDENTE", "mean"),
                                                    DRvp_wm=("TAB_I2A5_VL_CRED_VENCIDO_PENDENTE", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRrec_m =("TAB_I2A6_VL_CRED_EMP_RECUP", "mean"),
                                                    DRrec_wm=("TAB_I2A6_VL_CRED_EMP_RECUP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRrp_m =("TAB_I2A7_VL_CRED_RECEITA_PUBLICA", "mean"),
                                                    DRrp_wm=("TAB_I2A7_VL_CRED_RECEITA_PUBLICA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRaj_m =("TAB_I2A8_VL_CRED_ACAO_JUDIC", "mean"),
                                                    DRaj_wm=("TAB_I2A8_VL_CRED_ACAO_JUDIC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRfr_m =("TAB_I2A9_VL_CRED_FATOR_RISCO", "mean"),
                                                    DRfr_wm=("TAB_I2A9_VL_CRED_FATOR_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRdiv_m =("TAB_I2A10_VL_CRED_DIVERSO", "mean"),
                                                    DRdiv_wm=("TAB_I2A10_VL_CRED_DIVERSO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRrj_m =("TAB_I2A11_VL_REDUCAO_RECUP", "mean"),
                                                    DRrj_wm=("TAB_I2A11_VL_REDUCAO_RECUP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_I2A1_VL_CRED_VENC_AD",'size')
                                                    ).reset_index()


    # df_dr1.isna().any()    
    # df_dr1[pd.isnull(df_dr1['TAB_IV_B_VL_PL_MEDIO'])]
    # df_dr1.loc[:, df_dr1.isna().any()]

    
    
    df_dr1[df_dr1.select_dtypes(include=np.number).columns.tolist()]=df_dr1.select_dtypes(include=np.number)/1000000
    df_dr1['n']=df_dr1['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_dr1[df_dr1['Rating_AUX']=='AAA'],
                  'AA+':df_dr1[df_dr1['Rating_AUX']=='AA+'],
                  'AA':df_dr1[df_dr1['Rating_AUX']=='AA'],
                  'AA-':df_dr1[df_dr1['Rating_AUX']=='AA-']}
        
     
    ################################### PLOT 2A ###################################
    
    
    ############# MEDIA PONDERADA ##################
            
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['DRva_wm'],  df_aux['DRvi_wm'], df_aux['DRdi_wm'],df_aux['DRper_wm'],df_aux['DRvp_wm'],
                     df_aux['DRrec_wm'],df_aux['DRrp_wm'],df_aux['DRaj_wm'],df_aux['DRfr_wm'],df_aux['DRdiv_wm'], df_aux['DRrj_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
    #                    'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='best')
    fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
                       'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='center left')
  
    fig.suptitle("Dir. Cred. s/ Aquisição Substancial dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - DR s risco FIDC - Media Ponderada.png') 
    plt.show()
    


    ############# MEDIA SIMPLES ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['DRva_m'],  df_aux['DRvi_m'], df_aux['DRdi_m'],df_aux['DRper_m'],df_aux['DRvp_m'],
                     df_aux['DRrec_m'],df_aux['DRrp_m'],df_aux['DRaj_m'],df_aux['DRfr_m'],df_aux['DRdiv_m'], df_aux['DRrj_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
    #                    'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='best')
    fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
                       'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='center left')
  
    fig.suptitle("Dir. Cred. s/ Aquisição Substancial dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - DR s risco FIDC - Media Simples.png') 
    plt.show()
    
    
   
    
    ################################### SET DATABASE TO PLOT 2B ###################################
    
    dr2_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_I2B_VL_DIRCRED_SEM_RISCO','TAB_I2B1_VL_CRED_VENC_AD',
                    'TAB_I2B2_VL_CRED_VENC_INAD','TAB_I2B21_VL_TOTAL_PARCELA_INAD','TAB_I2B3_VL_CRED_INAD','TAB_I2B4_VL_CRED_DIRCRED_PERFM',
                    'TAB_I2B5_VL_CRED_VENCIDO_PENDENTE','TAB_I2B6_VL_CRED_EMP_RECUP','TAB_I2B7_VL_CRED_RECEITA_PUBLICA',
                    'TAB_I2B8_VL_CRED_ACAO_JUDIC','TAB_I2B9_VL_CRED_FATOR_RISCO','TAB_I2B10_VL_CRED_DIVERSO','TAB_I2B11_VL_REDUCAO_RECUP', 'TAB_IV_B_VL_PL_MEDIO']
 
    
    df_dr2 = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*dr2_columnlist]].dropna()


    df_dr2['Total']=df_dr2[['TAB_I2B1_VL_CRED_VENC_AD','TAB_I2B2_VL_CRED_VENC_INAD','TAB_I2B21_VL_TOTAL_PARCELA_INAD','TAB_I2B3_VL_CRED_INAD','TAB_I2B4_VL_CRED_DIRCRED_PERFM',
                            'TAB_I2B5_VL_CRED_VENCIDO_PENDENTE','TAB_I2B6_VL_CRED_EMP_RECUP','TAB_I2B7_VL_CRED_RECEITA_PUBLICA',
                            'TAB_I2B8_VL_CRED_ACAO_JUDIC','TAB_I2B9_VL_CRED_FATOR_RISCO','TAB_I2B10_VL_CRED_DIVERSO','TAB_I2B11_VL_REDUCAO_RECUP']].sum(axis = 1, skipna = True) 
    
    
    # df_dr2.isna().any()    
    # #df_dr2[pd.isnull(df_dr2)]
    # df_dr2.loc[:, df_dr2.isna().any()]

    df_dr2=df_dr2.groupby(['Data','Rating_AUX']).agg(DRva_m =("TAB_I2B1_VL_CRED_VENC_AD", "mean"),
                                                    DRva_wm=("TAB_I2B1_VL_CRED_VENC_AD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRvi_m =("TAB_I2B2_VL_CRED_VENC_INAD", "mean"),
                                                    DRvi_wm=("TAB_I2B2_VL_CRED_VENC_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRdi_m =("TAB_I2B3_VL_CRED_INAD", "mean"),
                                                    DRdi_wm=("TAB_I2B3_VL_CRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRper_m =("TAB_I2B4_VL_CRED_DIRCRED_PERFM", "mean"),
                                                    DRper_wm=("TAB_I2B4_VL_CRED_DIRCRED_PERFM", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRvp_m =("TAB_I2B5_VL_CRED_VENCIDO_PENDENTE", "mean"),
                                                    DRvp_wm=("TAB_I2B5_VL_CRED_VENCIDO_PENDENTE", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRrec_m =("TAB_I2B6_VL_CRED_EMP_RECUP", "mean"),
                                                    DRrec_wm=("TAB_I2B6_VL_CRED_EMP_RECUP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRrp_m =("TAB_I2B7_VL_CRED_RECEITA_PUBLICA", "mean"),
                                                    DRrp_wm=("TAB_I2B7_VL_CRED_RECEITA_PUBLICA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRaj_m =("TAB_I2B8_VL_CRED_ACAO_JUDIC", "mean"),
                                                    DRaj_wm=("TAB_I2B8_VL_CRED_ACAO_JUDIC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRfr_m =("TAB_I2B9_VL_CRED_FATOR_RISCO", "mean"),
                                                    DRfr_wm=("TAB_I2B9_VL_CRED_FATOR_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRdiv_m =("TAB_I2B10_VL_CRED_DIVERSO", "mean"),
                                                    DRdiv_wm=("TAB_I2B10_VL_CRED_DIVERSO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRrj_m =("TAB_I2B11_VL_REDUCAO_RECUP", "mean"),
                                                    DRrj_wm=("TAB_I2B11_VL_REDUCAO_RECUP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_I2B1_VL_CRED_VENC_AD",'size')
                                                    ).reset_index()

    
    df_dr2[df_dr2.select_dtypes(include=np.number).columns.tolist()]=df_dr2.select_dtypes(include=np.number)/1000000
    df_dr2['n']=df_dr2['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_dr2[df_dr2['Rating_AUX']=='AAA'],
                  'AA+':df_dr2[df_dr2['Rating_AUX']=='AA+'],
                  'AA':df_dr2[df_dr2['Rating_AUX']=='AA'],
                  'AA-':df_dr2[df_dr2['Rating_AUX']=='AA-']}
  
    ################################### PLOT 2B ###################################
    
    ############# MEDIA PONDERADA ##################
        
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['DRva_wm'],  df_aux['DRvi_wm'], df_aux['DRdi_wm'],df_aux['DRper_wm'],df_aux['DRvp_wm'],
                     df_aux['DRrec_wm'],df_aux['DRrp_wm'],df_aux['DRaj_wm'],df_aux['DRfr_wm'],df_aux['DRdiv_wm'], df_aux['DRrj_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
    #                    'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='best')
    fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
                       'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='center left')

    fig.suptitle("Dir. Cred. c/ Aquisição Substancial dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - DR c risco FIDC - Media Ponderada.png') 
    plt.show()


    ############# MEDIA SIMPLES ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]

        ax.stackplot(df_aux['Data'], df_aux['DRva_m'],  df_aux['DRvi_m'], df_aux['DRdi_m'],df_aux['DRper_m'],df_aux['DRvp_m'],
                     df_aux['DRrec_m'],df_aux['DRrp_m'],df_aux['DRaj_m'],df_aux['DRfr_m'],df_aux['DRdiv_m'], df_aux['DRrj_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
    #                    'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='best')
    fig.legend(labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ','Receitas Públicas',
                       'Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'], loc='center left')

    fig.suptitle("Dir. Cred. c/ Aquisição Substancial dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - DR c risco FIDC - Media Simples.png') 
    plt.show()
    
    
    
    ################################### SET DATABASE TO PLOT 2C ###################################

    #EXPLODIR VALORES MOBILIARIOS
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    vm_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_I2C_VL_VLMOB','TAB_IV_B_VL_PL_MEDIO',
                      'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC','TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']
 
    
    df_vm = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*vm_columnlist]].dropna()


    # df_vm['Total']=df_vm[[ 'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC',
    #                       'TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']].sum(axis = 1, skipna = True) 
    # df_vm['diff']=df_vm['Total']-df_vm['TAB_I2C_VL_VLMOB']
    
    # df_vm.isna().any()    
    #df_vm[pd.isnull(df_vm)]
    # df_vm.loc[:, df_vm.isna().any()]

    df_vm=df_vm.groupby(['Data','Rating_AUX']).agg(deb_m =("TAB_I2C1_VL_DEBENTURE", "mean"),
                                                    deb_wm=("TAB_I2C1_VL_DEBENTURE", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    cri_m =("TAB_I2C2_VL_CRI", "mean"),
                                                    cri_wm=("TAB_I2C2_VL_CRI", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    npc_m =("TAB_I2C3_VL_NP_COMERC", "mean"),
                                                    npc_wm=("TAB_I2C3_VL_NP_COMERC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    lf_m =("TAB_I2C4_VL_LETRA_FINANC", "mean"),
                                                    lf_wm=("TAB_I2C4_VL_LETRA_FINANC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    oc_m =("TAB_I2C5_VL_COTA_FUNDO_ICVM555", "mean"),
                                                    oc_wm=("TAB_I2C5_VL_COTA_FUNDO_ICVM555", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    outros_m =("TAB_I2C6_VL_OUTRO", "mean"),
                                                    outros_wm=("TAB_I2C6_VL_OUTRO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_I2C_VL_VLMOB",'size')
                                                    ).reset_index()

    
    df_vm[df_vm.select_dtypes(include=np.number).columns.tolist()]=df_vm.select_dtypes(include=np.number)/1000000
    df_vm['n']=df_vm['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_vm[df_vm['Rating_AUX']=='AAA'],
                  'AA+':df_vm[df_vm['Rating_AUX']=='AA+'],
                  'AA':df_vm[df_vm['Rating_AUX']=='AA'],
                  'AA-':df_vm[df_vm['Rating_AUX']=='AA-']}

    ################################### PLOT 2C ###################################

    ############# MEDIA PONDERADA ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['oc_wm'], df_aux['deb_wm'],  df_aux['cri_wm'], df_aux['npc_wm'],df_aux['lf_wm'],df_aux['outros_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    fig.legend(labels=['Cotas Fundos ICVM409', 'Debentures','CRI','Nota Promissória Comp.','Letras Financeiras','Outros'], loc='best')
    fig.suptitle("Valores Mobiliários\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Valores Mobiliarios - Media Ponderada.png') 
    plt.show()


    ############# MEDIA SIMPLES ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['oc_m'], df_aux['deb_m'],  df_aux['cri_m'], 
                     df_aux['npc_m'],df_aux['lf_m'],df_aux['outros_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    fig.legend(labels=['Cotas Fundos ICVM409', 'Debentures','CRI','Nota Promissória Comp.','Letras Financeiras','Outros'], loc='best')
    fig.suptitle("Valores Mobiliários\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Valores Mobiliarios - Media Simples.png') 
    plt.show()
    
    
    
     ################################### SET DATABASE TO PLOT 2.2 ###################################

    #EXPLODIR CARTEIRA POR SETOR

    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    setor_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_IV_B_VL_PL_MEDIO', 'TAB_II_VL_CARTEIRA','TAB_II_A_VL_INDUST',
                      'TAB_II_B_VL_IMOBIL','TAB_II_C_VL_COMERC','TAB_II_D_VL_SERV','TAB_II_E_VL_AGRONEG','TAB_II_F_VL_FINANC',
                      'TAB_II_G_VL_CREDITO','TAB_II_H_VL_FACTOR','TAB_II_I_VL_SETOR_PUBLICO','TAB_II_J_VL_JUDICIAL','TAB_II_K_VL_MARCA']
 
    
    df_setor = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*setor_columnlist]].dropna()


    # df_setor['Total']=df_setor[['TAB_II_A_VL_INDUST','TAB_II_B_VL_IMOBIL','TAB_II_C_VL_COMERC','TAB_II_D_VL_SERV','TAB_II_E_VL_AGRONEG','TAB_II_F_VL_FINANC',
    #                             'TAB_II_G_VL_CREDITO','TAB_II_H_VL_FACTOR','TAB_II_I_VL_SETOR_PUBLICO','TAB_II_J_VL_JUDICIAL','TAB_II_K_VL_MARCA']].sum(axis = 1, skipna = True) 
    # df_setor['diff']=df_setor['Total']-df_setor['TAB_II_VL_CARTEIRA']

    
    # df_setor.isna().any()    
    # #df_setor[pd.isnull(df_setor)]
    # df_setor.loc[:, df_setor.isna().any()]

    df_setor=df_setor.groupby(['Data','Rating_AUX']).agg(   ind_m =("TAB_II_A_VL_INDUST", "mean"),
                                                            ind_wm=("TAB_II_A_VL_INDUST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            imob_m =("TAB_II_B_VL_IMOBIL", "mean"),
                                                            imob_wm=("TAB_II_B_VL_IMOBIL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            com_m =("TAB_II_C_VL_COMERC", "mean"),
                                                            com_wm=("TAB_II_C_VL_COMERC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            serv_m =("TAB_II_D_VL_SERV", "mean"),
                                                            serv_wm=("TAB_II_D_VL_SERV", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            agron_m =("TAB_II_E_VL_AGRONEG", "mean"),
                                                            agron_wm=("TAB_II_E_VL_AGRONEG", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            fin_m =("TAB_II_F_VL_FINANC", "mean"),
                                                            fin_wm=("TAB_II_F_VL_FINANC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            cred_m =("TAB_II_G_VL_CREDITO", "mean"),
                                                            cred_wm=("TAB_II_G_VL_CREDITO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            fact_m =("TAB_II_H_VL_FACTOR", "mean"),
                                                            fact_wm=("TAB_II_H_VL_FACTOR", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            sp_m =("TAB_II_I_VL_SETOR_PUBLICO", "mean"),
                                                            sp_wm=("TAB_II_I_VL_SETOR_PUBLICO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            jud_m =("TAB_II_J_VL_JUDICIAL", "mean"),
                                                            jud_wm=("TAB_II_J_VL_JUDICIAL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            marca_m =("TAB_II_K_VL_MARCA", "mean"),
                                                            marca_wm=("TAB_II_K_VL_MARCA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                            ).reset_index()

    
    df_setor[df_setor.select_dtypes(include=np.number).columns.tolist()]=df_setor.select_dtypes(include=np.number)/1000000
    df_setor['n']=df_setor['n']*1000000


    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_setor[df_setor['Rating_AUX']=='AAA'],
                  'AA+':df_setor[df_setor['Rating_AUX']=='AA+'],
                  'AA':df_setor[df_setor['Rating_AUX']=='AA'],
                  'AA-':df_setor[df_setor['Rating_AUX']=='AA-']}
  
        



    ################################### PLOT 2.2 ###################################

    ############# MEDIA PONDERADA ##################


    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['ind_wm'],  df_aux['imob_wm'], df_aux['com_wm'],df_aux['serv_wm'],df_aux['agron_wm'],
                     df_aux['fin_wm'],df_aux['cred_wm'],df_aux['fact_wm'],df_aux['sp_wm'],df_aux['jud_wm'], df_aux['marca_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio','Financeiros','Cartão de Crédito',
    #                    'Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes'], loc='best')
    fig.legend(labels=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio','Financeiros','Cartão de Crédito',
                       'Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes'], loc='center left')

    fig.suptitle("Carteira de Ativos por Setor\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Setor - Media Ponderada.png') 
    plt.show()
 


     ############# MEDIA SIMPLES ##################

 
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['ind_m'],  df_aux['imob_m'], df_aux['com_m'],df_aux['serv_m'],df_aux['agron_m'],
                     df_aux['fin_m'],df_aux['cred_m'],df_aux['fact_m'],df_aux['sp_m'],df_aux['jud_m'], df_aux['marca_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio','Financeiros','Cartão de Crédito',
    #                    'Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes'], loc='best')
    fig.legend(labels=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio','Financeiros','Cartão de Crédito',
                       'Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes'], loc='center left')

    fig.suptitle("Carteira de Ativos por Setor\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Setor - Media Simples.png') 
    plt.show()
 
    
    ################################### SET DATABASE TO PLOT 3 ###################################

    #VERIFICAR PASSIVO DA CARTEIRA (TALVES SO VALORES A PAGAR)
            
         
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    passivo_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_IV_B_VL_PL_MEDIO','TAB_III_VL_PASSIVO',
                        'TAB_III_A_VL_PAGAR','TAB_III_A1_VL_CPRAZO','TAB_III_A2_VL_LPRAZO','TAB_III_B_VL_POSICAO_DERIV',
                        'TAB_III_B1_VL_TERMO','TAB_III_B2_VL_OPCAO','TAB_III_B3_VL_FUTURO','TAB_III_B4_VL_SWAP_PAGAR']
 
    
    df_passivo= fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*passivo_columnlist]].dropna()


    df_passivo['Total']=df_passivo[['TAB_III_B1_VL_TERMO','TAB_III_B2_VL_OPCAO','TAB_III_B3_VL_FUTURO','TAB_III_B4_VL_SWAP_PAGAR']].sum(axis = 1, skipna = True) 
    df_passivo['diff']=df_passivo['Total']-df_passivo['TAB_III_B_VL_POSICAO_DERIV']

    
    # df_passivo.isna().any()    
    # #df_passivo[pd.isnull(df_setor)]
    # df_passivo.loc[:, df_passivo.isna().any()]

    df_passivo=df_passivo.groupby(['Data','Rating_AUX']).agg(pcp_m =("TAB_III_A1_VL_CPRAZO", "mean"),
                                                            pcp_wm=("TAB_III_A1_VL_CPRAZO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            plp_m =("TAB_III_A2_VL_LPRAZO", "mean"),
                                                            plp_wm=("TAB_III_A2_VL_LPRAZO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            der_m =("TAB_III_B_VL_POSICAO_DERIV", "mean"),
                                                            der_wm=("TAB_III_B_VL_POSICAO_DERIV", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            n=("TAB_III_VL_PASSIVO",'size')
                                                            ).reset_index()

    
    df_passivo[df_passivo.select_dtypes(include=np.number).columns.tolist()]=df_passivo.select_dtypes(include=np.number)/1000000
    df_passivo['n']=df_passivo['n']*1000000


    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA': df_passivo[df_passivo['Rating_AUX']=='AAA'],
                  'AA+': df_passivo[df_passivo['Rating_AUX']=='AA+'],
                  'AA' : df_passivo[df_passivo['Rating_AUX']=='AA'],
                  'AA-': df_passivo[df_passivo['Rating_AUX']=='AA-']}
 


    ################################### PLOT 3 ###################################
    ################################### MEDIA PODNERADA ###################################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['pcp_wm'], df_aux['plp_wm'],  df_aux['der_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='center left')

    fig.suptitle("Passivo Médios dos Fundos por Rating\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Passivo - Media Ponderada.png') 
    plt.show()
    
    ################################### MEDIA SIMPLES ###################################
    
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['pcp_m'], df_aux['plp_m'],  df_aux['der_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='center left')

    fig.suptitle("Passivo Médios dos Fundos por Rating\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Passivo - Media Simples.png') 
    plt.show()


    ################################### SET DATABASE TO PLOT 4 ###################################
    
        # 106	TAB_IV_A_VL_PL
        # 107	TAB_IV_B_VL_PL_MEDIO
        

    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    pl_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_IV_B_VL_PL_MEDIO','TAB_IV_A_VL_PL']
 
    
    df_pl= fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*pl_columnlist]].dropna()


    # df_pl['Total'] = df_pl[['TAB_III_B1_VL_TERMO','TAB_III_B2_VL_OPCAO','TAB_III_B3_VL_FUTURO','TAB_III_B4_VL_SWAP_PAGAR']].sum(axis = 1, skipna = True) 
    # df_pl['diff'] = df_pl['Total']-df_pl['TAB_III_B_VL_POSICAO_DERIV']

    
    # df_pl.isna().any()    
    # #df_pl[pd.isnull(df_setor)]
    # df_pl.loc[:, df_pl.isna().any()]

    df_pl=df_pl.groupby(['Data','Rating_AUX']).agg( plm_m =("TAB_IV_B_VL_PL_MEDIO", "mean"),
                                                    plm_wm=("TAB_IV_B_VL_PL_MEDIO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    pl_m =("TAB_IV_A_VL_PL", "mean"),
                                                    pl_wm=("TAB_IV_A_VL_PL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                    ).reset_index()

    
    df_pl[df_pl.select_dtypes(include=np.number).columns.tolist()]=df_pl.select_dtypes(include=np.number)/1000000
    df_pl['n']=df_pl['n']*1000000


    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA': df_pl[df_pl['Rating_AUX']=='AAA'],
                  'AA+': df_pl[df_pl['Rating_AUX']=='AA+'],
                  'AA' : df_pl[df_pl['Rating_AUX']=='AA'],
                  'AA-': df_pl[df_pl['Rating_AUX']=='AA-']}    
    
    ################################### PLOT 4 ###################################
    ################################### MEDIA PONDERADA ###################################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['plm_wm'])
        ax.plot(df_aux['Data'],df_aux['pl_wm'])
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    fig.legend(labels=['PL Médio','PL'], loc='center right')
    fig.suptitle("PL Médios dos Fundos por Rating\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('PL - Media Ponderada.png') 
    plt.show()
    
    
     ################################### MEDIA SIMPLES ###################################
   
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['plm_m'])
        ax.plot(df_aux['Data'],df_aux['pl_m'])
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    fig.legend(labels=['PL Médio','PL'], loc='center right')
    fig.suptitle("PL Médios dos Fundos por Rating\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('PL - Media Simples.png') 
    plt.show()
    


         
    ################################### SET DATABASE TO PLOT 5A ###################################
    
    
    #V - Comportamento da Carteira de Direitos Creditórios COM Aquisição Substancial dos Riscos e Benefícios	

    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    dr3_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO', 'TAB_V_A_VL_DIRCRED_PRAZO','TAB_V_B_VL_DIRCRED_INAD','TAB_V_C_VL_DIRCRED_ANTECIPADO']
 
    
    df_dr3 = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*dr3_columnlist]].dropna()


    # df_dr3['Total']=df_dr3[[ 'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC',
    #                       'TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']].sum(axis = 1, skipna = True) 
    # df_dr3['diff']=df_dr3['Total']-df_vm['TAB_I2C_VL_VLMOB']
    
    # df_dr3.isna().any()    
    #df_dr3[pd.isnull(df_vm)]
    # df_dr3.loc[:, df_dr3.isna().any()]

    df_dr3=df_dr3.groupby(['Data','Rating_AUX']).agg(avenc_m =("TAB_V_A_VL_DIRCRED_PRAZO", "mean"),
                                                    avenc_wm=("TAB_V_A_VL_DIRCRED_PRAZO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    inad_m =("TAB_V_B_VL_DIRCRED_INAD", "mean"),
                                                    inad_wm=("TAB_V_B_VL_DIRCRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    pagant_m =("TAB_V_C_VL_DIRCRED_ANTECIPADO", "mean"),
                                                    pagant_wm=("TAB_V_C_VL_DIRCRED_ANTECIPADO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                    ).reset_index()

    
    df_dr3[df_dr3.select_dtypes(include=np.number).columns.tolist()]=df_dr3.select_dtypes(include=np.number)/1000000
    df_dr3['n']=df_dr3['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_dr3[df_dr3['Rating_AUX']=='AAA'],
                  'AA+':df_dr3[df_dr3['Rating_AUX']=='AA+'],
                  'AA':df_dr3[df_dr3['Rating_AUX']=='AA'],
                  'AA-':df_dr3[df_dr3['Rating_AUX']=='AA-']}

     
    
    ################################### PLOT 5A ###################################
    
        ############# MEDIA PONDERADA ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['avenc_wm'], df_aux['inad_wm'],  df_aux['pagant_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['A Vencer','Inadimplentes','Pagos Antecipadamente'], loc='center left')

    fig.suptitle("Comportamento dos DRs c/ Aquisição dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Comp DR c risco - Media Ponderada.png') 
    plt.show()
    
    
    ############# MEDIA SIMPLES ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['avenc_m'], df_aux['inad_m'],  df_aux['pagant_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['A Vencer','Inadimplentes','Pagos Antecipadamente'], loc='center left')

    fig.suptitle("Comportamento dos DRs c/ Aquisição dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Comp DR c risco - Media Simples.png') 
    plt.show()
    
             
    ################################### SET DATABASE TO PLOT 5B ###################################
        
    #VI - Comportamento da Carteira de Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios	
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    dr4_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO', 'TAB_VI_A_VL_DIRCRED_PRAZO','TAB_VI_B_VL_DIRCRED_INAD','TAB_VI_C_VL_DIRCRED_ANTECIPADO']
 
    
    df_dr4 = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*dr4_columnlist]].dropna()


    # df_dr4['Total']=df_dr4[[ 'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC',
    #                       'TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']].sum(axis = 1, skipna = True) 
    # df_dr4['diff']=df_dr4['Total']-df_vm['TAB_I2C_VL_VLMOB']
    
    # df_dr4.isna().any()    
    #df_dr4[pd.isnull(df_vm)]
    # df_dr4.loc[:, df_dr3.isna().any()]

    df_dr4=df_dr4.groupby(['Data','Rating_AUX']).agg(avenc_m =("TAB_VI_A_VL_DIRCRED_PRAZO", "mean"),
                                                    avenc_wm=("TAB_VI_A_VL_DIRCRED_PRAZO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    inad_m =("TAB_VI_B_VL_DIRCRED_INAD", "mean"),
                                                    inad_wm=("TAB_VI_B_VL_DIRCRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    pagant_m =("TAB_VI_C_VL_DIRCRED_ANTECIPADO", "mean"),
                                                    pagant_wm=("TAB_VI_C_VL_DIRCRED_ANTECIPADO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                    ).reset_index()

    
    df_dr4[df_dr4.select_dtypes(include=np.number).columns.tolist()]=df_dr4.select_dtypes(include=np.number)/1000000
    df_dr4['n']=df_dr4['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_dr4[df_dr4['Rating_AUX']=='AAA'],
                  'AA+':df_dr4[df_dr4['Rating_AUX']=='AA+'],
                  'AA':df_dr4[df_dr4['Rating_AUX']=='AA'],
                  'AA-':df_dr4[df_dr4['Rating_AUX']=='AA-']}
     
    
    ################################### PLOT 5B ###################################
    
    
    ############# MEDIA PONDERADA ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['avenc_wm'], df_aux['inad_wm'],  df_aux['pagant_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['A Vencer','Inadimplentes','Pagos Antecipadamente'], loc='center left')

    fig.suptitle("Comportamento dos DRs s/ Aquisição dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Comp DR s risco - Media Ponderada.png') 
    plt.show()         
    
    
    ############# MEDIA SIMPLES ##################

    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'],df_aux['avenc_m'], df_aux['inad_m'],  df_aux['pagant_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['A Vencer','Inadimplentes','Pagos Antecipadamente'], loc='center left')

    fig.suptitle("Comportamento dos DRs s/ Aquisição dos Riscos e Benefícios\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Ativo - Comp DR s risco - Media Simples.png') 
    plt.show()  
    
    
    
    
    ################################### SET DATABASE TO PLOT 6 ###################################
    


    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    oper_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                        #A)AQUISICOES
                        'TAB_VII_A1_1_QT_DIRCRED_RISCO','TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO','TAB_VII_A3_1_QT_DIRCRED_VENC_AD','TAB_VII_A4_1_QT_DIRCRED_VENC_INAD','TAB_VII_A5_1_QT_DIRCRED_INAD',
                        'TAB_VII_A1_2_VL_DIRCRED_RISCO','TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO','TAB_VII_A3_2_VL_DIRCRED_VENC_AD','TAB_VII_A4_2_VL_DIRCRED_VENC_INAD','TAB_VII_A5_2_VL_DIRCRED_INAD',
                        #B) ALIENACOES
                        'TAB_VII_B1_1_QT_CEDENTE','TAB_VII_B2_1_QT_PREST','TAB_VII_B3_1_QT_TERCEIRO',
                        'TAB_VII_B1_2_VL_CEDENTE','TAB_VII_B2_2_VL_PREST','TAB_VII_B3_2_VL_TERCEIRO',
                        'TAB_VII_B1_3_VL_CONTAB_CEDENTE','TAB_VII_B2_3_VL_CONTAB_PREST','TAB_VII_B3_3_VL_CONTAB_TERCEIRO',     
                        #C) SUBSTIITUICAO        
                        'TAB_VII_C_1_QT_SUBST',
                        'TAB_VII_C_2_VL_SUBST',
                        'TAB_VII_C_3_VL_CONTAB_SUBST',    
                        #D) RECOMPRA
                        'TAB_VII_D_1_QT_RECOMPRA',
                        'TAB_VII_D_2_VL_RECOMPRA',
                        'TAB_VII_D_3_VL_CONTAB_RECOMPRA']
 
    
    df_oper = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*oper_columnlist]].dropna()
    
    df_oper['AQUIS_QT'] = df_oper[['TAB_VII_A1_1_QT_DIRCRED_RISCO','TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO','TAB_VII_A3_1_QT_DIRCRED_VENC_AD','TAB_VII_A4_1_QT_DIRCRED_VENC_INAD','TAB_VII_A5_1_QT_DIRCRED_INAD']].sum(axis = 1, skipna = True) 
    df_oper['AQUIS_VL'] = df_oper[['TAB_VII_A1_2_VL_DIRCRED_RISCO','TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO','TAB_VII_A3_2_VL_DIRCRED_VENC_AD','TAB_VII_A4_2_VL_DIRCRED_VENC_INAD','TAB_VII_A5_2_VL_DIRCRED_INAD',]].sum(axis = 1, skipna = True) 
    df_oper['ALIEN_QT'] = df_oper[['TAB_VII_B1_1_QT_CEDENTE','TAB_VII_B2_1_QT_PREST','TAB_VII_B3_1_QT_TERCEIRO',]].sum(axis = 1, skipna = True) 
    df_oper['ALIEN_VL'] = df_oper[['TAB_VII_B1_2_VL_CEDENTE','TAB_VII_B2_2_VL_PREST','TAB_VII_B3_2_VL_TERCEIRO']].sum(axis = 1, skipna = True) 
    df_oper['ALEIN_VLCONT'] = df_oper[['TAB_VII_B1_3_VL_CONTAB_CEDENTE','TAB_VII_B2_3_VL_CONTAB_PREST','TAB_VII_B3_3_VL_CONTAB_TERCEIRO']].sum(axis = 1, skipna = True) 


    # df_oper['Total']=df_oper[[ 'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC',
    #                       'TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']].sum(axis = 1, skipna = True) 
    # df_oper['diff']=df_oper['Total']-df_vm['TAB_I2C_VL_VLMOB']
    
    # df_oper.isna().any()    
    # df_oper[pd.isnull(df_vm)]
    # df_oper.loc[:, df_oper.isna().any()]

    df_oper=df_oper.groupby(['Data','Rating_AUX']).agg( aqqt_m =("AQUIS_QT", "mean"),
                                                        aqqt_wm=("AQUIS_QT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        aqvl_m =("AQUIS_VL", "mean"),
                                                        aqvl_wm=("AQUIS_VL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        aliqt_m =("ALIEN_QT", "mean"),
                                                        aliqt_wm=("ALIEN_QT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        alivl_m =("ALIEN_VL", "mean"),
                                                        alivl_wm=("ALIEN_VL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        subsqt_m =("TAB_VII_C_1_QT_SUBST", "mean"),
                                                        subsqt_wm=("TAB_VII_C_1_QT_SUBST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        subsvl_m =("TAB_VII_C_2_VL_SUBST", "mean"),                                                        
                                                        subsvl_wm=("TAB_VII_C_2_VL_SUBST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        recqt_m =("TAB_VII_D_1_QT_RECOMPRA", "mean"),
                                                        recqt_wm=("TAB_VII_D_1_QT_RECOMPRA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        recvl_m =("TAB_VII_D_2_VL_RECOMPRA", "mean"),                                                        
                                                        recvl_wm=("TAB_VII_D_2_VL_RECOMPRA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    
    df_oper[df_oper.select_dtypes(include=np.number).columns.tolist()]=df_oper.select_dtypes(include=np.number)/1000000
    df_oper['n']=df_oper['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_oper[df_oper['Rating_AUX']=='AAA'],
                  'AA+':df_oper[df_oper['Rating_AUX']=='AA+'],
                  'AA':df_oper[df_oper['Rating_AUX']=='AA'],
                  'AA-':df_oper[df_oper['Rating_AUX']=='AA-']}

    
    ################################### PLOT 6 ###################################
    
    ############# MEDIA PONDERADA ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['aqvl_wm'], df_aux['alivl_wm'],  df_aux['subsvl_wm'],df_aux['recvl_wm'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['Aquisições','Alienações','Substituições','Recompras'], loc='center left')

    fig.suptitle("Negcóios Realizados no Mês\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Negocios Realizados no Mês - Agregado - Media Ponderada.png') 
    plt.show()     
    
    ############# MEDIA SIMPLES ##################

    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['aqvl_m'], df_aux['alivl_m'],  df_aux['subsvl_m'],df_aux['recvl_m'],alpha=.6)
            
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['Aquisições','Alienações','Substituições','Recompras'], loc='center left')

    fig.suptitle("Negcóios Realizados no Mês\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Negocios Realizados no Mês - Agregado - Media Simples.png') 
    plt.show()   
        

    ################################### SET DATABASE TO PLOT 6B ###################################
    #EXPLODIR AQUISICOES
    
    df_oper2 = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*oper_columnlist]].dropna()
    
 
    df_oper2 = df_oper2.groupby(['Data','Rating_AUX']).agg( DRrqt_m =("TAB_VII_A1_1_QT_DIRCRED_RISCO", "mean"),
                                                            DRrqt_wm=("TAB_VII_A1_1_QT_DIRCRED_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRrvl_m =("TAB_VII_A1_2_VL_DIRCRED_RISCO", "mean"),
                                                            DRrvl_wm=("TAB_VII_A1_2_VL_DIRCRED_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRsrqt_m =("TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO", "mean"),
                                                            DRsrqt_wm=("TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRsrvl_m =("TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO", "mean"),
                                                            DRsrvl_wm=("TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRadqt_m =("TAB_VII_A3_1_QT_DIRCRED_VENC_AD", "mean"),
                                                            DRadqt_wm=("TAB_VII_A3_1_QT_DIRCRED_VENC_AD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRadqtvl_m =("TAB_VII_A3_2_VL_DIRCRED_VENC_AD", "mean"),                                                        
                                                            DRadqtvl_wm=("TAB_VII_A3_2_VL_DIRCRED_VENC_AD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRvinadqt_m =("TAB_VII_A4_1_QT_DIRCRED_VENC_INAD", "mean"),
                                                            DRvinadqt_wm=("TAB_VII_A4_1_QT_DIRCRED_VENC_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRvinadvl_m =("TAB_VII_A4_2_VL_DIRCRED_VENC_INAD", "mean"),                                                        
                                                            DRvinadvl_wm=("TAB_VII_A4_2_VL_DIRCRED_VENC_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRinadqt_m =("TAB_VII_A5_1_QT_DIRCRED_INAD", "mean"),
                                                            DRinadqt_wm=("TAB_VII_A5_1_QT_DIRCRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                            DRinadvl_m =("TAB_VII_A5_2_VL_DIRCRED_INAD", "mean"),                                                        
                                                            DRinadvl_wm=("TAB_VII_A5_2_VL_DIRCRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),                                                        
                                                            n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                            ).reset_index()

    
    df_oper2[df_oper2.select_dtypes(include=np.number).columns.tolist()]=df_oper2.select_dtypes(include=np.number)/1000000
    df_oper2['n']=df_oper2['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_oper2[df_oper2['Rating_AUX']=='AAA'],
                  'AA+':df_oper2[df_oper2['Rating_AUX']=='AA+'],
                  'AA':df_oper2[df_oper2['Rating_AUX']=='AA'],
                  'AA-':df_oper2[df_oper2['Rating_AUX']=='AA-']}
    
    
    
    
    
    ################################################### PLOT 6B ###################################3######
    
    
    ############# MEDIA PONDERADA ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['DRrvl_wm'], df_aux['DRsrvl_wm'],  df_aux['DRadqtvl_wm'],df_aux['DRvinadvl_wm'],df_aux['DRinadvl_wm'],alpha=.6)          
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='center left')
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='best')

    fig.suptitle("Aquisições Realizadas no Mês\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Negocios Realizados no Mês - Aquisicoes - Media Ponderada.png') 
    plt.show() 

    
    ############# MEDIA SIMPLES ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['DRrvl_m'], df_aux['DRsrvl_m'],  df_aux['DRadqtvl_m'],df_aux['DRvinadvl_m'],df_aux['DRinadvl_m'],alpha=.6)          
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='center left')
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='best')

    fig.suptitle("Aquisições Realizadas no Mês\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Negocios Realizados no Mês - Aquisicoes - Media Simples.png') 
    plt.show()   
        
        
         
    ################################### SET DATABASE TO PLOT 7 ###################################
    
        
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    # cotas_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO','TAB_X_NR_COTST','TAB_X_QT_COTA','TAB_X_VL_COTA']
 
    
    # df_cota = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*cotas_columnlist]]#.dropna()
    
   

    # df_cota['Total']=df_cota[[ 'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC',
    #                       'TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']].sum(axis = 1, skipna = True) 
    # df_cota['diff']=df_cota['Total']-df_vm['TAB_I2C_VL_VLMOB']
    
    # df_cota.isna().any()    
    # df_cota[pd.isnull(df_vm)]
    # df_cota.loc[:, df_cota.isna().any()]

    # df_cota=df_cota.groupby(['Data','Rating_AUX']).agg( ncot_m =("TAB_X_NR_COTST", "mean"),
    #                                                     ncot_wm=("TAB_X_NR_COTST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
    #                                                     qtcota_m =("TAB_X_QT_COTA", "mean"),
    #                                                     qtcota_wm=("TAB_X_QT_COTA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
    #                                                     vlcota_m =("TAB_X_VL_COTA", "mean"),
    #                                                     vlcota_wm=("TAB_X_VL_COTA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
    #                                                     n=("TAB_IV_B_VL_PL_MEDIO",'size')
    #                                                     ).reset_index()

    
    # # df_cota[df_cota.select_dtypes(include=np.number).columns.tolist()]=df_cota.select_dtypes(include=np.number)/1000000
    # # df_cota['n']=df_oper['n']*1000000
    
    # df_cota['qtcota_m']=df_cota['qtcota_m']/1000000
    # df_cota['qtcota_wm']=df_cota['qtcota_wm']/1000000


    # baseline=['AAA','AA+','AA','AA-']
    # dict_ativo = {'AAA':df_cota[df_cota['Rating_AUX']=='AAA'],
    #               'AA+':df_cota[df_cota['Rating_AUX']=='AA+'],
    #               'AA':df_cota[df_cota['Rating_AUX']=='AA'],
    #               'AA-':df_cota[df_cota['Rating_AUX']=='AA-']}   
    
    
    
    ################################### PLOT 7 ###################################
    
    
    
    
    
    

        
    ################################### SET DATABASE TO PLOT 8 ###################################
      

        
            
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    mov_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                          'TAB_X_VL_TOTAL_AMORT','TAB_X_VL_TOTAL_CAPT','TAB_X_VL_TOTAL_RESG','TAB_X_VL_TOTAL_RESGSOL',
                          'TAB_X_QT_TOTAL_AMORT','TAB_X_QT_TOTAL_CAPT','TAB_X_QT_TOTAL_RESG','TAB_X_QT_TOTAL_RESGSOL']
 
    
    df_mov= fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*mov_columnlist]].dropna()

    
 
    df_mov = df_mov.groupby(['Data','Rating_AUX']).agg( amortqt_m =("TAB_X_QT_TOTAL_AMORT", "mean"),
                                                        amortqt_wm=("TAB_X_QT_TOTAL_AMORT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        amortvl_m =("TAB_X_VL_TOTAL_AMORT", "mean"),
                                                        amortvl_wm=("TAB_X_VL_TOTAL_AMORT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        captqt_m =("TAB_X_QT_TOTAL_CAPT", "mean"),
                                                        captqt_wm=("TAB_X_QT_TOTAL_CAPT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        captvl_m =("TAB_X_VL_TOTAL_CAPT", "mean"),
                                                        captvl_wm=("TAB_X_VL_TOTAL_CAPT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgqt_m =("TAB_X_QT_TOTAL_RESG", "mean"),
                                                        resgqt_wm=("TAB_X_QT_TOTAL_RESG", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgvl_m =("TAB_X_VL_TOTAL_RESG", "mean"),                                                        
                                                        resgvl_wm=("TAB_X_VL_TOTAL_RESG", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgsolqt_m =("TAB_X_QT_TOTAL_RESGSOL", "mean"),
                                                        resgsolqt_wm=("TAB_X_QT_TOTAL_RESGSOL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgsolvl_m =("TAB_X_VL_TOTAL_RESGSOL", "mean"),                                                        
                                                        resgsolvl_wm=("TAB_X_VL_TOTAL_RESGSOL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    
    df_mov[df_mov.select_dtypes(include=np.number).columns.tolist()]=df_mov.select_dtypes(include=np.number)/1000000
    df_mov['n']=df_mov['n']*1000000

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_mov[df_mov['Rating_AUX']=='AAA'],
                  'AA+':df_mov[df_mov['Rating_AUX']=='AA+'],
                  'AA':df_mov[df_mov['Rating_AUX']=='AA'],
                  'AA-':df_mov[df_mov['Rating_AUX']=='AA-']}
    
    
    
    
    ################################### PLOT 8 ###################################
    
    
    ############# MEDIA PONDERADA ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['amortvl_wm'], df_aux['captvl_wm'],  df_aux['resgvl_wm'],df_aux['resgsolvl_wm'],alpha=.6)          
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['Amoritzação','Captção','Resgate','Resgate Solicitado'], loc='center left')
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='best')

    fig.suptitle("Movimentações Realizadas no Fundo\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Movimentações Realizadas no mês - Media Ponderada.png') 
    plt.show()  



    ############# MEDIA SIMPLES ##################
    
    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['amortvl_m'], df_aux['captvl_m'],  df_aux['resgvl_m'],df_aux['resgsolvl_m'],alpha=.6)          
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['Amoritzação','Captção','Resgate','Resgate Solicitado'], loc='center left')
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='best')

    fig.suptitle("Movimentações Realizadas no Fundo\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Movimentações Realizadas no mês - Media Simples.png') 
    plt.show()  
         
    
    
    
    
    ################################### SET DATABASE TO PLOT 9A ###################################
    

            
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    rent_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO','TAB_X_VL_RENTAB_MES'] 
    
    df_rent = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*rent_columnlist]].dropna() 
    df_rent = df_rent[~((df_rent['TAB_X_VL_RENTAB_MES']>40) | (df_rent['TAB_X_VL_RENTAB_MES']<-15))]
    
  # Retirar OUTLIERS QUE PUXAM MUITO A MEDIA
    df_rent = df_rent[~((df_rent['TAB_IV_B_VL_PL_MEDIO']>1e10) & (df_rent['TAB_X_VL_RENTAB_MES']<-5))]
    df_rent = df_rent[~((df_rent['TAB_IV_B_VL_PL_MEDIO']>1e9) & (df_rent['TAB_X_VL_RENTAB_MES']>20))]
    

     # todas_series_mensais_ativas = todas_series_mensais_ativas[(todas_series_mensais_ativas['SERIES STATUS']=='A')]    
    # a=todas_series_mensais_ativas[todas_series_mensais_ativas.NAME.str.contains('Selic')]    

    df_rent = df_rent.groupby(['Data','Rating_AUX']).agg(RENT_MES_m =("TAB_X_VL_RENTAB_MES", "mean"),
                                                        RENT_MES_mw=("TAB_X_VL_RENTAB_MES", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    ipeaseries_dict={
                    'PRECOS12_IPCAG12':'IPCA_MENSAL',
                    'PAN12_IPCAG12':'IPCA_MENSAL_ANUALIZADO',
                    'PRECOS12_INPCBR12':'INPC_MENSAL',
                    'BM12_TJOVER12':'SELIC_MENSAL',
                    'PAN12_TJOVER12':'SELIC_MENSAL_ANUALIZADO'
                    }
    
    for serie in ipeaseries_dict.items():
        #print(serie)
        
        serie_df=ipea.timeseries(serie[0])        
        serie_df['data']=pd.to_datetime(serie_df['DATE'],utc=True).apply(lambda d: d.replace(hour=0, minute=0, second=0,tzinfo=None))  
        serie_df=serie_df.drop_duplicates()     
        serie_df=serie_df.rename(columns={serie_df.columns[-2]:serie[1] })
        serie_df=serie_df.iloc[:,[-2,-1]]
        
        df_rent = pd.merge(df_rent, serie_df, left_on='Data', right_on='data', how='left')
        df_rent = df_rent.drop('data', axis=1)
        
     
        #ANUALIZAR RENTABILIDADE
    df_rent['RENT_MENSAL_ANUALIZADA_m']=(((1+df_rent['RENT_MES_m']/100)**(12))-1)*100    
    df_rent['RENT_MENSAL_ANUALIZADA_mw']=(((1+df_rent['RENT_MES_mw']/100)**(12))-1)*100    
    df_rent['INPC_MENSAL_ANUALIZADO']=(((1+df_rent['INPC_MENSAL']/100)**(12))-1)*100  

    df_rent['RENTREAL_MENSAL_ANUALIZADA_m']=((1+df_rent['RENT_MES_m'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['RENTREAL_MENSAL_ANUALIZADA_mw']=((1+df_rent['RENT_MES_mw'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_rent[df_rent['Rating_AUX']=='AAA'],
                  'AA+':df_rent[df_rent['Rating_AUX']=='AA+'],
                  'AA': df_rent[df_rent['Rating_AUX']=='AA'],
                  'AA-':df_rent[df_rent['Rating_AUX']=='AA-']
                  }
        
    
    ################################### PLOT 9A ###################################
    
    ############# MEDIA Ponderada ##################    
    ############# RENTABILDIADE NOMINAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_mw'])
        ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade','IPCA','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média das Cotas Sêniores\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Seniores - Media Ponderada.png') 
    plt.show()
    
    
    ############# RENTABILDIADE REAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_mw'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade Real','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Real Média das Cotas Sêniores\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Real Seniores - Media Ponderada.png') 
    plt.show()
    
    
    
    
   ############# MEDIA SIMPLES ##################    
    ############# RENTABILDIADE NOMINAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_m'])
        ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade','IPCA','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média das Cotas Sêniores\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Seniores - Media Simples.png') 
    plt.show()
    
    
    ############# RENTABILDIADE REAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_m'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade Real','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Real Média das Cotas Sêniores\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Real Seniores - Media Simples.png') 
    plt.show()
    
    
    
    
    ################################### SET DATABASE TO PLOT 9B ###################################

    
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    rent_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO','TAB_X_VL_RENTAB_MES'] 
    
    df_rent_sub = fidcs_rating_sub[(fidcs_rating_sub['Data']>=fitler_date1) & (fidcs_rating_sub['Data']<=fitler_date2)][[*rent_columnlist]].dropna()  
    df_rent_sub = df_rent_sub[~((df_rent_sub['TAB_X_VL_RENTAB_MES']>40) | (df_rent_sub['TAB_X_VL_RENTAB_MES']<-15))]


    #Retirar OUTLIERS QUE PUXAM MUITO A MEDIA
    df_rent_sub = df_rent_sub[~((df_rent_sub['TAB_IV_B_VL_PL_MEDIO']>1e10) & (df_rent_sub['TAB_X_VL_RENTAB_MES']<-5))]
    df_rent_sub = df_rent_sub[~((df_rent_sub['TAB_IV_B_VL_PL_MEDIO']>1e9) & (df_rent_sub['TAB_X_VL_RENTAB_MES']>20))]



     # todas_series_mensais_ativas = todas_series_mensais_ativas[(todas_series_mensais_ativas['SERIES STATUS']=='A')]    
    # a=todas_series_mensais_ativas[todas_series_mensais_ativas.NAME.str.contains('Selic')]    

    df_rent_sub= df_rent_sub.groupby(['Data','Rating_AUX']).agg(RENT_MES_m =("TAB_X_VL_RENTAB_MES", "mean"),
                                                                RENT_MES_mw=("TAB_X_VL_RENTAB_MES", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                                                n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                                ).reset_index()

    ipeaseries_dict={
                    'PRECOS12_IPCAG12':'IPCA_MENSAL',
                    'PAN12_IPCAG12':'IPCA_MENSAL_ANUALIZADO',
                    'PRECOS12_INPCBR12':'INPC_MENSAL',
                    'BM12_TJOVER12':'SELIC_MENSAL',
                    'PAN12_TJOVER12':'SELIC_MENSAL_ANUALIZADO'
                    }
    
    for serie in ipeaseries_dict.items():
        #print(serie)
        
        serie_df=ipea.timeseries(serie[0])        
        serie_df['data']=pd.to_datetime(serie_df['DATE'],utc=True).apply(lambda d: d.replace(hour=0, minute=0, second=0,tzinfo=None))  
        serie_df=serie_df.drop_duplicates()     
        serie_df=serie_df.rename(columns={serie_df.columns[-2]:serie[1] })
        serie_df=serie_df.iloc[:,[-2,-1]]
        
        df_rent_sub = pd.merge(df_rent_sub, serie_df, left_on='Data', right_on='data', how='left')
        df_rent_sub = df_rent_sub.drop('data', axis=1)
        
     
        #ANUALIZAR RENTABILIDADE
    df_rent_sub['RENT_MENSAL_ANUALIZADA_m']=(((1+df_rent_sub['RENT_MES_m']/100)**(12))-1)*100    
    df_rent_sub['RENT_MENSAL_ANUALIZADA_mw']=(((1+df_rent_sub['RENT_MES_mw']/100)**(12))-1)*100    
    df_rent_sub['INPC_MENSAL_ANUALIZADO']=(((1+df_rent_sub['INPC_MENSAL']/100)**(12))-1)*100  

    df_rent_sub['RENTREAL_MENSAL_ANUALIZADA_m']=((1+df_rent_sub['RENT_MES_m'])/(1+df_rent_sub['IPCA_MENSAL']/100))#*100    
    df_rent_sub['RENTREAL_MENSAL_ANUALIZADA_mw']=((1+df_rent_sub['RENT_MES_mw'])/(1+df_rent_sub['IPCA_MENSAL']/100))#*100    
    

    baseline=['AAA','AA+','AA','AA-']
    dict_ativo = {'AAA':df_rent_sub[df_rent_sub['Rating_AUX']=='AAA'],
                  'AA+':df_rent_sub[df_rent_sub['Rating_AUX']=='AA+'],
                  'AA': df_rent_sub[df_rent_sub['Rating_AUX']=='AA'],
                  'AA-':df_rent_sub[df_rent_sub['Rating_AUX']=='AA-']
                  }
    
    
    
    
    
    
    ################################### PLOT 9B ###################################

    ############# MEDIA Ponderada ##################    
    ############# RENTABILDIADE NOMINAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_mw'])
        ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade','IPCA','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média das Cotas Subordinadas\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Subordinadas - Media Ponderada.png') 
    plt.show()
    
    
    ############# RENTABILDIADE REAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_mw'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade Real','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Real Média das Cotas Subordinadas\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Real Subordinadas - Media Ponderada.png') 
    plt.show()
    
    
    
    
   ############# MEDIA SIMPLES ##################    
    ############# RENTABILDIADE NOMINAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_m'])
        ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade','IPCA','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média das Cotas Subordinadas\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Subordinadas - Media Simples.png') 
    plt.show()
    
    
    ############# RENTABILDIADE REAL ##################

    fig,axes = plt.subplots(nrows = 4, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_m'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Rentabilidade Real','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Real Média das Cotas Subordinadas\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Real Subordinadas - Media Simples.png') 
    plt.show()


    
         
    ################################### SET DATABASE TO PLOT 10 ###################################
    
    
        
        
        
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    liq_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                          'TAB_X_VL_LIQUIDEZ_0','TAB_X_VL_LIQUIDEZ_30','TAB_X_VL_LIQUIDEZ_60','TAB_X_VL_LIQUIDEZ_90',
                          'TAB_X_VL_LIQUIDEZ_180','TAB_X_VL_LIQUIDEZ_360','TAB_X_VL_LIQUIDEZ_MAIOR_360']
 
    
    df_liq= fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*liq_columnlist]].dropna()

    
 
    df_liq = df_liq.groupby(['Data','Rating_AUX']).agg( liq0_m =("TAB_X_VL_LIQUIDEZ_0", "mean"),
                                                        liq0_wm=("TAB_X_VL_LIQUIDEZ_0", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq30_m =("TAB_X_VL_LIQUIDEZ_30", "mean"),
                                                        liq30_wm=("TAB_X_VL_LIQUIDEZ_30", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq60_m =("TAB_X_VL_LIQUIDEZ_60", "mean"),
                                                        liq60_wm=("TAB_X_VL_LIQUIDEZ_60", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq90_m =("TAB_X_VL_LIQUIDEZ_90", "mean"),
                                                        liq90_wm=("TAB_X_VL_LIQUIDEZ_90", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq180_m =("TAB_X_VL_LIQUIDEZ_180", "mean"),
                                                        liq180_wm=("TAB_X_VL_LIQUIDEZ_180", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq360_m =("TAB_X_VL_LIQUIDEZ_360", "mean"),  
                                                        liq360_wm=("TAB_X_VL_LIQUIDEZ_360", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq360m_m =("TAB_X_VL_LIQUIDEZ_MAIOR_360", "mean"),                                                        
                                                        liq360m_wm=("TAB_X_VL_LIQUIDEZ_MAIOR_360", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    
    df_liq[df_liq.select_dtypes(include=np.number).columns.tolist()]=df_liq.select_dtypes(include=np.number)/1000000
    df_liq['n']=df_liq['n']*1000000

    # baseline=['AAA','AA+','AA','AA-']
    baseline=['AAA','AA+','AA']
    dict_ativo = {'AAA':df_liq[df_liq['Rating_AUX']=='AAA'],
                  'AA+':df_liq[df_liq['Rating_AUX']=='AA+'],
                  'AA':df_liq[df_liq['Rating_AUX']=='AA'],
                  #'AA-':df_liq[df_liq['Rating_AUX']=='AA-']
                  }

    
    ################################### PLOT 10 ###################################
    
    ############# MEDIA PONDERADA ##################

    
    fig,axes = plt.subplots(nrows = 3, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['liq0_wm'], df_aux['liq30_wm'],  df_aux['liq60_wm'],df_aux['liq90_wm'],
                     df_aux['liq180_wm'],df_aux['liq360_wm'], df_aux['liq360m_wm'], alpha=.6)          
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['Liquidez Imediata','Até 30 dias', 'Até 60 dias','Até 90 dias','Até 180 dias','Até 360 dias','Mais de 360 dias' ], loc='center left')
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='best')

    fig.suptitle("Liquidez Média dos Fundos\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Liquidez - Media Ponderada.png') 
    plt.show()  

    ############# MEDIA SIMPLES ##################

    fig,axes = plt.subplots(nrows = 3, sharex=True,  figsize=(8, 8))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.stackplot(df_aux['Data'], df_aux['liq0_m'], df_aux['liq30_m'],  df_aux['liq60_m'],df_aux['liq90_m'],
                     df_aux['liq180_m'],df_aux['liq360_m'], df_aux['liq360m_m'], alpha=.6)          
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['A Pagar - Curto Prazo','A Pagar - Longo Prazo','Posições em Derivativos'], loc='best')
    fig.legend(labels=['Liquidez Imediata','Até 30 dias', 'Até 60 dias','Até 90 dias','Até 180 dias','Até 360 dias','Mais de 360 dias' ], loc='center left')
    #fig.legend(labels=['DR c/ Risco','DR s/ Risco','C/ Parcelas Adimplentes','C/ Parcelas Inadimplentes','Inadimplentes'], loc='best')

    fig.suptitle("Liquidez Média dos Fundos\n (em R$ milhões)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Liquidez - Media Simples.png') 
    plt.show()  
  
    return 'Plots Feitos!'



















def analyze_fidcs2(df_fidc_senior,df_fidc ,df_rating_final, fitler_date0, fitler_date1, fitler_date2):
    
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Plots')
    
    
    print('Agregando as duas bases')
    df_fidc_agg = df_fidc_senior.merge(df_rating_final,how='left',on='CNPJ_FUNDO')
    
    fidcs_rating_rent = df_fidc_agg[~pd.isnull(df_fidc_agg['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    #fidcs_wrating= df_fidc_agg[pd.isnull(df_fidc_agg['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    
    fidcs_rating_rent['TAB_X_CLASSE_SERIE'] = fidcs_rating_rent['TAB_X_CLASSE_SERIE'].replace(to_replace=['Classe Sénior|Sênior'], value='Série', regex=True)
    fidcs_rating_rent = fidcs_rating_rent.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])
    

    fidcs_rating = fidcs_rating_rent[~fidcs_rating_rent['Rating_AUX'].isin(['A+','A','A-'])]



    print('Agregando com a base de cotas Subordinadas')

    df_fidcs_sub = df_fidc[(df_fidc['CNPJ_FUNDO'].isin(fidcs_rating_rent['CNPJ_FUNDO'].unique().tolist())) & (df_fidc['TAB_X_CLASSE_SERIE_AUX']=='Subordinada')]
    
    df_fidc_agg_sub = df_fidcs_sub.merge(df_rating_final,how='left',on='CNPJ_FUNDO')
    
    fidcs_rating_sub = df_fidc_agg_sub[~pd.isnull(df_fidc_agg_sub['Rating'])]#['DENOM_SOCIAL'].unique().tolist()
    fidcs_rating_sub = fidcs_rating_sub.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])

    
    #CHECK COTAS DE FUNDOS 
    
    # fidc_dict={}
    # for cnpj in fidcs_rating['CNPJ_FUNDO'].unique():
    #     df_aux=fidcs_rating[fidcs_rating['CNPJ_FUNDO']==cnpj] 

    #     fidc_dict[cnpj]={}
    #     for serie in df_aux['TAB_X_CLASSE_SERIE'].unique():
            
    #         df_aux2 = df_aux[df_aux['TAB_X_CLASSE_SERIE']==serie][['CNPJ_FUNDO','DENOM_SOCIAL','TAB_X_CLASSE_SERIE','Data','TAB_I1_VL_DISP','TAB_I2_VL_CARTEIRA','TAB_I3_VL_POSICAO_DERIV','TAB_I4_VL_OUTRO_ATIVO' ]]
            
    #         fidc_dict[cnpj].update({serie:df_aux2})
            

    # a=fidc_dict['08.315.045/0001-67']['Série 1']
    # b=fidc_dict['08.315.045/0001-67']['Série 2']


        

    
    ################################### SET DATABASE TO PLOT 1 ###################################
    # VERIFICANTO COMO ESTAO OS ATIVOS  (Ativos estao muito concentrados na Carteira - pouca disp, derivativos, e outros)
    
    
    #VERIFICANDO COMO ESTAO OS ATIVOS DA CARTEIRA
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')


    carteira_columnlist = ['Data','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_I2A_VL_DIRCRED_RISCO','TAB_I2B_VL_DIRCRED_SEM_RISCO',
                             'TAB_I2C_VL_VLMOB','TAB_I2D_VL_TITPUB_FED','TAB_I2E_VL_CDB','TAB_I2F_VL_OPER_COMPROM','TAB_I2G_VL_OUTRO_RF',
                             'TAB_I2H_VL_COTA_FIDC','TAB_I2I_VL_COTA_FIDC_NP','TAB_I2J_VL_CONTRATO_FUTURO' ,'TAB_IV_B_VL_PL_MEDIO', 'TAB_IV_A_VL_PL']
    
                
    df_carteira = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*carteira_columnlist]].dropna()
    df_carteira=df_carteira.drop_duplicates()

    
 
    # df_carteira.isna().any()    
    # df_carteira[pd.isnull(df_carteira['TAB_IV_B_VL_PL_MEDIO'])]
    # df_carteira.loc[:, df_carteira.isna().any()]
    
    
    # % DO PL
    #df_carteira[df_carteira.select_dtypes(include=np.number).columns.tolist()]=df_carteira.select_dtypes(include=np.number).div(df_carteira['TAB_IV_A_VL_PL'], axis=0)
    # df_carteira[df_carteira.select_dtypes(include=np.number).columns.tolist()]=df_carteira.select_dtypes(include=np.number).div(df_carteira['TAB_I_VL_ATIVO'], axis=0).dropna()
    
    #EM R$ MILHOES
    df_carteira[df_carteira.select_dtypes(include=np.number).columns.tolist()]=df_carteira.select_dtypes(include=np.number)/1000000
    

    df_carteira=df_carteira.dropna()
    df_carteira = df_carteira.groupby(['Data']).agg(DRr_m =("TAB_I2A_VL_DIRCRED_RISCO", "mean"),
                                                    DRr_wm=("TAB_I2A_VL_DIRCRED_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    DRsr_m =("TAB_I2B_VL_DIRCRED_SEM_RISCO", "mean"),
                                                    DRsr_wm=("TAB_I2B_VL_DIRCRED_SEM_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    VM_m =("TAB_I2C_VL_VLMOB", "mean"),
                                                    VM_wm=("TAB_I2C_VL_VLMOB", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    TPF_m =("TAB_I2D_VL_TITPUB_FED", "mean"),
                                                    TPF_wm=("TAB_I2D_VL_TITPUB_FED", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    CDB_m =("TAB_I2E_VL_CDB", "mean"),
                                                    CDB_wm=("TAB_I2E_VL_CDB", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    OPCM_m =("TAB_I2F_VL_OPER_COMPROM", "mean"),
                                                    OPCM_wm=("TAB_I2F_VL_OPER_COMPROM", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    ORF_m =("TAB_I2G_VL_OUTRO_RF", "mean"),
                                                    ORF_wm=("TAB_I2G_VL_OUTRO_RF", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    COTAFIDC_m =("TAB_I2H_VL_COTA_FIDC", "mean"),
                                                    COTAFIDC_wm=("TAB_I2H_VL_COTA_FIDC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    COTAFIDCNP_m =("TAB_I2I_VL_COTA_FIDC_NP", "mean"),
                                                    COTAFIDCNP_wm=("TAB_I2I_VL_COTA_FIDC_NP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    FUT_m =("TAB_I2J_VL_CONTRATO_FUTURO", "mean"),
                                                    FUT_wm=("TAB_I2J_VL_CONTRATO_FUTURO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                    n=("TAB_I2A_VL_DIRCRED_RISCO",'size')
                                                    ).reset_index()

    
    df_carteira['DR_m']=df_carteira['DRr_m']+df_carteira['DRsr_m']
    df_carteira['DR_wm']=df_carteira['DRr_wm']+df_carteira['DRsr_wm']

    #CHECK WM

    # c = df_carteira   
    # c['X'] = c['TAB_I2A_VL_DIRCRED_RISCO'] * c['TAB_IV_B_VL_PL_MEDIO']
    # c=c.groupby(['Data', 'Rating_AUX'])[['TAB_I2A_VL_DIRCRED_RISCO','X','TAB_IV_B_VL_PL_MEDIO']].sum()
    # c['XX']=c['X']/c['TAB_IV_B_VL_PL_MEDIO']
    
    

   
    

    
    ################################################# PLOT 1 ###############################################

    ############# MEDIA PONDERADA ##################

    
    plt.stackplot(df_carteira['Data'],
                  df_carteira['DR_wm'], df_carteira['VM_wm'],df_carteira['TPF_wm'],df_carteira['CDB_wm'],
                  df_carteira['OPCM_wm'],df_carteira['ORF_wm'],df_carteira['COTAFIDC_wm'],df_carteira['COTAFIDCNP_wm'],df_carteira['FUT_wm'],
                  labels=['Direitos Creditórios','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'])
    plt.legend(loc='upper left')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    
    plt.title('Carteira Média dos FIDCS')
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1, borderaxespad=0)

    plt.xticks(rotation=30)
    plt.savefig('Ativo - Carteira FIDC - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()
        
  
    ############# MEDIA SIMPLES ##################

  
    plt.stackplot( df_carteira['Data'],
                  df_carteira['DR_m'], df_carteira['VM_m'],df_carteira['TPF_m'],df_carteira['CDB_m'],
                  df_carteira['OPCM_m'],df_carteira['ORF_m'],df_carteira['COTAFIDC_m'],df_carteira['COTAFIDCNP_m'],df_carteira['FUT_m'],
                  labels=['Direitos Creditórios','Valores Mob.','TPF','CDB','Op. Compromissada','Outros Ativos','Cota FIDC','Cot FIDC NP','Cont Futuro'])
    plt.legend(loc='upper left')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    
    plt.title('Carteira Média dos FIDCS')
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
    plt.savefig('Ativo - Carteira FIDC - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()


    
    ################################### SET DATABASE TO PLOT 2 ###################################
    #EXPLODIR CARTEIRA
    
    # fitler_date0 = np.datetime64('2019-11-01')
    # fitler_date2 = np.datetime64('2020-04-01')


                   
    dr_columnlist=['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_IV_B_VL_PL_MEDIO', 
                   #TABELA 1
                   'TAB_I2A_VL_DIRCRED_RISCO','TAB_I2A1_VL_CRED_VENC_AD','TAB_I2A2_VL_CRED_VENC_INAD',
                   'TAB_I2A21_VL_TOTAL_PARCELA_INAD','TAB_I2A3_VL_CRED_INAD','TAB_I2A4_VL_CRED_DIRCRED_PERFM',
                    'TAB_I2A5_VL_CRED_VENCIDO_PENDENTE','TAB_I2A6_VL_CRED_EMP_RECUP','TAB_I2A7_VL_CRED_RECEITA_PUBLICA',
                    'TAB_I2A8_VL_CRED_ACAO_JUDIC','TAB_I2A9_VL_CRED_FATOR_RISCO','TAB_I2A10_VL_CRED_DIVERSO','TAB_I2A11_VL_REDUCAO_RECUP', 
                    #TABELA 2
                    'TAB_I2B_VL_DIRCRED_SEM_RISCO','TAB_I2B1_VL_CRED_VENC_AD','TAB_I2B2_VL_CRED_VENC_INAD',
                    'TAB_I2B21_VL_TOTAL_PARCELA_INAD','TAB_I2B3_VL_CRED_INAD','TAB_I2B4_VL_CRED_DIRCRED_PERFM',
                    'TAB_I2B5_VL_CRED_VENCIDO_PENDENTE','TAB_I2B6_VL_CRED_EMP_RECUP','TAB_I2B7_VL_CRED_RECEITA_PUBLICA',
                    'TAB_I2B8_VL_CRED_ACAO_JUDIC','TAB_I2B9_VL_CRED_FATOR_RISCO','TAB_I2B10_VL_CRED_DIVERSO','TAB_I2B11_VL_REDUCAO_RECUP']
                 
    # df_dr = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*dr_columnlist]].dropna(subset=['TAB_IV_B_VL_PL_MEDIO'])
    # df_dr=df_dr.fillna(0)

    df_dr = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*dr_columnlist]].dropna()
    df_dr=df_dr.drop_duplicates()


    df_dr['TAB_VL_DIRCRED'] = df_dr['TAB_I2A_VL_DIRCRED_RISCO']+df_dr['TAB_I2B_VL_DIRCRED_SEM_RISCO'] 
    df_dr['TAB_VL_CRED_VENC_AD'] = df_dr['TAB_I2A1_VL_CRED_VENC_AD']+df_dr['TAB_I2B1_VL_CRED_VENC_AD'] 
    df_dr['TAB_VL_CRED_VENC_INAD'] = df_dr['TAB_I2A2_VL_CRED_VENC_INAD']+df_dr['TAB_I2B2_VL_CRED_VENC_INAD'] 
    df_dr['TAB_VL_TOTAL_PARCELA_INAD'] = df_dr['TAB_I2A21_VL_TOTAL_PARCELA_INAD']+df_dr['TAB_I2B21_VL_TOTAL_PARCELA_INAD'] 
    df_dr['TAB_VL_CRED_INAD'] = df_dr['TAB_I2A3_VL_CRED_INAD']+df_dr['TAB_I2B3_VL_CRED_INAD'] 
    df_dr['TAB_VL_CRED_DIRCRED_PERFM'] = df_dr['TAB_I2A4_VL_CRED_DIRCRED_PERFM']+df_dr['TAB_I2B4_VL_CRED_DIRCRED_PERFM'] 
    df_dr['TAB_VL_CRED_VENCIDO_PENDENTE'] = df_dr['TAB_I2A5_VL_CRED_VENCIDO_PENDENTE']+df_dr['TAB_I2B5_VL_CRED_VENCIDO_PENDENTE'] 
    df_dr['TAB_VL_CRED_EMP_RECUP'] = df_dr['TAB_I2A6_VL_CRED_EMP_RECUP']+df_dr['TAB_I2B6_VL_CRED_EMP_RECUP'] 
    df_dr['TAB_VL_CRED_RECEITA_PUBLICA'] = df_dr['TAB_I2A7_VL_CRED_RECEITA_PUBLICA']+df_dr['TAB_I2B7_VL_CRED_RECEITA_PUBLICA'] 
    df_dr['TAB_VL_CRED_ACAO_JUDIC'] = df_dr['TAB_I2A8_VL_CRED_ACAO_JUDIC']+df_dr['TAB_I2B8_VL_CRED_ACAO_JUDIC'] 
    df_dr['TAB_VL_CRED_FATOR_RISCO'] = df_dr['TAB_I2A9_VL_CRED_FATOR_RISCO']+df_dr['TAB_I2B9_VL_CRED_FATOR_RISCO'] 
    df_dr['TAB_VL_CRED_DIVERSO'] = df_dr['TAB_I2A10_VL_CRED_DIVERSO']+df_dr['TAB_I2B10_VL_CRED_DIVERSO'] 
    df_dr['TAB_VL_REDUCAO_RECUP'] = df_dr['TAB_I2A11_VL_REDUCAO_RECUP']+df_dr['TAB_I2B11_VL_REDUCAO_RECUP'] 


  # % DO PL
    #df_dr[df_dr.select_dtypes(include=np.number).columns.tolist()]=df_dr.select_dtypes(include=np.number).div(df_dr['TAB_IV_A_VL_PL'], axis=0)
    # df_dr[df_dr.select_dtypes(include=np.number).columns.tolist()]=df_dr.select_dtypes(include=np.number).div(df_dr['TAB_I_VL_ATIVO'], axis=0).dropna()
    
    #EM R$ MILHOES
    df_dr[df_dr.select_dtypes(include=np.number).columns.tolist()]=df_dr.select_dtypes(include=np.number)/1000000
  
    
  
    
    # df_dr1['Total']=df_dr1[['TAB_I2A1_VL_CRED_VENC_AD','TAB_I2A2_VL_CRED_VENC_INAD','TAB_I2A3_VL_CRED_INAD','TAB_I2A4_VL_CRED_DIRCRED_PERFM',
    #                         'TAB_I2A5_VL_CRED_VENCIDO_PENDENTE','TAB_I2A6_VL_CRED_EMP_RECUP','TAB_I2A7_VL_CRED_RECEITA_PUBLICA',
    #                         'TAB_I2A8_VL_CRED_ACAO_JUDIC','TAB_I2A9_VL_CRED_FATOR_RISCO','TAB_I2A10_VL_CRED_DIVERSO', 'TAB_I2A11_VL_REDUCAO_RECUP']].sum(axis = 1, skipna = True) #- df_dr1['TAB_I2A11_VL_REDUCAO_RECUP']

    # a=df_dr1[['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_I2A_VL_DIRCRED_RISCO','Total']]
    # df_dr1['diff']=df_dr1['Total']- df_dr1['TAB_I2A_VL_DIRCRED_RISCO']
    # df_dr1=df_dr1.round(5)



    df_dr = df_dr.groupby(['Data']).agg(DRva_m =("TAB_VL_CRED_VENC_AD", "mean"),
                                        DRva_wm=("TAB_VL_CRED_VENC_AD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRvi_m =("TAB_VL_CRED_VENC_INAD", "mean"),
                                        DRvi_wm=("TAB_VL_CRED_VENC_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRdi_m =("TAB_VL_CRED_INAD", "mean"),
                                        DRdi_wm=("TAB_VL_CRED_INAD", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRper_m =("TAB_VL_CRED_DIRCRED_PERFM", "mean"),
                                        DRper_wm=("TAB_VL_CRED_DIRCRED_PERFM", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRvp_m =("TAB_VL_CRED_VENCIDO_PENDENTE", "mean"),
                                        DRvp_wm=("TAB_VL_CRED_VENCIDO_PENDENTE", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRrec_m =("TAB_VL_CRED_EMP_RECUP", "mean"),
                                        DRrec_wm=("TAB_VL_CRED_EMP_RECUP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRrp_m =("TAB_VL_CRED_RECEITA_PUBLICA", "mean"),
                                        DRrp_wm=("TAB_VL_CRED_RECEITA_PUBLICA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRaj_m =("TAB_VL_CRED_ACAO_JUDIC", "mean"),
                                        DRaj_wm=("TAB_VL_CRED_ACAO_JUDIC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRfr_m =("TAB_VL_CRED_FATOR_RISCO", "mean"),
                                        DRfr_wm=("TAB_VL_CRED_FATOR_RISCO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRdiv_m =("TAB_VL_CRED_DIVERSO", "mean"),
                                        DRdiv_wm=("TAB_VL_CRED_DIVERSO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        DRrj_m =("TAB_VL_REDUCAO_RECUP", "mean"),
                                        DRrj_wm=("TAB_VL_REDUCAO_RECUP", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        n=("TAB_VL_CRED_VENC_AD",'size')
                                        ).reset_index()


 
     
    ################################### PLOT 2A ###################################
    
    
    ############# MEDIA PONDERADA ##################
    

    
    plt.stackplot(df_dr['Data'], 
                  df_dr['DRva_wm'],  df_dr['DRvi_wm'], df_dr['DRdi_wm'],df_dr['DRper_wm'],df_dr['DRvp_wm'],
                  df_dr['DRrec_wm'],df_dr['DRrp_wm'],df_dr['DRaj_wm'],df_dr['DRfr_wm'],df_dr['DRdiv_wm'], df_dr['DRrj_wm'],
                  labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ',
                          'Receitas Públicas','Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'])
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    
    plt.title("Composição de Direitos Creditórios", fontsize=16)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
    # plt.ylim(2000,4000)
    plt.ylim(1500,4000)
    plt.savefig('Ativo - DR - Media Ponderada - Individual - 2.png', bbox_inches='tight') 
    plt.show()
    


    ############# MEDIA SIMPLES ##################
    
    plt.stackplot(df_dr['Data'], 
                  df_dr['DRva_m'],  df_dr['DRvi_m'], df_dr['DRdi_m'],df_dr['DRper_m'],df_dr['DRvp_m'],
                  df_dr['DRrec_m'],df_dr['DRrp_m'],df_dr['DRaj_m'],df_dr['DRfr_m'],df_dr['DRdiv_m'], df_dr['DRrj_m'],
                  labels=['Adimplentes','Parc.Inadimplentes','Inadimplentes','A Performar','Pendentes de Pgto','Empresa em RJ',
                          'Receitas Públicas','Cred. de RJ','Fator Preponderante de Risco','Outros Créditos','Provisão de Recuperação'])
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    
    plt.title("Composição de Direitos Creditórios", fontsize=16)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
    plt.savefig('Ativo - DR - Media Simples - Individual.png', bbox_inches='tight') 
    plt.show()
    
    
   
    
      
    
     ################################### SET DATABASE TO PLOT 2.2 ###################################

    #EXPLODIR CARTEIRA POR SETOR

    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    setor_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_IV_B_VL_PL_MEDIO', 'TAB_II_VL_CARTEIRA','TAB_II_A_VL_INDUST',
                      'TAB_II_B_VL_IMOBIL','TAB_II_C_VL_COMERC','TAB_II_D_VL_SERV','TAB_II_E_VL_AGRONEG','TAB_II_F_VL_FINANC',
                      'TAB_II_G_VL_CREDITO','TAB_II_H_VL_FACTOR','TAB_II_I_VL_SETOR_PUBLICO','TAB_II_J_VL_JUDICIAL','TAB_II_K_VL_MARCA']
 
    
    df_setor = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*setor_columnlist]].dropna()
    df_setor = df_setor.drop_duplicates()


    df_setor2 = fidcs_rating[(fidcs_rating['Data']==np.datetime64('2020-04-01'))][[*setor_columnlist]].dropna()
    df_setor2 = df_setor2.drop_duplicates()


    df_setor2 = df_setor2.drop(['Data', 'Rating_AUX','TAB_IV_B_VL_PL_MEDIO', 'TAB_II_VL_CARTEIRA'], axis=1).melt(['DENOM_SOCIAL', 'CNPJ_FUNDO'], var_name='Setor', value_name='Valor')

  # % DO PL
    #df_setor[df_setor.select_dtypes(include=np.number).columns.tolist()]=df_setor.select_dtypes(include=np.number).div(df_setor['TAB_IV_A_VL_PL'], axis=0)
    # df_setor[df_setor.select_dtypes(include=np.number).columns.tolist()]=df_setor.select_dtypes(include=np.number).div(df_setor['TAB_I_VL_ATIVO'], axis=0).dropna()
    
    #EM R$ MILHOES
    df_setor[df_setor.select_dtypes(include=np.number).columns.tolist()]=df_setor.select_dtypes(include=np.number)/1000000
    df_setor2[df_setor2.select_dtypes(include=np.number).columns.tolist()]=df_setor2.select_dtypes(include=np.number)/1000000

    #CRIAR COLUNA SETOR E COLOCAR NO GROUPBY


    # df_setor['Total']=df_setor[['TAB_II_A_VL_INDUST','TAB_II_B_VL_IMOBIL','TAB_II_C_VL_COMERC','TAB_II_D_VL_SERV','TAB_II_E_VL_AGRONEG','TAB_II_F_VL_FINANC',
    #                             'TAB_II_G_VL_CREDITO','TAB_II_H_VL_FACTOR','TAB_II_I_VL_SETOR_PUBLICO','TAB_II_J_VL_JUDICIAL','TAB_II_K_VL_MARCA']].sum(axis = 1, skipna = True) 
    # df_setor['diff']=df_setor['Total']-df_setor['TAB_II_VL_CARTEIRA']

    
    # df_setor.isna().any()    
    # #df_setor[pd.isnull(df_setor)]
    # df_setor.loc[:, df_setor.isna().any()]

    df_setor=df_setor.groupby(['Data']).agg(ind_m =("TAB_II_A_VL_INDUST", "mean"),
                                            ind_wm=("TAB_II_A_VL_INDUST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            imob_m =("TAB_II_B_VL_IMOBIL", "mean"),
                                            imob_wm=("TAB_II_B_VL_IMOBIL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            com_m =("TAB_II_C_VL_COMERC", "mean"),
                                            com_wm=("TAB_II_C_VL_COMERC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            serv_m =("TAB_II_D_VL_SERV", "mean"),
                                            serv_wm=("TAB_II_D_VL_SERV", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            agron_m =("TAB_II_E_VL_AGRONEG", "mean"),
                                            agron_wm=("TAB_II_E_VL_AGRONEG", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            fin_m =("TAB_II_F_VL_FINANC", "mean"),
                                            fin_wm=("TAB_II_F_VL_FINANC", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            cred_m =("TAB_II_G_VL_CREDITO", "mean"),
                                            cred_wm=("TAB_II_G_VL_CREDITO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            fact_m =("TAB_II_H_VL_FACTOR", "mean"),
                                            fact_wm=("TAB_II_H_VL_FACTOR", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            sp_m =("TAB_II_I_VL_SETOR_PUBLICO", "mean"),
                                            sp_wm=("TAB_II_I_VL_SETOR_PUBLICO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            jud_m =("TAB_II_J_VL_JUDICIAL", "mean"),
                                            jud_wm=("TAB_II_J_VL_JUDICIAL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            marca_m =("TAB_II_K_VL_MARCA", "mean"),
                                            marca_wm=("TAB_II_K_VL_MARCA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                            n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                            ).reset_index()

  
    df_setor2 = df_setor2.groupby(['Setor']).agg(ativo_setor =("Valor", "mean")).reset_index()
    df_setor2['Label']=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio',
                        'Financeiros','Cartão de Crédito','Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes']
    df_setor2['Explode']=0.1
        

    df_setor2=df_setor2[~(df_setor2['ativo_setor']==0)]

    ################################### PLOT 2.2 ###################################

    ############# MEDIA PONDERADA ##################


    #### STACK PLOT #######

    plt.stackplot(df_setor['Data'], df_setor['ind_wm'],  df_setor['imob_wm'], df_setor['com_wm'],df_setor['serv_wm'],df_setor['agron_wm'],
                  df_setor['fin_wm'],df_setor['cred_wm'],df_setor['fact_wm'],df_setor['sp_wm'],df_setor['jud_wm'], df_setor['marca_wm'],
                  labels=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio','Financeiros','Cartão de Crédito',
                       'Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes'],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Carteira de Ativos por Setor", fontsize=16)
    plt.savefig('Ativo - Setor - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()


    ########### PIE PLOT ############
    
  
    pal = sns.diverging_palette(255,130, l=60, n=len(df_setor2), center="dark")
    
    #PLOT1
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.pie(df_setor2['ativo_setor'],  labels =  df_setor2['Setor'], autopct='%1.1f%%',shadow=False, startangle=90, textprops={'color':"w"}, colors=pal)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.legend(df_setor2['Label'], loc='center left', bbox_to_anchor=(1, 0.5))
    plt.title("Ativo Médio Total por Setor\n Data: 04/2020")
    
    plt.savefig('Pie Plot por Setor.png', bbox_inches='tight') 
    plt.show()   



     ############# MEDIA SIMPLES ##################

 
    plt.stackplot(df_setor['Data'], df_setor['ind_m'],  df_setor['imob_m'], df_setor['com_m'],df_setor['serv_m'],df_setor['agron_m'],
                  df_setor['fin_m'],df_setor['cred_m'],df_setor['fact_m'],df_setor['sp_m'],df_setor['jud_m'], df_setor['marca_m'],
                  labels=['Industrial','Valores Imobiliários','Comercial','Serviços','Agronegócio','Financeiros','Cartão de Crédito',
                       'Factoring','Setor Público','Aõoes Judiciais','Marcas e Patentes'],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)

    plt.title("Carteira de Ativos por Setor", fontsize=16)
    plt.savefig('Ativo - Setor - Media Simples - Individual.png', bbox_inches='tight') 
    plt.show()
 

 



    
  

    ################################### SET DATABASE TO PLOT 4 ###################################
    
        # 106	TAB_IV_A_VL_PL
        # 107	TAB_IV_B_VL_PL_MEDIO
        

    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    pl_columnlist = ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO', 'TAB_IV_B_VL_PL_MEDIO','TAB_IV_A_VL_PL']
 
    
    df_pl = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*pl_columnlist]].dropna()
    df_pl = df_pl.drop_duplicates()


     # % DO PL
    #df_pl[df_pl.select_dtypes(include=np.number).columns.tolist()]=df_pl.select_dtypes(include=np.number).div(df_setor['TAB_IV_A_VL_PL'], axis=0)
    # df_pl[df_pl.select_dtypes(include=np.number).columns.tolist()]=df_pl.select_dtypes(include=np.number).div(df_setor['TAB_I_VL_ATIVO'], axis=0).dropna()
  

    df_pl[df_pl.select_dtypes(include=np.number).columns.tolist()]=df_pl.select_dtypes(include=np.number)/1000000


    # df_pl['Total'] = df_pl[['TAB_III_B1_VL_TERMO','TAB_III_B2_VL_OPCAO','TAB_III_B3_VL_FUTURO','TAB_III_B4_VL_SWAP_PAGAR']].sum(axis = 1, skipna = True) 
    # df_pl['diff'] = df_pl['Total']-df_pl['TAB_III_B_VL_POSICAO_DERIV']

    
    # df_pl.isna().any()    
    # #df_pl[pd.isnull(df_setor)]
    # df_pl.loc[:, df_pl.isna().any()]

    df_pl= df_pl.groupby(['Data']).agg( plm_m =("TAB_IV_B_VL_PL_MEDIO", "mean"),
                                        plm_wm=("TAB_IV_B_VL_PL_MEDIO", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        pl_m =("TAB_IV_A_VL_PL", "mean"),
                                        pl_wm=("TAB_IV_A_VL_PL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                        plm_s =("TAB_IV_B_VL_PL_MEDIO", "sum"),
                                        pl_s =("TAB_IV_A_VL_PL", "sum"),
                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                        ).reset_index()

    


    ################################### PLOT 4 ###################################
    ################################### MEDIA PONDERADA ###################################
    
    plt.plot(df_pl['Data'],df_pl['plm_wm'],label='PL médio')
    plt.plot(df_pl['Data'],df_pl['pl_wm'],label='PL')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("PL médio", fontsize=16)
    plt.savefig('PL - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()
    
    
    print('VL PL em 04/19',df_pl[df_pl['Data']==fitler_date1]['pl_wm'].item()*1000000)
    print('VL PL em 04/20',df_pl[df_pl['Data']== fitler_date2 - np.timedelta64(61,'D')]['pl_wm'].item()*1000000)


    
     ################################### MEDIA SIMPLES ###################################
   
    plt.plot(df_pl['Data'],df_pl['plm_m'],label='PL médio')
    plt.plot(df_pl['Data'],df_pl['pl_m'],label='PL')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("PL médio", fontsize=16)
    plt.savefig('PL - Media Simples - Individual.png', bbox_inches='tight') 
    plt.show()
    
    
         ################################### SOMA SIMPLES ###################################
   
    
   
    plt.plot(df_pl['Data'],df_pl['plm_s']/1000,label='PL médio')
    plt.plot(df_pl['Data'],df_pl['pl_s']/1000,label='PL')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ bilhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("PL Somado dos Fundos por Rating\n (em R$ milhões)", fontsize=16)
    plt.savefig('PL - Soma.png', bbox_inches='tight') 
    plt.show()
         
  
    
    
    
    ################################### SET DATABASE TO PLOT 6 ###################################
    


    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    oper_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                        #A)AQUISICOES
                        'TAB_VII_A1_1_QT_DIRCRED_RISCO','TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO','TAB_VII_A3_1_QT_DIRCRED_VENC_AD','TAB_VII_A4_1_QT_DIRCRED_VENC_INAD','TAB_VII_A5_1_QT_DIRCRED_INAD',
                        'TAB_VII_A1_2_VL_DIRCRED_RISCO','TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO','TAB_VII_A3_2_VL_DIRCRED_VENC_AD','TAB_VII_A4_2_VL_DIRCRED_VENC_INAD','TAB_VII_A5_2_VL_DIRCRED_INAD',
                        #B) ALIENACOES
                        'TAB_VII_B1_1_QT_CEDENTE','TAB_VII_B2_1_QT_PREST','TAB_VII_B3_1_QT_TERCEIRO',
                        'TAB_VII_B1_2_VL_CEDENTE','TAB_VII_B2_2_VL_PREST','TAB_VII_B3_2_VL_TERCEIRO',
                        'TAB_VII_B1_3_VL_CONTAB_CEDENTE','TAB_VII_B2_3_VL_CONTAB_PREST','TAB_VII_B3_3_VL_CONTAB_TERCEIRO',     
                        #C) SUBSTIITUICAO        
                        'TAB_VII_C_1_QT_SUBST',
                        'TAB_VII_C_2_VL_SUBST',
                        'TAB_VII_C_3_VL_CONTAB_SUBST',    
                        #D) RECOMPRA
                        'TAB_VII_D_1_QT_RECOMPRA',
                        'TAB_VII_D_2_VL_RECOMPRA',
                        'TAB_VII_D_3_VL_CONTAB_RECOMPRA']
 
    
    df_oper = fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*oper_columnlist]].dropna()
 
    df_oper = df_oper.drop_duplicates()

    
    df_oper['AQUIS_QT'] = df_oper[['TAB_VII_A1_1_QT_DIRCRED_RISCO','TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO','TAB_VII_A3_1_QT_DIRCRED_VENC_AD','TAB_VII_A4_1_QT_DIRCRED_VENC_INAD','TAB_VII_A5_1_QT_DIRCRED_INAD']].sum(axis = 1, skipna = True) 
    df_oper['AQUIS_VL'] = df_oper[['TAB_VII_A1_2_VL_DIRCRED_RISCO','TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO','TAB_VII_A3_2_VL_DIRCRED_VENC_AD','TAB_VII_A4_2_VL_DIRCRED_VENC_INAD','TAB_VII_A5_2_VL_DIRCRED_INAD',]].sum(axis = 1, skipna = True) 
    df_oper['ALIEN_QT'] = df_oper[['TAB_VII_B1_1_QT_CEDENTE','TAB_VII_B2_1_QT_PREST','TAB_VII_B3_1_QT_TERCEIRO',]].sum(axis = 1, skipna = True) 
    df_oper['ALIEN_VL'] = df_oper[['TAB_VII_B1_2_VL_CEDENTE','TAB_VII_B2_2_VL_PREST','TAB_VII_B3_2_VL_TERCEIRO']].sum(axis = 1, skipna = True) 
    df_oper['ALEIN_VLCONT'] = df_oper[['TAB_VII_B1_3_VL_CONTAB_CEDENTE','TAB_VII_B2_3_VL_CONTAB_PREST','TAB_VII_B3_3_VL_CONTAB_TERCEIRO']].sum(axis = 1, skipna = True) 


    # df_oper['Total']=df_oper[[ 'TAB_I2C1_VL_DEBENTURE','TAB_I2C2_VL_CRI','TAB_I2C3_VL_NP_COMERC','TAB_I2C4_VL_LETRA_FINANC',
    #                       'TAB_I2C5_VL_COTA_FUNDO_ICVM555','TAB_I2C6_VL_OUTRO']].sum(axis = 1, skipna = True) 
    # df_oper['diff']=df_oper['Total']-df_vm['TAB_I2C_VL_VLMOB']
    
    # df_oper.isna().any()    
    # df_oper[pd.isnull(df_vm)]
    # df_oper.loc[:, df_oper.isna().any()]
    
    
    # % DO PL
    #df_oper[df_oper.select_dtypes(include=np.number).columns.tolist()]=df_oper.select_dtypes(include=np.number).div(df_oper['TAB_IV_A_VL_PL'], axis=0)
    # df_oper[df_oper.select_dtypes(include=np.number).columns.tolist()]=df_oper.select_dtypes(include=np.number).div(df_oper['TAB_I_VL_ATIVO'], axis=0).dropna()
  
    
    df_oper[df_oper.select_dtypes(include=np.number).columns.tolist()]=df_oper.select_dtypes(include=np.number)/1000000


    df_oper=df_oper.groupby(['Data']).agg( aqqt_m =("AQUIS_QT", "mean"),
                                                        aqqt_wm=("AQUIS_QT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        aqvl_m =("AQUIS_VL", "mean"),
                                                        aqvl_wm=("AQUIS_VL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        aliqt_m =("ALIEN_QT", "mean"),
                                                        aliqt_wm=("ALIEN_QT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        alivl_m =("ALIEN_VL", "mean"),
                                                        alivl_wm=("ALIEN_VL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        subsqt_m =("TAB_VII_C_1_QT_SUBST", "mean"),
                                                        subsqt_wm=("TAB_VII_C_1_QT_SUBST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        subsvl_m =("TAB_VII_C_2_VL_SUBST", "mean"),                                                        
                                                        subsvl_wm=("TAB_VII_C_2_VL_SUBST", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        recqt_m =("TAB_VII_D_1_QT_RECOMPRA", "mean"),
                                                        recqt_wm=("TAB_VII_D_1_QT_RECOMPRA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        recvl_m =("TAB_VII_D_2_VL_RECOMPRA", "mean"),                                                        
                                                        recvl_wm=("TAB_VII_D_2_VL_RECOMPRA", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    

    
    print('Qtd recompra em 05/19', df_oper[df_oper['Data']==fitler_date1]['recqt_wm'].item()*1000000)
    print('Qtd recompra em 05/20',df_oper[df_oper['Data']== fitler_date2 - np.timedelta64(61,'D')]['recqt_wm'].item()*1000000)
    print('VL recompra em 05/19',df_oper[df_oper['Data']==fitler_date1]['recvl_wm'].item()*1000000)
    print('VL recompra em 05/20',df_oper[df_oper['Data']== fitler_date2 - np.timedelta64(61,'D')]['recvl_wm'].item()*1000000)


    
    ################################### PLOT 6 ###################################
    
    ############# MEDIA PONDERADA ##################

    plt.stackplot(df_oper['Data'], df_oper['aqvl_wm'], df_oper['alivl_wm'],  df_oper['subsvl_wm'],df_oper['recvl_wm'],
                  labels=['Aquisições','Alienações','Substituições','Recompras'],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Negcóios Realizados", fontsize=16)
    plt.savefig('Negocios Realizados- Agregado - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()     
    
    ############# MEDIA SIMPLES ##################

    
    plt.stackplot(df_oper['Data'], df_oper['aqvl_m'], df_oper['alivl_m'],  df_oper['subsvl_m'],df_oper['recvl_m'],
                  labels=['Aquisições','Alienações','Substituições','Recompras'],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Negcóios Realizados", fontsize=16)
    plt.savefig('Negocios Realizados- Agregado - Media Simples - Individual.png', bbox_inches='tight') 
    plt.show()  

         
        
         
    ################################### SET DATABASE TO PLOT 7 ###################################
    
    
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-05-01')

    cotas_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO','TAB_X_NR_COTST','TAB_X_QT_COTA','TAB_X_VL_COTA']
 
    
    df_cota = fidcs_rating_sub[(fidcs_rating_sub['Data']>=fitler_date1) & (fidcs_rating_sub['Data']<=fitler_date2)][[*cotas_columnlist]].dropna() 
    df_cota=df_cota[~(df_cota['TAB_X_QT_COTA']>1e10)]
    df_cota=df_cota[~(df_cota['TAB_X_VL_COTA']>1e8)]
    
    df_cota = df_cota.drop_duplicates()

    # df_cota.isna().any()    
    # df_cota[pd.isnull(df_vm)]
    # df_cota.loc[:, df_cota.isna().any()]

    df_cota=df_cota.groupby(['Data','Rating_AUX']).agg( ncot_m =("TAB_X_NR_COTST", "mean"),
                                                        ncot_wm=("TAB_X_NR_COTST", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        qtcota_m =("TAB_X_QT_COTA", "mean"),
                                                        qtcota_wm=("TAB_X_QT_COTA", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        vlcota_m =("TAB_X_VL_COTA", "mean"),
                                                        vlcota_wm=("TAB_X_VL_COTA", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    
    # df_cota[df_cota.select_dtypes(include=np.number).columns.tolist()]=df_cota.select_dtypes(include=np.number)/1000000
    # df_cota['n']=df_oper['n']*1000000
    
    df_cota['qtcota_m']=df_cota['qtcota_m']/1000000
    df_cota['qtcota_wm']=df_cota['qtcota_wm']/1000000


    
    baseline=['AAA','AA+','AA','AA-','A+', 'A', 'A-']
    dict_ativo = {'AAA':df_cota[df_cota['Rating_AUX']=='AAA'],
                  'AA+':df_cota[df_cota['Rating_AUX']=='AA+'],
                  'AA': df_cota[df_cota['Rating_AUX']=='AA'],
                  'AA-':df_cota[df_cota['Rating_AUX']=='AA-'],
                  'A+':df_cota[df_cota['Rating_AUX']=='A+'],
                  'A':df_cota[df_cota['Rating_AUX']=='A'],
                  'A-':df_cota[df_cota['Rating_AUX']=='A-']                  
                  }

 ################################### PLOT 7 ###################################
    
    
    ############# MEDIA PONDERADA ##################    

    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['ncot_wm'], label='N Cotista')
        ax.plot(df_aux['Data'],df_aux['qtcota_wm'], label='Qtd Cotas')

        # ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sub_mw'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['N Cotista','Qtd Cotas'], loc='center right')
    fig.suptitle("Numero Cotistas vs Qtd de Cotas (em milhão)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('N e Qtd Cota- Media Ponderada.png', bbox_inches='tight') 
    plt.show()
    
    
      
    ############# MEDIA SIMPLES ##################    

      ############# MEDIA PONDERADA ##################    

    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['ncot_m'], label='N Cotista')
        ax.plot(df_aux['Data'],df_aux['qtcota_m'], label='Qtd Cotas')

        # ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sub_mw'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['N Cotista','Qtd Cotas'], loc='center right')
    fig.suptitle("Numero Cotistas vs Qtd de Cotas (em milhão)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('N e Qtd Cotas- Media Simples.png', bbox_inches='tight') 
    plt.show()
    
    
    
    
    
    ############# MEDIA PONDERADA ##################    

    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['vlcota_wm'], label='Valor Cota')
        # ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sub_mw'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    fig.suptitle("Valor das Cotas", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('VL Cota - Media Ponderada.png', bbox_inches='tight') 
    plt.show()
    
    
      
    ############# MEDIA SIMPLES ##################    

    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['qtcota_m'], label='Qtd Cotas')
        # ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sub_mw'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
        fig.suptitle("Valor das Cotas", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('VL Cota - Media Simples.png', bbox_inches='tight') 
    plt.show()    
    
    
    
    
    

        
    ################################### SET DATABASE TO PLOT 8 ###################################
      

        
            
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    mov_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                          'TAB_X_VL_TOTAL_AMORT','TAB_X_VL_TOTAL_CAPT','TAB_X_VL_TOTAL_RESG','TAB_X_VL_TOTAL_RESGSOL',
                          'TAB_X_QT_TOTAL_AMORT','TAB_X_QT_TOTAL_CAPT','TAB_X_QT_TOTAL_RESG','TAB_X_QT_TOTAL_RESGSOL']
 
    
    df_mov= fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*mov_columnlist]].dropna()
    df_mov = df_mov.drop_duplicates()

    df_mov=df_mov[~(df_mov['TAB_X_VL_TOTAL_AMORT']>1e9)]

      # % DO PL
    #df_mov[df_mov.select_dtypes(include=np.number).columns.tolist()]=df_mov.select_dtypes(include=np.number).div(df_mov['TAB_IV_A_VL_PL'], axis=0)
    # df_mov[df_mov.select_dtypes(include=np.number).columns.tolist()]=df_mov.select_dtypes(include=np.number).div(df_mov['TAB_I_VL_ATIVO'], axis=0).dropna()
  
    
    df_mov[df_mov.select_dtypes(include=np.number).columns.tolist()]=df_mov.select_dtypes(include=np.number)/1000000

    df_mov = df_mov.groupby(['Data']).agg( amortqt_m =("TAB_X_QT_TOTAL_AMORT", "mean"),
                                                        amortqt_wm=("TAB_X_QT_TOTAL_AMORT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        amortvl_m =("TAB_X_VL_TOTAL_AMORT", "mean"),
                                                        amortvl_wm=("TAB_X_VL_TOTAL_AMORT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        captqt_m =("TAB_X_QT_TOTAL_CAPT", "mean"),
                                                        captqt_wm=("TAB_X_QT_TOTAL_CAPT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        captvl_m =("TAB_X_VL_TOTAL_CAPT", "mean"),
                                                        captvl_wm=("TAB_X_VL_TOTAL_CAPT", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgqt_m =("TAB_X_QT_TOTAL_RESG", "mean"),
                                                        resgqt_wm=("TAB_X_QT_TOTAL_RESG", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgvl_m =("TAB_X_VL_TOTAL_RESG", "mean"),                                                        
                                                        resgvl_wm=("TAB_X_VL_TOTAL_RESG", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgsolqt_m =("TAB_X_QT_TOTAL_RESGSOL", "mean"),
                                                        resgsolqt_wm=("TAB_X_QT_TOTAL_RESGSOL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        resgsolvl_m =("TAB_X_VL_TOTAL_RESGSOL", "mean"),                                                        
                                                        resgsolvl_wm=("TAB_X_VL_TOTAL_RESGSOL", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    

    ################################### PLOT 8 ###################################
    
    
    ############# MEDIA PONDERADA ##################
    
    
    
    plt.stackplot(df_mov['Data'], df_mov['amortvl_wm'], df_mov['captvl_wm'],  df_mov['resgvl_wm'],df_mov['resgsolvl_wm'],
                  labels=['Amoritzação','Captção','Resgate','Resgate Solicitado'],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Movimentações Realizadas no Fundo", fontsize=16)
    plt.savefig('Movimentações Realizadas no mês - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()  



    ############# MEDIA SIMPLES ##################
    
    plt.stackplot(df_mov['Data'], df_mov['amortvl_m'], df_mov['captvl_m'],  df_mov['resgvl_m'],df_mov['resgsolvl_m'],
                  labels=['Amoritzação','Captção','Resgate','Resgate Solicitado'],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Movimentações Realizadas no Fundo", fontsize=16)
    plt.savefig('Movimentações Realizadas no mês - Media Simple - Individual.png', bbox_inches='tight') 
    plt.show()   
         
    
    
    
    
    
    
    
    
    ################################### SET DATABASE TO PLOT 9A ###################################
    

            
    # fitler_date1 = np.datetime64('2019-04-01')
    # fitler_date2 = np.datetime64('2020-04-01')

    
    rent_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                         'TAB_X_VL_RENTAB_MES', 'TAB_X_PR_DESEMP_ESPERADO'] 
    
    df_rent = fidcs_rating_rent[(fidcs_rating_rent['Data']>=fitler_date1) & (fidcs_rating_rent['Data']<=fitler_date2)][[*rent_columnlist]].dropna()#subset=['TAB_IV_B_VL_PL_MEDIO','TAB_X_VL_RENTAB_MES']   
    df_rent = df_rent.drop_duplicates()

  
    df_rent = df_rent[((df_rent['TAB_X_VL_RENTAB_MES']<np.percentile(df_rent['TAB_X_VL_RENTAB_MES'], 99)) & 
                        (df_rent['TAB_X_VL_RENTAB_MES']>np.percentile(df_rent['TAB_X_VL_RENTAB_MES'], 5)))]

    df_rent = df_rent[((df_rent['TAB_X_PR_DESEMP_ESPERADO']<np.percentile(df_rent['TAB_X_PR_DESEMP_ESPERADO'], 99)) & 
                        (df_rent['TAB_X_PR_DESEMP_ESPERADO']>np.percentile(df_rent['TAB_X_PR_DESEMP_ESPERADO'], 5)))]


  # Retirar OUTLIERS QUE PUXAM MUITO A MEDIA
    # df_rent = df_rent[~((df_rent['TAB_X_VL_RENTAB_MES']>40) | (df_rent['TAB_X_VL_RENTAB_MES']<-15))]
  
    # df_rent = df_rent[~((df_rent['TAB_IV_B_VL_PL_MEDIO']>1e10) & (df_rent['TAB_X_VL_RENTAB_MES']<-5))]
    # df_rent = df_rent[~((df_rent['TAB_IV_B_VL_PL_MEDIO']>1e9) & (df_rent['TAB_X_VL_RENTAB_MES']>20))]
    
    
    
    df_rent2 = df_rent.groupby(['Data']).agg(RENT_MES_sen_m =("TAB_X_VL_RENTAB_MES", "mean"),
                                             RENT_MES_sen_mw=("TAB_X_VL_RENTAB_MES", weighted_mean(fidcs_rating_rent,"TAB_IV_B_VL_PL_MEDIO" )),
                                             BENCH_MES_sen_m =("TAB_X_PR_DESEMP_ESPERADO", "mean"),
                                             BENCH_MES_sen_mw=("TAB_X_PR_DESEMP_ESPERADO", weighted_mean(fidcs_rating_rent,"TAB_IV_B_VL_PL_MEDIO" )),
                                             n_sen=("TAB_IV_B_VL_PL_MEDIO",'size')
                                             ).reset_index()

    df_rent=df_rent.groupby(['Data', 'Rating_AUX']).agg(RENT_MES_sen_m =("TAB_X_VL_RENTAB_MES", "mean"),
                                                        RENT_MES_sen_mw=("TAB_X_VL_RENTAB_MES", weighted_mean(fidcs_rating_rent,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        BENCH_MES_sen_m =("TAB_X_PR_DESEMP_ESPERADO", "mean"),
                                                        BENCH_MES_sen_mw=("TAB_X_PR_DESEMP_ESPERADO", weighted_mean(fidcs_rating_rent,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n_sen=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()
         
   
                    
    df_rent_sub = fidcs_rating_sub[(fidcs_rating_sub['Data']>=fitler_date1) & (fidcs_rating_sub['Data']<=fitler_date2)][[*rent_columnlist]].dropna()#subset=['TAB_IV_B_VL_PL_MEDIO','TAB_X_VL_RENTAB_MES']  
 
    df_rent_sub = df_rent_sub.drop_duplicates()
    df_rent_sub = df_rent_sub[((df_rent_sub['TAB_X_VL_RENTAB_MES']<np.percentile(df_rent_sub['TAB_X_VL_RENTAB_MES'], 99)) & 
                               (df_rent_sub['TAB_X_VL_RENTAB_MES']>np.percentile(df_rent_sub['TAB_X_VL_RENTAB_MES'], 5)))]

    df_rent_sub = df_rent_sub[((df_rent_sub['TAB_X_PR_DESEMP_ESPERADO']<np.percentile(df_rent_sub['TAB_X_PR_DESEMP_ESPERADO'], 99)) & 
                               (df_rent_sub['TAB_X_PR_DESEMP_ESPERADO']>np.percentile(df_rent_sub['TAB_X_PR_DESEMP_ESPERADO'], 5)))]




    #Retirar OUTLIERS QUE PUXAM MUITO A MEDIA
    # df_rent_sub = df_rent_sub[~((df_rent_sub['TAB_X_VL_RENTAB_MES']>40) | (df_rent_sub['TAB_X_VL_RENTAB_MES']<-15))]

   
    # df_rent_sub = df_rent_sub[~((df_rent_sub['TAB_IV_B_VL_PL_MEDIO']>1e10) & (df_rent_sub['TAB_X_VL_RENTAB_MES']<-5))]
    # df_rent_sub = df_rent_sub[~((df_rent_sub['TAB_IV_B_VL_PL_MEDIO']>1e9) & (df_rent_sub['TAB_X_VL_RENTAB_MES']>20))]

  
    df_rent_sub2 = df_rent_sub.groupby(['Data']).agg(RENT_MES_sub_m =("TAB_X_VL_RENTAB_MES", "mean"),
                                             RENT_MES_sub_mw=("TAB_X_VL_RENTAB_MES", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                             BENCH_MES_sub_m =("TAB_X_PR_DESEMP_ESPERADO", "mean"),
                                             BENCH_MES_sub_mw=("TAB_X_PR_DESEMP_ESPERADO", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                             n_sen=("TAB_IV_B_VL_PL_MEDIO",'size')
                                             ).reset_index()

    df_rent_sub=df_rent_sub.groupby(['Data', 'Rating_AUX']).agg(RENT_MES_sub_m =("TAB_X_VL_RENTAB_MES", "mean"),
                                                        RENT_MES_sub_mw=("TAB_X_VL_RENTAB_MES", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        BENCH_MES_sub_m =("TAB_X_PR_DESEMP_ESPERADO", "mean"),
                                                        BENCH_MES_sub_mw=("TAB_X_PR_DESEMP_ESPERADO", weighted_mean(fidcs_rating_sub,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n_sen=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    
    df_rent = pd.merge(df_rent, df_rent_sub, left_on=['Data', 'Rating_AUX'], right_on=['Data', 'Rating_AUX'], how='left')
    df_rent2 = pd.merge(df_rent2, df_rent_sub2, left_on=['Data'], right_on=['Data'], how='left')


    ipeaseries_dict={
                    'PRECOS12_IPCAG12':'IPCA_MENSAL',
                    'PAN12_IPCAG12':'IPCA_MENSAL_ANUALIZADO',
                    'PRECOS12_INPCBR12':'INPC_MENSAL',
                    'BM12_TJOVER12':'SELIC_MENSAL',
                    'PAN12_TJOVER12':'SELIC_MENSAL_ANUALIZADO'
                    }
    
    for serie in ipeaseries_dict.items():
        #print(serie)
        
        serie_df=ipea.timeseries(serie[0])        
        serie_df['data']=pd.to_datetime(serie_df['DATE'],utc=True).apply(lambda d: d.replace(hour=0, minute=0, second=0,tzinfo=None))  
        serie_df=serie_df.drop_duplicates()     
        serie_df=serie_df.rename(columns={serie_df.columns[-2]:serie[1] })
        serie_df=serie_df.iloc[:,[-2,-1]]
        
        df_rent = pd.merge(df_rent, serie_df, left_on='Data', right_on='data', how='left')
        df_rent = df_rent.drop('data', axis=1)

        df_rent2 = pd.merge(df_rent2, serie_df, left_on='Data', right_on='data', how='left')
        df_rent2 = df_rent2.drop('data', axis=1)
 
        
     
        #ANUALIZAR RENTABILIDADE
    df_rent['RENT_MENSAL_ANUALIZADA_sen_m']=(((1+df_rent['RENT_MES_sen_m']/100)**(12))-1)*100    
    df_rent['RENT_MENSAL_ANUALIZADA_sen_mw']=(((1+df_rent['RENT_MES_sen_mw']/100)**(12))-1)*100  
    df_rent['BENCH_MENSAL_ANUALIZADA_sen_m']=(((1+df_rent['BENCH_MES_sen_m']/100)**(12))-1)*100  
    df_rent['BENCH_MENSAL_ANUALIZADA_sen_mw']=(((1+df_rent['BENCH_MES_sen_mw']/100)**(12))-1)*100  
    df_rent['RENT_MENSAL_ANUALIZADA_sub_m']=(((1+df_rent['RENT_MES_sub_m']/100)**(12))-1)*100    
    df_rent['RENT_MENSAL_ANUALIZADA_sub_mw']=(((1+df_rent['RENT_MES_sub_mw']/100)**(12))-1)*100 
    df_rent['BENCH_MENSAL_ANUALIZADA_sub_m']=(((1+df_rent['BENCH_MES_sub_m']/100)**(12))-1)*100  
    df_rent['BENCH_MENSAL_ANUALIZADA_sub_mw']=(((1+df_rent['BENCH_MES_sub_mw']/100)**(12))-1)*100  
    
    df_rent['INPC_MENSAL_ANUALIZADO']=(((1+df_rent['INPC_MENSAL']/100)**(12))-1)*100  

    df_rent['RENTREAL_MENSAL_ANUALIZADA_sen_m']=((1+df_rent['RENT_MES_sen_m'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['RENTREAL_MENSAL_ANUALIZADA_sen_mw']=((1+df_rent['RENT_MES_sen_mw'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['BENCHREAL_MENSAL_ANUALIZADA_sen_m']=((1+df_rent['BENCH_MES_sen_m'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['BENCHREAL_MENSAL_ANUALIZADA_sen_mw']=((1+df_rent['BENCH_MES_sen_mw'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['RENTREAL_MENSAL_ANUALIZADA_sub_m']=((1+df_rent['RENT_MES_sub_m'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['RENTREAL_MENSAL_ANUALIZADA_sub_mw']=((1+df_rent['RENT_MES_sub_mw'])/(1+df_rent['IPCA_MENSAL']/100))#*100  
    df_rent['BENCHREAL_MENSAL_ANUALIZADA_sub_m']=((1+df_rent['BENCH_MES_sub_m'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    df_rent['BENCHREAL_MENSAL_ANUALIZADA_sub_mw']=((1+df_rent['BENCH_MES_sub_mw'])/(1+df_rent['IPCA_MENSAL']/100))#*100    
    
    
    #OUTLIERS 
    df_rent = df_rent[~(df_rent['RENT_MENSAL_ANUALIZADA_sub_mw']>np.percentile(df_rent['RENT_MENSAL_ANUALIZADA_sub_mw'],99.9))]
    df_rent = df_rent[~(df_rent['BENCH_MENSAL_ANUALIZADA_sub_mw']>np.percentile(df_rent['RENT_MENSAL_ANUALIZADA_sub_mw'],99.9))]

    
    baseline=['AAA','AA+','AA','AA-','A+', 'A', 'A-']
    
    dict_ativo = {'AAA':df_rent[df_rent['Rating_AUX']=='AAA'],
                  'AA+':df_rent[df_rent['Rating_AUX']=='AA+'],
                  'AA': df_rent[df_rent['Rating_AUX']=='AA'],
                  'AA-':df_rent[df_rent['Rating_AUX']=='AA-'],
                  'A+':df_rent[df_rent['Rating_AUX']=='A+'],
                  'A':df_rent[df_rent['Rating_AUX']=='A'],
                  'A-':df_rent[df_rent['Rating_AUX']=='A-']                  
                  }

 

        #ANUALIZAR RENTABILIDADE
    df_rent2['RENT_MENSAL_ANUALIZADA_sen_m']=(((1+df_rent2['RENT_MES_sen_m']/100)**(12))-1)*100    
    df_rent2['RENT_MENSAL_ANUALIZADA_sen_mw']=(((1+df_rent2['RENT_MES_sen_mw']/100)**(12))-1)*100 
    df_rent2['BENCH_MENSAL_ANUALIZADA_sen_m']=(((1+df_rent2['BENCH_MES_sen_m']/100)**(12))-1)*100 
    df_rent2['BENCH_MENSAL_ANUALIZADA_sen_mw']=(((1+df_rent2['BENCH_MES_sen_mw']/100)**(12))-1)*100 
    df_rent2['RENT_MENSAL_ANUALIZADA_sub_m']=(((1+df_rent2['RENT_MES_sub_m']/100)**(12))-1)*100    
    df_rent2['RENT_MENSAL_ANUALIZADA_sub_mw']=(((1+df_rent2['RENT_MES_sub_mw']/100)**(12))-1)*100 
    df_rent2['BENCH_MENSAL_ANUALIZADA_sub_m']=(((1+df_rent2['BENCH_MES_sub_m']/100)**(12))-1)*100 
    df_rent2['BENCH_MENSAL_ANUALIZADA_sub_mw']=(((1+df_rent2['BENCH_MES_sub_mw']/100)**(12))-1)*100 

    
    df_rent2['INPC_MENSAL_ANUALIZADO']=(((1+df_rent2['INPC_MENSAL']/100)**(12))-1)*100  

    df_rent2['RENTREAL_MENSAL_ANUALIZADA_sen_m']=((1+df_rent2['RENT_MES_sen_m'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    df_rent2['RENTREAL_MENSAL_ANUALIZADA_sen_mw']=((1+df_rent2['RENT_MES_sen_mw'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    df_rent2['BENCHREAL_MENSAL_ANUALIZADA_sen_m']=((1+df_rent2['BENCH_MES_sen_m'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    df_rent2['BENCHREAL_MENSAL_ANUALIZADA_sen_mw']=((1+df_rent2['BENCH_MES_sen_mw'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    df_rent2['RENTREAL_MENSAL_ANUALIZADA_sub_m']=((1+df_rent2['RENT_MES_sub_m'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    df_rent2['RENTREAL_MENSAL_ANUALIZADA_sub_mw']=((1+df_rent2['RENT_MES_sub_mw'])/(1+df_rent2['IPCA_MENSAL']/100))#*100  
    df_rent2['BENCHREAL_MENSAL_ANUALIZADA_sub_m']=((1+df_rent2['BENCH_MES_sub_m'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    df_rent2['BENCHREAL_MENSAL_ANUALIZADA_sub_mw']=((1+df_rent2['BENCH_MES_sub_mw'])/(1+df_rent2['IPCA_MENSAL']/100))#*100    
    
    
    #OUTLIERS 
    df_rent2 = df_rent2[~(df_rent2['RENT_MENSAL_ANUALIZADA_sub_mw']>np.percentile(df_rent2['RENT_MENSAL_ANUALIZADA_sub_mw'],99.9))]
    df_rent2 = df_rent2[~(df_rent2['BENCH_MENSAL_ANUALIZADA_sub_mw']>np.percentile(df_rent2['RENT_MENSAL_ANUALIZADA_sub_mw'],99.9))]




    
    ################################### PLOT 9A ###################################
    
    
    #FIQUEI DE ARRUMAR AQUI
    
    ############# MEDIA Ponderada ##################    
    ############# RENTABILDIADE NOMINAL ##################

    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sen_mw'])
        ax.plot(df_aux['Data'],df_aux['BENCH_MENSAL_ANUALIZADA_sen_mw'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Senior','Benchmark','Selic'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média - Cota Senior\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Sen - Media Ponderada.png') 
    plt.show()
    
    
    
    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sub_mw'])
        ax.plot(df_aux['Data'],df_aux['BENCH_MENSAL_ANUALIZADA_sub_mw'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Subordinada','Benchmark', 'Selic'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média - Cota Subordinada\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Sub - Media Ponderada.png') 
    plt.show()
    
    
    
    
   ############# MEDIA SIMPLES ##################    
    ############# RENTABILDIADE NOMINAL ##################

    
    ############# MEDIA Ponderada ##################    

    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sen_m'])
        ax.plot(df_aux['Data'],df_aux['BENCH_MENSAL_ANUALIZADA_sen_m'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Senior','Benchmark','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média - Cota Senior\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Sen - Media Simples.png') 
    plt.show()
    

    
    fig,axes = plt.subplots(nrows = 7, sharex=True,  figsize=(8, 10))
    fig.subplots_adjust(hspace=0.5, wspace=0.3)

    for i,ax in enumerate(axes.flat):
        
        df_aux = dict_ativo[list(dict_ativo)[i]]
    
        ax.plot(df_aux['Data'],df_aux['RENT_MENSAL_ANUALIZADA_sub_m'])
        ax.plot(df_aux['Data'],df_aux['BENCH_MENSAL_ANUALIZADA_sub_m'])

        #ax.plot(df_aux['Data'],df_aux['IPCA_MENSAL_ANUALIZADO'])
        #ax.plot(df_aux['Data'],df_aux['INPC_MENSAL_ANUALIZADO'])
        ax.plot(df_aux['Data'],df_aux['SELIC_MENSAL_ANUALIZADO'])
   
        ax.set_title(baseline[i])
        plt.xticks(rotation=60)
        #ax.set_xticks(df_aux['Data'], rotation=120)
        #ax.legend((p1[0], p2[0]), ('Men', 'Women'))
    # fig.legend(labels=['PL Médio','PL'], loc='best')
    # fig.legend(labels=['Rentabilidae','IPCA','INPC','SELIC'], loc='center right')
    fig.legend(labels=['Subordinada','SELIC'], loc='center right')
    fig.suptitle("Rentabilidades Nominal Média - Cota Subordinada\n (em %)", fontsize=16)
    #fig.tight_layout()
    
    plt.savefig('Rentabilidade Nominal Sub - Media Simples.png', bbox_inches='tight') 
    plt.show()
    
    
    
    
    
    ######## GRAFICO SEM RATING
    
    plt.figure(figsize=(14,6))
    plt.plot(df_rent2['Data'],df_rent2['RENT_MENSAL_ANUALIZADA_sen_mw'],label='Senior')
    plt.plot(df_rent2['Data'],df_rent2['RENT_MENSAL_ANUALIZADA_sub_mw'], label='Subordinada')
    plt.plot(df_rent2['Data'],df_rent2['SELIC_MENSAL_ANUALIZADO'], label='SELIC')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em  %')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    # plt.xticks(rotation=30)
  
    plt.title("Rentabilidades Nominal Média\n (em %)", fontsize=16)
    
    plt.savefig('Rentabilidade Nominal - Media Ponderada.png', bbox_inches='tight') 
    plt.show()
    
    
    plt.figure(figsize=(15,8))
    plt.plot(df_rent2['Data'],df_rent2['RENT_MENSAL_ANUALIZADA_sen_m'],label='Senior')
    plt.plot(df_rent2['Data'],df_rent2['RENT_MENSAL_ANUALIZADA_sub_m'], label='Subordinada')
    plt.plot(df_rent2['Data'],df_rent2['SELIC_MENSAL_ANUALIZADO'], label='SELIC')
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em  %')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Rentabilidades Nominal Média\n (em %)", fontsize=16)
    
    plt.savefig('Rentabilidade Nominal - Media Simples.png', bbox_inches='tight') 
    plt.show()
  
    
         
    ################################### SET DATABASE TO PLOT 10 ###################################
    
    
 

    liq_columnlist  =  ['Data','Rating_AUX','DENOM_SOCIAL', 'CNPJ_FUNDO','TAB_IV_B_VL_PL_MEDIO',
                          'TAB_X_VL_LIQUIDEZ_0','TAB_X_VL_LIQUIDEZ_30','TAB_X_VL_LIQUIDEZ_60','TAB_X_VL_LIQUIDEZ_90',
                          'TAB_X_VL_LIQUIDEZ_180','TAB_X_VL_LIQUIDEZ_360','TAB_X_VL_LIQUIDEZ_MAIOR_360']
 
    
    df_liq= fidcs_rating[(fidcs_rating['Data']>=fitler_date1) & (fidcs_rating['Data']<=fitler_date2)][[*liq_columnlist]].dropna()
    df_liq = df_liq.drop_duplicates()

    
  # % DO PL
    #df_liq[df_liq.select_dtypes(include=np.number).columns.tolist()]=df_liq.select_dtypes(include=np.number).div(df_liq['TAB_IV_A_VL_PL'], axis=0)
    # df_liq[df_liq.select_dtypes(include=np.number).columns.tolist()]=df_liq.select_dtypes(include=np.number).div(df_liq['TAB_I_VL_ATIVO'], axis=0).dropna()
  
    df_liq[df_liq.select_dtypes(include=np.number).columns.tolist()]=df_liq.select_dtypes(include=np.number)/1000000

    df_liq = df_liq.groupby(['Data']).agg( liq0_m =("TAB_X_VL_LIQUIDEZ_0", "mean"),
                                                        liq0_wm=("TAB_X_VL_LIQUIDEZ_0", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq30_m =("TAB_X_VL_LIQUIDEZ_30", "mean"),
                                                        liq30_wm=("TAB_X_VL_LIQUIDEZ_30", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq60_m =("TAB_X_VL_LIQUIDEZ_60", "mean"),
                                                        liq60_wm=("TAB_X_VL_LIQUIDEZ_60", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq90_m =("TAB_X_VL_LIQUIDEZ_90", "mean"),
                                                        liq90_wm=("TAB_X_VL_LIQUIDEZ_90", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq180_m =("TAB_X_VL_LIQUIDEZ_180", "mean"),
                                                        liq180_wm=("TAB_X_VL_LIQUIDEZ_180", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq360_m =("TAB_X_VL_LIQUIDEZ_360", "mean"),  
                                                        liq360_wm=("TAB_X_VL_LIQUIDEZ_360", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        liq360m_m =("TAB_X_VL_LIQUIDEZ_MAIOR_360", "mean"),                                                        
                                                        liq360m_wm=("TAB_X_VL_LIQUIDEZ_MAIOR_360", weighted_mean(fidcs_rating,"TAB_IV_B_VL_PL_MEDIO" )),
                                                        n=("TAB_IV_B_VL_PL_MEDIO",'size')
                                                        ).reset_index()

    
    
    ################################### PLOT 10 ###################################
    
    ############# MEDIA PONDERADA ##################

    

    plt.stackplot(df_liq['Data'], df_liq['liq0_wm'], df_liq['liq30_wm'],  df_liq['liq60_wm'],df_liq['liq90_wm'],
                  df_liq['liq180_wm'],df_liq['liq360_wm'], df_liq['liq360m_wm'],
                  labels=['Liquidez Imediata','Até 30 dias', 'Até 60 dias','Até 90 dias',
                          'Até 180 dias','Até 360 dias','Mais de 360 dias' ],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Liquidez Média dos Fundos", fontsize=16)
    plt.savefig('Liquidez - Media Ponderada - Individual.png', bbox_inches='tight') 
    plt.show()  

    ############# MEDIA SIMPLES ##################

    plt.stackplot(df_liq['Data'], df_liq['liq0_m'], df_liq['liq30_m'],  df_liq['liq60_m'],df_liq['liq90_m'],
                  df_liq['liq180_m'],df_liq['liq360_m'], df_liq['liq360m_m'],
                  labels=['Liquidez Imediata','Até 30 dias', 'Até 60 dias','Até 90 dias',
                          'Até 180 dias','Até 360 dias','Mais de 360 dias' ],alpha=.6)
    
    #plt.xlabel('Tempo')
    #plt.ylabel('% do PL')
    plt.ylabel('em R$ milhões')
    plt.tight_layout()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
               fancybox=True, shadow=True, ncol=1)
    plt.xticks(rotation=30)
  
    plt.title("Liquidez Média dos Fundos", fontsize=16)
    plt.savefig('Liquidez - Media Simples - Individual.png', bbox_inches='tight') 
    plt.show()  
  
    return 'Plots Feitos!'











def case_study():
    
    cnpj = '08.632.394/0001-02'
    fidc_filter = df_fidc[df_fidc['CNPJ_FUNDO']==cnpj]
    
    fidc_filter['TAB_X_CLASSE_SERIE'] = fidc_filter['TAB_X_CLASSE_SERIE'].replace(to_replace=['Classe Sénior|Sênior'], value='Série', regex=True)
    fidc_filter = fidc_filter.sort_values(['CNPJ_FUNDO','TAB_X_CLASSE_SERIE','Data'])
 
    fidc_filter['TAB_X_CLASSE_SERIE'].unique()

    
    return 'Plots Feitos!'




if __name__=='__main__':
    
    
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/')

    df_fidc, df_rating= open_dfs()
    df_fidc_senior, df_rating_filter4, df_rating_append, df_rating_final = filter_dfs(df_fidc, df_rating)
    plot_rating(df_rating, df_rating_filter4, df_rating_append)
    
    fitler_date0 = np.datetime64('2019-11-01')   
    fitler_date1 = np.datetime64('2019-04-01')
    fitler_date2 = np.datetime64('2020-06-01')
    
    #analyze_fidcs(df_fidc_senior,df_fidc ,df_rating_final, fitler_date0, fitler_date1, fitler_date2)
    analyze_fidcs2(df_fidc_senior,df_fidc ,df_rating_final, fitler_date0, fitler_date1, fitler_date2)
  
    
 
#VARIAVEIS 
    
    #TAB 1
    	
    # 23	TAB_I_VL_ATIVO 
    
        # 24	TAB_I1_VL_DISP      
        # 25	TAB_I2_VL_CARTEIRA        
            # 26	TAB_I2A_VL_DIRCRED_RISCO
                # 27	TAB_I2A1_VL_CRED_VENC_AD
                # 28	TAB_I2A2_VL_CRED_VENC_INAD
                # 29	TAB_I2A21_VL_TOTAL_PARCELA_INAD
                # 30	TAB_I2A3_VL_CRED_INAD
                # 31	TAB_I2A4_VL_CRED_DIRCRED_PERFM
                # 32	TAB_I2A5_VL_CRED_VENCIDO_PENDENTE
                # 33	TAB_I2A6_VL_CRED_EMP_RECUP
                # 34	TAB_I2A7_VL_CRED_RECEITA_PUBLICA
                # 35	TAB_I2A8_VL_CRED_ACAO_JUDIC
                # 36	TAB_I2A9_VL_CRED_FATOR_RISCO
                # 37	TAB_I2A10_VL_CRED_DIVERSO
                # 38	TAB_I2A11_VL_REDUCAO_RECUP
           
            # 39	TAB_I2B_VL_DIRCRED_SEM_RISCO 
                # 282	TAB_I2B1_VL_CRED_VENC_AD
                    # 283	TAB_I2B2_VL_CRED_VENC_INAD
                    # 284	TAB_I2B21_VL_TOTAL_PARCELA_INAD
                    # 285	TAB_I2B3_VL_CRED_INAD
                    # 286	TAB_I2B4_VL_CRED_DIRCRED_PERFM
                    # 287	TAB_I2B5_VL_CRED_VENCIDO_PENDENTE
                    # 288	TAB_I2B6_VL_CRED_EMP_RECUP
                    # 289	TAB_I2B7_VL_CRED_RECEITA_PUBLICA
                    # 290	TAB_I2B8_VL_CRED_ACAO_JUDIC
                    # 291	TAB_I2B9_VL_CRED_FATOR_RISCO
                    # 292	TAB_I2B10_VL_CRED_DIVERSO
                    # 293	TAB_I2B11_VL_REDUCAO_RECUP
                                            # 294	TAB_I2_DEBENTURE_CRI (???)
                                            # 295	TAB_I2_COTA_FIDC (????)
                                            # 296	TAB_I2_VL_OUTRO_ATIVO (????)
        
            # 40	TAB_I2C_VL_VLMOB        
                # 41	TAB_I2C1_VL_DEBENTURE
                # 42	TAB_I2C2_VL_CRI
                # 43	TAB_I2C3_VL_NP_COMERC
                # 44	TAB_I2C4_VL_LETRA_FINANC
                # 45	TAB_I2C5_VL_COTA_FUNDO_ICVM555
                # 46	TAB_I2C6_VL_OUTRO
                
            # 47	TAB_I2D_VL_TITPUB_FED            
            # 48	TAB_I2E_VL_CDB            
            # 49	TAB_I2F_VL_OPER_COMPROM            
            # 50	TAB_I2G_VL_OUTRO_RF            
            # 51	TAB_I2H_VL_COTA_FIDC            
            # 52	TAB_I2I_VL_COTA_FIDC_NP            
            # 53	TAB_I2J_VL_CONTRATO_FUTURO
            
        # 54	TAB_I3_VL_POSICAO_DERIV
            # 55	TAB_I3A_VL_MERCADO_TERMO
            # 56	TAB_I3B_VL_MERCADO_OPCAO
            # 57	TAB_I3C_VL_MERCADO_FUTURO
            # 58	TAB_I3D_VL_DIFER_SWAP
            # 59	TAB_I3E_VL_COBERTURA
            # 60	TAB_I3F_VL_DEPOSITO_MARGEM            
        # 61	TAB_I4_VL_OUTRO_ATIVO        
            # 62	TAB_I4A_VL_CPRAZO
            # 63	TAB_I4B_VL_LPRAZO

    
    #TAB 2	
    #VERIFICAR DIVERSIFICACAO DA CARTEIRA
    
        # 64	TAB_II_VL_CARTEIRA
            # 65	TAB_II_A_VL_INDUST
            # 66	TAB_II_B_VL_IMOBIL
            # 67	TAB_II_C_VL_COMERC
                # 68	TAB_II_C1_VL_COMERC
                # 69	TAB_II_C2_VL_VAREJO
                # 70	TAB_II_C3_VL_ARREND
           
            # 71	TAB_II_D_VL_SERV
                # 72	TAB_II_D1_VL_SERV
                # 73	TAB_II_D2_VL_SERV_PUBLICO
                # 74	TAB_II_D3_VL_SERV_EDUC
                # 75	TAB_II_D4_VL_ENTRET
                
            # 76	TAB_II_E_VL_AGRONEG
            # 77	TAB_II_F_VL_FINANC
                # 78	TAB_II_F1_VL_CRED_PESSOA
                # 79	TAB_II_F2_VL_CRED_PESSOA_CONSIG
                # 80	TAB_II_F3_VL_CRED_CORP
                # 81	TAB_II_F4_VL_MIDMARKET
                # 82	TAB_II_F5_VL_VEICULO
                # 83	TAB_II_F6_VL_IMOBIL_EMPRESA
                # 84	TAB_II_F7_VL_IMOBIL_RESID
                # 85	TAB_II_F8_VL_OUTRO
                
            # 86	TAB_II_G_VL_CREDITO
            # 87	TAB_II_H_VL_FACTOR
            
                # 88	TAB_II_H1_VL_PESSOA
                # 89	TAB_II_H2_VL_CORP
                
            # 90	TAB_II_I_VL_SETOR_PUBLICO
                # 91	TAB_II_I1_VL_PRECAT
                # 92	TAB_II_I2_VL_TRIBUT
                # 93	TAB_II_I3_VL_ROYALTIES
                # 94	TAB_II_I4_VL_OUTRO
                
            # 95	TAB_II_J_VL_JUDICIAL
            # 96	TAB_II_K_VL_MARCA

    
    
    #TAB 3 - PASSIVO
	
        # 97	TAB_III_VL_PASSIVO
            # 98	TAB_III_A_VL_PAGAR 
                # 99	TAB_III_A1_VL_CPRAZO
                # 100	TAB_III_A2_VL_LPRAZO
            # 101	TAB_III_B_VL_POSICAO_DERIV
                # 102	TAB_III_B1_VL_TERMO
                # 103	TAB_III_B2_VL_OPCAO
                # 104	TAB_III_B3_VL_FUTURO
                # 105	TAB_III_B4_VL_SWAP_PAGAR

    
    #TAB 4 - PL
    
        # 106	TAB_IV_A_VL_PL
        # 107	TAB_IV_B_VL_PL_MEDIO
    
    
    #TAB 5 - Comportamento da Carteira de Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios	
    
        # 108	TAB_V_A_VL_DIRCRED_PRAZO
            # 109	TAB_V_A1_VL_PRAZO_VENC_30
            # 110	TAB_V_A2_VL_PRAZO_VENC_60
            # 111	TAB_V_A3_VL_PRAZO_VENC_90
            # 112	TAB_V_A4_VL_PRAZO_VENC_120
            # 113	TAB_V_A5_VL_PRAZO_VENC_150
            # 114	TAB_V_A6_VL_PRAZO_VENC_180
            # 115	TAB_V_A7_VL_PRAZO_VENC_360
            # 116	TAB_V_A8_VL_PRAZO_VENC_720
            # 117	TAB_V_A9_VL_PRAZO_VENC_1080
            # 118	TAB_V_A10_VL_PRAZO_VENC_MAIOR_1080

        # 119	TAB_V_B_VL_DIRCRED_INAD
            # 120	TAB_V_B1_VL_INAD_30
            # 121	TAB_V_B2_VL_INAD_60
            # 122	TAB_V_B3_VL_INAD_90
            # 123	TAB_V_B4_VL_INAD_120
            # 124	TAB_V_B5_VL_INAD_150
            # 125	TAB_V_B6_VL_INAD_180
            # 126	TAB_V_B7_VL_INAD_360
            # 127	TAB_V_B8_VL_INAD_720
            # 128	TAB_V_B9_VL_INAD_1080
            # 129	TAB_V_B10_VL_INAD_MAIOR_1080
  
        # 130	TAB_V_C_VL_DIRCRED_ANTECIPADO
            # 131	TAB_V_C1_VL_ANTECIPADO_30
            # 132	TAB_V_C2_VL_ANTECIPADO_60
            # 133	TAB_V_C3_VL_ANTECIPADO_90
            # 134	TAB_V_C4_VL_ANTECIPADO_120
            # 135	TAB_V_C5_VL_ANTECIPADO_150
            # 136	TAB_V_C6_VL_ANTECIPADO_180
            # 137	TAB_V_C7_VL_ANTECIPADO_360
            # 138	TAB_V_C8_VL_ANTECIPADO_720
            # 139	TAB_V_C9_VL_ANTECIPADO_1080
            # 140	TAB_V_C10_VL_ANTECIPADO_MAIOR_1080
    
    
    #TAB 6
        #V - Comportamento da Carteira de Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios	
        
        # 141	TAB_VI_A_VL_DIRCRED_PRAZO
            # 142	TAB_VI_A1_VL_PRAZO_VENC_30
            # 143	TAB_VI_A2_VL_PRAZO_VENC_60
            # 144	TAB_VI_A3_VL_PRAZO_VENC_90
            # 145	TAB_VI_A4_VL_PRAZO_VENC_120
            # 146	TAB_VI_A5_VL_PRAZO_VENC_150
            # 147	TAB_VI_A6_VL_PRAZO_VENC_180
            # 148	TAB_VI_A7_VL_PRAZO_VENC_360
            # 149	TAB_VI_A8_VL_PRAZO_VENC_720
            # 150	TAB_VI_A9_VL_PRAZO_VENC_1080
            # 151	TAB_VI_A10_VL_PRAZO_VENC_MAIOR_1080
        
        # 152	TAB_VI_B_VL_DIRCRED_INAD
            # 153	TAB_VI_B1_VL_INAD_30
            # 154	TAB_VI_B2_VL_INAD_60
            # 155	TAB_VI_B3_VL_INAD_90
            # 156	TAB_VI_B4_VL_INAD_120
            # 157	TAB_VI_B5_VL_INAD_150
            # 158	TAB_VI_B6_VL_INAD_180
            # 159	TAB_VI_B7_VL_INAD_360
            # 160	TAB_VI_B8_VL_INAD_720
            # 161	TAB_VI_B9_VL_INAD_1080
            # 162	TAB_VI_B10_VL_INAD_MAIOR_1080
        
        # 163	TAB_VI_C_VL_DIRCRED_ANTECIPADO
            # 164	TAB_VI_C1_VL_ANTECIPADO_30
            # 165	TAB_VI_C2_VL_ANTECIPADO_60
            # 166	TAB_VI_C3_VL_ANTECIPADO_90
            # 167	TAB_VI_C4_VL_ANTECIPADO_120
            # 168	TAB_VI_C5_VL_ANTECIPADO_150
            # 169	TAB_VI_C6_VL_ANTECIPADO_180
            # 170	TAB_VI_C7_VL_ANTECIPADO_360
            # 171	TAB_VI_C8_VL_ANTECIPADO_720
            # 172	TAB_VI_C9_VL_ANTECIPADO_1080
            # 173	TAB_VI_C10_VL_ANTECIPADO_MAIOR_1080
    
    
    #TAB 7 
    
    #A) AQUISICOES
        # 174	TAB_VII_A1_1_QT_DIRCRED_RISCO
        # 175	TAB_VII_A1_2_VL_DIRCRED_RISCO
        
        # 176	TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO
        # 177	TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO
        
        # 178	TAB_VII_A3_1_QT_DIRCRED_VENC_AD
        # 179	TAB_VII_A3_2_VL_DIRCRED_VENC_AD
        
        # 180	TAB_VII_A4_1_QT_DIRCRED_VENC_INAD
        # 181	TAB_VII_A4_2_VL_DIRCRED_VENC_INAD
        
        # 182	TAB_VII_A5_1_QT_DIRCRED_INAD
        # 183	TAB_VII_A5_2_VL_DIRCRED_INAD

    #B) ALIENACOES
        
        # 184	TAB_VII_B1_1_QT_CEDENTE
        # 185	TAB_VII_B1_2_VL_CEDENTE
        # 186	TAB_VII_B1_3_VL_CONTAB_CEDENTE
        # 187	TAB_VII_B2_1_QT_PREST
        # 188	TAB_VII_B2_2_VL_PREST
        # 189	TAB_VII_B2_3_VL_CONTAB_PREST
        # 190	TAB_VII_B3_1_QT_TERCEIRO
        # 191	TAB_VII_B3_2_VL_TERCEIRO
        # 192	TAB_VII_B3_3_VL_CONTAB_TERCEIRO
        
    #C) SUBSTIITUICAO
        
        # 193	TAB_VII_C_1_QT_SUBST
        # 194	TAB_VII_C_2_VL_SUBST
        # 195	TAB_VII_C_3_VL_CONTAB_SUBST
        
    #D) RECOMPRA
        
        # 196	TAB_VII_D_1_QT_RECOMPRA
        # 197	TAB_VII_D_2_VL_RECOMPRA
        # 198	TAB_VII_D_3_VL_CONTAB_RECOMPRA
    
    #TAB 9
    
        # 199	TAB_IX_A1_1_1_COMPRA_MIN
        # 200	TAB_IX_A1_1_2_COMPRA_MEDIA
        # 201	TAB_IX_A1_1_3_COMPRA_MAX
        
        # 202	TAB_IX_A1_2_1_VENDA_MIN
        # 203	TAB_IX_A1_2_2_VENDA_MEDIA
        # 204	TAB_IX_A1_2_3_VENDA_MAX
        
        # 205	TAB_IX_A2_1_1_COMPRA_MIN
        # 206	TAB_IX_A2_1_2_COMPRA_MEDIA
        # 207	TAB_IX_A2_1_3_COMPRA_MAX
        
        # 208	TAB_IX_A2_2_1_VENDA_MIN
        # 209	TAB_IX_A2_2_2_VENDA_MEDIA
        # 210	TAB_IX_A2_2_3_VENDA_MAX
        
        # 211	TAB_IX_B1_1_1_COMPRA_MIN
        # 212	TAB_IX_B1_1_2_COMPRA_MEDIA
        # 213	TAB_IX_B1_1_3_COMPRA_MAX
        
        # 214	TAB_IX_B1_2_1_VENDA_MIN
        # 215	TAB_IX_B1_2_2_VENDA_MEDIA
        # 216	TAB_IX_B1_2_3_VENDA_MAX
        
        # 217	TAB_IX_B2_1_1_COMPRA_MIN
        # 218	TAB_IX_B2_1_2_COMPRA_MEDIA
        # 219	TAB_IX_B2_1_3_COMPRA_MAX
        
        # 220	TAB_IX_B2_2_1_VENDA_MIN
        # 221	TAB_IX_B2_2_2_VENDA_MEDIA
        # 222	TAB_IX_B2_2_3_VENDA_MAX
        
        # 223	TAB_IX_C1_1_1_COMPRA_MIN
        # 224	TAB_IX_C1_1_2_COMPRA_MEDIA
        # 225	TAB_IX_C1_1_3_COMPRA_MAX
        
        # 226	TAB_IX_C1_2_1_VENDA_MIN
        # 227	TAB_IX_C1_2_2_VENDA_MEDIA
        # 228	TAB_IX_C1_2_3_VENDA_MAX
        
        # 229	TAB_IX_C2_1_1_COMPRA_MIN
        # 230	TAB_IX_C2_1_2_COMPRA_MEDIA
        # 231	TAB_IX_C2_1_3_COMPRA_MAX
        
        # 232	TAB_IX_C2_2_1_VENDA_MIN
        # 233	TAB_IX_C2_2_2_VENDA_MEDIA
        # 234	TAB_IX_C2_2_3_VENDA_MAX
        
        # 235	TAB_IX_D1_1_1_COMPRA_MIN
        # 236	TAB_IX_D1_1_2_COMPRA_MEDIA
        # 237	TAB_IX_D1_1_3_COMPRA_MAX
        
        # 238	TAB_IX_D1_2_1_VENDA_MIN
        # 239	TAB_IX_D1_2_2_VENDA_MEDIA
        # 240	TAB_IX_D1_2_3_VENDA_MAX
        
        # 241	TAB_IX_D2_1_1_COMPRA_MIN
        # 242	TAB_IX_D2_1_2_COMPRA_MEDIA
        # 243	TAB_IX_D2_1_3_COMPRA_MAX
        
        # 244	TAB_IX_D2_2_1_VENDA_MIN
        # 245	TAB_IX_D2_2_2_VENDA_MEDIA
        # 246	TAB_IX_D2_2_3_VENDA_MAX
        
        # 247	TAB_IX_E1_1_1_COMPRA_MIN
        # 248	TAB_IX_E1_1_2_COMPRA_MEDIA
        # 249	TAB_IX_E1_1_3_COMPRA_MAX
        
        # 250	TAB_IX_E1_2_1_VENDA_MIN
        # 251	TAB_IX_E1_2_2_VENDA_MEDIA
        # 252	TAB_IX_E1_2_3_VENDA_MAX
        
        # 253	TAB_IX_E2_1_1_COMPRA_MIN
        # 254	TAB_IX_E2_1_2_COMPRA_MEDIA
        # 255	TAB_IX_E2_1_3_COMPRA_MAX
        
        # 256	TAB_IX_E2_2_1_VENDA_MIN
        # 257	TAB_IX_E2_2_2_VENDA_MEDIA
        # 258	TAB_IX_E2_2_3_VENDA_MAX
        
        # 259	TAB_IX_F1_1_1_COMPRA_MIN
        # 260	TAB_IX_F1_1_2_COMPRA_MEDIA
        # 261	TAB_IX_F1_1_3_COMPRA_MAX
        
        # 262	TAB_IX_F1_2_1_VENDA_MIN
        # 263	TAB_IX_F1_2_2_VENDA_MEDIA
        # 264	TAB_IX_F1_2_3_VENDA_MAX
        
        # 265	TAB_IX_F2_1_1_COMPRA_MIN
        # 266	TAB_IX_F2_1_2_COMPRA_MEDIA
        # 267	TAB_IX_F2_1_3_COMPRA_MAX
        
        # 268	TAB_IX_F2_2_1_VENDA_MIN
        # 269	TAB_IX_F2_2_2_VENDA_MEDIA
        # 270	TAB_IX_F2_2_3_VENDA_MAX
        
    #TAB X
    
    
        # 22	TAB_X_NR_COTST

        # 11	TAB_X_QT_COTA
        # 12	TAB_X_VL_COTA
        
        # 13	TAB_X_VL_TOTAL_AMORT
        # 14	TAB_X_VL_TOTAL_CAPT
        # 15	TAB_X_VL_TOTAL_RESG
        # 16	TAB_X_VL_TOTAL_RESGSOL
        
        # 17	TAB_X_QT_TOTAL_AMORT
        # 18	TAB_X_QT_TOTAL_CAPT
        # 19	TAB_X_QT_TOTAL_RESG
        # 20	TAB_X_QT_TOTAL_RESGSOL
        
        
        # 21	TAB_X_VL_RENTAB_MES
    
        # 271	TAB_X_VL_LIQUIDEZ_0
        # 272	TAB_X_VL_LIQUIDEZ_30
        # 273	TAB_X_VL_LIQUIDEZ_60
        # 274	TAB_X_VL_LIQUIDEZ_90
        # 275	TAB_X_VL_LIQUIDEZ_180
        # 276	TAB_X_VL_LIQUIDEZ_360
        # 277	TAB_X_VL_LIQUIDEZ_MAIOR_360
        
        
        # 278	PRAZO_CONVERSAO_COTA
        # 279	TP_PRAZO_CONVERSAO_COTA
        # 280	PRAZO_PAGTO_RESGATE
        # 281	TP_PRAZO_PAGTO_RESGATE

