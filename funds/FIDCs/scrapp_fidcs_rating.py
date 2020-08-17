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



from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from shutil import which
from selenium.common.exceptions import NoSuchElementException  
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC   
     




def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def open_old_dfs():
    
    #Essa funcao abre todas os relatoriso de rating antigos de todas as agencias e salva como arquivo antigo.
    
    df_agg_old= pd.read_excel('Ratings FIDCs.xlsx', sheet_name='Agregado')
    df_lf_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='LF')
    df_austin_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='AUSTIN')
    df_liberium_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='LIBERIUM')
    df_sr_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='SR')
    df_sp_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='SP')
    df_moodys_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='MOODYS')
    df_fitch_old = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='FITCH')
    df_solis = pd.read_excel('Ratings FIDCs.xlsx', sheet_name='SOLIS')
    
    writer = pd.ExcelWriter('Rating FIDCs - OLD.xlsx', engine='xlsxwriter')
    
    df_agg_old.to_excel(writer, sheet_name='Agregado', index=False)
    df_lf_old.to_excel(writer, sheet_name='LF', index=False)
    df_austin_old.to_excel(writer, sheet_name='AUSTIN', index=False)
    df_liberium_old.to_excel(writer, sheet_name='LIBERIUM', index=False)
    df_sr_old.to_excel(writer, sheet_name='SR', index=False)
    df_sp_old.to_excel(writer, sheet_name='SP', index=False)
    df_moodys_old.to_excel(writer, sheet_name='MOODYS', index=False)
    df_fitch_old.to_excel(writer, sheet_name='FITCH', index=False)
    df_solis.to_excel(writer, sheet_name='SOLIS', index=False)


    writer.save()

    return df_lf_old, df_austin_old, df_liberium_old, df_sr_old, df_sp_old, df_moodys_old, df_fitch_old
    


  

def scrap_lf(chrome_options, df_lf_old):
    
    #Esta funcao faz o Scrao no site da LF RATING e compara com o relatorio antigo
    
    driver = webdriver.Chrome(executable_path="/Users/pedrocampelo/Projects/selenium/chromedriver", options = chrome_options)
    driver.get("http://www.lfrating.com/ratings-realizados")
    
    print("Fazendo scrap para a agencia LF")
    
    ativos=[]
    statuss = []
    notas=[]
    data_refs=[]
    prazos=[]
    relatorios=[]
        
    print('Fazendo a coleta da SR RATINGs')
    
    table_lines = [el.text for el in driver.find_elements_by_xpath("(//table[@id='tabela-ratings'])[2]/tbody/tr")]
        
    for line in range(2,len(table_lines)+1):
            
        #table_column_path =  "((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td"
        #table_columns= [el.text for el in driver.find_elements_by_xpath()]
    
        #print('Fazendo a coleta do produto',line)
        ativo_path = "(((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td)[1]/a"
        status_path = "(((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td)[2]"
        notas_path = "(((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td)[3]"
        data_ref_path = "(((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td)[4]"
        prazo_path = "(((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td)[5]"
        relatorio_path = "(((//table[@id='tabela-ratings'])[2]/tbody/tr)["+str(line)+"]/td)[6]/a"
        
        
        ativo = driver.find_element_by_xpath(ativo_path).text
        status = driver.find_element_by_xpath(status_path).text
        nota = driver.find_element_by_xpath(notas_path).text
        data_ref = driver.find_element_by_xpath(data_ref_path).text
        prazo = driver.find_element_by_xpath(prazo_path).text
               
        
        
        try:
           check =  driver.find_element_by_xpath(relatorio_path)
        except NoSuchElementException:
            check = False
        
        if check:
            relatorio = driver.find_element_by_xpath(relatorio_path).get_attribute("href")
        
        else:
            relatorio=''
        
        ativos.append(str(ativo))
        statuss.append(str(status))
        notas.append(str(nota))
        data_refs.append(str(data_ref))
        prazos.append(str(prazo))
        relatorios.append(str(relatorio))
                                
    
    driver.close()
   
    df_lf = pd.DataFrame({"Ativo":ativos, 
                        "Status":statuss,
                        "Notas":notas,
                        "Data":data_refs,
                        "Prazo":prazos,
                        "Relatorios":relatorios}) 
    
    df_lf['Agencia'] = 'LF' 
    print("Scrap feito!")
       
    #RETIRAR LINHA CORONA VIRUS                                
    index_names = df_lf[ (df_lf['Ativo'].str.contains('AVISO'))].index
    if len(index_names)>0:
         df_lf=df_lf.drop(index_names)

              
    intersect_list = set(df_lf['Ativo'].tolist()).intersection(set(df_lf_old['Fundo'].tolist()))
    new_assets_list = set(df_lf['Ativo'].tolist()) - set(df_lf_old['Fundo'].tolist())
    old_assets_list = set(df_lf_old['Fundo'].tolist()) - set(df_lf['Ativo'].tolist())
    
    if len(intersect_list)>0:
        print('1) Intercessao entre as duas listas: ')

        [print('- ',x) for x in intersect_list]
    else:
        print ('1) Nenhum ativo em comum entre a analise nova e a antiga')

        
    if len(new_assets_list)>0:
        print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
        [print('- ',x) for x in new_assets_list]
    else:
        print('2) Nenhum ativo novo na nova analise')
        
        

    if len(old_assets_list)>0:
        
        print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
        [print('- ',x) for x in old_assets_list]
    else:
        print('3) Nenhum ativo antigo deixou de ser analisado')

    df_lf_old=df_lf_old.rename(columns={"Fundo":"Ativo",
                                        "Rating": "Rating Antigo", 
                                        "Data Rating":"Data Rating Antigo", 
                                        "Data vencimento":"Data Vencimento Antigo"})

    df_lf_old = df_lf_old[['CNPJ','ISIN','Ativo', 'Cota','Rating Antigo',
                           'Data Rating Antigo', 'Data Vencimento Antigo']]
  
    
    df_lf = df_lf.merge(df_lf_old,how='left',on='Ativo')
    
    
    #Arrumar CNPJ
    df_aux = pd.DataFrame()
    for nome in df_lf['Ativo'].unique():
        print(nome)
        
        df_aux2= df_lf[df_lf['Ativo']==nome]
        cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
        cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
        if len([cnpj_list])>1:
            #print('erro')
            break
        else:
            #print('ok')
            df_aux2['CNPJ2']=cnpj_list
            df_aux=df_aux.append(df_aux2)
            
            
    df_aux = df_aux.drop(['CNPJ'], axis=1)      
    df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'})      

    df_lf=df_aux
    df_lf['Agencia']='LF'
    
    
    df_lf['Data'] = df_lf['Data'].replace(to_replace=[''], value=np.nan, regex=True)
    #df_lf['Data'] = pd.to_datetime(df_lf['Data'])
    
    print('DF arrumado!')
 
    return df_lf








