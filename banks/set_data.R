library(readxl)
library(dplyr)
library(tidyr)
library(Hmisc)
library(sjmisc)
library(stringr)
library(openxlsx)



setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/Planilhas IF")


#year_list = paste0("0",as.character(seq(0,1)))
#names_list=c("resumo")

year_list = append(paste0("0",as.character(seq(0,9))),as.character(seq(10,19)))
month_list = append(paste0("0",as.character(seq(3,9,3))),12)
names_list = c("resumo", "ativo", "passivo","dre","ic","ccapf_mpv",
               "ccapj_mpv","ccapj_cnae","ccapj_pt","cca_qco","cca_nro", "cca_ind", "cca_rg")

df_resumo = data.frame(matrix(ncol=0, nrow=0))
df_ativo = data.frame(matrix(ncol=0, nrow=0))
df_passivo = data.frame(matrix(ncol=0, nrow=0))
df_dre = data.frame(matrix(ncol=0, nrow=0))
df_ic = data.frame(matrix(ncol=0, nrow=0))
df_ccapf_mpv = data.frame(matrix(ncol=0, nrow=0))
df_ccapj_mpv = data.frame(matrix(ncol=0, nrow=0))
df_ccapj_cnae = data.frame(matrix(ncol=0, nrow=0))
df_ccapj_pt = data.frame(matrix(ncol=0, nrow=0))
df_cca_qco = data.frame(matrix(ncol=0, nrow=0))
df_cca_nro = data.frame(matrix(ncol=0, nrow=0))
df_cca_ind = data.frame(matrix(ncol=0, nrow=0))
df_cca_rg = data.frame(matrix(ncol=0, nrow=0))

