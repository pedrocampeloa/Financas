############################################################ Setting FIDC Data ############################################################

library(xml2)
library(devtools)
library(lubridate)
library(openxlsx)
library(readxl)
library(dplyr)    
library(plyr)
library(reshape2)
library(data.table)
library(tidyr)
library(stringr)


set_wd = function(wd) {
  
  "Esta funcao define a pasta onde os arquivos serao retirados/salvados. Pasta colar o caminho desejado ao chamar a funcao"
  
  print (paste0("[SET_wD]: Diretorio Atual: ", getwd()))
  #print (paste0("Caminho das bibliotecas: ", .libPaths()))
  
  cwd = gsub('\\\\' , '/', wd)
  setwd(cwd)
  
  print (paste0("[SET_wD]: Seu novo Diretorio eh: ", getwd()))
  
  return (cwd)
}

set_FIDC_columnnames = function(FIDC_date){
  
  "Esta funcao define ao nome das colunas para apendar no dataframe de forma automática"
  
  FIDC_year=substr(FIDC_date, start = 1, stop = 4)
  
  print(paste0("[SET_FIDC_COLUMNAMES]: Abrindo a base de dados para a data, ", FIDC_date," e para o ano, ", FIDC_year))
  start_time <- Sys.time()
  
  FIDC_index_list=c("I", "II","III","IV","V","VI","VII","IX","X_1","X_2","X_3","X_4", "X_5")
  FIDC_list=list()
  
  
  FIDC_year=substr(FIDC_date, start = 1, stop = 4)
  print(paste0("[SET_FIDC_DATABASE]: Abrindo a base de dados para a data, ", FIDC_date," e para o ano, ", FIDC_year))
  
  for (FIDC_index in FIDC_index_list){
    
    print(paste0("[SET_FIDC_DATABASE]: Abrindo a base de dados Número, ", FIDC_index))
    
    
    file_name = paste0(FIDC_year, "/", FIDC_date,"/inf_mensal_fidc_tab_",FIDC_index,"_",FIDC_date,".csv")
    FIDC_csv = read.csv(file_name, header=TRUE, sep=";", encoding='UFT-8')
    FIDC_list[[FIDC_index]]=FIDC_csv
  }
  
  print(paste0("[SET_FIDC_DATABASE]: Arrumando cada tabela da base de dados"))
  
  df1=FIDC_list["I"][[1]]
  df2=FIDC_list["II"][[1]]
  df3=FIDC_list["III"][[1]]
  df4=FIDC_list["IV"][[1]]
  df5=FIDC_list["V"][[1]]
  df6=FIDC_list["VI"][[1]]
  df7=FIDC_list["VII"][[1]]
  df8=FIDC_list["IX"][[1]]
  
  df9 = FIDC_list["X_1"][[1]]  
  df10 = FIDC_list["X_2"][[1]]  
  df11 = FIDC_list["X_3"][[1]]   %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE))%>% 
    mutate(TAB_X_CLASSE_SERIE = case_when(TAB_X_CLASSE_SERIE=="Classe Sênior"  ~ "Sênior",
                                          TRUE ~ TAB_X_CLASSE_SERIE))
  print("Arrumando dataframe das movimentações")
  df12 = FIDC_list["X_4"][[1]]  
  
  df12_new = data.frame(matrix(ncol = 0, nrow = 0))
  # names(df12_new)=c("CNPJ_FUNDO","DENOM_SOCIAL","DT_COMPTC","TAB_X_TP_OPER","TAB_X_CLASSE_SERIE","TAB_X_VL_TOTAL_AMORT","TAB_X_VL_TOTAL_CAPT",
  #                   "TAB_X_VL_TOTAL_RESG","TAB_X_VL_TOTAL_RESGSOL","TAB_X_QT_TOTAL_AMORT","TAB_X_QT_TOTAL_CAPT","TAB_X_QT_TOTAL_RESG","TAB_X_QT_TOTAL_RESGSOL")
  for (i in df12$DENOM_SOCIAL[!duplicated(df12$DENOM_SOCIAL)]){
    
    df_filtered = df12 %>% filter(DENOM_SOCIAL==i)
    
    for (j in  df_filtered$TAB_X_CLASSE_SERIE[!duplicated(df_filtered$TAB_X_CLASSE_SERIE)]){
      
      df12_append = data.frame(CNPJ_FUNDO= df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(CNPJ_FUNDO) %>% as.list() %>% .[[1]] %>% .[[1]], 
                              DENOM_SOCIAL=df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(DENOM_SOCIAL) %>% as.list() %>% .[[1]] %>% .[[1]], 
                              DT_COMPTC=df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(DT_COMPTC) %>% as.list() %>% .[[1]] %>% .[[1]],
                              TAB_X_CLASSE_SERIE=j,
                              TAB_X_VL_TOTAL_AMORT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                          df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                          NA),
                              TAB_X_VL_TOTAL_CAPT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                         df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                         NA),
                              TAB_X_VL_TOTAL_RESG=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                         df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                         NA),
                              TAB_X_VL_TOTAL_RESGSOL=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                            df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                            NA),
                              TAB_X_QT_TOTAL_AMORT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                          df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                          NA),
                              TAB_X_QT_TOTAL_CAPT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                         df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                         NA),
                              TAB_X_QT_TOTAL_RESG=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                         df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                         NA),
                              TAB_X_QT_TOTAL_RESGSOL=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                            df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                            NA))
      df12_new=bind_rows(df12_new,df12_append) 
    }
  }
  
  print("Dataframe das movimentações arrumado")
  df13=FIDC_list["X_5"][[1]]
  
  
  #Agreggate dfs 9 and 11
  if (nrow(df11)>nrow(df9)){
    df9e11 = df11 %>% left_join(df9 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)), 
                                by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE")) 
    
  }else {
    
    df9e11 = df9 %>%  mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)) %>% 
      left_join(df11 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)), 
                by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE")) 
  }
  
  #Agreggate dfs  10 and 12 
  if (nrow(df10)>nrow(df12_new)){
    df10e12 = df10 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)) %>%
      left_join(df12_new %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)),
                by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
    
  }else {
    
    df10e12 = df12_new %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE))%>% 
      left_join(df10 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)), 
                by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
  }
  
  #Agreggate dfs 9e11 and 10e12 
  df10e12 = df10e12 %>% mutate(TAB_X_CLASSE_SERIE_AUX=case_when(substr(TAB_X_CLASSE_SERIE, start = 1, stop = 5) == "Série" ~ "Sênior", TRUE ~ TAB_X_CLASSE_SERIE)) 
  
  if (nrow(df10e12)>nrow(df9e11)){
    
    df9a12 = df10e12 %>% left_join(df9e11, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE_AUX"="TAB_X_CLASSE_SERIE"))
    
  } else{
    
    print ("Número de Séries é menor que o Número de cotas -> verificar!!!! ")
    
  }
  
  print(paste0("[SET_FIDC_DATABASE]: Base de dados ajustadas, agregando todas elas..."))

  
  df_agg=plyr::join_all(list(df1,df2,df3,df4, df5, df6, df7, df8, df13), by=c("CNPJ_FUNDO","DENOM_SOCIAL", "DT_COMPTC"), type = 'full')
  df = df9a12 %>% left_join(df_agg, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC"))
  
  FIDC_date_aux=paste0("01-",substr(FIDC_date, start = 5, stop = 6),"-",substr(FIDC_date, start = 1, stop = 4))
  df$Data=as.Date(FIDC_date_aux, "%d-%m-%Y")
  
  df = df %>% select(Data, CNPJ_FUNDO, DENOM_SOCIAL, DT_COMPTC, TAB_X_CLASSE_SERIE,TAB_X_CLASSE_SERIE_AUX, CNPJ_ADMIN, ADMIN, CONDOM, FUNDO_EXCLUSIVO, everything())
  

  print(paste0("[SET_FIDC_COLUMNAMES]: Base de dados agregadas!"))
  print(paste0('[SET_FIDC_COLUMNAMES]: set_FIDC_columnames demorou ', Sys.time() - start_time, ' segundos para selecionar as colunas do df a ser criado'))
  
  return (names(df))
  
}

set_FIDC_database = function(){
  
  
  "Esta funcao abre cada csv com os dados dos mercados de FIDC e os agrega em um dataframe único"
  
  #print(paste0("[SET_FIDC_DATABASE]: Abrindo a base de dados para a data, ", FIDC_date," e para o ano, ", FIDC_year))
  start_time <- Sys.time()
  
  
  df_aggregate = data.frame(matrix(ncol = 0, nrow = 0))
  #names(df_aggregate) = column_names
  
  FIDC_list=list()
  FIDC_list2=list()
  FIDC_date_list=c("201701","201702","201703","201704","201705","201706","201707","201708","201709","201710","201711","201712",
                   "201801","201802","201803","201804","201805","201806","201807","201808","201809","201810","201811","201812",
                   "201901","201902","201903","201904","201905","201906", "201907", "201908")
  FIDC_index_list=c("I", "II","III","IV","V","VI","VII","IX","X_1","X_2","X_3","X_4", "X_5")
  
  for (FIDC_date in FIDC_date_list){
    
    FIDC_year=substr(FIDC_date, start = 1, stop = 4)
    print(paste0("[SET_FIDC_DATABASE]: Abrindo a base de dados para a data, ", FIDC_date," e para o ano, ", FIDC_year))
    
    for (FIDC_index in FIDC_index_list){
      
      print(paste0("[SET_FIDC_DATABASE]: Abrindo a base de dados Número, ", FIDC_index))
      
      
      file_name = paste0(FIDC_year, "/", FIDC_date,"/inf_mensal_fidc_tab_",FIDC_index,"_",FIDC_date,".csv")
      FIDC_csv = read.csv(file_name, header=TRUE, sep=";")
      FIDC_list[[FIDC_index]]=FIDC_csv
    }
    
    print(paste0("[SET_FIDC_DATABASE]: Arrumando cada tabela da base de dados"))
    
    df1=FIDC_list["I"][[1]]
    df2=FIDC_list["II"][[1]]
    df3=FIDC_list["III"][[1]]
    df4=FIDC_list["IV"][[1]]
    df5=FIDC_list["V"][[1]]
    df6=FIDC_list["VI"][[1]]
    df7=FIDC_list["VII"][[1]]
    df8=FIDC_list["IX"][[1]]

    df9 = FIDC_list["X_1"][[1]]  
    df10 = FIDC_list["X_2"][[1]]  
    df11 = FIDC_list["X_3"][[1]]   %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE))%>% 
                                       mutate(TAB_X_CLASSE_SERIE=case_when(TAB_X_CLASSE_SERIE=="Classe Sênior"  ~ "Sênior",
                                                                              TRUE ~ TAB_X_CLASSE_SERIE))
    print("Arrumando dataframe das movimentações")
    df12 = FIDC_list["X_4"][[1]]  
    
    df12_new = data.frame(matrix(ncol = 0, nrow = 0))
    # names(df12_new)=c("CNPJ_FUNDO","DENOM_SOCIAL","DT_COMPTC","TAB_X_TP_OPER","TAB_X_CLASSE_SERIE","TAB_X_VL_TOTAL_AMORT","TAB_X_VL_TOTAL_CAPT",
    #                   "TAB_X_VL_TOTAL_RESG","TAB_X_VL_TOTAL_RESGSOL","TAB_X_QT_TOTAL_AMORT","TAB_X_QT_TOTAL_CAPT","TAB_X_QT_TOTAL_RESG","TAB_X_QT_TOTAL_RESGSOL")
    for (i in df12$DENOM_SOCIAL[!duplicated(df12$DENOM_SOCIAL)]){
      
      df_filtered = df12 %>% filter(DENOM_SOCIAL==i)
      
      for (j in  df_filtered$TAB_X_CLASSE_SERIE[!duplicated(df_filtered$TAB_X_CLASSE_SERIE)]){
        
        df12_append= data.frame(CNPJ_FUNDO= df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(CNPJ_FUNDO) %>% as.list() %>% .[[1]] %>% .[[1]], 
                                DENOM_SOCIAL=df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(DENOM_SOCIAL) %>% as.list() %>% .[[1]] %>% .[[1]], 
                                DT_COMPTC=df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(DT_COMPTC) %>% as.list() %>% .[[1]] %>% .[[1]],
                                TAB_X_CLASSE_SERIE=j,
                                TAB_X_VL_TOTAL_AMORT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                            df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                            NA),
                                TAB_X_VL_TOTAL_CAPT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_VL_TOTAL_RESG=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_VL_TOTAL_RESGSOL=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                              df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                              NA),
                                TAB_X_QT_TOTAL_AMORT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                            df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                            NA),
                                TAB_X_QT_TOTAL_CAPT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_QT_TOTAL_RESG=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_QT_TOTAL_RESGSOL=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                              df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                              NA))
        df12_new=bind_rows(df12_new,df12_append) 
      }
    }
    
    print("Dataframe das movimentações arrumado")
    df13=FIDC_list["X_5"][[1]]
    
    
    #Agreggate dfs 9 and 11
    if (nrow(df11)>nrow(df9)){
      df9e11 = df11 %>% left_join(df9 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)), 
                                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE")) 
      
    }else {
      
      df9e11 = df9 %>%  mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)) %>% 
                        left_join(df11 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)), 
                                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE")) 
    }
    
    #Agreggate dfs  10 and 12 
    if (nrow(df10)>nrow(df12_new)){
      df10e12 = df10 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)) %>%
                        left_join(df12_new %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)),
                                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
      
    }else {

      df10e12 = df12_new %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE))%>% 
                            left_join(df10 %>% mutate(TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE)), 
                                      by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
    }
    
    #Agreggate dfs 9e11 and 10e12 
    df10e12 = df10e12 %>% mutate(TAB_X_CLASSE_SERIE_AUX=case_when(substr(TAB_X_CLASSE_SERIE, start = 1, stop = 5) == "Série" ~ "Sênior", TRUE ~ TAB_X_CLASSE_SERIE)) 

    if (nrow(df10e12)>nrow(df9e11)){
      
      df9a12 = df10e12 %>% left_join(df9e11, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE_AUX"="TAB_X_CLASSE_SERIE"))
      
    } else{
      
      print ("Número de Séries é menor que o Número de cotas -> verificar!!!! ")
    
      }
    
    print(paste0("[SET_FIDC_DATABASE]: Base de dados ajustadas, agregando todas elas..."))
    
    df_agg=plyr::join_all(list(df1,df2,df3,df4, df5, df6, df7, df8, df13), by=c("CNPJ_FUNDO","DENOM_SOCIAL", "DT_COMPTC"), type = 'full')
    df = df9a12 %>% left_join(df_agg, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC")) 
    
    FIDC_date_aux=paste0("01-",substr(FIDC_date, start = 5, stop = 6),"-",substr(FIDC_date, start = 1, stop = 4))
    df$Data=as.Date(FIDC_date_aux, "%d-%m-%Y")
    
    df = df %>% select(Data, CNPJ_FUNDO, DENOM_SOCIAL, DT_COMPTC, TAB_X_CLASSE_SERIE,TAB_X_CLASSE_SERIE_AUX, CNPJ_ADMIN, ADMIN, CONDOM, FUNDO_EXCLUSIVO, everything())
    
    df = df %>% mutate(#Data=as.Date(paste0("01/",Data), format="%d/%m/%Y"),
                       CNPJ_FUNDO=as.character(CNPJ_FUNDO),
                       DENOM_SOCIAL=as.character(DENOM_SOCIAL),
                       TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
                       CNPJ_ADMIN=as.character(CNPJ_ADMIN),
                       ADMIN=as.character(ADMIN),
                       DT_COMPTC = as.Date(DT_COMPTC, format="%Y-%m-%d"),
                       TAB_X_VL_RENTAB_MES = as.numeric(TAB_X_VL_RENTAB_MES),
                       TAB_X_NR_COTST = as.numeric(TAB_X_NR_COTST),
                       CONDOM = case_when(CONDOM=="ABERTO" ~ 1, CONDOM=="FECHADO" ~ 0),
                       FUNDO_EXCLUSIVO = case_when(FUNDO_EXCLUSIVO=="S" ~ 1, FUNDO_EXCLUSIVO=="N" ~ 0),
                       COTST_INTERESSE = case_when(COTST_INTERESSE=="S" ~ 1, COTST_INTERESSE=="N" ~ 0)) %>%
                mutate_at(vars(names(df[,11:length(df)])), as.numeric)
    df_aggregate=bind_rows(df_aggregate,df) 
    
    
    if (FIDC_date=="201712"|FIDC_date=="201801"|FIDC_date=="201802") {
      
      print(paste0("Removendo duplicadas para a data", FIDC_date))
      
      df_aggregate1 = df_aggregate %>% filter(DENOM_SOCIAL!="FUNDO DE INVESTIMENTO EM QUOTAS DE FUNDO DE INVESTIMENTO EM DIREITOS CREDITÓRIOS BLUE CAPITAL")
      df_aggregate2 = df_aggregate %>% filter(DENOM_SOCIAL=="FUNDO DE INVESTIMENTO EM QUOTAS DE FUNDO DE INVESTIMENTO EM DIREITOS CREDITÓRIOS BLUE CAPITAL") %>% distinct(TAB_X_CLASSE_SERIE, .keep_all= TRUE) 
      
      df_aggregate = bind_rows(df_aggregate1,df_aggregate2)
      
    }
  }
  
  df_aggregate=df_aggregate[2:nrow(df_aggregate),]
  df_aggregate$Data=format(as.POSIXlt(df_aggregate$Data, format="%m/%Y"),format="%m/%Y")

  print(paste0("[SET_FIDC_DATABASE]: Base de dados para todos os anos!!"))
  print(paste0('[SET_FIDC_DATABASE]: set_FIDC_database demorou ', Sys.time() - start_time, ' minutos para selecionar as colunas do df a ser criado'))
  
  return (df_aggregate)
}