def scrap_austin(chrome_options,df_austin_old):
    
    #    #Esta funcao faz o Scrao no site da LF AUSTIN e compara com o relatorio antigo
    
    driver = webdriver.Chrome(executable_path="/Users/pedrocampelo/Projects/selenium/chromedriver", options = chrome_options)
    driver.get("http://www.austin.com.br/Ratings-FIDCs.html")
    
    print("Fazendo scrap para a agencia Austin")
    
    
    links=[]
    names = []
    cotas=[]
    series=[]
    ratings=[]
    perspectivas=[]
    acao_ratings=[]
    datas=[]
    pageCounter=1
    
    while type(pageCounter) == int:
    #while pageCounter<2:
        
        print('Fazendo a coleta da página ',pageCounter)
        
        table_lines = [el.text for el in driver.find_elements_by_xpath("//table[@id='tableRating']/tbody/tr")]
            
        for line in range(1,19):     
            if  (line+(18*(pageCounter-1)))<=len(table_lines):
                #print('linha', (line+(18*(pageCounter-1))))
            
                name_path = "((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[1]/a" 
                cotas_path = "((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[2]/div"
                series_path= "((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[3]/div"
                ratings_path ="((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[4]/div"
                perspectivas_path = "((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[5]/div"
                acao_ratings_path = "((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[6]/div"
                datas_path = "((//table[@id='tableRating']/tbody/tr)["+str(line+(18*(pageCounter-1)))+"]/td)[7]/div"
                
                link= driver.find_element_by_xpath(name_path).get_attribute("href")
                name = driver.find_element_by_xpath(name_path).text
                cota = driver.find_element_by_xpath(cotas_path).text
                serie = driver.find_element_by_xpath(series_path).text
                rating = driver.find_element_by_xpath(ratings_path).text
                perspectiva = driver.find_element_by_xpath(perspectivas_path).text
                acao_rating = driver.find_element_by_xpath(acao_ratings_path).text
                data = driver.find_element_by_xpath(datas_path).text
            
            
                links.append(str(link))
                names.append(str(name))
                cotas.append(str(cota))
                series.append(str(serie))
                ratings.append(str(rating))
                perspectivas.append(str(perspectiva))
                acao_ratings.append(str(acao_rating))
                datas.append(str(data))
            
            else:
                break        
                    
        df_austin = pd.DataFrame({"Nome":names, 
                            "Cota":cotas,
                            "Série":series,
                            "Rating":ratings,
                            "Perspectiva":perspectivas,
                            "Acao Rating":acao_ratings,
                            "Data":datas,
                            "Link":links}) 
      
        btns_page = [el.text for el in driver.find_elements_by_xpath("//div[@class='paging-nav']/a")]
        print(len(btns_page))
        
        
        if pageCounter!=len(btns_page)-2:
      
            nextpg_btn = driver.find_element_by_xpath("//div[@class='paging-nav']/a[@data-direction='1']")
            print("Mudando de página")
            
            nextpg_btn.click()            
            time.sleep(2)
            pageCounter+=1  
        else:
    
            pageCounter=False
    
    print('Scrap feito!')
    driver.close()   
    
    #Fazer chave para mesclas df novo e antigo
    #DF NEW
    df_austin['Cota2'] = np.where(df_austin['Cota'].str.contains('Seniores|Única'),'Senior','Subordinada')
    
    df_austin2 = pd.DataFrame()
    for nome in df_austin['Nome'].unique():
        
        df_aux2 = df_austin[df_austin['Nome']==nome]
        for cota in df_aux2['Cota2'].unique():
            
            df_aux = df_aux2[df_aux2['Cota2']==cota]
            df_aux=df_aux.reset_index()
            df_aux['index'] = df_aux.index+1
    
            df_austin2=df_austin2.append(df_aux)
          
    df_austin2['Cota3'] = df_austin2['Cota2'] + ' ' + df_austin2['index'].apply(str)
    df_austin2['key'] = df_austin2['Nome'] + ' ' + df_austin2['Cota3']

    #DF OLD
    df_austin_old['Cota2'] = np.where(df_austin_old['Cota'].str.contains('Seniores|Única'),'Senior','Subordinada')
    
    df_austin_old2 = pd.DataFrame()
    for nome in df_austin_old['Fundo'].unique():
        
        df_aux_old2 = df_austin_old[df_austin_old['Fundo']==nome]
        for cota in df_aux_old2['Cota2'].unique():
            
            df_aux_old = df_aux_old2[df_aux_old2['Cota2']==cota]
            df_aux_old=df_aux_old.reset_index()
            df_aux_old['index'] = df_aux_old.index+1
    
            df_austin_old2=df_austin_old2.append(df_aux_old)
          
    df_austin_old2['Cota3'] = df_austin_old2['Cota2'] + ' ' + df_austin_old2['index'].apply(str)
    df_austin_old2['key'] = df_austin_old2['Fundo'] + ' ' + df_austin_old2['Cota3']
    
    
    
    df_austin = df_austin2
    df_austin_old=df_austin_old2
    
    intersect_list = set(df_austin['key'].tolist()).intersection(set(df_austin_old['key'].tolist()))
    new_assets_list = set(df_austin['key'].tolist()) - set(df_austin_old['key'].tolist())
    old_assets_list = set(df_austin_old['key'].tolist()) - set(df_austin['key'].tolist())
    
    if len(intersect_list)>0:
        print('1) Intercessao entre as duas listas: ')

        [print('- ',x) for x in intersect_list]
    else:
        print ('1) Nenhum ativo em comum entre a analise nova e a antiga')

        
    if len(new_assets_list)>0:
        print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
        [print('- ',x) for x in new_assets_list]
    else:
        print('2) Nenhum ativo novo na nova analise')
        
        

    if len(old_assets_list)>0:
        
        print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
        [print('- ',x) for x in old_assets_list]
    else:
        print('3) Nenhum ativo antigo deixou de ser analisado')

    df_austin_old=df_austin_old.rename(columns={"Fundo":"Ativo",
                                        "Rating Nacional": "Rating Antigo", 
                                        "Data Rating":"Data Rating Antigo"})

    df_austin_old = df_austin_old[['CNPJ','ISIN','key', 'Rating Antigo','Data Rating Antigo']]
    
    df_austin = df_austin.merge(df_austin_old,how='left',on='key')
    #df_austin=df_austin.drop(['Cota3'], axis=1)
    
    
    #Arrumar CNPJ
    df_aux = pd.DataFrame()
    for nome in df_austin['Nome'].unique():
        print(nome)
        
        df_aux2= df_austin[df_austin['Nome']==nome]
        cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
        cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
        if len([cnpj_list])>1:
            #print('erro')
            break
        else:
            #print('ok')
            df_aux2['CNPJ2']=cnpj_list
            df_aux=df_aux.append(df_aux2)
            
            
    df_aux = df_aux.drop(['CNPJ', 'index'], axis=1)      
    df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'})      

    df_austin=df_aux
    df_austin['Agencia']='AUSTIN'
    
    df_austin['Data'] = df_austin['Data'].replace(to_replace=[''], value=np.nan, regex=True)
    df_austin['Data'] = pd.to_datetime(df_austin['Data'], format="%d/%m/%Y")
    
    print('DF arrumado!')
    
    return df_austin