dim_df = data.frame(matrix(ncol=0, nrow=0))
for (name in names_list) {
  for (year in year_list){
    for (month in month_list){
      
      file_name = paste0(month,year,"_",name,".csv")
      
      if (file.exists(file_name)){
        if (name=="resumo"){                           #RESUMO
        
          print(paste0("Baixando DF, ", file_name))
          df_resumo2 = read.csv(file_name, sep=";",stringsAsFactors = FALSE)
          
          #limpando a base
          df_resumo2 = df_resumo2 %>% 
            rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
            select(-c("X")) %>%
            filter(Data!="") %>%
            #mutate_if(is.factor, as.character) %>%
            mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) #%>%
          
          df_resumo2 = data.frame(lapply(df_resumo2, function(x) {gsub(" - PRUDENCIAL", "", x)}))
          df_resumo2 = data.frame(lapply(df_resumo2, function(x) {gsub("\\.", "", x)})) 
          df_resumo2 = data.frame(lapply(df_resumo2, function(x) {gsub("\\%", "", x)})) 
          df_resumo2 = data.frame(lapply(df_resumo2, function(x) {gsub("NI", NA, x)})) 
          df_resumo2 = data.frame(lapply(df_resumo2, function(x) {gsub(",", ".", x)})) %>% 
            mutate_if(is.factor, as.character) 
            
          #transformando as variaveis em numericas
          if ("Segmento" %in% names(df_resumo2)){
            df_resumo2 = df_resumo2 %>% mutate_at(names(df_resumo2[11:length(df_resumo2)]), as.numeric) %>%
              mutate(Data=as.Date(Data)) %>%
              rename("SEG"="Segmento")
              
          } else {
            df_resumo2 = df_resumo2 %>% mutate_at(names(df_resumo2[10:length(df_resumo2)]), as.numeric) %>%
              mutate(Data=as.Date(Data))
          }
          
          print(nrow(df_resumo2))
          print(paste0("Numero de colunas deste df é: ", length(df_resumo2)))
          print(names(df_resumo2)[names(df_resumo2) %nin% names(df_resumo)])
          
          dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_resumo2), "ncol"=ncol(df_resumo2))
          
          df_resumo = bind_rows(df_resumo,df_resumo2) 
          dim_df = bind_rows(dim_df, dim_df2)
          
        }  else if (name=="ativo"){                            #ATIVO
          
          print(paste0("Baixando DF,", file_name))
          df_ativo2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)

          df_ativo2 = df_ativo2[2:nrow(df_ativo2), 2:length(df_ativo2)-1]
          # names(df_ativo2)[which(str_detect(names(df_ativo2), "X"))] = df_ativo2[1:1,which(str_detect(names(df_ativo2), "X"))]

          #limpando a base
          df_ativo2 = df_ativo2 %>% 
            rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
            mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
            filter(!is.na(Data))
            #mutate_if(is.factor, as.character) %>%
          
          df_ativo2 = data.frame(lapply(df_ativo2, function(x) {gsub(" - PRUDENCIAL", "", x)}))
          df_ativo2 = data.frame(lapply(df_ativo2, function(x) {gsub("\\.", "", x)})) %>%
            mutate_if(is.factor, as.character) 
          
          #transformando as variaveis em numericas
          if ("Segmento" %in% names(df_ativo2)){
            df_ativo2 = df_ativo2 %>% mutate_at(names(df_ativo2[11:length(df_ativo2)]), as.numeric) %>%
              mutate(Data=as.Date(Data)) %>%
              rename("SEG"="Segmento")
          } else {
            df_ativo2 = df_ativo2 %>% mutate_at(names(df_ativo2[10:length(df_ativo2)]), as.numeric) %>%
              mutate(Data=as.Date(Data))
          }
          print(nrow(df_ativo2))
          print(paste0("Numero de colunas deste df é: ", length(df_ativo2)))
          print(names(df_ativo2)[names(df_ativo2) %nin% names(df_ativo2)])
          
          
          dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ativo2), "ncol"=ncol(df_ativo2))
          
          df_ativo = bind_rows(df_ativo,df_ativo2) 
          dim_df = bind_rows(dim_df, dim_df2)
          
        }  else if (name=="passivo"){


            print(paste0("Baixando DF,", file_name))
            df_passivo2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
            
            df_passivo2 = df_passivo2[3:nrow(df_passivo2), 2:length(df_passivo2)-1]
            
            #limpando a base
            df_passivo2 = df_passivo2 %>% 
              rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
              mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
              filter(!is.na(Data))
              #mutate_if(is.factor, as.character) %>%
            
            df_passivo2 = data.frame(lapply(df_passivo2, function(x) {gsub(" - PRUDENCIAL", "", x)}))
            df_passivo2 = data.frame(lapply(df_passivo2, function(x) {gsub("\\.", "", x)})) %>%
              mutate_if(is.factor, as.character) 
            
            #transformando as variaveis em numericas
            if ("Segmento" %in% names(df_passivo2)){
              df_passivo2 = df_passivo2 %>% mutate_at(names(df_passivo2[11:length(df_passivo2)]), as.numeric) %>%
                mutate(Data=as.Date(Data)) %>%
                rename("SEG"="Segmento")
            } else {
              df_passivo2 = df_passivo2 %>% mutate_at(names(df_passivo2[10:length(df_passivo2)]), as.numeric) %>%
                mutate(Data=as.Date(Data))
            }
            print(nrow(df_passivo2))
            print(paste0("Numero de colunas deste df é: ", length(df_passivo2)))
            print(names(df_passivo2)[names(df_passivo2) %nin% names(df_passivo2)])
            
            dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_passivo2), "ncol"=ncol(df_passivo2))
            
            dim_df = bind_rows(dim_df, dim_df2)
            df_passivo = bind_rows(df_passivo,df_passivo2) 
            
          } else if (name=="dre"){                                 #DRE

          print(paste0("Baixando DF,", file_name))
          df_dre2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
          
          df_dre2 = df_dre2[3:nrow(df_dre2), 2:length(df_dre2)-1]
          
          #limpando a base
          df_dre2 = df_dre2 %>% 
            rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
            mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
            filter(!is.na(Data))
          #mutate_if(is.factor, as.character) %>%
          
          df_dre2 = data.frame(lapply(df_dre2, function(x) {gsub(" - PRUDENCIAL", "", x)}))
          df_dre2 = data.frame(lapply(df_dre2, function(x) {gsub("\\.", "", x)})) %>%
            mutate_if(is.factor, as.character) 
          
          #transformando as variaveis em numericas
          if ("Segmento" %in% names(df_dre2)){
            df_dre2 = df_dre2 %>% mutate_at(names(df_dre2[11:length(df_dre2)]), as.numeric) %>%
              mutate(Data=as.Date(Data)) %>%
              rename("SEG"="Segmento")
          } else {
            df_dre2 = df_dre2 %>% mutate_at(names(df_dre2[10:length(df_dre2)]), as.numeric) %>%
              mutate(Data=as.Date(Data))
          }
          print(nrow(df_dre2))
          print(paste0("Numero de colunas deste df é: ", length(df_dre2)))
          print(names(df_dre2)[names(df_dre2) %nin% names(df_dre2)])
          
          dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_dre2), "ncol"=ncol(df_dre2))
          
          dim_df = bind_rows(dim_df, dim_df2)
          df_dre = bind_rows(df_dre,df_dre2)
          
        } else if (name=="ic"){                     #IC

            print(paste0("Baixando DF,", file_name))
            df_ic2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
            
            df_ic2 = df_ic2[3:nrow(df_ic2), 2:length(df_ic2)-1]
            
            #limpando a base
            df_ic2 = df_ic2 %>% 
              rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
              mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
              filter(!is.na(Data))
            #mutate_if(is.factor, as.character) %>%
            
            df_ic2 = data.frame(lapply(df_ic2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
            df_ic2 = data.frame(lapply(df_ic2, function(x) {gsub("\\.", "", x)})) 
            df_ic2 = data.frame(lapply(df_ic2, function(x) {gsub("\\%", "", x)})) 
            df_ic2 = data.frame(lapply(df_ic2, function(x) {gsub("NI", NA, x)})) 
            df_ic2 = data.frame(lapply(df_ic2, function(x) {gsub(",", ".", x)})) %>% 
              mutate_if(is.factor, as.character) 
            
            #transformando as variaveis em numericas
            if ("Segmento" %in% names(df_ic2)){
              df_ic2 = df_ic2 %>% mutate_at(names(df_ic2[11:length(df_ic2)]), as.numeric) %>%
                mutate(Data=as.Date(Data)) %>%
                rename("SEG"="Segmento")
            } else {
              df_ic2 = df_ic2 %>% mutate_at(names(df_ic2[10:length(df_ic2)]), as.numeric) %>%
                mutate(Data=as.Date(Data))
            }
            print(nrow(df_ic2))
            print(paste0("Numero de colunas deste df é: ", length(df_ic2)))
            print(names(df_ic2)[names(df_ic2) %nin% names(df_ic2)])
            
            # dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ic2), "ncol"=ncol(df_ic2), "names"=paste(names(df_ic2), collapse = '/////'))
            dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ic2), "ncol"=ncol(df_ic2))
            
            dim_df = bind_rows(dim_df, dim_df2)
            
            
            df_ic = bind_rows(df_ic,df_ic2)

        } else if (name=="ccapf_mpv"){
            
            print(paste0("Baixando DF,", file_name))
            df_ccapf_mpv2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
            
            df_ccapf_mpv2 = df_ccapf_mpv2[2:nrow(df_ccapf_mpv2),2:length(df_ccapf_mpv2)-1]
            
            #limpando a base
            df_ccapf_mpv2 = df_ccapf_mpv2 %>% 
              rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
              mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
              filter(!is.na(Data))
            #mutate_if(is.factor, as.character) %>%
            
            # df_ccapf_mpv2 = data.frame(lapply(df_ccapf_mpv2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
            df_ccapf_mpv2 = data.frame(lapply(df_ccapf_mpv2, function(x) {gsub("\\.", "", x)})) 
            #df_ccapf_mpv2 = data.frame(lapply(df_ccapf_mpv2, function(x) {gsub("\\%", "", x)})) 
            #df_ccapf_mpv2 = data.frame(lapply(df_ccapf_mpv2, function(x) {gsub(",", ".", x)})) 
            df_ccapf_mpv2 = data.frame(lapply(df_ccapf_mpv2, function(x) {gsub("NI", NA, x)})) %>% 
              mutate_if(is.factor, as.character) 
            
            #transformando as variaveis em numericas
            if ("Segmento" %in% names(df_ccapf_mpv2)){
              df_ccapf_mpv2 = df_ccapf_mpv2 %>% mutate_at(names(df_ccapf_mpv2[11:length(df_ccapf_mpv2)]), as.numeric) %>%
                mutate(Data=as.Date(Data)) %>%
                rename("SEG"="Segmento")
            } else {
              df_ccapf_mpv2 = df_ccapf_mpv2 %>% mutate_at(names(df_ccapf_mpv2[10:length(df_ccapf_mpv2)]), as.numeric) %>%
                mutate(Data=as.Date(Data))
            }
            print(nrow(df_ccapf_mpv2))
            print(paste0("Numero de colunas deste df é: ", length(df_ccapf_mpv2)))
            print(names(df_ccapf_mpv2)[names(df_ccapf_mpv2) %nin% names(df_ccapf_mpv2)])
            
            dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ccapf_mpv2), "ncol"=ncol(df_ccapf_mpv2))
            dim_df = bind_rows(dim_df, dim_df2)
            
            df_ccapf_mpv = bind_rows(df_ccapf_mpv,df_ccapf_mpv2)

        } else if (name=="ccapj_mpv"){

          print(paste0("Baixando DF,", file_name))
          df_ccapj_mpv2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
          
          df_ccapj_mpv2 = df_ccapj_mpv2[2:nrow(df_ccapj_mpv2),2:length(df_ccapj_mpv2)-1]
          
          #limpando a base
          df_ccapj_mpv2 = df_ccapj_mpv2 %>% 
            rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
            mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
            filter(!is.na(Data))
          #mutate_if(is.factor, as.character) %>%

          # df_ccapj_mpv2 = data.frame(lapply(df_ccapj_mpv2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
          df_ccapj_mpv2 = data.frame(lapply(df_ccapj_mpv2, function(x) {gsub("\\.", "", x)})) 
          #df_ccapj_mpv2 = data.frame(lapply(df_ccapj_mpv2, function(x) {gsub("\\%", "", x)})) 
          #df_ccapj_mpv2 = data.frame(lapply(df_ccapj_mpv2, function(x) {gsub(",", ".", x)})) 
          df_ccapj_mpv2 = data.frame(lapply(df_ccapj_mpv2, function(x) {gsub("NI", NA, x)})) %>% 
            mutate_if(is.factor, as.character) 
          
          #transformando as variaveis em numericas
          if ("Segmento" %in% names(df_ccapj_mpv2)){
            df_ccapj_mpv2 = df_ccapj_mpv2 %>% mutate_at(names(df_ccapj_mpv2[11:length(df_ccapj_mpv2)]), as.numeric) %>%
              mutate(Data=as.Date(Data)) %>%
              rename("SEG"="Segmento")
          } else {
            df_ccapj_mpv2 = df_ccapj_mpv2 %>% mutate_at(names(df_ccapj_mpv2[10:length(df_ccapj_mpv2)]), as.numeric) %>%
              mutate(Data=as.Date(Data))
          }
          print(nrow(df_ccapj_mpv2))
          print(paste0("Numero de colunas deste df é: ", length(df_ccapj_mpv2)))
          print(names(df_ccapj_mpv2)[names(df_ccapj_mpv2) %nin% names(df_ccapj_mpv2)])
          
          dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ccapj_mpv2), "ncol"=ncol(df_ccapj_mpv2))
          
          dim_df = bind_rows(dim_df, dim_df2)
          df_ccapj_mpv = bind_rows(df_ccapj_mpv,df_ccapj_mpv2)

      } else if (name=="ccapj_cnae"){

          print(paste0("Baixando DF,", file_name))
          df_ccapj_cnae2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
          
          df_ccapj_cnae2 = df_ccapj_cnae2[2:nrow(df_ccapj_cnae2),2:length(df_ccapj_cnae2)-1]
          
          #limpando a base
          df_ccapj_cnae2 = df_ccapj_cnae2 %>% 
            rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
            mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
            filter(!is.na(Data))
          #mutate_if(is.factor, as.character) %>%

          # df_ccapj_cnae2 = data.frame(lapply(df_ccapj_cnae2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
          df_ccapj_cnae2 = data.frame(lapply(df_ccapj_cnae2, function(x) {gsub("\\.", "", x)})) 
          #df_ccapj_cnae2 = data.frame(lapply(df_ccapj_cnae2, function(x) {gsub("\\%", "", x)})) 
          #df_ccapj_cnae2 = data.frame(lapply(df_ccapj_cnae2, function(x) {gsub(",", ".", x)})) 
          df_ccapj_cnae2 = data.frame(lapply(df_ccapj_cnae2, function(x) {gsub("NI", NA, x)})) %>% 
            mutate_if(is.factor, as.character) 
          
          #transformando as variaveis em numericas
          if ("Segmento" %in% names(df_ccapj_cnae2)){
            df_ccapj_cnae2 = df_ccapj_cnae2 %>% mutate_at(names(df_ccapj_cnae2[11:length(df_ccapj_cnae2)]), as.numeric) %>%
              mutate(Data=as.Date(Data)) %>%
              rename("SEG"="Segmento")
          } else {
            df_ccapj_cnae2 = df_ccapj_cnae2 %>% mutate_at(names(df_ccapj_cnae2[10:length(df_ccapj_cnae2)]), as.numeric) %>%
              mutate(Data=as.Date(Data))
          }
          print(nrow(df_ccapj_cnae2))
          print(paste0("Numero de colunas deste df é: ", length(df_ccapj_cnae2)))
          print(names(df_ccapj_cnae2)[names(df_ccapj_cnae2) %nin% names(df_ccapj_cnae2)])
          
          dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ccapj_cnae2), "ncol"=ncol(df_ccapj_cnae2))
          dim_df = bind_rows(dim_df, dim_df2)
          
          df_ccapj_cnae = bind_rows(df_ccapj_cnae,df_ccapj_cnae2)

    }   else if (name=="ccapj_pt"){

        print(paste0("Baixando DF,", file_name))
        df_ccapj_pt2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
        
        df_ccapj_pt2 = df_ccapj_pt2[,2:length(df_ccapj_pt2)-1]
        
        #limpando a base
        df_ccapj_pt2 = df_ccapj_pt2 %>% 
          rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
          mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
          filter(!is.na(Data))
        #mutate_if(is.factor, as.character) %>%
        
        # df_ccapj_pt2 = data.frame(lapply(df_ccapj_pt2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
        df_ccapj_pt2 = data.frame(lapply(df_ccapj_pt2, function(x) {gsub("\\.", "", x)})) 
        #df_ccapj_pt2 = data.frame(lapply(df_ccapj_pt2, function(x) {gsub("\\%", "", x)})) 
        #df_ccapj_pt2 = data.frame(lapply(df_ccapj_pt2, function(x) {gsub(",", ".", x)})) 
        df_ccapj_pt2 = data.frame(lapply(df_ccapj_pt2, function(x) {gsub("NI", NA, x)})) %>% 
          mutate_if(is.factor, as.character) 
        
        #transformando as variaveis em numericas
        if ("Segmento" %in% names(df_ccapj_pt2)){
          df_ccapj_pt2 = df_ccapj_pt2 %>% mutate_at(names(df_ccapj_pt2[11:length(df_ccapj_pt2)]), as.numeric) %>%
            mutate(Data=as.Date(Data)) %>%
            rename("SEG"="Segmento")
        } else {
          df_ccapj_pt2 = df_ccapj_pt2 %>% mutate_at(names(df_ccapj_pt2[10:length(df_ccapj_pt2)]), as.numeric) %>%
            mutate(Data=as.Date(Data))
        }
        print(nrow(df_ccapj_pt2))
        print(paste0("Numero de colunas deste df é: ", length(df_ccapj_pt2)))
        print(names(df_ccapj_pt2)[names(df_ccapj_pt2) %nin% names(df_ccapj_pt2)])
        
        dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ccapj_pt2), "ncol"=ncol(df_ccapj_pt2))
        #im_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_ccapj_pt2), "ncol"=ncol(df_ccapj_pt2), "names"=paste(names(df_ccapj_pt2), collapse = '/////'))
        
        dim_df = bind_rows(dim_df, dim_df2)

        df_ccapj_pt = bind_rows(df_ccapj_pt,df_ccapj_pt2)

    } else if (name=="cca_qco"){
      

      print(paste0("Baixando DF,", file_name))
      
      df_cca_qco2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
      df_cca_qco2 = df_cca_qco2[,2:length(df_cca_qco2)-1]
      
      #limpando a base
      df_cca_qco2 = df_cca_qco2 %>% 
        rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
        mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
        filter(!is.na(Data))
      #mutate_if(is.factor, as.character) %>%
      
      # df_cca_qco2 = data.frame(lapply(df_cca_qco2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
      df_cca_qco2 = data.frame(lapply(df_cca_qco2, function(x) {gsub("\\.", "", x)})) 
      #df_cca_qco2 = data.frame(lapply(df_cca_qco2, function(x) {gsub("\\%", "", x)})) 
      #df_cca_qco2 = data.frame(lapply(df_cca_qco2, function(x) {gsub(",", ".", x)})) 
      df_cca_qco2 = data.frame(lapply(df_cca_qco2, function(x) {gsub("NI", NA, x)})) %>% 
        mutate_if(is.factor, as.character) 
      
      #transformando as variaveis em numericas
      if ("Segmento" %in% names(df_cca_qco2)){
        df_cca_qco2 = df_cca_qco2 %>% mutate_at(names(df_cca_qco2[11:length(df_cca_qco2)]), as.numeric) %>%
          mutate(Data=as.Date(Data)) %>%
          rename("SEG"="Segmento")
      } else {
        df_cca_qco2 = df_cca_qco2 %>% mutate_at(names(df_cca_qco2[10:length(df_cca_qco2)]), as.numeric) %>%
          mutate(Data=as.Date(Data)) 
      }
      print(nrow(df_cca_qco2))
      print(paste0("Numero de colunas deste df é: ", length(df_cca_qco2)))
      print(names(df_cca_qco2)[names(df_cca_qco2) %nin% names(df_cca_qco2)])
      
      dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_cca_qco2), "ncol"=ncol(df_cca_qco2))
      dim_df = bind_rows(dim_df, dim_df2)
      
      df_cca_qco = bind_rows(df_cca_qco,df_cca_qco2)
      
      
    } else if (name=="cca_nro"){
      

      print(paste0("Baixando DF,", file_name))
      df_cca_nro2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
      
      df_cca_nro2 = df_cca_nro2[,2:length(df_cca_nro2)-1]
      
      #limpando a base
      df_cca_nro2 = df_cca_nro2 %>% 
        rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
        mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
        filter(!is.na(Data))
      #mutate_if(is.factor, as.character) %>%
      
      # df_cca_nro2 = data.frame(lapply(df_cca_nro2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
      df_cca_nro2 = data.frame(lapply(df_cca_nro2, function(x) {gsub("\\.", "", x)})) 
      #df_cca_nro2 = data.frame(lapply(df_cca_nro2, function(x) {gsub("\\%", "", x)})) 
      #df_cca_nro2 = data.frame(lapply(df_cca_nro2, function(x) {gsub(",", ".", x)})) 
      df_cca_nro2 = data.frame(lapply(df_cca_nro2, function(x) {gsub("NI", NA, x)})) %>% 
        mutate_if(is.factor, as.character) 
      
      #transformando as variaveis em numericas
      if ("Segmento" %in% names(df_cca_nro2)){
        df_cca_nro2 = df_cca_nro2 %>% mutate_at(names(df_cca_nro2[11:length(df_cca_nro2)]), as.numeric) %>%
          mutate(Data=as.Date(Data)) %>%
          rename("SEG"="Segmento")
      } else {
        df_cca_nro2 = df_cca_nro2 %>% mutate_at(names(df_cca_nro2[10:length(df_cca_nro2)]), as.numeric) %>%
          mutate(Data=as.Date(Data))
      }
      print(nrow(df_cca_nro2))
      print(paste0("Numero de colunas deste df é: ", length(df_cca_nro2)))
      print(names(df_cca_nro2)[names(df_cca_nro2) %nin% names(df_cca_nro2)])
      
      dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_cca_nro2), "ncol"=ncol(df_cca_nro2))
      dim_df = bind_rows(dim_df, dim_df2)
      
      df_cca_nro = bind_rows(df_cca_nro,df_cca_nro2)

      
    }   else if (name=="cca_ind"){
      

      print(paste0("Baixando DF,", file_name))
      df_cca_ind2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
      
      df_cca_ind2 = df_cca_ind2[,2:length(df_cca_ind2)-1]
      
      #limpando a base
      df_cca_ind2 = df_cca_ind2 %>% 
        rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
        mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
        filter(!is.na(Data))
      #mutate_if(is.factor, as.character) %>%
      
      # df_cca_ind2 = data.frame(lapply(df_cca_ind2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
      df_cca_ind2 = data.frame(lapply(df_cca_ind2, function(x) {gsub("\\.", "", x)})) 
      #df_cca_ind2 = data.frame(lapply(df_cca_ind2, function(x) {gsub("\\%", "", x)})) 
      #df_cca_ind2 = data.frame(lapply(df_cca_ind2, function(x) {gsub(",", ".", x)})) 
      df_cca_ind2 = data.frame(lapply(df_cca_ind2, function(x) {gsub("NI", NA, x)})) %>% 
        mutate_if(is.factor, as.character) 
      
      #transformando as variaveis em numericas
      if ("Segmento" %in% names(df_cca_ind2)){
        df_cca_ind2 = df_cca_ind2 %>% mutate_at(names(df_cca_ind2[11:length(df_cca_ind2)]), as.numeric) %>%
          mutate(Data=as.Date(Data)) %>%
          rename("SEG"="Segmento")
      } else {
        df_cca_ind2 = df_cca_ind2 %>% mutate_at(names(df_cca_ind2[10:length(df_cca_ind2)]), as.numeric) %>%
          mutate(Data=as.Date(Data))
      }
      print(nrow(df_cca_ind2))
      print(paste0("Numero de colunas deste df é: ", length(df_cca_ind2)))
      print(names(df_cca_ind2)[names(df_cca_ind2) %nin% names(df_cca_ind2)])
      
      dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_cca_ind2), "ncol"=ncol(df_cca_ind2))
      dim_df = bind_rows(dim_df, dim_df2)
      
      df_cca_ind = bind_rows(df_cca_ind,df_cca_ind2)
      

    } else if (name=="cca_rg"){
          
        df_cca_rg2 = read.csv(file_name, sep=";")
        
        print(paste0("Baixando DF,", file_name))
        df_cca_rg2 = read.csv(file_name, sep=";", stringsAsFactors = FALSE)
        
        df_cca_rg2 = df_cca_rg2[,2:length(df_cca_rg2)-1]
        
        #limpando a base
        df_cca_rg2 = df_cca_rg2 %>% 
          rename("IF"="Instituição.financeira","COD"="Código", "CID"="Cidade") %>%
          mutate("Data" = as.Date(as.factor(paste0("01/", Data)), format="%d/%m/%Y")) %>%
          filter(!is.na(Data))
        #mutate_if(is.factor, as.character) %>%
        
        # df_cca_rg2 = data.frame(lapply(df_cca_rg2, function(x) {gsub(" - PRUDENCIAL", "", x)})) 
        df_cca_rg2 = data.frame(lapply(df_cca_rg2, function(x) {gsub("\\.", "", x)})) 
        #df_cca_rg2 = data.frame(lapply(df_cca_rg2, function(x) {gsub("\\%", "", x)})) 
        #df_cca_rg2 = data.frame(lapply(df_cca_rg2, function(x) {gsub(",", ".", x)})) 
        df_cca_rg2 = data.frame(lapply(df_cca_rg2, function(x) {gsub("NI", NA, x)})) %>% 
          mutate_if(is.factor, as.character) 
        
        #transformando as variaveis em numericas
        if ("Segmento" %in% names(df_cca_rg2)){
          df_cca_rg2 = df_cca_rg2 %>% mutate_at(names(df_cca_rg2[11:length(df_cca_rg2)]), as.numeric) %>%
            mutate(Data=as.Date(Data))   %>%
            rename("SEG"="Segmento")
        } else {
          df_cca_rg2 = df_cca_rg2 %>% mutate_at(names(df_cca_rg2[10:length(df_cca_rg2)]), as.numeric) %>%
            mutate(Data=as.Date(Data))
        }
        print(nrow(df_cca_rg2))
        print(paste0("Numero de colunas deste df é: ", length(df_cca_rg2)))
        print(names(df_cca_rg2)[names(df_cca_rg2) %nin% names(df_cca_rg2)])
        
        dim_df2 = data.frame("name"=name,"date"=paste0("01/",month,"/20", year), "nrow"=nrow(df_cca_rg2), "ncol"=ncol(df_cca_rg2))
        dim_df = bind_rows(dim_df, dim_df2)
        
        df_cca_rg = bind_rows(df_cca_rg,df_cca_rg2)
     }
    }
   }
  }
}
  

