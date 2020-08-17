library(readxl)
library(dplyr)
library(tidyr)
library(Hmisc)
library(sjmisc)
library(stringr)
library(openxlsx)
library(ggpubr)
library(tibble)
library(ipeaData) # esse pra dar load
library(ipeadatar) # esse pra pesquisar as series



open_database = function () {
  
  setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/")
  
  df_var   = read_excel("Variaveis IF BACEN.xlsx")
  
  df_bacen = read_excel("BACEN IF Data.xlsx" , col_types=append(append(rep("text",10),"date"), rep("numeric", 353))) 
  df_bacen = df_bacen %>% mutate(Data=as.Date(Data))
  
  default_df   = read_excel("default banks.xlsx", sheet = "Check names")
  
  
  return (list("VAR"=df_var,"DF"=df_bacen, "DEFAULT"=default_df))
}


#verificar quais bancos deram default (verificar bancos que sairam da base)
filterdefaultbanks = function(df_bacen) {
  
  date_list = df_bacen %>% distinct(Data) %>% as.list() %>% .[[1]]
  df_aux = data.frame(matrix(ncol=0, nrow=0))
  list_aux=list()
  
  df_help= data.frame(matrix(ncol=0, nrow=0))
  df_help4= data.frame(matrix(ncol=0, nrow=0))
  
  for (i in 2:length(date_list)) {
    
    print(i)
    print(lista_aux[[i]])
    
    cod0_list = df_bacen %>% filter(Data==lista_aux[[i-1]] & TCB %in% c("b1","b2","b4")) %>% distinct(COD) %>% as.list() %>% .[[1]]
    cod1_list = df_bacen %>% filter(Data==lista_aux[[i]] & TCB %in% c("b1","b2","b4")) %>% distinct(COD) %>% as.list() %>% .[[1]]
    
    code_getout_list = cod0_list[cod0_list %nin% cod1_list]
    code_getin_list = cod1_list[cod1_list %nin% cod0_list]
    
    names_getout_list = df_bacen %>% filter(Data==lista_aux[[i-1]] & COD %in% code_getout_list) %>% distinct(IF) %>% as.list() %>% .[[1]]
    names_getin_list = df_bacen %>% filter(Data==lista_aux[[i]] & COD %in% code_getin_list) %>% distinct(IF) %>% as.list() %>% .[[1]]
    
    df_aux2 = data.frame(n_n0=length(cod0_list),
                         n_n1=length(cod1_list),
                         n_getout=length(code_getout_list),
                         n_getin=length(code_getin_list),
                         date_n0=lista_aux[[i-1]],
                         date_n1=lista_aux[[i]],
                         codes_getout=paste(code_getout_list, collapse = '///'),
                         codes_getin=paste(code_getin_list, collapse = '///'),
                         names_getout=paste(names_getout_list, collapse = '///'),
                         names_getin=paste(names_getin_list, collapse = '///'))
    
    df_aux=bind_rows(df_aux,df_aux2)
    
    df_help2 = df_bacen %>% filter(IF%in%str_split(df_aux$names_getout[i:i-1], "///")[[1]]) %>% arrange(IF,Data)
    df_help = bind_rows(df_help,df_help2)
    
    df_help3 = df_bacen %>% filter(IF%in%str_split(df_aux$names_getin[i:i-1], "///")[[1]]) %>% arrange(IF,Data)
    df_help4 = bind_rows(df_help3,df_help4)
    
    list_aux[[i]] = df_bacen %>% filter(IF%in%str_split(df_aux$names_getout[i:i-1], "///")[[1]]) %>% arrange(IF,Data)
    
  }
  
  
  list_aux[[1]] = df_aux
  
  list_aux$agg = df_help
  list_aux$list_getout = df_help %>% distinct(IF)
  list_aux$list_getin = df_help4 %>% distinct(IF)
  
  
  write.xlsx(list_aux, file = "Bancos DEFAULT.xlsx")
  a = df_bacen %>% filter(TCB %in% c("b1","b2","b4")) %>% group_by(IF) %>%  summarise_if(is.numeric, funs(mean(., na.rm=TRUE)))
  
  return (list(list_aux, a))
  }