def scrap_liberium (chrome_options,df_liberium_old):
    

    #SCRAP LIBERIUM RATING
    driver = webdriver.Chrome(executable_path="/Users/pedrocampelo/Projects/selenium/chromedriver", options = chrome_options)
    driver.get("http://www.liberumratings.com.br/lista_ratings.php?cd_ct_rt=MQ,,")
    
    
    print("Fazendo scrap para a agencia LIBERIUM")
    
    links=[]
    codes=[]
    names=[]
    acao_ratings=[]
    ratings_lp=[]
    ratings_cp=[]
    perspectivas=[]
    datas=[]
    dict_page={}
    
    
    for i in range(1,5):
        
        pageCounter=1
    
        asset_selected_path = "//select//option[@value='"+str(i)+"']"
        asset_selected = driver.find_element_by_xpath(asset_selected_path)
        
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, asset_selected_path)))
    
        print("Pegando informacoes sobre ", asset_selected.text)
        tipo_aux=str(asset_selected.text)
    
        asset_selected.click()
        time.sleep(2)
        
        while type(pageCounter) == int:
            
            print('Fazendo a coleta da página ',pageCounter)        
            table_lines = [el.text for el in driver.find_elements_by_xpath("//tr[@class='Texto']")]
            
                     
            for line in range(1,len(table_lines)+1):     
                #print('linha', line)
                       
                codes_path = "((//tr[@class='Texto'])["+str(line)+"]/td)[2]/a"
                names_path ="((//tr[@class='Texto'])["+str(line)+"]/td)[3]/a"
                acao_ratings_path = "((//tr[@class='Texto'])["+str(line)+"]/td)[4]/a"
                ratings_lp_path= "((//tr[@class='Texto'])["+str(line)+"]/td)[5]/a"
                ratings_cp_path="((//tr[@class='Texto'])["+str(line)+"]/td)[6]/a"
                perspectivas_path = "((//tr[@class='Texto'])["+str(line)+"]/td)[7]/a"
                datas_path = "((//tr[@class='Texto'])["+str(line)+"]/td)[8]/a"
                
                link= driver.find_element_by_xpath(codes_path).get_attribute("href")
                code = driver.find_element_by_xpath(codes_path).text
                name = driver.find_element_by_xpath(names_path).text
                acao_rating = driver.find_element_by_xpath(acao_ratings_path).text
                rating_lp = driver.find_element_by_xpath(ratings_lp_path).text
                rating_cp = driver.find_element_by_xpath(ratings_cp_path).text
                perspectiva = driver.find_element_by_xpath(perspectivas_path).text
                data = driver.find_element_by_xpath(datas_path).text
            
            
                links.append(str(link))
                codes.append(str(code))
                names.append(str(name))
                acao_ratings.append(str(acao_rating))
                ratings_lp.append(str(rating_lp))
                ratings_cp.append(str(rating_cp))
                perspectivas.append(str(perspectiva))
                datas.append(str(data))          
              
              
            dict_page[tipo_aux]= [pageCounter, line]
                
            df_liberium= pd.DataFrame({
                                        "Código":codes,
                                        "Nome":names, 
                                        "Acao Rating":acao_ratings,         
                                        "Rating Longo Prazo":ratings_lp,
                                        "Rating Curto Prazo":ratings_cp,
                                        "Perspectiva":perspectivas,
                                        "Data":datas,
                                        "Link":links}) 
                  
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//td[@class='Texto']/a)[1]")))
    
            btns_page = [el.text for el in driver.find_elements_by_xpath("//td[@class='Texto']/a")]
            print(len(btns_page))        
            print(btns_page)
            
            
            if 'Próxima >' in btns_page:
                
                btn_path = "(//td[@class='Texto']/a)["+str(btns_page.index('Próxima >')+1)+"]"
                next_btn = driver.find_element_by_xpath(btn_path) 
    
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, btn_path)))
                print("Mudando de página")
                
                next_btn.click()            
                time.sleep(2)
                pageCounter+=1  
                
            else:
                pageCounter=False
    
        
    driver.close()
    
    fidc_type=[]
    n_pages = []
    for fidc in dict_page.keys():
        pages = dict_page[fidc][0]
        n_page = dict_page[fidc][1]
           
        fidc_type.extend([fidc]*(20*(pages-1)))    
        fidc_type.extend([fidc]*n_page)       
        
        n_pages.extend(np.repeat([i+1 for i in range(pages-1)],20))
        n_pages.extend([pages]*n_page)
    
    
    df_liberium['Tipo FIDC'] = fidc_type
    df_liberium['Pagina'] = n_pages
    
    
    df_liberium_aux = pd.DataFrame(df_liberium.Nome.str.split(' - ',3).tolist())
    df_liberium_aux = df_liberium_aux.replace(to_replace=[None], value='')
    
    df_liberium_aux['FIDC'] = np.where(df_liberium_aux[1].str.contains('Cota'), 
                                        df_liberium_aux[0],
                                        df_liberium_aux[0]+' '+df_liberium_aux[1])
    df_liberium_aux['Cota'] = np.where(df_liberium_aux[1].str.contains('Cota'), 
                                        df_liberium_aux[1]+' '+df_liberium_aux[2]+' '+df_liberium_aux[3], 
                                        df_liberium_aux[2]+' '+df_liberium_aux[3])
    
    df_liberium_aux['Cota'] = df_liberium_aux['Cota'].replace(to_replace=[' - '], value='', regex=True)
    
    df_liberium['FIDC']=df_liberium_aux['FIDC']
    df_liberium['Cota']=df_liberium_aux['Cota']
    
    
    df_liberium = df_liberium[['Código', 'Nome', 'FIDC', 'Cota','Acao Rating', 'Rating Longo Prazo',
                                'Rating Curto Prazo', 'Perspectiva', 'Data', 'Link']]  

    
    df_liberium_old['Fundo'] = df_liberium_old['Fundo'].str.strip()
    
    
    #CRIAR CHAVE PARA MESCLAR BASE ANTIGA COM NOVA
    #DF NEW
    df_liberium['Cota2'] = np.where(df_liberium['Cota'].str.contains('Sênior|Única'),'Senior','Subordinada')

    
    df_liberium2 = pd.DataFrame()
    for fidc in df_liberium['FIDC'].unique():
        
        df_aux2 = df_liberium[df_liberium['FIDC']==fidc]
        for cota in df_aux2['Cota2'].unique():
            
            df_aux = df_aux2[df_aux2['Cota2']==cota]
            df_aux=df_aux.reset_index()
            df_aux['index'] = df_aux.index+1
    
            df_liberium2=df_liberium2.append(df_aux)
          
    df_liberium2['Cota3'] = df_liberium2['Cota2'] + ' ' + df_liberium2['index'].apply(str)
    df_liberium2['key'] = df_liberium2['FIDC'] + ' ' + df_liberium2['Cota3']

    #DF OLD
    df_liberium_old['Cota2'] = np.where(df_liberium_old['Cota'].str.contains('Sênior|Única'),'Senior','Subordinada')
    
    df_liberium_old2 = pd.DataFrame()
    for nome in df_liberium_old['Fundo'].unique():
        
        df_aux_old2 = df_liberium_old[df_liberium_old['Fundo']==nome]
        for cota in df_aux_old2['Cota2'].unique():
            
            df_aux_old = df_aux_old2[df_aux_old2['Cota2']==cota]
            df_aux_old=df_aux_old.reset_index()
            df_aux_old['index'] = df_aux_old.index+1
    
            df_liberium_old2=df_liberium_old2.append(df_aux_old)
          
    df_liberium_old2['Cota3'] = df_liberium_old2['Cota2'] + ' ' + df_liberium_old2['index'].apply(str)
    df_liberium_old2['key'] = df_liberium_old2['Fundo'] + ' ' + df_liberium_old2['Cota3']
    
        
    df_liberium = df_liberium2
    df_liberium_old=df_liberium_old2
    
    
    #ARRUMAR AQUI   
    intersect_list = set(df_liberium['key'].tolist()).intersection(set(df_liberium_old['key'].tolist()))
    new_assets_list = set(df_liberium['key'].tolist()) - set(df_liberium_old['key'].tolist())
    old_assets_list = set(df_liberium_old['key'].tolist()) - set(df_liberium['key'].tolist())
    
    if len(intersect_list)>0:
        print('1) Intercessao entre as duas listas: ')

        [print('- ',x) for x in intersect_list]
    else:
        print ('1) Nenhum ativo em comum entre a analise nova e a antiga')

        
    if len(new_assets_list)>0:
        print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
        [print('- ',x) for x in new_assets_list]
    else:
        print('2) Nenhum ativo novo na nova analise')
        
        

    if len(old_assets_list)>0:
        
        print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
        [print('- ',x) for x in old_assets_list]
    else:
        print('3) Nenhum ativo antigo deixou de ser analisado')


    df_liberium_old=df_liberium_old.rename(columns={"Fundo":"Ativo",
                                        "Rating Nacional": "Rating Antigo", 
                                        "Data Rating":"Data Rating Antigo"})

    df_liberium_old = df_liberium_old[['CNPJ','ISIN','Rating Antigo','Data Rating Antigo','key']]

    df_liberium = df_liberium.merge(df_liberium_old,how='left',on='key')
    
    
    #Arrumar CNPJ
    df_aux = pd.DataFrame()
    for fidc in df_liberium['FIDC'].unique():
        print(fidc)
        
        df_aux2= df_liberium[df_liberium['FIDC']==fidc]
        cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
        cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
        if len([cnpj_list])>1:
            #print('erro')
            break
        else:
            #print('ok')
            df_aux2['CNPJ2']=cnpj_list
            df_aux=df_aux.append(df_aux2)
            
            
    df_aux = df_aux.drop(['CNPJ', 'index'], axis=1)      
    df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'})      

    df_liberium=df_aux
    df_liberium['Agencia']='LIBERIUM'
        
    df_liberium['Data'] = df_liberium['Data'].replace(to_replace=[''], value=np.nan, regex=True)
    df_liberium['Data'] = pd.to_datetime(df_liberium['Data'], format="%d/%m/%Y")

    print('DF arrumado!')
    
    return df_liberium