#change columns names

#Resumo
if ("SEG" %in% names(df_resumo)){
  len_col=length(df_resumo)-10
  if(len_col<10){
    names(df_resumo)[11:length(df_resumo)] = paste0("01_0", seq(1,len_col))
  } else {
    names(df_resumo)[11:length(df_resumo)] = append(paste0("01_0", 1:9),paste0("01_",10:len_col))
  }
}else{
  len_col=length(df_resumo)-9
  if(len_col<10){
    names(df_resumo)[10:length(df_resumo)] = paste0("01_0", seq(1,len_col))
  } else {
    names(df_resumo)[10:length(df_resumo)] = append(paste0("01_0", 1:9),paste0("01_",10:len_col))
  }
}


#Ativo
if ("SEG" %in% names(df_ativo)){
  len_col=length(df_ativo)-10
  if(len_col<10){
    names(df_ativo)[11:length(df_ativo)] = paste0("02_0", seq(1,len_col))
  } else {
    names(df_ativo)[11:length(df_ativo)] = append(paste0("02_0", 1:9),paste0("02_",10:len_col))
  }
}else{
  len_col=length(df_ativo)-9
  if(len_col<10){
    names(df_ativo)[10:length(df_ativo)] = paste0("02_0", seq(1,len_col))
  } else {
    names(df_ativo)[10:length(df_ativo)] = append(paste0("02_0", 1:9),paste0("02_",10:len_col))
  }
}