setdataset = function(flag=1, df_bacen, df_var, default_df) {
  
  
  if (flag==1) {
    
    names_default = default_df %>% select(`Possíveis default`) %>% as.list() %>% .[[1]]
    
    #remover variaveis RESUMO (menos numero de agencia)
    list_remove1 = df_var %>% filter((Grupo=="Resumo")|(str_detect(Grupo, "Carteira"))) %>% select('Variável') %>% as.list() %>% .[[1]]
    list_remove1 = list_remove1[-8]
    
    
    df_filter = df_bacen %>% 
      left_join(default_df %>% select(names(default_df)[1:2]), by=c("IF"="Possíveis default")) %>% 
      filter(Data>as.Date("2000-09-01")) %>%
      filter(TCB %in% c("b1","b2","b4")) %>%
      #filter(!is.na(IF)) %>%
      select(-c(list_remove1)) %>% 
      mutate(DEFAULT=case_when(Situação=="Falência"~1,T~0)) %>%
      mutate('Ano'=format(Data, "%Y"),'Mes'=format(Data, "%m")) %>%
      mutate('Trim' = case_when((Mes=='01')|(Mes=='02')|(Mes=='03')~'1T',(Mes=='04')|(Mes=='05')|(Mes=='06')~'2T',
                                (Mes=='07')|(Mes=='08')|(Mes=='09')~'3T',(Mes=='10')|(Mes=='11')|(Mes=='12')~'4T'))  %>%
      filter(IF %nin% c("LAVRA", "PONTUAL")) %>%
      select(names(df_bacen)[1:11], Situação, DEFAULT, Ano, Mes, Trim, everything()) %>%
      mutate(IF = case_when(str_detect(IF,'PRUDENCIAL')~'HSBC BI',T~IF)) %>%
      arrange(IF,Data)
  
    
    df_aux = data.frame(matrix(ncol=0, nrow=0))
    for (bank in  df_filter %>% distinct(IF) %>% filter(!is.na(IF)) %>% as.list() %>% .[[1]]) {
      
      print(bank)
      
      data_inicial = df_filter %>% filter(IF==bank) %>% distinct(Data) %>% as.list() %>% .[[1]] %>% .[[1]]
      data_final = tail(df_filter%>%distinct(Data)%>%as.list() %>% .[[1]],1)
      
      df_filter2 = df_filter %>% filter(IF==bank) 
      df_filter3 = df_filter2[1:16]
      
      if (nrow(df_filter3)>4) {
        print('default')
        if (df_filter3 %>% distinct(DEFAULT) %>% .[[1]]==1){
          for (colum in 17:length(df_filter2)) {
            
            serie=df_filter2[colum]
            serie$Data = df_filter3$Data 
            serie$lag = lag(serie[[1]], default = NA) 
            #serie$var = (serie[[1]]-serie[['lag']])/abs(serie[['lag']])
            
            if (length(serie %>% filter(!is.na(lag)) %>% distinct(lag) %>% .[[1]])==1){
              if ((serie %>% filter(!is.na(lag)) %>% distinct(lag) %>% .[[1]])==0){
                
                serie$var = 0
              }else{
                
                serie$var = (serie[[1]]-serie[['lag']])/abs(serie[['lag']])
              }
            } else {
              
              serie$var = (serie[[1]]-serie[['lag']])/abs(serie[['lag']])
              if(Inf %in% serie$var | -Inf %in% serie$var) {
                
                serie['lag'][serie['lag']==0]=0.01
                serie$var = (serie[[1]]-serie[['lag']])/abs(serie[['lag']])
              }
            }
            
            last1_mean =  ifelse(nrow(serie %>% filter(!is.na(var)))>0,
                                 tail(serie %>% filter(!is.na(var)) %>% select(var) %>% as.list() %>% .[[1]],1)[[1]],
                                 NA_real_) 
            last2_mean =  ifelse(nrow(serie %>% filter(!is.na(var)))>0,
                                 mean(tail(serie %>% filter(!is.na(var)) %>% select(var) %>% as.list() %>% .[[1]],2)[[1]]),
                                 NA_real_)
            last3_mean =  ifelse(nrow(serie %>% filter(!is.na(var)))>0,
                                 mean(tail(serie %>% filter(!is.na(var)) %>% select(var) %>% as.list() %>% .[[1]],3)[[1]]),
                                 NA_real_)
            
            vmean = mean(c(last1_mean,last2_mean,last3_mean))
            vector_mean=c()
            
            for (i in 1:nrow(df_filter3)) {
              if (is.na(serie[[i,1]]) & df_filter3$Data[i]!=data_inicial & !is.na(vmean)>0){ 
                
                vector_mean[i]=  ifelse(vector_mean[i-1]>0,vector_mean[i-1]*(1+(vmean)),vector_mean[i-1]*(1-(vmean))) 
              } else {                                
                
                vector_mean[i]=  serie[[i,1]]
              }
            }
            
            serie[1]=vector_mean
            
            serie = serie %>% select(-c("Data", "lag", "var"))
            names(serie)[2:4] = paste0(names(serie)[[1]],'_',names(serie)[2:4]) 
            
            df_filter3=cbind(df_filter3, serie)
          }
        } else {
          
          print('N default')
          
          df_filter3=df_filter2
        }

        df_row1 = as.data.frame(rowSums(!is.na(df_filter3))) %>% rownames_to_column("row")
        names(df_row1)[2]='naRow'
        df_row1 = df_row1 %>% mutate('total'=length(df_filter3)) %>% mutate('ratio'=naRow/total) 
        rows = df_row1 %>% mutate(row=as.numeric(row)) %>% filter(ratio>0.75) %>% select('row') %>% as.list() %>% .[[1]]
      
        df_filter3 = df_filter3 %>% slice(rows) 
        
        if (nrow(df_filter3)>4) {
          
          limrow=nrow(df_filter3)-2
          df_filter3 = df_filter3 %>% 
            rownames_to_column("row") %>% 
            mutate(y = case_when((DEFAULT==1) & (as.numeric(row)<limrow)~0,
                                  DEFAULT==0~0,T~1)) %>%
            select(-c('row'))
          
          y=df_filter3 %>% slice(5:nrow(df_filter3)) %>% select('Data','y') %>% rename('Data_Y'='Data')
          x=df_filter3 %>% slice(5:nrow(df_filter3)-4) %>% rename('Data_X'='Data') %>% select(-c('y'))
          
          df_filter3=cbind(y, x) %>% select(names(df_filter3)[1:10],'Data_Y', 'Data_X', everything())
          
          df_aux = bind_rows(df_filter3,df_aux) 
        }
      }
    }
    
    df_row1 = as.data.frame(rowSums(!is.na(df_aux))) %>% rownames_to_column("row")
    names(df_row1)[2]='naRow'
    df_row1 = df_row1 %>% mutate('total'=length(df_aux)) %>% mutate('ratio'=naRow/total) 
    
    df_row1 %>% distinct(ratio, .keep_all=T) #%>% filter(ratio<0.75)
    df_row1 %>% mutate(row=as.numeric(row)) %>% filter(ratio<0.75)
    rownames = df_row1 %>% mutate(row=as.numeric(row)) %>% filter(ratio>0.75) %>% select('row') %>% as.list() %>% .[[1]]
    
    df_1_filtered = df_aux %>% slice(rownames) 
    
    df_col1 = data.frame(colSums(is.na(df_1_filtered))) %>% rownames_to_column("var")
    names(df_col1)[2]='naCol'
    
    list_remove2 = df_col1 %>%  filter(naCol>length(df_1_filtered)/2) %>% slice(4:nrow(df_col1)) %>%select(var) %>% as.list() %>% .[[1]]
    
    df_col1 = df_col1 %>% left_join(df_var %>% select(Coluna, `Variável`),by=c('var'="Variável"))  
    df_1_filtered_final_aux = df_1_filtered %>% 
      mutate(`04_30` = case_when(Ano>2018~`04_31`, T~`04_30`)) %>%
      select(-c(list_remove2)) %>% 
      filter(!is.na(`05_17`)) %>%
      mutate(dummy_IB = case_when((Data_X>=as.Date("2000-01-01")&Data_X<as.Date("2016-01-01"))&(`05_17`<11+2)~1,
                                  (Data_X>=as.Date("2016-01-01")&Data_X<as.Date("2017-01-01"))&(`05_17`<9.875+2)~1,
                                  (Data_X>=as.Date("2017-01-01")&Data_X<as.Date("2018-01-01"))&(`05_17`<9.25+2)~1,
                                  (Data_X>=as.Date("2018-01-01")&Data_X<as.Date("2019-01-01"))&(`05_17`<8.625+2)~1,
                                  (Data_X>=as.Date("2019-01-01")&Data_X<as.Date("2020-01-01"))&(`05_17`<8+2)~1,
                                  (Data_X>=as.Date("2000-12-01"))&(is.na(`05_17`))~1,T~0),
             dummy_II = case_when((Data_X>=as.Date("2000-01-01")&Data_X<as.Date("2002-01-01"))&(`05_19` > 70+2)~1,
                                  (Data_X>=as.Date("2002-01-01")&Data_X<as.Date("2003-01-01"))&(`05_19`> 60+2)~1,
                                  (Data_X>=as.Date("2019-01-01")&Data_X<as.Date("2020-01-01"))&(`05_19`> 50+2)~1,
                                  (Data_X>=as.Date("2000-12-01"))&(is.na(`05_17`))~1,T~0))
    
    df_names = df_1_filtered_final_aux %>% select(names(df_1_filtered_final_aux[1:17]), dummy_IB,dummy_II)
    df_data_normalized = as.data.frame(scale(df_1_filtered_final_aux[20:length(df_1_filtered_final_aux)-2]))
    
    print(names(df_names))
    print(names(df_data_normalized))
    
    df_1_filtered_final=cbind(df_names,df_data_normalized)
    
    df_1_filtered_final = df_1_filtered_final  %>% 
      mutate(ROI = `04_29`/`03_20`) %>%
      mutate('2000'=case_when(Ano==2000~1,T~0),'2001'=case_when(Ano==2001~1,T~0),'2002'=case_when(Ano==2002~1,T~0),'2003'=case_when(Ano==2003~1,T~0),
             '2004'=case_when(Ano==2004~1,T~0),'2005'=case_when(Ano==2005~1,T~0),'2006'=case_when(Ano==2006~1,T~0),'2007'=case_when(Ano==2007~1,T~0),
             '2008'=case_when(Ano==2008~1,T~0),'2009'=case_when(Ano==2009~1,T~0),'2010'=case_when(Ano==2010~1,T~0),'2011'=case_when(Ano==2011~1,T~0),
             '2012'=case_when(Ano==2012~1,T~0),'2013'=case_when(Ano==2013~1,T~0),'2014'=case_when(Ano==2013~1,T~0),'2015'=case_when(Ano==2015~1,T~0),
             '2016'=case_when(Ano==2016~1,T~0),'2017'=case_when(Ano==2017~1,T~0),'2018'=case_when(Ano==2018~1,T~0),'2019'=case_when(Ano==2019~1,T~0)) %>%
      #mutate('mar'=case_when(Mes=='03'~1,T~0),'jun'=case_when(Mes=='06'~1,T~0),'set'=case_when(Mes=='09'~1,T~0),'dez'=case_when(Mes=='12'~1,T~0)) %>%
      mutate('1T'=case_when(Trim=='1T'~1,T~0),'2T'=case_when(Trim=='2T'~1,T~0),
             '3T'=case_when(Trim=='3T'~1,T~0),'4T'=case_when(Trim=='4T'~1,T~0)) %>%
      #select(append(names(df_filter)[1:11],names(df_filter)[355:394]), everything()) %>%
      mutate(CID=case_when(IF=='GM'~'SAO PAULO', T~CID), UF = case_when(IF=='GM'~'SP', T~UF)) %>%
      mutate(SP_UF=case_when(UF=='SP'~1,T~0),RJ_UF=case_when(UF=='RJ'~1,T~0),DF_UF=case_when(UF=='DF'~1,T~0),
             MG_UF=case_when(UF=='MG'~1,T~0), BA_UF=case_when(UF=='BA'~1,T~0), RS_UF=case_when(UF=='RS'~1,T~0),
             OUTRA_UF=case_when((UF!='SP')&(UF!='RJ')&(UF!='DF')&(UF!='BA')&(UF!='RS')&(UF!='MG')~1,T~0))  %>%
      mutate(SP_CID=case_when(CID=='SAO PAULO'~1,T~0),RJ_CID=case_when(CID=='RIO DE JANEIRO'~1,T~0),BSB_CID=case_when(CID=='BRASILIA'~1,T~0),
             BH_CID=case_when(CID=='BELO HORIZONTE'~1,T~0),SAL_CID=case_when(CID=='SALVADOR'~1,T~0),MG_CID=case_when(CID=='	PORTO ALEGRE'~1,T~0),
             OUTRA_CID=case_when((CID!='SAO PAULO')&(CID!='RIO DE JANEIRO')&(CID!='BRASILIA')&(CID!='BELO HORIZONTE')&(CID!='SALVADOR')&(CID!='PORTO ALEGRE')~1,T~0))  %>%
      mutate(B1_TIPO=case_when(TCB=='b1'~1,T~0), B2_TIPO=case_when(TCB=='b2'~1,T~0),B4_TIPO=case_when("TCB"=='b4'~1,T~0) ) %>%
      mutate(S1_SEG=case_when(SR2=='S1'~1,T~0), S2_SEG=case_when(SR2=='S2'~1,T~0),
             S3_SEG=case_when(SR2=='S3'~1,T~0),S4_SEG=case_when(SR2=='S4'~1,T~0),NI_SEG=case_when(is.na(SR2)~1,T~0) ) %>%
      mutate(CONG_CONS=case_when(TD=='C'~1,T~0), II_CONS=case_when(TD=='I'~1,T~0)) %>%
      mutate(CONT_PUB=case_when(TC=='1'~1,T~0), CONT_PRIVNAC=case_when(TC=='2'~1,T~0),CONT_PRIVEST=case_when("TC"=='3'~1,T~0)) %>%
      mutate(S1_CREDPROV=S1_SEG*`02_05`,S1_CREDSPROV=S1_SEG*`02_06`,S1_ATAj=S1_SEG*`02_15`,S1_AT=S1_SEG*`02_17`,S1_PCELG=S1_SEG*`03_18`,
             S1_PL = S1_SEG*`03_20`,S1_PT = S1_SEG*`03_21`,S1_RPC=S1_SEG*`04_12`,S1_LL = S1_SEG*`04_29`,S1_ROI = S1_SEG*`ROI`,
             S1_CNII= S1_SEG*`05_04`,S1_PRWA = S1_SEG*`05_05`,S1_ARWA = S1_SEG*`05_13`,S1_IB=S1_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S1_IM=S1_SEG*`05_19`,
             S2_CREDPROV=S2_SEG*`02_05`,S2_CREDSPROV=S2_SEG*`02_06`,S2_ATAj=S2_SEG*`02_15`,S2_AT=S2_SEG*`02_17`,S2_PCELG=S2_SEG*`03_18`,
             S2_PL = S2_SEG*`03_20`,S2_PT = S2_SEG*`03_21`,S2_RPC=S2_SEG*`04_12`,S2_LL = S2_SEG*`04_29`,S2_ROI = S2_SEG*`ROI`,
             S2_CNII= S2_SEG*`05_04`,S2_PRWA = S2_SEG*`05_05`,S2_ARWA = S2_SEG*`05_13`,S2_IB=S2_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S2_IM=S2_SEG*`05_19`,
             S3_CREDPROV=S3_SEG*`02_05`,S3_CREDSPROV=S3_SEG*`02_06`,S3_ATAj=S3_SEG*`02_15`,S3_AT=S3_SEG*`02_17`,S3_PCELG=S3_SEG*`03_18`,
             S3_PL = S3_SEG*`03_20`,S3_PT = S3_SEG*`03_21`,S3_RPC=S3_SEG*`04_12`,S3_LL = S3_SEG*`04_29`,S3_ROI = S3_SEG*`ROI`,
             S3_CNII= S3_SEG*`05_04`,S3_PRWA = S3_SEG*`05_05`,S3_ARWA = S3_SEG*`05_13`,S3_IB=S3_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S3_IM=S3_SEG*`05_19`,
             S4_CREDPROV=S4_SEG*`02_05`,S4_CREDSPROV=S4_SEG*`02_06`,S4_ATAj=S4_SEG*`02_15`,S4_AT=S4_SEG*`02_17`,S4_PCELG=S4_SEG*`03_18`,
             S4_PL = S4_SEG*`03_20`,S4_PT = S4_SEG*`03_21`,S4_RPC=S4_SEG*`04_12`,S4_LL = S4_SEG*`04_29`,S4_ROI = S4_SEG*`ROI`,
             S4_CNII= S4_SEG*`05_04`,S4_PRWA = S4_SEG*`05_05`,S4_ARWA = S4_SEG*`05_13`,S4_IB=S4_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S4_IM=S4_SEG*`05_19`)  %>%
      #select(-c(IB_lag,IB_var)) %>%
      arrange(IF,Data_X) 
    
    
    df_2_filtered_final = df_1_filtered_final_aux %>%  
      mutate(ROI = `04_29`/`03_20`) %>%
      mutate('2000'=case_when(Ano==2000~1,T~0),'2001'=case_when(Ano==2001~1,T~0),'2002'=case_when(Ano==2002~1,T~0),'2003'=case_when(Ano==2003~1,T~0),
             '2004'=case_when(Ano==2004~1,T~0),'2005'=case_when(Ano==2005~1,T~0),'2006'=case_when(Ano==2006~1,T~0),'2007'=case_when(Ano==2007~1,T~0),
             '2008'=case_when(Ano==2008~1,T~0),'2009'=case_when(Ano==2009~1,T~0),'2010'=case_when(Ano==2010~1,T~0),'2011'=case_when(Ano==2011~1,T~0),
             '2012'=case_when(Ano==2012~1,T~0),'2013'=case_when(Ano==2013~1,T~0),'2014'=case_when(Ano==2013~1,T~0),'2015'=case_when(Ano==2015~1,T~0),
             '2016'=case_when(Ano==2016~1,T~0),'2017'=case_when(Ano==2017~1,T~0),'2018'=case_when(Ano==2018~1,T~0),'2019'=case_when(Ano==2019~1,T~0)) %>%
      #mutate('mar'=case_when(Mes=='03'~1,T~0),'jun'=case_when(Mes=='06'~1,T~0),'set'=case_when(Mes=='09'~1,T~0),'dez'=case_when(Mes=='12'~1,T~0)) %>%
      mutate('1T'=case_when(Trim=='1T'~1,T~0),'2T'=case_when(Trim=='2T'~1,T~0),
             '3T'=case_when(Trim=='3T'~1,T~0),'4T'=case_when(Trim=='4T'~1,T~0)) %>%
      #select(append(names(df_filter)[1:11],names(df_filter)[355:394]), everything()) %>%
      mutate(CID=case_when(IF=='GM'~'SAO PAULO', T~CID), UF = case_when(IF=='GM'~'SP', T~UF)) %>%
      mutate(SP_UF=case_when(UF=='SP'~1,T~0),RJ_UF=case_when(UF=='RJ'~1,T~0),DF_UF=case_when(UF=='DF'~1,T~0),
             MG_UF=case_when(UF=='MG'~1,T~0), BA_UF=case_when(UF=='BA'~1,T~0), RS_UF=case_when(UF=='RS'~1,T~0),
             OUTRA_UF=case_when((UF!='SP')&(UF!='RJ')&(UF!='DF')&(UF!='BA')&(UF!='RS')&(UF!='MG')~1,T~0))  %>%
      mutate(SP_CID=case_when(CID=='SAO PAULO'~1,T~0),RJ_CID=case_when(CID=='RIO DE JANEIRO'~1,T~0),BSB_CID=case_when(CID=='BRASILIA'~1,T~0),
             BH_CID=case_when(CID=='BELO HORIZONTE'~1,T~0),SAL_CID=case_when(CID=='SALVADOR'~1,T~0),MG_CID=case_when(CID=='	PORTO ALEGRE'~1,T~0),
             OUTRA_CID=case_when((CID!='SAO PAULO')&(CID!='RIO DE JANEIRO')&(CID!='BRASILIA')&(CID!='BELO HORIZONTE')&(CID!='SALVADOR')&(CID!='PORTO ALEGRE')~1,T~0))  %>%
      mutate(B1_TIPO=case_when(TCB=='b1'~1,T~0), B2_TIPO=case_when(TCB=='b2'~1,T~0),B4_TIPO=case_when("TCB"=='b4'~1,T~0) ) %>%
      mutate(S1_SEG=case_when(SR2=='S1'~1,T~0), S2_SEG=case_when(SR2=='S2'~1,T~0),
             S3_SEG=case_when(SR2=='S3'~1,T~0),S4_SEG=case_when(SR2=='S4'~1,T~0),NI_SEG=case_when(is.na(SR2)~1,T~0) ) %>%
      mutate(CONG_CONS=case_when(TD=='C'~1,T~0), II_CONS=case_when(TD=='I'~1,T~0)) %>%
      mutate(CONT_PUB=case_when(TC=='1'~1,T~0), CONT_PRIVNAC=case_when(TC=='2'~1,T~0),CONT_PRIVEST=case_when("TC"=='3'~1,T~0)) %>%
      mutate(S1_CREDPROV=S1_SEG*`02_05`,S1_CREDSPROV=S1_SEG*`02_06`,S1_ATAj=S1_SEG*`02_15`,S1_AT=S1_SEG*`02_17`,S1_PCELG=S1_SEG*`03_18`,
             S1_PL = S1_SEG*`03_20`,S1_PT = S1_SEG*`03_21`,S1_RPC=S1_SEG*`04_12`,S1_LL = S1_SEG*`04_29`,S1_ROI = S1_SEG*`ROI`,
             S1_CNII= S1_SEG*`05_04`,S1_PRWA = S1_SEG*`05_05`,S1_ARWA = S1_SEG*`05_13`,S1_IB=S1_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S1_IM=S1_SEG*`05_19`,
             S2_CREDPROV=S2_SEG*`02_05`,S2_CREDSPROV=S2_SEG*`02_06`,S2_ATAj=S2_SEG*`02_15`,S2_AT=S2_SEG*`02_17`,S2_PCELG=S2_SEG*`03_18`,
             S2_PL = S2_SEG*`03_20`,S2_PT = S2_SEG*`03_21`,S2_RPC=S2_SEG*`04_12`,S2_LL = S2_SEG*`04_29`,S2_ROI = S2_SEG*`ROI`,
             S2_CNII= S2_SEG*`05_04`,S2_PRWA = S2_SEG*`05_05`,S2_ARWA = S2_SEG*`05_13`,S2_IB=S2_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S2_IM=S2_SEG*`05_19`,
             S3_CREDPROV=S3_SEG*`02_05`,S3_CREDSPROV=S3_SEG*`02_06`,S3_ATAj=S3_SEG*`02_15`,S3_AT=S3_SEG*`02_17`,S3_PCELG=S3_SEG*`03_18`,
             S3_PL = S3_SEG*`03_20`,S3_PT = S3_SEG*`03_21`,S3_RPC=S3_SEG*`04_12`,S3_LL = S3_SEG*`04_29`,S3_ROI = S3_SEG*`ROI`,
             S3_CNII= S3_SEG*`05_04`,S3_PRWA = S3_SEG*`05_05`,S3_ARWA = S3_SEG*`05_13`,S3_IB=S3_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S3_IM=S3_SEG*`05_19`,
             S4_CREDPROV=S4_SEG*`02_05`,S4_CREDSPROV=S4_SEG*`02_06`,S4_ATAj=S4_SEG*`02_15`,S4_AT=S4_SEG*`02_17`,S4_PCELG=S4_SEG*`03_18`,
             S4_PL = S4_SEG*`03_20`,S4_PT = S4_SEG*`03_21`,S4_RPC=S4_SEG*`04_12`,S4_LL = S4_SEG*`04_29`,S4_ROI = S4_SEG*`ROI`,
             S4_CNII= S4_SEG*`05_04`,S4_PRWA = S4_SEG*`05_05`,S4_ARWA = S4_SEG*`05_13`,S4_IB=S4_SEG*`05_17`,S1_IB2=S1_SEG*`05_17`,S4_IM=S4_SEG*`05_19`) %>%
      # mutate(dummy_IB = case_when((Data_X>=as.Date("2000-01-01")&Data_X<as.Date("2016-01-01"))&(`05_17` < 11+2)~1,
      #                             (Data_X>=as.Date("2016-01-01")&Data_X<as.Date("2017-01-01"))&(`05_17`<9.875+2)~1,
      #                             (Data_X>=as.Date("2017-01-01")&Data_X<as.Date("2018-01-01"))&(`05_17`<9.25+2)~1,
      #                             (Data_X>=as.Date("2018-01-01")&Data_X<as.Date("2019-01-01"))&(`05_17`<8.625+2)~1,
      #                             (Data_X>=as.Date("2019-01-01")&Data_X<as.Date("2020-01-01"))&(`05_17`<8+2)~1,
      #                             (Data_X>=as.Date("2000-12-01"))&(is.na(`05_17`))~1,T~0),
      #        dummy_II = case_when((Data_X>=as.Date("2000-01-01")&Data_X<as.Date("2002-01-01"))&(`05_19` > 70+2)~1,
      #                             (Data_X>=as.Date("2002-01-01")&Data_X<as.Date("2003-01-01"))&(`05_19`> 60+2)~1,
      #                             (Data_X>=as.Date("2019-01-01")&Data_X<as.Date("2020-01-01"))&(`05_19`> 50+2)~1,
      #                             (Data_X>=as.Date("2000-12-01"))&(is.na(`05_17`))~1,T~0)) %>%
      #select(-c(IB_lag,IB_var)) %>%
      arrange(IF,Data_X)
    
    print(dim(df_1_filtered_final))
    print(dim(df_1_filtered_final))
    
    
  }
  
  return (list(df_1_filtered_final,df_2_filtered_final))
}
  