def scrap_sr (chrome_options,df_sr_old):
    
    
    #APPEND SR RATING
    #ESSE EXCEL É TIRADO DO SITE QUANDO FOR RODAR
    df_sr_aux = pd.read_excel('Scrapp Rating/SR_rating.xlsx')
    
    n1=df_sr_aux[df_sr_aux['RATING ATIVOS'].str.contains("RATING DE FUNDOS DE INVESTIMENTOS", na=False)].index[0]
    # n1=df_sr.loc[df_sr['RATING ATIVOS'] == "RATING DE FUNDOS DE INVESTIMENTOS"].index[0]
    n2=df_sr_aux[df_sr_aux['RATING ATIVOS'].str.contains("RATING DE QUALIDADE DE GESTÃO", na=False)].index[0]
    # n2=df_sr.loc[df_sr['RATING ATIVOS'] == "RATING DE QUALIDADE DE GESTÃO"].index[0]
    
    # df_sr = df_sr_aux.iloc[[i for i in range(n1+1,n2-2)], :]
    df_sr = df_sr_aux.iloc[n1+1:n2-2]
    df_sr.columns = df_sr.iloc[0]
    df_sr = df_sr.iloc[1:]
    df_sr = df_sr.reset_index()
    
    df_sr['FUNDO'] = df_sr['FUNDO'].replace(r'\n',' - ', regex=True) 
    df_sr_aux = pd.DataFrame(df_sr['FUNDO'].str.split(' - ',2).tolist())
    df_sr_aux=df_sr_aux.replace(to_replace=[None], value='')
    
    df_sr_aux['FIDC'] = np.where(df_sr_aux[2]!='', df_sr_aux[0]+' - '+df_sr_aux[2],df_sr_aux[0])
    df_sr_aux = df_sr_aux.rename(columns={1: "Cota"})
    
    df_sr['FIDC']=df_sr_aux['FIDC']
    df_sr['Cota']=df_sr_aux['Cota']
    
    df_sr = df_sr[['FUNDO','FIDC','Cota','NOTA GLOBAL','EQUIVALÊNCIA BR','TENDÊNCIA',
                    'VIGÊNCIA DA CLASSIFICAÇÃO', 'RELATÓRIO', 'INFORMAÇÃO ADICIONAL']]
    
    
    #CRIAR CHAVE PARA MESCLAR BASE ANTIGA COM NOVA
    #DF NEW
    df_sr['Cota2'] = np.where(df_sr['Cota'].str.contains('SÊNIOR|ÚNICA'),'Senior','Subordinada')

    
    df_sr2 = pd.DataFrame()
    for fidc in df_sr['FIDC'].unique():
        
        df_aux2 = df_sr[df_sr['FIDC']==fidc]
        for cota in df_aux2['Cota2'].unique():
            
            df_aux = df_aux2[df_aux2['Cota2']==cota]
            df_aux=df_aux.reset_index()
            df_aux['index'] = df_aux.index+1
    
            df_sr2=df_sr2.append(df_aux)
          
    df_sr2['Cota3'] = df_sr2['Cota2'] + ' ' + df_sr2['index'].apply(str)
    df_sr2['key'] = df_sr2['FIDC'] + ' ' + df_sr2['Cota3']


    #DF OLD
    df_sr_old['Cota2'] = np.where(df_sr_old['Cota'].str.contains('SÊNIOR|ÚNICA'),'Senior','Subordinada')
    
    df_sr_old2 = pd.DataFrame()
    for nome in df_sr_old['Fundo'].unique():
        
        df_aux_old2 = df_sr_old[df_sr_old['Fundo']==nome]
        for cota in df_aux_old2['Cota2'].unique():
            
            df_aux_old = df_aux_old2[df_aux_old2['Cota2']==cota]
            df_aux_old=df_aux_old.reset_index()
            df_aux_old['index'] = df_aux_old.index+1
    
            df_sr_old2=df_sr_old2.append(df_aux_old)
          
    df_sr_old2['Cota3'] = df_sr_old2['Cota2'] + ' ' + df_sr_old2['index'].apply(str)
    df_sr_old2['key'] = df_sr_old2['Fundo'] + ' ' + df_sr_old2['Cota3']    
    
    df_sr = df_sr2
    df_sr_old=df_sr_old2
         
    
    intersect_list = set(df_sr['key'].tolist()).intersection(set(df_sr_old['key'].tolist()))
    new_assets_list = set(df_sr['key'].tolist()) - set(df_sr_old['key'].tolist())
    old_assets_list = set(df_sr_old['key'].tolist()) - set(df_sr['key'].tolist())
    
    if len(intersect_list)>0:
        print(len(intersect_list))
        print('1) Intercessao entre as duas listas: ')

        [print('- ',x) for x in intersect_list]
    else:
        print ('1) Nenhum ativo em comum entre a analise nova e a antiga')

        
    if len(new_assets_list)>0:
        print(len(new_assets_list))

        print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
        [print('- ',x) for x in new_assets_list]
    else:
        print('2) Nenhum ativo novo na nova analise')       
        

    if len(old_assets_list)>0:
        print(len(old_assets_list))
        print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
        [print('- ',x) for x in old_assets_list]
    else:
        print('3) Nenhum ativo antigo deixou de ser analisado')

    df_sr_old=df_sr_old.rename(columns={"Fundo":"Ativo",
                                        "Rating Nacional": "Rating Antigo", 
                                        "Data Vencimento":"Data Vencimento Antigo"})
    df_sr_old = df_sr_old[['CNPJ','ISIN','Ativo','Rating Antigo','Data Vencimento Antigo','key']]
        
    df_sr = df_sr.merge(df_sr_old,how='left',on='key')
   
    #Arrumar CNPJ
    df_aux = pd.DataFrame()
    for nome in df_sr['FUNDO'].unique():
        print(nome)
        
        df_aux2= df_sr[df_sr['FUNDO']==nome]
        cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
        cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
        if len([cnpj_list])>1:
            #print('erro')
            break
        else:
            #print('ok')
            df_aux2['CNPJ2']=cnpj_list
            df_aux=df_aux.append(df_aux2)
            
            
    df_aux = df_aux.drop(['CNPJ','index'], axis=1)      
    df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'})      

    df_sr=df_aux
    df_sr['Agencia']='SR'
    
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=[''], value=np.nan, regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['janeiro'], value='01', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['fevereiro'], value='02', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['marco'], value='03', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['abril'], value='04', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['maio'], value='05', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['junho'], value='06', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['julho'], value='07', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['agosto'], value='08', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['setembro'], value='09', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['outubro'], value='10', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['novembro'], value='11', regex=True)
    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'].replace(to_replace=['dezembro'], value='12', regex=True)

    df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'] = pd.to_datetime(df_sr['VIGÊNCIA DA CLASSIFICAÇÃO'], format="%m-%y")
    
    
    
    #df_sr['Data'] = df_sr['Data'].replace(to_replace=[''], value=np.nan, regex=True)
    #df_sr['Data'] = pd.to_datetime(df_sr['Data'], format="%d/%m/%Y")
    
    
    print('DF arrumado!')
    
    return df_sr