#Passivo
if ("SEG" %in% names(df_passivo)){
  len_col=length(df_passivo)-10
  if(len_col<10){
    names(df_passivo)[11:length(df_passivo)] = paste0("03_0", seq(1,len_col))
  } else {
    names(df_passivo)[11:length(df_passivo)] = append(paste0("03_0", 1:9),paste0("03_",10:len_col))
  }
}else{
  len_col=length(df_passivo)-9
  if(len_col<10){
    names(df_passivo)[10:length(df_passivo)] = paste0("03_0", seq(1,len_col))
  } else {
    names(df_passivo)[10:length(df_passivo)] = append(paste0("03_0", 1:9),paste0("03_",10:len_col))
  }
}


#Dre
if ("SEG" %in% names(df_dre)){
  len_col=length(df_dre)-10
  if(len_col<10){
    names(df_dre)[11:length(df_dre)] = paste0("04_0", seq(1,len_col))
  } else {
    names(df_dre)[11:length(df_dre)] = append(paste0("04_0", 1:9),paste0("04_",10:len_col))
  }
}else{
  len_col=length(df_dre)-9
  if(len_col<10){
    names(df_dre)[10:length(df_dre)] = paste0("04_0", seq(1,len_col))
  } else {
    names(df_dre)[10:length(df_dre)] = append(paste0("04_0", 1:9),paste0("04_",10:len_col))
  }
}