append_economicvar = function (df_filter_normalized,df_filter, df_var) {
  
  dates = df_filtered %>% distinct(Data_X) %>% as.list %>% .[[1]]
  
  todas_series_ativas <- ipeadatar::available_series()
  todas_series_ativas <- filter(todas_series_ativas, status=="Active")
  
  seriesquar = filter(todas_series_ativas, status=="Active" & freq=="Quarterly")
  
  var_quar = c(
    # "BPAG4_DEXBC4", #	Dívida Externa - Banco Central	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBCCP4", #	Dívida Externa - Banco Central - Curto prazo	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBCLP4", #	Dívida Externa - Banco Central - Longo prazo	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXB4", #	Dívida Externa - Bancos	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBCP4", #	Dívida Externa - Bancos - Curto prazo	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBLP4", #	Dívida Externa - Bancos - Longo prazo	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBLPE4", #	Dívida Externa - Bancos - Longo prazo - Empréstimos	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBLPO4", #	Dívida Externa - Bancos - Longo prazo - Outros passivos de dívida	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXBLPT4", #	Dívida Externa - Bancos - Longo prazo - Títulos de dívida	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEX4", #	Dívida Externa - Dívida externa bruta	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXEF4", #	Dívida Externa - Empresas financeiras não bancárias	NA	Bacen/Dív. Ext.	Quarterly	2020-04-16	Active
    # "BPAG4_DEXENF4", #	Dívida Externa - Empresas não financeiras	NA	Bacen/Dív. Ext.	Quarterly	2020-01-03	Active
    # "BPAG4_DEXG4", #	Dívida Externa - Governo geral  
    "CSP12_SCPCC12", #	SPC - número de consultas	NA	ACSP/IEGV	Monthly	2020-05-07	Active
    "ACSP12_TELCH12", #	Usecheque - número de consultas	NA	ACSP/IEGV	Monthly	2020-05-07	Active
    "ANBIMA12_IBVSP12", #Índice de ações - Ibovespa - fechamento		
    "PAN4_IPCAG4",	#	Índice de Preços ao Consumidor Ampliado (IPCA)	NA	IBGE/SNIPC	Quarterly	2020-04-09	Active
    "PAN4_IGPDIG4",	#	Índice Geral de Preços (IGP-DI)	NA	FGV/Conj. Econ. - IGP	Quarterly	2020-04-06	Active
    "PAN4_FBKFI90G4",	#Investimento real	NA	IPEA	Quarterly	2020-03-04	Active
    # "PAN4_PO4",	#Pessoas ocupadas	#NA	IBGE/PNAD Contínua	Quarterly	2020-04-30	Active
    "SCN104_PIBAGPV104",	#PIB - agropecuária	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBAGPG104",	#PIB - agropecuária   - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_NFB104",	#PIB - capacidade / necessidade líquida de financiamento	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_CFGGN104",	#PIB - consumo final - APU	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_CFGGG104",	#PIB - consumo final - APU - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_CFPPN104",	#PIB - consumo final - famílias	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_CFPPG104",	#PIB - consumo final - famílias - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_XBSZN104",	#PIB - exportações - bens e serviços	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_XBSZG104",	#PIB - exportações - bens e serviços - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_VESTON104",	#PIB - formação bruta de capital - variação de estoque	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_FBKFG104",	#PIB - formação bruta de capital fixo - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_MBSZN104",	#PIB - importações - bens e serviços	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_MBSZG104",	#PIB - importações - bens e serviços - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBIVAV104",	#PIB - impostos sobre produtos	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBIVAG104",	#PIB - impostos sobre produtos - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBINDV104",	#PIB - indústria	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBICCG104",	#PIB - indústria - construção civil - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBIUPV104",	#PIB - indústria - elet., gás e saneamento básico	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBIUPG104",	#PIB - indústria - elet., gás, e saneamento básico - var. real trim	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBIEXV104",	#PIB - indústria - extrativa	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBIEXG104",	#PIB - indústria - extrativa - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBITRV104",	#PIB - indústria - transformação	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBITRG104",#PIB - indústria - transformação - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBINDG104",	#PIB - indústria - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_RLEX1N104",	#PIB - ordenados e salários - líquidos recebidos do exterior	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_TRUNIN104",	#PIB - outras transferências correntes - líquidas recebidas do exterior - total	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_SBN104",	#PIB - poupança bruta	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBPBN104", #PIB - preços básicos	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBPBG104",	#PIB - preços básicos - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBPMV104",	#PIB - preços de mercado	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBPMG104",	#PIB - preços de mercado - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PNBN104",	#PIB - renda nacional bruta	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_RNDBN104",	#PIB - renda nacional disponível bruta	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_RLEX2N104",	#PIB - rendas de propriedade - líquidas recebidas do exterior	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSERV104",	#PIB - serviços	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSAPV104",	#PIB - serviços - APU, educação e saúde públicas	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSAPG104",	#PIB - serviços - APU, educação e saúde públicas - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSALV104",	#PIB - serviços - atividades imobiliárias	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSALG104",	#PIB - serviços - atividades imobiliárias - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSCOV104",	#PIB - serviços - comércio	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSCOG104",	#PIB - serviços - comércio - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
  	"SCN104_PIBSCMNV104",	#PIB - serviços - informação e comunicação	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
  	"SCN104_PIBSCMNG104",	#PIB - serviços - informação e comunicação - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSIFV104",	#PIB - serviços - intermediação finaceira	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
  	"SCN104_PIBSIFG104",	#PIB - serviços - intermediação finaceira - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
   	"SCN104_PIBSOSV104",	#PIB - serviços - outros	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
  	"SCN104_PIBSOSG104",	#PIB - serviços - outros - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSTRV104",	#PIB - serviços - transp., armazenagem e correio	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
  	"SCN104_PIBSTRG104",	#PIB - serviços - transp., armazenagem e correio - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "SCN104_PIBSERG104",	#PIB - serviços - var. real trim.	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
    "PAN4_PIBPMV4",	#PIB nominal	NA	IBGE/SCN Trim.	Quarterly	2020-03-04	Active
  	"PAN4_PIBPMG4",	#PIB real	
  	#"PAN4_QIIGG4",	#Produção industrial	#NA	IBGE/PIM-PF	Quarterly	2020-05-13	Active
  	#"PAN4_RRPE4",	#Rend. real méd. princip. efet.	#NA	IBGE/PNAD Contínua	Quarterly	2020-04-30	Active
  	"PAN4_TCERXTINPC4",	#Taxa de câmbio - efetiva real - INPC - exportações - índice (média 2010 = 100)	NA	IPEA	Quarterly	2020-02-28	Active
  	"PAN4_ERV4",	#Taxa de câmbio nominal	NA	Bacen/Boletim/BP	Quarterly	2020-04-09	Active
  	#"PAN4_TDESOC4",	#Taxa de desocupação	NA	IBGE/PNAD Contínua	Quarterly	2020-04-30	Active
  	"PAN4_FBKFPIBV4",	#Taxa de investimento nominal	NA	IPEA	Quarterly	2020-03-04	Active
  	"PAN4_TJOVER4",	#Taxa de juros nominal - Over / Selic	NA	Bacen/Boletim/M. Finan.	Quarterly	2020-04-01	Active
  	"PAN4_STC4"	#Transações correntes - Saldo (BPM6)	NA	Bacen/Notas Imprensa/Set. Ext.	Quarterly	2020-05-06	Active
  	#"PAN4_IVVRG4"	#Valor real das vendas no varejo	NA	IBGE/PMC	Quarterly	2020-05-13	Active
  )
    	
    
  listaux = c()
  for (serie in var_quar){
    squar <- ipeaData::ipeadata(serie)
    #print(serie)
    if (nrow(squar)<4 ) {
      print(paste0("Erro na série ",serie))
      listaux= append(listaux,serie)
    } else {
      
      print(paste0("Appendando a serie ",serie))
      
      namecol = squar %>% distinct(SERCODIGO) %>% .[[1]]
      
      squar = squar %>% 
        mutate(DIA = case_when(nchar(DIA)==1~paste0("0",as.character(DIA)),T~as.character(DIA)),
               MES = case_when(nchar(MES)==1~paste0("0",as.character(MES+2)),T~as.character(MES+2))) %>%
        mutate(Data = as.Date(paste0(ANO,"-",MES,"-",DIA))) %>% 
        select('VALVALOR', 'Data') 
      
      names(squar)[1] = namecol
      
      df_filter = df_filter %>% left_join(squar, by=c("Data_X"="Data")) 
      df_filter_normalized = df_filter_normalized %>% left_join(squar, by=c("Data_X"="Data")) 
      
    }
  }
  
  df_filter_names = df_filter_normalized %>% select(names(df_filter_normalized[1:209]))
  df_filter_normalized_aux <- as.data.frame(scale(df_filter[210:length(df_filter)]))
  
  df_filter_normalized=cbind(df_filter_names,df_filter_normalized_aux)
  
  quarvariables_selected = seriesquar %>% 
    filter(code %in% var_quar) %>% 
    select(code, name, source) %>% 
    rename('Coluna'='source', 'Variável'='code', 'Descrição'='name') %>%
    mutate(Grupo = 'Variaveis Economicas')
  df_var = bind_rows(df_var,quarvariables_selected) 

  
  list_df = list("DF normalized" = df_filter_normalized, "DF Final" = df_filter, "Dicionario" = df_var)
  #write.xlsx(list_df, "DF Final.xlsx")
  
  return(list_df)
}