def scrap_sp (chrome_options,df_sp_old):
    
    

    # #SCRAP SP RATING
    driver = webdriver.Chrome(executable_path="/Users/pedrocampelo/Projects/selenium/chromedriver", options = chrome_options)
    driver.get("https://www.standardandpoors.com/pt_LA/web/guest/ratings/search/-/search/searchType/E/searchTerm/FUNDO")
    
    
    sign_btn = driver.find_element_by_xpath("//li[@class='signin']/a")
    sign_btn.click()
    
    login = "pedroalbuquerque@funcef.com.br"
    password = "Campominado1"
    
    email_login = driver.find_element_by_xpath("(//input[@type='email'])[2]")
    email_login.send_keys(login)
    
    password_login = driver.find_element_by_xpath("(//input[@type='password'])[2]")
    password_login.send_keys(password)
        
    btn_login = driver.find_element_by_xpath("//button[@id='submitForm']")
    
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@id='submitForm']")))
    btn_login.click()
    
    time.sleep(2)
    
    names=[]
    links=[]
    cotas=[]
    datas_venc=[]
    tipos_rating=[]
    ratings=[]
    datas_rating=[]
    datas_revisao=[]
    regulatorios=[]
    perspectivas=[]
    data_perspectivas=[]
    
    print('bb')
    
    fidcs_tables = [el.text for el in driver.find_elements_by_xpath("//table/tbody/tr/td/a")]
    for fidc in range(1,len(fidcs_tables)+1):     
    
        
        fidc_path = "(//table/tbody/tr/td/a)[" + str(fidc) + "]"
        fidc_btn = driver.find_element_by_xpath(fidc_path)
        
        name=fidc_btn.text
        link= fidc_btn.get_attribute("href")
        
        print('Fazendo scrapp do rating do FIDC ', name)
        
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, fidc_path)))
        fidc_btn.click()
        
        
        issue_list = [el.text for el in driver.find_elements_by_xpath("//table//thead/tr/th")]
        print(len(issue_list))
        
        if len(issue_list)==1:
            print('Tem issue_list')
            time.sleep(.5)
            fidc_last_report = driver.find_element_by_xpath("(//table/tbody/tr/td/a)[1]")
            
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr/td/a[1]")))
            fidc_last_report.click()
        
            table_lines = [el.text for el in driver.find_elements_by_xpath("(//table)[1]/tbody/tr")]         
            for line in range(1,len(table_lines)+1):     
                #print('linha', line)
                
                time.sleep(.5)
        
                      
                cotas_path = "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[1]" 
                datas_venc_path ="(((//table)[1]/tbody/tr)["+str(line)+"]/td)[2]" 
                tipos_rating_path = "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[3]" 
                ratings_path = "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[4]" 
                datas_rating_path= "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[5]" 
                data_revisao_path= "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[6]" 
                regulatorios_path = "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[7]" 
                perspectivas_path="(((//table)[1]/tbody/tr)["+str(line)+"]/td)[8]" 
                data_perspectivas_path = "(((//table)[1]/tbody/tr)["+str(line)+"]/td)[9]" 
                
                # name = driver.find_element_by_xpath(names_path).text
                # link= driver.find_element_by_xpath(names_path).get_attribute("href")
                cota = driver.find_element_by_xpath(cotas_path).text
                data_venc = driver.find_element_by_xpath(datas_venc_path).text    
                tipo_rating = driver.find_element_by_xpath(tipos_rating_path).text
                rating = driver.find_element_by_xpath(ratings_path).text    
                data_rating = driver.find_element_by_xpath(datas_rating_path).text
                data_revisao= driver.find_element_by_xpath(data_revisao_path).text
                regulatorio= driver.find_element_by_xpath(regulatorios_path).text
                perspectiva = driver.find_element_by_xpath(perspectivas_path).text
                data_perspectiva = driver.find_element_by_xpath(data_perspectivas_path).text
                
                names.append(str(name))
                links.append(str(link))
                cotas.append(str(cota))
                datas_venc.append(str(data_venc))
                tipos_rating.append(str(tipo_rating))
                ratings.append(str(rating))
                datas_rating.append(str(data_rating))
                datas_revisao.append(str(data_revisao))
                regulatorios.append(str(regulatorio))
                perspectivas.append(str(perspectiva))
                data_perspectivas.append(str(data_perspectiva))
                
            print("FIDC coletado")    
            
            driver.back()
            driver.back()
            
            time.sleep(2)
        
        else:
            driver.back()
            time.sleep(2)
            
            
        df_sp= pd.DataFrame({
                            "Nome":names, 
                            "Cota":cotas,
                            "Data Vencimento": datas_venc,
                            "Tipo Rating":tipos_rating,
                            "Rating":ratings,
                            "Data":datas_rating,         
                            "Data Revisao":datas_revisao,
                            "Regulatorio":regulatorios,
                            "Perspectiva":perspectivas,
                            "Data Perspectivas":data_perspectivas,
                            "Link":links}) 
        
    driver.close()
     
    #CRIAR CHAVE PARA MESCLAR BASE ANTIGA COM NOVA
    #DF NEW
    df_sp['Cota2'] = np.where(df_sp['Cota'].str.contains('Mezz|Sub'),'Subordinada','Senior')
    
    df_sp2 = pd.DataFrame()
    for fidc in df_sp['Nome'].unique():
        
        df_aux2 = df_sp[df_sp['Nome']==fidc]
        for cota in df_aux2['Cota2'].unique():
            
            df_aux = df_aux2[df_aux2['Cota2']==cota]
            df_aux=df_aux.reset_index()
            df_aux['index'] = df_aux.index+1
    
            df_sp2=df_sp2.append(df_aux)
          
    df_sp2['Cota3'] = df_sp2['Cota2'] + ' ' + df_sp2['index'].apply(str)
    df_sp2['key'] = df_sp2['Nome'] + ' ' + df_sp2['Cota3']


    #DF OLD
    df_sp_old['Cota2'] = np.where(df_sp_old['Cota'].str.contains('Mezz|Sub'),'Subordinada','Senior')
    
    df_sp_old2 = pd.DataFrame()
    for nome in df_sp_old['Fundo'].unique():
        
        df_aux_old2 = df_sp_old[df_sp_old['Fundo']==nome]
        for cota in df_aux_old2['Cota2'].unique():
            
            df_aux_old = df_aux_old2[df_aux_old2['Cota2']==cota]
            df_aux_old=df_aux_old.reset_index()
            df_aux_old['index'] = df_aux_old.index+1
    
            df_sp_old2=df_sp_old2.append(df_aux_old)
          
    df_sp_old2['Cota3'] = df_sp_old2['Cota2'] + ' ' + df_sp_old2['index'].apply(str)
    df_sp_old2['key'] = df_sp_old2['Fundo'] + ' ' + df_sp_old2['Cota3']    
    
    df_sp = df_sp2
    df_sp_old=df_sp_old2
    
    #ARRUMAR AQUI   
    intersect_list = set(df_sp['key'].tolist()).intersection(set(df_sp_old['key'].tolist()))
    new_assets_list = set(df_sp['key'].tolist()) - set(df_sp_old['key'].tolist())
    old_assets_list = set(df_sp_old['key'].tolist()) - set(df_sp['key'].tolist())
    
    if len(intersect_list)>0:
        print('1) Intercessao entre as duas listas: ')

        [print('- ',x) for x in intersect_list]
    else:
        print ('1) Nenhum ativo em comum entre a analise nova e a antiga')

        
    if len(new_assets_list)>0:
        print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
        [print('- ',x) for x in new_assets_list]
    else:
        print('2) Nenhum ativo novo na nova analise')       

    if len(old_assets_list)>0:
        
        print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
        [print('- ',x) for x in old_assets_list]
    else:
        print('3) Nenhum ativo antigo deixou de ser analisado')
        
               

    df_sp_old=df_sp_old.rename(columns={"Fundo":"Ativo",
                                        "Rating Nacional": "Rating Antigo", 
                                        "Data Rating":"Data Rating Antigo", 
                                        "Data Vencimento":"Data Vencimento Antigo"})

    df_sp_old = df_sp_old[['CNPJ','ISIN','Ativo','Rating Antigo',
                           'Data Rating Antigo', 'Data Vencimento Antigo', 'key']]

    
    df_sp = df_sp.merge(df_sp_old,how='left',on='key')
    
    df_aux = pd.DataFrame()
    for nome in df_sp['Nome'].unique():
        print(nome)
        
        df_aux2= df_sp[df_sp['Nome']==nome]
        cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
        cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
        if len([cnpj_list])>1:
            #print('erro')
            break
        else:
            #print('ok')
            df_aux2['CNPJ2']=cnpj_list
            df_aux=df_aux.append(df_aux2)
            
            
    df_aux = df_aux.drop(['CNPJ', 'index'], axis=1)      
    df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'})      

    df_sp=df_aux
    df_sp['Agencia']='SP'
    
    df_sp['Data'] = df_sp['Data'].replace(to_replace=[''], value=np.nan, regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Jan'], value='01', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Fev'], value='02', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Mar'], value='03', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Abr'], value='04', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Mai'], value='05', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Jun'], value='06', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Jul'], value='07', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Ago'], value='08', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Set'], value='09', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Out'], value='10', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Nov'], value='11', regex=True)
    df_sp['Data'] = df_sp['Data'].replace(to_replace=['Dez'], value='12', regex=True)

    df_sp['Data'] = pd.to_datetime(df_sp['Data'], format="%d-%m-%Y")
    
    
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=[''], value=np.nan, regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Jan'], value='01', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Fev'], value='02', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Mar'], value='03', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Abr'], value='04', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Mai'], value='05', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Jun'], value='06', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Jul'], value='07', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Ago'], value='08', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Set'], value='09', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Out'], value='10', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Nov'], value='11', regex=True)
    df_sp['Data Vencimento'] = df_sp['Data Vencimento'].replace(to_replace=['Dez'], value='12', regex=True)

    df_sp['Data Vencimento'] = pd.to_datetime(df_sp['Data Vencimento'], format="%d-%m-%Y")
    
    print('DF arrumado!')
        
    return df_sp




def scrap_moodys(df_moody_old,new):
    
    
    # SCRAP MOODY RATING
    #PESQUISAR NO SITE, PEGAR PDF E PASSAR PRO EXCEL

    df_moody = pd.read_excel('Scrapp Rating/MOODYS_rating.xlsx')
    
    #CRIAR CHAVE PARA MESCLAR BASE ANTIGA COM NOVA
    #DF NEW
    df_moody['Cota2'] = np.where(df_moody['Cota'].str.contains('Sub'),'Subordinada','Senior')
    
    
    df_moody2 = pd.DataFrame()
    for fidc in df_moody['Fundo'].unique():
        
        df_aux2 = df_moody[df_moody['Fundo']==fidc]
        for cota in df_aux2['Cota2'].unique():
            
            df_aux = df_aux2[df_aux2['Cota2']==cota]
            df_aux=df_aux.reset_index()
            df_aux['index'] = df_aux.index+1
    
            df_moody2=df_moody2.append(df_aux)
          
    df_moody2['Cota3'] = df_moody2['Cota2'] + ' ' + df_moody2['index'].apply(str)
    df_moody2['key'] = df_moody2['Fundo'] + ' ' + df_moody2['Cota3']
    
    df_moody = df_moody2

    
    if new==1:

    
        #DF OLD
        df_moody_old['Cota2'] = np.where(df_moody_old['Cota'].str.contains('Sub'),'Subordinada','Senior')
    
        
        df_moody_old2 = pd.DataFrame()
        for fidc in df_moody_old['Fundo'].unique():
            
            df_aux_old2 = df_moody_old[df_moody_old['Fundo']==fidc]
            for cota in df_aux_old2['Cota2'].unique():
                
                df_aux_old = df_aux_old2[df_aux_old2['Cota2']==cota]
                df_aux_old=df_aux_old.reset_index()
                df_aux_old['index'] = df_aux_old.index+1
        
                df_moody_old2=df_moody_old2.append(df_aux_old)
              
        df_moody_old2['Cota3'] = df_moody_old2['Cota2'] + ' ' + df_moody_old2['index'].apply(str)
        df_moody_old2['key'] = df_moody_old2['Fundo'] + ' ' + df_moody_old2['Cota3']    
        
        df_moody_old=df_moody_old2
        
        #ARRUMAR AQUI   
        intersect_list = set(df_moody['key'].tolist()).intersection(set(df_moody_old['key'].tolist()))
        new_assets_list = set(df_moody['key'].tolist()) - set(df_moody_old['key'].tolist())
        old_assets_list = set(df_moody_old['key'].tolist()) - set(df_moody['key'].tolist())
        
        if len(intersect_list)>0:
            print('1) Intercessao entre as duas listas: ')
    
            [print('- ',x) for x in intersect_list]
        else:
            print ('1) Nenhum ativo em comum entre a analise nova e a antiga')
    
            
        if len(new_assets_list)>0:
            print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
            [print('- ',x) for x in new_assets_list]
        else:
            print('2) Nenhum ativo novo na nova analise')
            
            
    
        if len(old_assets_list)>0:
            
            print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
            [print('- ',x) for x in old_assets_list]
        else:
            print('3) Nenhum ativo antigo deixou de ser analisado')
            
                   
    
        df_moody_old=df_moody_old.rename(columns={"Fundo":"Ativo",
                                            "Ratings Nacional": "Rating Antigo", 
                                            "Data Rating":"Data Rating Antigo"})
    
        if 'CNPJ' in df_moody.columns:      
            df_moody_old = df_moody_old.drop(['CNPJ'], axis=1)      
    
        if 'ISIN' in df_moody.columns:      
            df_moody_old = df_moody_old.drop(['ISIN'], axis=1)         
            
        if 'CNPJ|ISIN' in df_moody.columns:
            df_moody_old = df_moody_old[['CNPJ','ISIN','Ativo','Rating Antigo','Data Rating Antigo','key']]
        else:
            df_moody_old = df_moody_old[['Ativo','Rating Antigo','Data Rating Antigo','key']]
        
      
        df_moody = df_moody.merge(df_moody_old,how='left',on='key')
        
    
        df_aux = pd.DataFrame()
        for fidc in df_moody['Fundo'].unique():
            print(fidc)
            
            df_aux2= df_moody[df_moody['Fundo']==fidc]
            cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
            cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
            if len([cnpj_list])>1:
                #print('erro')
                break
            else:
                #print('ok')
                df_aux2['CNPJ2']=cnpj_list
                df_aux=df_aux.append(df_aux2)
                
                
        df_aux = df_aux.drop(['CNPJ','index'], axis=1)      
        df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'}) 
        
        df_moody=df_aux
        df_moody['Agencia']='MOODYS'

    
        
        print('DF arrumado!')
    
    return df_moody