#ic
if ("SEG" %in% names(df_ic)){
  len_col=length(df_ic)-10
  if(len_col<10){
    names(df_ic)[11:length(df_ic)] = paste0("05_0", seq(1,len_col))
  } else {
    names(df_ic)[11:length(df_ic)] = append(paste0("05_0", 1:9),paste0("05_",10:len_col))
  }
}else{
  len_col=length(df_ic)-9
  if(len_col<10){
    names(df_ic)[10:length(df_ic)] = paste0("05_0", seq(1,len_col))
  } else {
    names(df_ic)[10:length(df_ic)] = append(paste0("05_0", 1:9),paste0("05_",10:len_col))
  }
}


#ccapf_mpv
if ("SEG" %in% names(df_ccapf_mpv)){
  len_col=length(df_ccapf_mpv)-10
  if(len_col<10){
    names(df_ccapf_mpv)[11:length(df_ccapf_mpv)] = paste0("06_0", seq(1,len_col))
  } else {
    names(df_ccapf_mpv)[11:length(df_ccapf_mpv)] = append(paste0("06_0", 1:9),paste0("06_",10:len_col))
  }
}else{
  len_col=length(df_ccapf_mpv)-9
  if(len_col<10){
    names(df_ccapf_mpv)[10:length(df_ccapf_mpv)] = paste0("06_0", seq(1,len_col))
  } else {
    names(df_ccapf_mpv)[10:length(df_ccapf_mpv)] = append(paste0("06_0", 1:9),paste0("06_",10:len_col))
  }
}


