############################################################ Setting FIDC Data ############################################################


library(lubridate)
library(xlsx)
library(openxlsx)
library(readxl)
library(dplyr)    
library(plyr)
library(Hmisc)
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

open_fidc_df = function(){
  
  "Esta funcao abre e modifica a base de dados de FIDC "
  
  print ('[OPEN_FIDC_DF]: Carregando open_fidc_df...')
  start_time <- Sys.time()
  
  path_FIDC = "M:\\03 - COOPE\\02 - Controle Gerencial\\02 - Instrumentos de Gestão e Análise\\01 - Análise\\06 - Bases de Dados Gerais\\FIDC"
  new_wd=set_wd(path_FIDC)
  
  print ('[OPEN_FIDC_DF]: Abrindo e arrumando a base de dados FIDCS')
  
  fidc_df = read.csv("Dados FIDCs.csv", header=TRUE, sep=";") 
  
  # fidc_df = fidc_df %>% mutate(Data=as.Date(paste0("01/",Data), format="%d/%m/%Y"),
  #                              CNPJ_FUNDO=as.character(CNPJ_FUNDO),
  #                              DENOM_SOCIAL=as.character(DENOM_SOCIAL),
  #                              TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
  #                              CNPJ_ADMIN=as.character(CNPJ_ADMIN),
  #                              ADMIN=as.character(ADMIN),
  #                              DT_COMPTC = as.Date(DT_COMPTC, format="%Y-%m-%d"),
  #                              TAB_X_VL_RENTAB_MES = as.numeric(TAB_X_VL_RENTAB_MES),
  #                              TAB_X_NR_COTST = as.numeric(TAB_X_NR_COTST),
  #                              CONDOM = case_when(CONDOM=="ABERTO" ~ 1, CONDOM=="FECHADO" ~ 0),
  #                              FUNDO_EXCLUSIVO = case_when(FUNDO_EXCLUSIVO=="S" ~ 1, FUNDO_EXCLUSIVO=="N" ~ 0),
  #                              COTST_INTERESSE = case_when(COTST_INTERESSE=="S" ~ 1, COTST_INTERESSE=="N" ~ 0)) %>%
  #                       mutate_at(vars(names(fidc_df[,13:length(fidc_df)])), as.numeric)
  
  
  fidc_df = fidc_df %>% mutate(Data=as.Date(paste0("01/",Data), format="%d/%m/%Y"),
                                           CNPJ_FUNDO=as.character(CNPJ_FUNDO),
                                           DENOM_SOCIAL=as.character(DENOM_SOCIAL),
                                           TAB_X_CLASSE_SERIE=as.character(TAB_X_CLASSE_SERIE),
                                           TAB_X_CLASSE_SERIE_AUX=as.character(TAB_X_CLASSE_SERIE_AUX),
                                           CNPJ_ADMIN=as.character(CNPJ_ADMIN),
                                           ADMIN=as.character(ADMIN),
                                           DT_COMPTC = as.Date(DT_COMPTC, format="%d/%m/%Y"),
                                           TAB_X_VL_RENTAB_MES = as.numeric(TAB_X_VL_RENTAB_MES),
                                           TAB_X_NR_COTST = as.numeric(TAB_X_NR_COTST)) %>%
    #CONDOM = case_when(CONDOM=="ABERTO" ~ 1, CONDOM=="FECHADO" ~ 0, TRUE ~ CONDOM),
    #FUNDO_EXCLUSIVO = case_when(FUNDO_EXCLUSIVO=="S" ~ 1, FUNDO_EXCLUSIVO=="N" ~ 0, TRUE ~ FUNDO_EXCLUSIVO),
    #COTST_INTERESSE = case_when(COTST_INTERESSE=="S" ~ 1, COTST_INTERESSE=="N" ~ 0, TRUE ~ COTST_INTERESSE)) %>%
    mutate_at(vars(names(fidc_df[,11:length(fidc_df)])), as.numeric)  
  
  print(str(fidc_df))
  print ('[OPEN_FIDC_DF]: base de dados FIDCS aberto e modificado com sucesso!')
  print(paste0('[OPEN_FIDC_DF]: set_date demorou ', Sys.time() - start_time, ' segundos para abrir e editar a base de dados FIDCS'))
  
  return (fidc_df)
}

fidc_date_list=fidc_df$Data[!duplicated(fidc_df$Data)]


#Check dimensions of the dataframes
fidc_list = list()
for (i in 1:length(fidc_date_list)){
  fidc_list[[as.character(fidc_date_list[[i]])]] = fidc_df %>% filter(Data==fidc_df$Data[!duplicated(fidc_df$Data)][[i]])
}


#Check new funds for every month
new_fidcs_list_diff=list()
new_fidcs_list_names=list()
for (i in 2:length(fidc_date_list)-1) {
  

  fidc_df_filter1 = fidc_df %>% filter(Data==fidc_date_list[[i]])
  fidc_df_filter2 = fidc_df %>% filter(Data==fidc_date_list[[i+1]])
  
  #funds that entered in database
  fidc_list1 = fidc_df_filter1$DENOM_SOCIAL[!duplicated(fidc_df_filter1$DENOM_SOCIAL)]
  
  fidc_list2_aux=fidc_df_filter2[!fidc_df_filter2$DENOM_SOCIAL %in% fidc_list1,"DENOM_SOCIAL"]
  fidc_list2=fidc_list2_aux[!duplicated(fidc_list2_aux)]
  
  
  #funds that left from database
  fidc_list3 = fidc_df_filter2$DENOM_SOCIAL[!duplicated(fidc_df_filter2$DENOM_SOCIAL)]
  
  fidc_list4_aux=fidc_df_filter2[!fidc_df_filter2$DENOM_SOCIAL %in% fidc_list3,"DENOM_SOCIAL"]
  fidc_list4=fidc_list4_aux[!duplicated(fidc_list4_aux)]
  
  
  new_fidcs_list_names[[i]]=fidc_list2
  new_fidcs_list_diff[[i]]=list("diff"=nrow(fidc_df_filter2)-nrow(fidc_df_filter1), 
                                "length_t"=length(fidc_list2), 
                                "length_t1"=length(fidc_list4),
                                "diff_orig"=length(fidc_list2)-length(fidc_list4))
  
}









#VERIFICAR RESULTADOS DE AUMENTOS DE FUNDOS
#VERIFICAR QUANTOS NAs POR COLUNA
#VERIFICAR FIDC POR CONCENTRACAO



############################################################### Rodando as funcoes #################################################################


#Chamar a funcao que define o caminho para abrir a planilha de dias uteis


fidc_df=open_fidc_df()