def scrap_fitch(df_fitch_old):
    
    
    #SCRAP FITCH RATING
    driver = webdriver.Chrome(executable_path="/Users/pedrocampelo/Projects/selenium/chromedriver", options = chrome_options)
    driver.get("https://www.fitchratings.com/search?expanded=issue&filter.country=Brazil&filter.sector=Structured%20Finance&isIdentifier=true&sort=recency")
    
    time.sleep(3)

    
    print("Fazendo scrap para a agencia FITCH")
    
    links=[]
    cotas=[]
    names=[]
    ratings=[]
    acao_ratings=[]
    perspectivas=[]
    datas=[]
            
    pageCounter=1
    
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='column__three column--merge-a'])[1]")))
    time.sleep(3)
    
    while type(pageCounter) == int:
        
        print('Fazendo a coleta da página ',pageCounter)        
        table_lines = [el.text for el in driver.find_elements_by_xpath("(//div[@class='column__three column--merge-a'])[1]/div")]
        
        
        
        print('elements', len(table_lines))
        if len(table_lines)==0:
            driver.refresh()
            time.sleep(5)
            table_lines = [el.text for el in driver.find_elements_by_xpath("(//div[@class='column__three column--merge-a'])[1]/div")]
            print('elements', len(table_lines))
            
            
            
        for line in range(1,len(table_lines)+1):     
            #print('linha', line)
                   
            names_path = "(((//div[@class='column__three column--merge-a'])[1]/div)["+str(line)+"]/div)[1]"
            cotas_path = "((//div[@class='column__three column--merge-a'])[1]/div)["+str(line)+"]/h3/a"
            ratings_path= "(((//table[@class='table__wrapper'])["+str(line)+"]/tbody/tr)[1]/td)[1]"
            acao_ratings_path="(((//table[@class='table__wrapper'])["+str(line)+"]/tbody/tr)[1]/td)[2]"
            datas_path = "(((//table[@class='table__wrapper'])["+str(line)+"]/tbody/tr)[1]/td)[3]"
            perspectivas_path = "((//table[@class='table__wrapper'])["+str(line)+"]/tbody/tr)[2]/td/p"
            
            name = driver.find_element_by_xpath(names_path).text
            link= driver.find_element_by_xpath(cotas_path).get_attribute("href")
            cota = driver.find_element_by_xpath(cotas_path).text
            acao_rating = driver.find_element_by_xpath(acao_ratings_path).text
            rating = driver.find_element_by_xpath(ratings_path).text
            perspectiva = driver.find_element_by_xpath(perspectivas_path).text
            data = driver.find_element_by_xpath(datas_path).text
            
            links.append(str(link))
            cotas.append(str(cota))
            names.append(str(name))
            acao_ratings.append(str(acao_rating))
            ratings.append(str(rating))
            perspectivas.append(str(perspectiva))
            datas.append(str(data))          
          
          
            
        df_fitch_scrapped = pd.DataFrame({"Cota":cotas,
                                            "Nome":names, 
                                            "Acao Rating":acao_ratings,         
                                            "Rating":ratings,
                                            "Perspectiva":perspectivas,
                                            "Data":datas,
                                            "Link":links}) 
        
        print('tamanho df',len(df_fitch_scrapped))
        time.sleep(2)
      
        #element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//ul[@class='pager__items']/li/a")))

        btns_page = [el.text for el in driver.find_elements_by_xpath("//ul[@class='pager__items']/li")]
        #print(len(btns_page))        
        
        
        if len(btns_page)==0:
            print("AAAAAAA")
            driver.refresh()
            time.sleep(3)
            btns_page = [el.text for el in driver.find_elements_by_xpath("//ul[@class='pager__items']/li")]
            print(len(btns_page))        
            print(btns_page)
            
        
        if '»' in btns_page or pageCounter<16:
            
            btn_path = "(//ul[@class='pager__items']/li)["+str(btns_page.index('»')+1)+"]/a"
            next_btn = driver.find_element_by_xpath(btn_path) 

            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, btn_path)))
            print("Mudando de página")
            
            next_btn.click()            
            time.sleep(2)
            pageCounter+=1  
            
        elif pageCounter>15:
            
            n_page = int(btns_page[-1])
            if pageCounter<n_page:
                
                print('> 15')           
                btn_path = "(//ul[@class='pager__items']/li)["+str(btns_page.index(str(pageCounter))+2)+"]/a"
                next_btn = driver.find_element_by_xpath(btn_path) 
                    
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, btn_path)))
                print("Mudando de página")
                
                next_btn.click()            
                time.sleep(2)
                pageCounter+=1  
            else:
                print('Nao tem mais pagina')
                pageCounter=False 
                 
        else:
            print('Nao tem mais pagina')
            pageCounter=False          
    driver.close()
   
    
    df_fitch = df_fitch_scrapped.copy()
   
    #SET NAME COLUMN    
    df_fitch['flag'] = np.where(df_fitch['Nome'].str.contains('FUNDO|FIDC'),1,0)
    df_fitch=df_fitch[df_fitch['flag']==1]
    df_fitch=df_fitch.drop('flag', axis=1)
    df_fitch['Nome'] = df_fitch['Nome'].replace(to_replace=['ENTITY / '], value='', regex=True)

    #SET AND FILTER DATA COLUMN
    df_fitch['Data']=df_fitch['Data'].replace(to_replace=[''], value=np.nan, regex=True)
    df_fitch['Data'] = pd.to_datetime(df_fitch['Data'], format="%d %b %Y")
    df_fitch['flag'] = np.where((df_fitch['Data']>dt.datetime.strptime('2017-01-01', "%Y-%m-%d").strftime("%Y-%m-%d"))|
                                (df_fitch['Data'].isnull()),
                                1,0)
    df_fitch=df_fitch[df_fitch['flag']==1]
    df_fitch=df_fitch.drop('flag', axis=1)
   
    #FILTER RATING COLUMN
    df_fitch['flag'] = np.where(df_fitch['Rating'].str.contains('PIF|WD|NR|F1'),0,1)
    df_fitch=df_fitch[df_fitch['flag']==1]
    df_fitch=df_fitch.drop('flag', axis=1)
    
    
    #CRIAR CHAVE PARA MESCLAR BASE ANTIGA COM NOVA
    #DF NEW
    
    df_fitch2 = pd.DataFrame()
    for fidc in df_fitch['Nome'].unique():
        
        df_aux2 = df_fitch[df_fitch['Nome']==fidc]
        ratings = df_aux2.Rating.unique()
        
        if len(ratings)>1:
            #print(fidc)
            #print(ratings)
            
            if any("AAA" in s for s in ratings):            
                df_aux2['Cota2']=np.where(df_aux2['Rating'].str.contains('AAA'),'Senior','Subordinada')
                #df_fitch2 = df_fitch2.append(df_aux2)
            
            elif any("AA" in s for s in ratings):           
                df_aux2['Cota2']=np.where(df_aux2['Rating'].str.contains('AA'),'Senior','Subordinada')
                #df_fitch2 = df_fitch2.append(df_aux2)
                
            elif any("A" in s for s in ratings):           
                df_aux2['Cota2']=np.where(df_aux2['Rating'].str.contains('A'),'Senior','Subordinada')
                #df_fitch2 = df_fitch2.append(df_aux2)
                
            else:              
               df_aux2['Cota2']=np.where(df_aux2['Cota'].str.contains('Senior'),'Senior','Subordinada')
                        
        else:
           
            #print('menor que 1')
            df_aux2['Cota2']=np.where((df_aux2['Cota'].str.contains('Senior')|
                                       (df_aux2['Rating'].str.contains('AAA|AA|A'))),'Senior','Subordinada')
            #df_fitch2 = df_fitch2.append(df_aux2)  
            
        
        for cota in df_aux2['Cota2'].unique():
            
            df_aux = df_aux2[df_aux2['Cota2']==cota]
            df_aux=df_aux.reset_index()
            df_aux['index'] = df_aux.index+1
    
            df_fitch2 = df_fitch2.append(df_aux)
            
            
    df_fitch2['Cota3'] = df_fitch2['Cota2'] + ' ' + df_fitch2['index'].apply(str)
    df_fitch2['key'] = df_fitch2['Nome'] + ' ' + df_fitch2['Cota3']   
    df_fitch2['key'] = df_fitch2['key'].replace(to_replace=['FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS ','FUNDO DE INVESTIMENTOS EM DIREITOS CREDITORIOS ', 'FIDC '], value='', regex=True)
    df_fitch2['key'] = df_fitch2['key'].replace(to_replace=['FORTBRASIL Subordinada'], value='FORTBRASIL Senior', regex=True)

    df_fitch = df_fitch2.drop(['index'], axis=1)
                            

    #DF OLD    
    df_fitch_old['Fundo']=df_fitch_old['Fundo'].str.strip()
    df_fitch_old['Link']=''
    
    # #pesquisa de mudancas de ratings na mao (so acima de A)
    # df_fitch_old['Rating Nacional'] = np.where(df_fitch_old['Fundo']=='SANASA FIDC','AA (bra)',df_fitch_old['Rating Nacional'])
    # df_fitch_old['Link'] = np.where(df_fitch_old['Fundo']=='SANASA FIDC',
    #                                 'https://www.fitchratings.com/research/pt/structured-finance/fitch-upgrades-rating-of-senior-quotas-of-sanasa-fidc-outlook-stable-09-09-2019',
    #                                 df_fitch_old['Rating Nacional'])

    #Novos ratings achados
    df_fitch_old=df_fitch_old.append(pd.DataFrame({'CNPJ':['33.534.867/0001-86','34.012.276/0001-01'],
                                                  'Fundo':['FIDC FARM SYNGENTA AGRONEGOCIO I','CORTEVA AGRISCIENCE FUNDO DE INVESTIMENTO EM DIREITOS CREDITÓRIOS AGRONEGÓCIO I'],
                                                  'Cota':['Senior','Senior'],
                                                  'ISIN':['BR032XCTF002','BR03EUCTF004'],
                                                  'Rating Nacional':['AAA','AAA'],
                                                  'Rating Agência':['FITCH','FITCH']}))

    df_fitch_old2 = pd.DataFrame()
    for nome in df_fitch_old['Fundo'].unique():
        
        df_aux_old2 = df_fitch_old[df_fitch_old['Fundo']==nome]
        df_aux_old2['Cota2']=np.where(df_aux_old2['Cota'].str.contains('Sênior|Única|Senior'),'Senior','Subordinada')

        for cota in df_aux_old2['Cota2'].unique():
            
            df_aux_old = df_aux_old2[df_aux_old2['Cota2']==cota]
            df_aux_old=df_aux_old.reset_index()
            df_aux_old['index'] = df_aux_old.index+1
    
            df_fitch_old2=df_fitch_old2.append(df_aux_old)
          
    df_fitch_old2['Cota3'] = df_fitch_old2['Cota2'] + ' ' + df_fitch_old2['index'].apply(str)
    df_fitch_old2['key'] = df_fitch_old2['Fundo'] + ' ' + df_fitch_old2['Cota3'] 
   
    df_fitch_old2['key'] = df_fitch_old2['key'].apply(unidecode.unidecode)   #remover acentos
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS ','FUNDO DE INVESTIMENTOS EM DIREITOS CREDITORIOS ', 'FIDC ', 'SENIOR '], value='', regex=True)

    
    #replace keys to match with the new df
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['SANEAMENTO DE GOIAS-SANEAGO INFRAESTRUTURA IV'], value='DA SANEAMENTO DE GOIAS - SANEAGO - INFRAESTRUTURA IV', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['CARTAO DE COMPRAS SUPPLIERCARD'], value='CARTAO DE COMPRA SUPPLIER', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['TRANSMISSAO INFINITY DI'], value='DE TRANSMISSAO INFINITY DI', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['CORTEVA AGRISCIENCE AGRONEGOCIO I'], value='CORTEVA AGRISCIENCE I', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['MINERVA CREDITO MERCANTIL'], value='MINERVA - CREDITO MERCANTIL', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['ENERGISA CENTRO OESTE IV NP'], value='NP ENERGISA IV CENTRO OESTE', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['FARM SYNGENTA AGRONEGOCIO I'], value='FARM SYNGENTA AGRONEGOCIO 1', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=['ZB MULTIRRECEBIVEIS'], value='ZB MULTI-RECEBIVEIS', regex=True)
    df_fitch_old2['key'] = df_fitch_old2['key'].replace(to_replace=[''], value='', regex=True)


    df_fitch_old = df_fitch_old2.drop(['Cota2','index'], axis=1)
    
     
    #ARRUMAR AQUI   
    intersect_list = set(df_fitch['key'].tolist()).intersection(set(df_fitch_old['key'].tolist()))
    new_assets_list = set(df_fitch['key'].tolist()) - set(df_fitch_old['key'].tolist())
    old_assets_list = set(df_fitch_old['key'].tolist()) - set(df_fitch['key'].tolist())
      
    if len(intersect_list)>0:
        print('1) Intercessao entre as duas listas: ')
      
        [print('- ',x) for x in intersect_list]
    else:
        print ('1) Nenhum ativo em comum entre a analise nova e a antiga')
      
          
    if len(new_assets_list)>0:
        print('2) Ativos que estao na analise nova, mas nao estao na antiga: ')
        [print('- ',x) for x in new_assets_list]
    else:
        print('2) Nenhum ativo novo na nova analise')
          
          
      
    if len(old_assets_list)>0:
          
        print('3) Ativos que estao na analise antiga, mas nao estao na nova: ')
        [print('- ',x) for x in old_assets_list]
    else:
        print('3) Nenhum ativo antigo deixou de ser analisado')
          
                 
      
    df_fitch_old=df_fitch_old.rename(columns={"Fundo":"Ativo",
                                        "Rating Nacional": "Rating Antigo"})
      
    if 'CNPJ' in df_fitch.columns:      
        df_fitch_old = df_fitch_old.drop(['CNPJ'], axis=1)      
      
    if 'ISIN' in df_fitch.columns:      
        df_fitch_old = df_fitch_old.drop(['ISIN'], axis=1)         
          
    if 'CNPJ|ISIN' in df_fitch.columns:
        df_fitch_old = df_fitch_old[['Ativo','Rating Antigo','key']]
    else:
        df_fitch_old = df_fitch_old[['CNPJ','ISIN','Ativo','Rating Antigo','key']]

      
    
    df_fitch = df_fitch.merge(df_fitch_old,how='left',on='key')

    df_aux = pd.DataFrame()
    for fidc in df_fitch['Nome'].unique():
        print(fidc)
        
        df_aux2= df_fitch[df_fitch['Nome']==fidc]
        cnpj_list_aux = df_aux2['CNPJ'].unique().tolist()        
        cnpj_list = cnpj_list_aux[cnpj_list_aux=='nan']
        if len([cnpj_list])>1:
            #print('erro')
            break
        else:
            #print('ok')
            df_aux2['CNPJ2']=cnpj_list
            df_aux=df_aux.append(df_aux2)
            
            
            
            
    df_aux = df_aux.drop(['CNPJ'], axis=1)      
    df_aux = df_aux.rename(columns={'CNPJ2':'CNPJ'})      

    df_fitch=df_aux  
    df_fitch['Agencia']='FITCH'
    
    
    print(df_fitch['Nome'][df_fitch['CNPJ'].isnull()].tolist())
   
    df_fitch['CNPJ'] = np.where(df_fitch['Nome']=='FIDC PCH BURITI','31.030.923/0001-10',df_fitch['CNPJ'])
    df_fitch['CNPJ'] = np.where(df_fitch['Nome']=='DRIVER BRASIL FOUR BANCO VOLKSWAGEN FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS FINANCIAMENTO DE VEÍCULOS','30.687.382/0001-34',df_fitch['CNPJ'])
    df_fitch['CNPJ'] = np.where(df_fitch['Nome']=='FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS DMCARD','32.101.535/0001-45',df_fitch['CNPJ'])
    df_fitch['CNPJ'] = np.where(df_fitch['Nome']=='BR ELETRO FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS','35.818.950/0001-02	',df_fitch['CNPJ'])
    df_fitch['CNPJ'] = np.where(df_fitch['Nome']=='APOLO FIDC (ELETROBRAS)','34.218.625/0001-46	',df_fitch['CNPJ'])

    
    return df_fitch