#ccapj_mpv
if ("SEG" %in% names(df_ccapj_mpv)){
  len_col=length(df_ccapj_mpv)-10
  if(len_col<10){
    names(df_ccapj_mpv)[11:length(df_ccapj_mpv)] = paste0("07_0", seq(1,len_col))
  } else {
    names(df_ccapj_mpv)[11:length(df_ccapj_mpv)] = append(paste0("07_0", 1:9),paste0("07_",10:len_col))
  }
}else{
  len_col=length(df_ccapj_mpv)-9
  if(len_col<10){
    names(df_ccapj_mpv)[10:length(df_ccapj_mpv)] = paste0("07_0", seq(1,len_col))
  } else {
    names(df_ccapj_mpv)[10:length(df_ccapj_mpv)] = append(paste0("07_0", 1:9),paste0("07_",10:len_col))
  }
}


#ccapj_cnae
if ("SEG" %in% names(df_ccapj_cnae)){
  len_col=length(df_ccapj_cnae)-10
  if(len_col<10){
    names(df_ccapj_cnae)[11:length(df_ccapj_cnae)] = paste0("08_0", seq(1,len_col))
  } else {
    names(df_ccapj_cnae)[11:length(df_ccapj_cnae)] = append(paste0("08_0", 1:9),paste0("08_",10:len_col))
  }
}else{
  len_col=length(df_ccapj_cnae)-9
  if(len_col<10){
    names(df_ccapj_cnae)[10:length(df_ccapj_cnae)] = paste0("08_0", seq(1,len_col))
  } else {
    names(df_ccapj_cnae)[10:length(df_ccapj_cnae)] = append(paste0("08_0", 1:9),paste0("08_",10:len_col))
  }
}