plot_group = function(df_bacen) {
  
  a=df%>%filter(SR %in% c("S1","S2")) %>% group_by(IF) %>%arrange(IF,Data)
  # a=df_bacen%>%filter(!is.na(`05_01`))  %>%arrange(IF,Data) #%>% distinct(Data)
  
  #plot 
  ativo_plot = df_bacen %>%
    ggplot(data=df_bacen, mapping = aes(x=Data, y=`01_01`/1000000,fill=IF, color=SR2)) +
    scale_x_date() + 
    geom_line() +
    # scale_fill_brewer(palette="Dark2") +
    ggtitle("Ativo Total por Segmento")+
    labs(y = "Ativo Total (em R$ milhão)", color='SR') + 
    theme_classic() + 
    theme(plot.title = element_text(hjust = 0.5))
  
  
  pl_plot = df_bacen %>%
    ggplot(data=df_bacen, mapping = aes(x=Data, y=`03_20`,fill=IF, color=SR2)) +
    scale_x_date() + 
    geom_line() +
    # scale_fill_brewer(palette="Dark2") +
    ggtitle("PL por Segmento")+
    labs(y = "PL (em R$ milhão)", color='SR') + 
    theme_classic() + 
    theme(plot.title = element_text(hjust = 0.5))
  
  
  basileia_plot = df_bacen %>%
    ggplot(data=df_bacen, mapping = aes(x=Data, y=`05_17`,fill=IF, color=SR2)) +
    scale_x_date() + 
    geom_line() +
    # scale_fill_brewer(palette="Dark2") +
    ggtitle("Indice de Basileira por Segmento")+
    labs(y = "IB (em %)", color='SR') + 
    theme_classic() + 
    theme(plot.title = element_text(hjust = 0.5))
  
  return (list("ativo"=ativo_plot,"PL"=pl_plot,"IB"=basileia_plot))
}
plotdefaultbanks = function (banks_filtered) {
  
 
  
  #########################################ativo total #########################################
  
  ##########################################Geral#########################################
   plot_df = banks_filtered %>%
    filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_10` > 5*boxplot(banks_filtered$`01_10`)$stats[1,])
    
    
    geral_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_10`,fill=IF, color=`group`)) +
    scale_x_date() + 
    geom_line() +
    # scale_fill_brewer(palette="Dark2") +
    ggtitle("Índice de Basileia")+
    labs(y = "Indice de Basileia (em %)", color='Grupos') + 
    theme_classic() + 
    theme(plot.title = element_text(hjust = 0.5))
  
  
    ##########################################Falencia#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_10` > 5*boxplot(banks_filtered$`01_10`)$stats[1,]) %>%
     filter(group=="RJ")
     
   falencia_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_10`,fill=IF, color=`IF`)) +
   scale_x_date() + 
   geom_line(show.legend = F) +
    # scale_fill_brewer(palette="Dark2") +
   ggtitle("Índice de Basileia - Bancos que faliram")+
   labs(y = "Indice de Basileia (em %)", color='Grupos') + 
   theme_classic() + 
   theme(plot.title = element_text(hjust = 0.5))  
    
   ##########################################M&A#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_10` > 5*boxplot(banks_filtered$`01_10`)$stats[1,]) %>%
     filter(group=="M&A")
   
   ma_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_10`,fill=IF, color=`IF`)) +
     scale_x_date() + 
     geom_line(show.legend = F) +
     # scale_fill_brewer(palette="Dark2") +
     ggtitle("Índice de Basileia - Bancos comprados")+
     labs(y = "Indice de Basileia (em %)", color='Grupos') + 
     theme_classic() + 
     theme(plot.title = element_text(hjust = 0.5))   


   #########################################MUDANCA INST#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_10` > 5*boxplot(banks_filtered$`01_10`)$stats[1,]) %>%
     filter(group=="Transformação")
   
   trans_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_10`,fill=IF, color=`IF`)) +
     scale_x_date() + 
     geom_line(show.legend = F) +
     # scale_fill_brewer(palette="Dark2") +
     ggtitle("Índice de Basileia - deixaram de ser bancos")+
     labs(y = "Indice de Basileia (em %)", color='Grupos') + 
     theme_classic() + 
     theme(plot.title = element_text(hjust = 0.5))  

   plot_agg = ggarrange(falencia_plot, ma_plot, trans_plot + rremove("x.text"), 
             labels = c("A", "B", "C"),
             ncol = 1, nrow = 3)  

   
   
   ##########################################INDICE DE IMOBILIZACAO #########################################
   
   ##########################################Geral#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_11`)$stats[5,] & `01_11` > 5*boxplot(banks_filtered$`01_10`)$stats[1,])
   
   
   geral_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_11`,fill=IF, color=`group`)) +
     scale_x_date() + 
     geom_line() +
     # scale_fill_brewer(palette="Dark2") +
     ggtitle("Índice de Imobilização")+
     labs(y = "Indice de Imobilização (em %)", color='Grupos') + 
     theme_classic() + 
     theme(plot.title = element_text(hjust = 0.5))
   
   
   #########################################alencia#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_11` > 5*boxplot(banks_filtered$`01_11`)$stats[1,]) %>%
     filter(group=="RJ")
   
   falencia_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_11`,fill=IF, color=`IF`)) +
     scale_x_date() + 
     geom_line(show.legend = F) +
     # scale_fill_brewer(palette="Dark2") +
     ggtitle("Índice de Imobilização - Bancos que faliram")+
     labs(y = "Indice de Imobilização (em %)", color='Grupos') + 
     theme_classic() + 
     theme(plot.title = element_text(hjust = 0.5))  
   
   ##########################################M&A#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_11` > 5*boxplot(banks_filtered$`01_11`)$stats[1,]) %>%
     filter(group=="M&A")
   
   ma_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_11`,fill=IF, color=`IF`)) +
     scale_x_date() + 
     geom_line(show.legend = F) +
     # scale_fill_brewer(palette="Dark2") +
     ggtitle("Índice de Imobilização - Bancos comprados")+
     labs(y = "Indice de Imobilização (em %)", color='Grupos') + 
     theme_classic() + 
     theme(plot.title = element_text(hjust = 0.5))   
   
   
   #########################################MUDANCA INST#########################################
   plot_df = banks_filtered %>%
     filter(`01_10` < 3*boxplot(banks_filtered$`01_10`)$stats[5,] & `01_11` > 5*boxplot(banks_filtered$`01_11`)$stats[1,]) %>%
     filter(group=="Transformação")
   
   trans_plot = ggplot(data=plot_df, mapping = aes(x=Data, y=`01_11`,fill=IF, color=`IF`)) +
     scale_x_date() + 
     geom_line(show.legend = F) +
     # scale_fill_brewer(palette="Dark2") +
     ggtitle("Índice de Imobilização - deixaram de ser bancos")+
     labs(y = "Indice de Imobilização (em %)", color='Grupos') + 
     theme_classic() + 
     theme(plot.title = element_text(hjust = 0.5))  
   
   plot_agg2 = ggarrange(falencia_plot, ma_plot, trans_plot + rremove("x.text"), 
                        labels = c("A", "B", "C"),
                        ncol = 1, nrow = 3)  
  
  
  return (c(plot_agg, plot_agg2))
}

############################################################### Rodando as funcoes #################################################################

setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/")

df_list = open_database()
df_bacen = df_list[[2]]
df_var = df_list[[1]]
default_df = df_list[[3]]
rm(df_list)

df_list = setdataset(1, df_bacen, df_var, default_df)
df_filtered_normalized = df_list[[1]]
df_filtered = df_list[[2]]
rm(df_list)


df_list = append_economicvar(df_filtered_normalized,df_filtered, df_var)
df_final_normalized=df_list[[1]]
df_final=df_list[[2]]
df_var=df_list[[3]]
a = d
rm(df_list)

#CONFERIR COLUNAS 
df_col1 = data.frame(colSums(is.na(df_final))) %>% rownames_to_column("var")
names(df_col1)[2]='naCol'
df_col1 %>% filter(naCol!=0)

#SAVE
list_df = list("DF normalized" = df_final_normalized, "DF Final" = df_final, "Dicionario" = df_var)
write.xlsx(list_df, "DF Final.xlsx")


#VAR IMPORTANTES
#               "01_01", "02_17", #Ativo total
#               "01_03", "03_21", #Passivo total
#               "01_05", "03_20", #PL
#               "01_06", "04_29", #LL
#               "01_09","05_05", #Prwa
#               "01_10","05_17", #IB
#               "01_11","05_19") %>% #