append_new_FIDC_data = function(FIDC_date_list){
  
  "Esta funcao pega o novo csv baixado do site da cvm e appenda na base de dados de FIDCs"
  
  start_time <- Sys.time()
  
  df_aggregate = data.frame(matrix(ncol = 0, nrow = 0))
  # names(df_aggregate) = columns_names
  
  FIDC_list=list()
  FIDC_list2=list()
  FIDC_index_list=c("I", "II","III","IV","V","VI","VII","IX","X_1","X_2","X_3","X_4", "X_5")
  
  for (FIDC_date in FIDC_date_list){
    
    FIDC_year=substr(FIDC_date, start = 1, stop = 4)
    print(paste0("[APPEND_NEW_FIDC_DATA]: Abrindo a base de dados para a data, ", FIDC_date," e para o ano, ", FIDC_year))
    
    for (FIDC_index in FIDC_index_list){
      
      print(paste0("[APPEND_NEW_FIDC_DATA]: Abrindo a base de dados Número, ", FIDC_index))
      
      
      file_name = paste0(FIDC_year, "/", FIDC_date,"/inf_mensal_fidc_tab_",FIDC_index,"_",FIDC_date,".csv")
      FIDC_csv = read.csv(file_name, header=TRUE, sep=";", quote="", "ISO-8859-1")
      FIDC_list[[FIDC_index]]=FIDC_csv
    }
    print(paste0("[APPEND_NEW_FIDC_DATA]: Arrumando cada tabela da base de dados"))
    
    df1=FIDC_list["I"][[1]]
    df2=FIDC_list["II"][[1]]
    df3=FIDC_list["III"][[1]]
    df4=FIDC_list["IV"][[1]]
    df5=FIDC_list["V"][[1]]
    df6=FIDC_list["VI"][[1]]
    df7=FIDC_list["VII"][[1]]
    df8=FIDC_list["IX"][[1]]
    
    df9 = FIDC_list["X_1"][[1]] %>% mutate_if(is.factor, as.character)  
    df10 = FIDC_list["X_2"][[1]]  
    df11 = FIDC_list["X_3"][[1]] %>% 
      mutate_if(is.factor, as.character)  %>% 
      mutate(TAB_X_CLASSE_SERIE = case_when(str_detect(TAB_X_CLASSE_SERIE, "Classe Sênior") ~ gsub("Classe Sênior", "Sênior", TAB_X_CLASSE_SERIE),
                                              str_detect(TAB_X_CLASSE_SERIE, "Classe Sénior") ~ gsub("Classe Sénior", "Sênior", TAB_X_CLASSE_SERIE),
                                              TRUE~TAB_X_CLASSE_SERIE)) 

    print("Arrumando dataframe das movimentações")
    
    df12 = FIDC_list["X_4"][[1]]  
    
    df12_new = data.frame(matrix(ncol = 0, nrow = 0))
    # names(df12_new)=c("CNPJ_FUNDO","DENOM_SOCIAL","DT_COMPTC","TAB_X_TP_OPER","TAB_X_CLASSE_SERIE","TAB_X_VL_TOTAL_AMORT","TAB_X_VL_TOTAL_CAPT",
    #                   "TAB_X_VL_TOTAL_RESG","TAB_X_VL_TOTAL_RESGSOL","TAB_X_QT_TOTAL_AMORT","TAB_X_QT_TOTAL_CAPT","TAB_X_QT_TOTAL_RESG","TAB_X_QT_TOTAL_RESGSOL")
    for (i in df12$DENOM_SOCIAL[!duplicated(df12$DENOM_SOCIAL)]){
      
      df_filtered = df12 %>% filter(DENOM_SOCIAL==i)
      
      for (j in  df_filtered$TAB_X_CLASSE_SERIE[!duplicated(df_filtered$TAB_X_CLASSE_SERIE)]){
        
        df12_append= data.frame(CNPJ_FUNDO= df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(CNPJ_FUNDO) %>% as.list() %>% .[[1]] %>% .[[1]], 
                                DENOM_SOCIAL=df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(DENOM_SOCIAL) %>% as.list() %>% .[[1]] %>% .[[1]], 
                                DT_COMPTC=df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>% select(DT_COMPTC) %>% as.list() %>% .[[1]] %>% .[[1]],
                                TAB_X_CLASSE_SERIE=j,
                                TAB_X_VL_TOTAL_AMORT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                            df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                            NA),
                                TAB_X_VL_TOTAL_CAPT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_VL_TOTAL_RESG=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_VL_TOTAL_RESGSOL=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]])>0,
                                                              df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_VL_TOTAL) %>% as.list() %>% .[[1]],
                                                              NA),
                                TAB_X_QT_TOTAL_AMORT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                            df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Amortizações") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                            NA),
                                TAB_X_QT_TOTAL_CAPT=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Captações no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_QT_TOTAL_RESG=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                           df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates no Mês") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                           NA),
                                TAB_X_QT_TOTAL_RESGSOL=ifelse(length(df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]])>0,
                                                              df_filtered %>% filter(TAB_X_CLASSE_SERIE==j) %>%  filter(TAB_X_TP_OPER=="Resgates Solicitados") %>% select(TAB_X_QT_COTA) %>% as.list() %>% .[[1]],
                                                              NA))
        df12_new=bind_rows(df12_new,df12_append) 
      }
    }
    
    print("Dataframe das movimentações arrumado")
    df13=FIDC_list["X_5"][[1]]
    
    
    #Agreggate dfs 9 and 11
    a = df9 %>% mutate(aux = paste0(CNPJ_FUNDO,"&",TAB_X_CLASSE_SERIE)) %>% distinct(aux) %>% .[[1]]
    b = df11 %>% mutate(aux = paste0(CNPJ_FUNDO,"&",TAB_X_CLASSE_SERIE)) %>% distinct(aux) %>% .[[1]]
    
    if (length(b[!(b %in% a)])>0){
      df9e11 = df11 %>%  
        mutate_if(is.factor, as.character) %>% 
        left_join(df9 %>% mutate_if(is.factor, as.character),
                                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))

    } else {

      df9e11 = df9 %>%  mutate_if(is.factor, as.character) %>%
        left_join(df11 %>% mutate_if(is.factor, as.character),
                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
    }
    
    
    #Agreggate dfs  10 and 12 
    if (nrow(df10)>nrow(df12_new)){
      df10e12 = df10 %>%  mutate_if(is.factor, as.character) %>%
        left_join(df12_new %>% mutate_if(is.factor, as.character),
                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
      
    } else {
      
      df10e12 = df12_new %>% mutate_if(is.factor, as.character) %>%
        left_join(df10 %>% mutate_if(is.factor, as.character), 
                  by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
    }
    
    
    
    #Agreggate dfs 9e11 and 10e12 
    df10e12 = df10e12 %>% 
      mutate(TAB_X_CLASSE_SERIE=gsub("Série", "Sênior", TAB_X_CLASSE_SERIE)) %>% 
      mutate(TAB_X_CLASSE_SERIE_AUX = case_when(str_detect(TAB_X_CLASSE_SERIE, "Sênior") ~ "Sênior", TRUE~TAB_X_CLASSE_SERIE))
    
    FIDC_date_aux=paste0("01-",substr(FIDC_date, start = 5, stop = 6),"-",substr(FIDC_date, start = 1, stop = 4))
    
    if (as.Date(FIDC_date_aux, "%d-%m-%Y") <= as.Date("2019-10-01")){
      if (nrow(df10e12)>nrow(df9e11)){
        
        df9a12 = df10e12 %>% 
          left_join(df9e11, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE_AUX"="TAB_X_CLASSE_SERIE")) 
        
      } else {
        
        df9a12 = df9e11 %>% 
          left_join(df10e12, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE_AUX"))
      }
      
    } else {
    
      a = df9e11 %>% mutate(aux = paste0(CNPJ_FUNDO,"&",TAB_X_CLASSE_SERIE)) %>% distinct(aux) %>% .[[1]]
      b = df10e12 %>% mutate(aux = paste0(CNPJ_FUNDO,"&",TAB_X_CLASSE_SERIE)) %>% distinct(aux) %>% .[[1]]

      if ((length(a[!(a %in% b)])>0)|nrow(df9e11)>=nrow(df10e12)){

        df9a12 = df9e11 %>% 
          left_join(df10e12, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
      } else {

        df9a12 = df10e12 %>% 
          left_join(df9e11, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC", "TAB_X_CLASSE_SERIE"="TAB_X_CLASSE_SERIE"))
      }
    }
    

    
    print(paste0("[APPEND_NEW_FIDC_DATA]: Base de dados ajustadas, agregando todas elas..."))
    
    df_agg=plyr::join_all(list(df1,df2,df3,df4, df5, df6, df7, df8, df13), by=c("CNPJ_FUNDO","DENOM_SOCIAL", "DT_COMPTC"), type = 'full') %>% mutate_if(is.factor, as.character) 
    df = df9a12  %>% mutate_if(is.factor, as.character) %>% left_join(df_agg, by=c("CNPJ_FUNDO"="CNPJ_FUNDO", "DENOM_SOCIAL"="DENOM_SOCIAL", "DT_COMPTC"="DT_COMPTC"))
    
    df$Data=as.Date(FIDC_date_aux, "%d-%m-%Y")

    df = df %>% mutate(TAB_X_CLASSE_SERIE_AUX = case_when(str_detect(TAB_X_CLASSE_SERIE, "Sênior") ~ "Sênior", TRUE~TAB_X_CLASSE_SERIE))
    df = df %>% select(Data, CNPJ_FUNDO, DENOM_SOCIAL, DT_COMPTC, TAB_X_CLASSE_SERIE,TAB_X_CLASSE_SERIE_AUX, CNPJ_ADMIN, ADMIN, CONDOM, FUNDO_EXCLUSIVO, everything())
    
    df = df %>% mutate(#Data=as.Date(paste0("01/",Data), format="%d/%m/%Y"),
      CNPJ_FUNDO=as.character(CNPJ_FUNDO),
      DENOM_SOCIAL=as.character(DENOM_SOCIAL),
      TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
      CNPJ_ADMIN=as.character(CNPJ_ADMIN),
      ADMIN=as.character(ADMIN),
      DT_COMPTC = as.Date(DT_COMPTC, format="%Y-%m-%d"),
      TAB_X_VL_RENTAB_MES = as.numeric(TAB_X_VL_RENTAB_MES),
      TAB_X_NR_COTST = as.numeric(TAB_X_NR_COTST),
      CONDOM = case_when(CONDOM=="ABERTO" ~ 1, CONDOM=="FECHADO" ~ 0),
      FUNDO_EXCLUSIVO = case_when(FUNDO_EXCLUSIVO=="S" ~ 1, FUNDO_EXCLUSIVO=="N" ~ 0),
      COTST_INTERESSE = case_when(COTST_INTERESSE=="S" ~ 1, COTST_INTERESSE=="N" ~ 0)) %>%
      mutate_at(vars(names(df[,11:length(df)])), as.numeric)
    
    df_aggregate=bind_rows(df_aggregate,df) 
    
    
    if (FIDC_date=="201712"|FIDC_date=="201801"|FIDC_date=="201802") {
      
      print(paste0("Removendo duplicadas para as datas ", FIDC_date))
      
      df_aggregate1 = df_aggregate %>% filter(DENOM_SOCIAL!="FUNDO DE INVESTIMENTO EM QUOTAS DE FUNDO DE INVESTIMENTO EM DIREITOS CREDITÓRIOS BLUE CAPITAL")
      df_aggregate2 = df_aggregate %>% filter(DENOM_SOCIAL=="FUNDO DE INVESTIMENTO EM QUOTAS DE FUNDO DE INVESTIMENTO EM DIREITOS CREDITÓRIOS BLUE CAPITAL") %>% distinct(TAB_X_CLASSE_SERIE, .keep_all= TRUE) 
      
      df_aggregate = bind_rows(df_aggregate1,df_aggregate2)
      
    }
  }
  
  print(paste0("[APPEND_NEW_FIDC_DATA]: Base de dados agregadas!"))
  
  # df_aggregate2 = read_excel("Dados FIDCs.csv", sheet = "FIDCs", col_names=TRUE)
  df_aggregate2 = read.xlsx("Dados FIDCs.xlsx")
  

  df_aggregate2 = df_aggregate2 %>% mutate(Data=as.Date(Data, origin = "1899-12-30"),
                                           CNPJ_FUNDO=as.character(CNPJ_FUNDO),
                                           DENOM_SOCIAL=as.character(DENOM_SOCIAL),
                                           TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
                                           TAB_X_CLASSE_SERIE_AUX=as.character(TAB_X_CLASSE_SERIE_AUX),
                                           CNPJ_ADMIN=as.character(CNPJ_ADMIN),
                                           ADMIN=as.character(ADMIN),
                                           DT_COMPTC = as.Date(DT_COMPTC, origin = "1899-12-30")) %>%
                                           #CONDOM = case_when(CONDOM=="ABERTO" ~ 1, CONDOM=="FECHADO" ~ 0, TRUE ~ CONDOM),
                                           #FUNDO_EXCLUSIVO = case_when(FUNDO_EXCLUSIVO=="S" ~ 1, FUNDO_EXCLUSIVO=="N" ~ 0, TRUE ~ FUNDO_EXCLUSIVO),
                                           #COTST_INTERESSE = case_when(COTST_INTERESSE=="S" ~ 1, COTST_INTERESSE=="N" ~ 0, TRUE ~ COTST_INTERESSE)) %>%
                mutate_at(vars(names(df_aggregate2[,9:length(df_aggregate2)])), as.numeric)  
  
  df_aggregate2 = df_aggregate2 %>% select(Data, CNPJ_FUNDO, DENOM_SOCIAL, DT_COMPTC, TAB_X_CLASSE_SERIE,TAB_X_CLASSE_SERIE_AUX, CNPJ_ADMIN, ADMIN, CONDOM, FUNDO_EXCLUSIVO,COTST_INTERESSE, everything())
  
  a=df_aggregate%>%distinct(Data) %>% as.list() %>% .[[1]]
  b=df_aggregate2%>%distinct(Data) %>% as.list() %>% .[[1]]
  if (length(b[b%in%a])>0){
    
    df_aggregate2 = df_aggregate2 %>% filter(!(Data %in% b[b%in%a]))
    #df_aggregate2 = df_aggregate2 %>% slice(1:which(df_aggregate2$Data == head(df_aggregate$Data,1))[[1]] - 1)  
    df = bind_rows(df_aggregate2,df_aggregate)
    
  } else {
    df = bind_rows(df_aggregate2,df_aggregate)
    
  }
  
  print(paste0('[APPEND_NEW_FIDC_DATA]: append_new_FIDC_data demorou ', Sys.time() - start_time, ' segundos para selecionar as colunas do df a ser criado'))
  
  return (df)
}

save_data = function(path_FIDC, excel_file_name,list_of_datasets){
  
  "Essa funcao agrega todos os dataframe filtrados e salva a planilha em xlsx"
  
  print ('[SAVE_DATA]: Carregando funcao save_data...')
  start_time <- Sys.time()
  
  # path_FIDC = "M:\\03 - COOPE\\02 - Controle Gerencial\\02 - Instrumentos de Gestão e Análise\\01 - Análise\\06 - Bases de Dados Gerais\\FIDC - Mercado Primário"
  #path_FIDC="/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Dados CVM"
  new_wd=set_wd(path_FIDC)

  write.xlsx(list_of_datasets, file = paste0(excel_file_name,".csv"), fileEncoding="UTF-8")
  write.xlsx(list_of_datasets, file = paste0(excel_file_name,".xlsx"),fileEncoding="UTF-8")
  print ('[SAVE_DATA]: Planilha agregada salva com sucesso')
  print(paste0('[SAVE_DATA]: save_data demorou ', Sys.time() - start_time, ' minutos para agrupar os dados e salvar em XLSX'))
  
  return ("Base de dados de FIDCs salva com sucesso com sucesso")
}

generate_fidcs_name = function (fidc_df_aux, flag) {
  
  "Essa funcao gera um df com todos os fidcs que ja passaram na base de dados"
  
  print ('[GENERATE_FIDCS_NAME]: Carregando funcao generate_fidcs_name')
  start_time <- Sys.time()
  
  if (flag==1){
    
    path_FIDC = "M:\\03 - COOPE\\02 - Controle Gerencial\\02 - Instrumentos de Gestão e Análise\\01 - Análise\\06 - Bases de Dados Gerais\\FIDC - Mercado Primário"
    new_wd=set_wd(path_FIDC)
    
    print ('[GENERATE_FIDCS_NAME]: Abrindo e arrumando a base de dados FIDCS')
    
    fidc_df = read.csv2("Dados FIDCs.csv", header=TRUE) 
    
    fidc_df = fidc_df %>% mutate(#Data=as.Date(Data, format="%d/%m/%Y"),
      CNPJ_FUNDO=as.character(CNPJ_FUNDO),
      DENOM_SOCIAL=as.character(DENOM_SOCIAL),
      TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
      TAB_X_CLASSE_SERIE_AUX=as.character(TAB_X_CLASSE_SERIE_AUX),
      CNPJ_ADMIN=as.character(CNPJ_ADMIN),
      ADMIN=as.character(ADMIN),
      DT_COMPTC = as.Date(DT_COMPTC, format="%d/%m/%Y"))
    
    
    fidc_df = fidc_df %>% mutate(#Data=as.Date(paste0("01/",Data), format="%d/%m/%Y"),
                                 CNPJ_FUNDO=as.character(CNPJ_FUNDO),
                                 DENOM_SOCIAL=as.character(DENOM_SOCIAL),
                                 TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
                                 TAB_X_CLASSE_SERIE_AUX=as.character(TAB_X_CLASSE_SERIE_AUX),
                                 CNPJ_ADMIN=as.character(CNPJ_ADMIN),
                                 ADMIN=as.character(ADMIN),
                                 DT_COMPTC = as.Date(DT_COMPTC, format="%d/%m/%Y")) %>%
      mutate_at(vars(names(df_aggregate2[,9:length(df_aggregate2)])), as.numeric)  
    
    fidc_df = fidc_df %>% select(Data, CNPJ_FUNDO, DENOM_SOCIAL, DT_COMPTC, TAB_X_CLASSE_SERIE,TAB_X_CLASSE_SERIE_AUX, CNPJ_ADMIN, ADMIN, CONDOM, FUNDO_EXCLUSIVO,COTST_INTERESSE, everything())
    
  } else{
    fidc_df = fidc_df_aux
  }
  
  fidc_df_key = fidc_df %>% mutate(KEY=paste0(CNPJ_FUNDO,"&&&",TAB_X_CLASSE_SERIE),
                                   CONDOM=case_when(CONDOM==1~"ABERTO", TRUE ~"FECHADO"),
                                   FUNDO_EXCLUSIVO=case_when(FUNDO_EXCLUSIVO==1~"S", TRUE ~"N"),
                                   COTST_INTERESSE=case_when(COTST_INTERESSE==1~"S", TRUE ~"N")) %>% 
    select(Data,DT_COMPTC,CNPJ_FUNDO,KEY,DENOM_SOCIAL,TAB_X_CLASSE_SERIE_AUX,TAB_X_CLASSE_SERIE,CNPJ_ADMIN,ADMIN, CONDOM, FUNDO_EXCLUSIVO, COTST_INTERESSE) %>% 
    rename(c("Data"="Data de Entrada na Base","DT_COMPTC"="Data de Compatibilidade","CNPJ_FUNDO"="CNPJ do Fundo","DENOM_SOCIAL"="Nome do Fundo", "TAB_X_CLASSE_SERIE_AUX"="Cota do Fundo","TAB_X_CLASSE_SERIE"="Número da Série de Emissão",
             "ADMIN"="Nome do Administrador","CNPJ_ADMIN"="CNPJ do Administrador","CONDOM"="Tipo de Condomínio", "FUNDO_EXCLUSIVO"="Fundo Exclusivo","COTST_INTERESSE"="Cotistas com Interesse Único")) %>%
    distinct(KEY, .keep_all= TRUE)
  
  write.xlsx(list("Nomes FIDCS" = fidc_df_key), file = "FIDCS Registrados na CVM.xlsx")
  
  
  print(paste0('[GENERATE_FIDCS_NAME]: save_data demorou ', Sys.time() - start_time, ' minutos gerar e salvar a base com todos os nomes e cnpjs dos fidcs'))
  
  return ("Base de dados de FIDCs salva com sucesso com sucesso")
  
}

############################################################### Rodando as funcoes #################################################################

#Chamar a funcao que define o caminho para abrir a planilha de dias uteis
# path_FIDC = "M:\\03 - COOPE\\02 - Controle Gerencial\\02 - Instrumentos de Gestão e Análise\\01 - Análise\\06 - Bases de Dados Gerais\\FIDC - Mercado Primário"
path_FIDC="/Users/pedrocampelo/Desktop/Work/FUNCEF/FIDCS/CVM/Dados CVM"
new_wd=set_wd(path_FIDC)
 
#Definir nome das columas para todas as 203 variaveis de forma automática
# FIDC_date="201701"
# columns_names = set_FIDC_columnnames(FIDC_date)

#Coletar todas as tabelas para todos os anos e agregar em um único dataframe
# aggregate_df=set_FIDC_database(columns_names)

#Salvar base de dados na pasta de FIDC
# df_list <- list("FIDCs" = aggregate_df)
# excel_file_name="Dados FIDCs"
# save_data(excel_file_name,df_list)

#Agregar um mes novo
#FIDC_date_list = c("201701","201702","201703","201704","201705","201706", "201707", "201708", "201709", "201710", "201711", "201712",
#                   "201801","201802","201803","201804","201805","201806", "201807", "201808", "201809", "201810", "201811", "201812",
#                   "201901","201902","201903","201904","201905","201906", "201907", "201908", "201909", "201910", "201911", "201912")

FIDC_date_list=c("201910","201911","201912", "202001","202002","202003","202004","202005")
aggregate_df=append_new_FIDC_data(FIDC_date_list)

#Salvar base de dados na pasta de FIDC
df_list <- list("FIDCs" = aggregate_df)
excel_file_name="Dados FIDCs 2"
save_data(excel_file_name,df_list)

#generate_fidcs_name(aggregate_df,0)
# generate_fidcs_name(NULL,1)