#ccapj_pt
df_ccapj_pt = df_ccapj_pt %>% select(names(df_ccapj_pt)[1:15],"Indisponível",everything())
if ("SEG" %in% names(df_ccapj_pt)){
  len_col=length(df_ccapj_pt)-10
  if(len_col<10){
    names(df_ccapj_pt)[11:length(df_ccapj_pt)] = paste0("09_0", seq(1,len_col))
  } else {
    names(df_ccapj_pt)[11:length(df_ccapj_pt)] = append(paste0("09_0", 1:9),paste0("09_",10:len_col))
  }
}else{
  len_col=length(df_ccapj_pt)-9
  if(len_col<10){
    names(df_ccapj_pt)[10:length(df_ccapj_pt)] = paste0("09_0", seq(1,len_col))
  } else {
    names(df_ccapj_pt)[10:length(df_ccapj_pt)] = append(paste0("09_0", 1:9),paste0("09_",10:len_col))
  }
}
  

#cca_qco
if ("SEG" %in% names(df_cca_qco)){
  len_col=length(df_cca_qco)-10
  if(len_col<10){
    names(df_cca_qco)[11:length(df_cca_qco)] = paste0("10_0", seq(1,len_col))
  } else {
    names(df_cca_qco)[11:length(df_cca_qco)] = append(paste0("10_0", 1:9),paste0("10_",10:len_col))
  }
}else{
  len_col=length(df_cca_qco)-9
  if(len_col<10){
    names(df_cca_qco)[10:length(df_cca_qco)] = paste0("10_0", seq(1,len_col))
  } else {
    names(df_cca_qco)[10:length(df_cca_qco)] = append(paste0("10_0", 1:9),paste0("10_",10:len_col))
  }
}


#cca_nro
if ("SEG" %in% names(df_cca_nro)){
  len_col=length(df_cca_nro)-10
  if(len_col<10){
    names(df_cca_nro)[11:length(df_cca_nro)] = paste0("11_0", seq(1,len_col))
  } else {
    names(df_cca_nro)[11:length(df_cca_nro)] = append(paste0("11_0", 1:9),paste0("11_",10:len_col))
  }
}else{
  len_col=length(df_cca_nro)-9
  if(len_col<10){
    names(df_cca_nro)[10:length(df_cca_nro)] = paste0("11_0", seq(1,len_col))
  } else {
    names(df_cca_nro)[10:length(df_cca_nro)] = append(paste0("11_0", 1:9),paste0("11_",10:len_col))
  }
}