def merge_dfs(df_lf, df_austin, df_liberium, df_sr, df_sp, df_moody, df_fitch):
    
    #Essa funcao abre todas os relatoriso de rating antigos de todas as agencias e salva como arquivo antigo.
    
    df_lf_agg=df_lf[['CNPJ','ISIN','Ativo', 'Cota','Status', 'Rating Antigo', 'Agencia']]
    df_lf_agg=df_lf_agg.rename(columns={"Ativo":"Fundo", "Status": "Acao Rating"})
    
    
    
    df_austin["Data"] = df_austin["Data"].dt.strftime("%d/%m/%Y")
    df_austin["Data Rating Antigo"] = df_austin["Data Rating Antigo"].dt.strftime("%d/%m/%Y")   
    df_austin_agg=df_austin[['CNPJ','ISIN','Nome','Cota2','Cota3', 'Cota', 'Série', 'Rating', 'Perspectiva', 'Acao Rating', 'Data', 'Rating Antigo', 'Data Rating Antigo', 'Agencia','Link']]
    df_austin_agg=df_austin_agg.rename(columns={"Nome":"Fundo", "Cota2": "Tipo Cota", "Cota3":"Cota", "Cota":"Nome Cota"})
    
    df_liberium["Data"] = df_liberium["Data"].dt.strftime("%d/%m/%Y")
    df_liberium["Data Rating Antigo"] = df_liberium["Data Rating Antigo"].dt.strftime("%d/%m/%Y")
    df_liberium_agg=df_liberium[['CNPJ','ISIN','FIDC', 'Cota2', 'Cota3', 'Cota', 'Rating Longo Prazo', 'Perspectiva','Acao Rating' ,'Data','Rating Antigo', 'Data Rating Antigo','Agencia','Link']]
    df_liberium_agg=df_liberium_agg.rename(columns={"FIDC":"Fundo", "Cota2": "Tipo Cota", "Cota3":"Cota", "Cota":"Nome Cota", "Rating Longo Prazo": "Rating"})
      
    df_sr["VIGÊNCIA DA CLASSIFICAÇÃO"] = df_sr["VIGÊNCIA DA CLASSIFICAÇÃO"].dt.strftime("%d/%m/%Y")
    df_sr["Data Vencimento Antigo"] = df_sr["Data Vencimento Antigo"].dt.strftime("%d/%m/%Y")   
    df_sr_agg=df_sr[['CNPJ','ISIN','FIDC','Cota2', 'Cota3', 'Cota', 'EQUIVALÊNCIA BR','VIGÊNCIA DA CLASSIFICAÇÃO','TENDÊNCIA', 'INFORMAÇÃO ADICIONAL', 'Rating Antigo','Data Vencimento Antigo', 'Agencia']]
    df_sr_agg=df_sr_agg.rename(columns={"FIDC":"Fundo", "Cota2": "Tipo Cota", "Cota3":"Cota", "Cota":"Nome Cota","EQUIVALÊNCIA BR":"Rating",
                                        "VIGÊNCIA DA CLASSIFICAÇÃO":"Data Vencimento", "TENDÊNCIA": "Perspectiva","INFORMAÇÃO ADICIONAL":"Acao Rating"})
    
    df_sp["Data"] = df_sp["Data"].dt.strftime("%d/%m/%Y")
    df_sp["Data Vencimento"] = df_sp["Data Vencimento"].dt.strftime("%d/%m/%Y")
    df_sp["Data Rating Antigo"] = df_sp["Data Rating Antigo"].dt.strftime("%d/%m/%Y")
    df_sp["Data Vencimento Antigo"] = df_sp["Data Vencimento Antigo"].dt.strftime("%d/%m/%Y")
    df_sp_agg=df_sp[['CNPJ','ISIN','Nome','Cota2', 'Cota3', 'Cota','Rating', 'Perspectiva','Data','Data Vencimento', 'Rating Antigo','Data Rating Antigo', 'Data Vencimento Antigo', 'Agencia','Link']]
    df_sp_agg=df_sp_agg.rename(columns={"Nome":"Fundo", "Cota2": "Tipo Cota", "Cota3":"Cota", "Cota":"Nome Cota"})
    
    df_moody["Data Rating"] = df_moody["Data Rating"].dt.strftime("%d/%m/%Y")
    df_moody_agg=df_moody[['CNPJ','ISIN', 'Fundo', 'Cota2', 'Cota3', 'Cota', 'Ratings Nacional','Data Rating','Agência ']]
    df_moody_agg=df_moody_agg.rename(columns={"Cota2": "Tipo Cota", "Cota3":"Cota", "Cota":"Nome Cota", "Data Rating": "Data", "Ratings Nacional":"Rating", "Agência ":"Agencia"})
    
    df_fitch["Data"] = df_fitch["Data"].dt.strftime("%d/%m/%Y")
    df_fitch_agg=df_fitch[['CNPJ','ISIN','Nome','Cota2', 'Cota3', 'Cota','Rating', 'Acao Rating', 'Perspectiva', 'Data', 'Link','Rating Antigo', 'Agencia']]
    df_fitch_agg=df_fitch_agg.rename(columns={"Nome":"Fundo", "Cota2": "Tipo Cota", "Cota3":"Cota", "Cota":"Nome Cota"})
    
    
    df_agg=df_austin_agg.append(df_liberium_agg)
    df_agg=df_agg.append(df_sr_agg)
    df_agg=df_agg.append(df_sp_agg)
    df_agg=df_agg.append(df_moody_agg)
    df_agg=df_agg.append(df_fitch_agg)
    df_agg=df_agg.append(df_lf_agg)

    df_agg=df_agg[['CNPJ', 'ISIN', 'Fundo', 'Tipo Cota', 'Cota', 'Nome Cota', 'Série','Rating', 'Perspectiva', 'Acao Rating',
                    'Data', 'Data Vencimento', 'Rating Antigo','Data Rating Antigo', 'Data Vencimento Antigo', 'Agencia', 'Link']]


    # df_agg["Data"] = df_agg["Data"].dt.strftime("%d/%m/%Y")
    # df_agg["Data Vencimento"] = df_agg["Data Vencimento"].dt.strftime("%d/%m/%Y")
    # df_agg["Data Rating Antigo"] = df_agg["Data Rating Antigo"].dt.strftime("%d/%m/%Y")
    # df_agg["Data Vencimento Antigo"] = df_agg["Data Vencimento Antigo"].dt.strftime("%d/%m/%Y")


    writer = pd.ExcelWriter('Rating FIDCs - 2020.xlsx', engine='xlsxwriter')
    
    df_agg.to_excel(writer, sheet_name='Agregado', index=False)
    df_lf.to_excel(writer, sheet_name='LF',index=False)
    df_austin.to_excel(writer, sheet_name='AUSTIN',index=False)
    df_liberium.to_excel(writer, sheet_name='LIBERIUM',index=False)
    df_sr.to_excel(writer, sheet_name='SR',index=False)
    df_sp.to_excel(writer, sheet_name='SP',index=False)
    df_moody.to_excel(writer, sheet_name='MOODYS',index=False)
    df_fitch.to_excel(writer, sheet_name='FITCH',index=False)


    writer.save()

    return df_lf_old, df_austin_old, df_liberium_old, df_sr_old, df_sp_old, df_moodys_old, df_fitch_old
    





if __name__== "__main__":

    ######## ########  ########  ######## PREFERENCIAS DO WEBDRIVER ######## ########  ########  ########
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    Initial_path = r"/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Rating"
    os.chdir('/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Rating/')
    prefs = {"download.default_directory" : Initial_path}
    chrome_options.add_experimental_option("prefs",prefs)
    chrome_path = which("./chromedriver")
       
    df_lf_old, df_austin_old, df_liberium_old, df_sr_old, df_sp_old, df_moodys_old, df_fitch_old = open_old_dfs()

    df_lf = scrap_lf(chrome_options,df_lf_old)
    df_austin = scrap_austin(chrome_options, df_austin_old)
    df_liberium = scrap_liberium(chrome_options, df_liberium_old)
    df_sr = scrap_sr(chrome_options, df_sr_old) 
    df_sp = scrap_sp(chrome_options, df_sp_old)
    df_moody = scrap_moodys(df_moodys_old, 0)
    df_fitch = scrap_fitch(df_fitch_old)



    df_agg = merge_dfs(df_lf, df_austin, df_liberium, df_sr, df_sp, df_moody, df_fitch)

 