#cca_ind
df_cca_ind = df_cca_ind %>% select(names(df_cca_ind)[1:14],"TLP",everything())
if ("SEG" %in% names(df_cca_ind)){
  len_col=length(df_cca_ind)-10
  if(len_col<10){
    names(df_cca_ind)[11:length(df_cca_ind)] = paste0("12_0", seq(1,len_col))
  } else {
    names(df_cca_ind)[11:length(df_cca_ind)] = append(paste0("12_0", 1:9),paste0("12_",10:len_col))
  }
}else{
  len_col=length(df_cca_ind)-9
  if(len_col<10){
    names(df_cca_ind)[10:length(df_cca_ind)] = paste0("12_0", seq(1,len_col))
  } else {
    names(df_cca_ind)[10:length(df_cca_ind)] = append(paste0("12_0", 1:9),paste0("12_",10:len_col))
  }
}


#cca_rg
if ("SEG" %in% names(df_cca_rg)){
  len_col=length(df_cca_rg)-10
  if(len_col<10){
    names(df_cca_rg)[11:length(df_cca_rg)] = paste0("13_0", seq(1,len_col))
  } else {
    names(df_cca_rg)[11:length(df_cca_rg)] = append(paste0("13_0", 1:9),paste0("13_",10:len_col))
  }
}else{
  len_col=length(df_cca_rg)-9
  if(len_col<10){
    names(df_cca_rg)[10:length(df_cca_rg)] = paste0("13_0", seq(1,len_col))
  } else {
    names(df_cca_rg)[10:length(df_cca_rg)] = append(paste0("13_0", 1:9),paste0("13_",10:len_col))
  }
}
      


df1_aggregate = df_resumo %>%
  left_join(df_ativo, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_passivo, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_dre, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_ic %>% select(-c("COD")), by=c("IF"="IF","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","CID"="CID","UF"="UF","Data"="Data")) %>%
  distinct(IF, TCB, TD,TC,SR,CID, UF, Data, COD, .keep_all = T)
  

df_agg_aux =  df1_aggregate %>% filter(!is.na(SR)) %>% distinct(IF, .keep_all = T) %>% select(IF,SR)
df1_aggregate = df1_aggregate  %>%
  #select(names(df1_aggregate)[1:10]) %>%
  left_join(df_agg_aux %>% rename("SR2"="SR"), by=c("IF"="IF"))%>% 
  select(names(df1_aggregate)[1:3],"SR","SR2", everything())


df2_aggregate = df_ccapf_mpv %>% 
  left_join(df_ccapj_mpv, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_ccapj_cnae, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_ccapj_pt, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_cca_qco, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_cca_nro, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_cca_ind, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) %>%
  left_join(df_cca_rg, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","SEG"="SEG","CID"="CID","UF"="UF","Data"="Data")) 
  

df_aggregate = df1_aggregate %>% left_join(df2_aggregate, by=c("IF"="IF","COD"="COD","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","CID"="CID","UF"="UF","Data"="Data"))
df_aggregate = df_aggregate %>% select(names(df_aggregate)[1:9],"SEG",everything())

##salvar em excerl ( 1) arquivao e 2) separaados por abas)
# list_of_datasets <- list("Agregado Geral"=df_aggregate,"Agregado 1"=df1_aggregate,"Agregado2"=df2_aggregate,
#                          'resumo'=df_resumo,'ativo'=df_ativo, 'passivo'=df_passivo,'dre'=df_dre,'ic'=df_ic,
#                          'ccapf_mpv'=df_ccapf_mpv,'ccapj_mpv'=df_ccapj_mpv,'ccapj_cnae'=df_ccapj_cnae,'ccapj_pt'=df_ccapj_pt,
#                          'cca_qco'=df_cca_qco,'cca_nro'=df_cca_nro,'cca_ind'=df_cca_ind,'cca_rg'=df_cca_rg)
# write.xlsx(list_of_datasets, file = "BACEN IF Data Agregado.xlsx")

setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/")
write.xlsx(list("Agregado" = df_aggregate), file = "BACEN IF Data.xlsx")





# #debug1
# a = dim_df %>% filter(name=="resumo") %>% left_join(dim_df %>% filter(name=="ativo"), by=c("date"="date")) %>%
#   left_join(dim_df %>% filter(name=="passivo"), by=c("date"="date")) %>%
#   left_join(dim_df %>% filter(name=="dre"), by=c("date"="date")) %>%
#   left_join(dim_df %>% filter(name=="ic"), by=c("date"="date"))


#debug2
# a = dim_df %>% filter(name=="ic") %>% slice(1:20)
# 
# for (i in a$names){
#   print(strsplit(i,split='/////', fixed=TRUE))
#   print("#############")
#   #print(a$date)
# }


#debug3
# a = df_ativo %>% filter(IF=="BB") %>% select(names(df_ativo)[1:13])
# b= df_ic %>% filter(IF%in%c("BB","ITAU")) %>% select(names(df_ic)[1:13]) %>% arrange(IF,Data)
# c  =a %>%  left_join(df_ic %>% select(-c("COD")), by=c("IF"="IF","TCB"="TCB","TD"="TD","TC"="TC","SR"="SR","CID"="CID","UF"="UF","Data"="Data")) 
#d=df_aggregate %>% filter(IF=="BB") %>% select(names(df_aggregate)[1:13], "05_01", "05_02",  "05_07", "05_05")



