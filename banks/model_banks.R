library(readxl)
library(openxlsx)
library(dplyr)
library(rfUtilities)	
library(MASS)
library(sda)
library(class)
library(boot)
library(randomForest)
library(gbm)
library(caret)
library(e1071)
library(stringr)

library(ggplot2)
library(ggraph)
library(igraph)

library(wordcloud)
library(RColorBrewer)
library(wordcloud2)


open_df = function() {

  setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/")
  
  df_var   = read_excel("DF Final.xlsx", sheet = "Dicionario")
  
  df_banks   = read_excel("DF Final.xlsx", sheet = "DF normalized")
  df_banks = df_banks %>% mutate(`Data_X`=as.Date(`Data_X`),`Data_Y`=as.Date(`Data_Y`))
  
  df_original = read_excel("DF Final.xlsx", sheet = "DF Final")
  df_original = df_original %>% mutate(`Data_X`=as.Date(`Data_X`),`Data_Y`=as.Date(`Data_Y`))
  
  #default_df   = read_excel("default banks.xlsx", sheet = "Check names")
  
  return (list("DF"=df_banks,"VAR"=df_var))
}

set_dataset = function(df_banks,seed) {
  
  #df_model = df_banks %>% dplyr::select(-c(names(df_banks)[1:12],names(df_banks)[14:17],`2019`)) 
  
  df_model = df_original %>% dplyr::select(-c(names(df_banks)[1:12],names(df_banks)[14:17],`2019`)) 
  
  df_model1 = df_model %>% filter(y==1)
  df_model2 = df_model %>% filter(y!=1)
  
  set.seed(seed)
  
  train_row1 = sample(nrow(df_model1),0.7*nrow(df_model1))
  train_row2 = sample(nrow(df_model2),0.7*nrow(df_model2))
  
  train1 = df_model1[train_row1,]
  test1 = df_model1[-train_row1,]
  train2 = df_model2[train_row2,]
  test2 = df_model2[-train_row2,]
  
  train = bind_rows(train1,train2)
  test = bind_rows(test1,test2)
  
  Y_train = train%>%dplyr::select('y') %>% as.matrix()
  X_train = train%>%dplyr::select(-'y') %>% as.matrix()
  
  Y_test = test%>%dplyr::select('y') %>% as.matrix() 
  X_test = test%>%dplyr::select(-'y') %>% as.matrix() 
  
  train_factor = train
  train_factor = train_factor %>% dplyr::mutate(y = as.factor(y))
  levels(train_factor$y) <- c("Ndefault", "default")
  
  Y_train_factor = train_factor$y
  
  return(df_model, train, test)
  
}
  

model_banks = function() {
  
  seed=30
  # set.seed(30)
  
  df_info = data.frame(matrix(ncol=0, nrow=0))
  list_info = list()
  for (model in c("logit", "lda", "knn", "rf", "boosting", "svmL", "svmNL", "bayes")){
    
    if (model=="logit") {
      
      #LOGIT MODEL
      
      print(model)
      set.seed(seed)
      
      glm.fits=glm(y ~ ., data = train, family=binomial)
      
      summary(glm.fits)
      coef(glm.fits)
      summary(glm.fits)$coef
      
      # define training control
      logit_control = trainControl(method = "repeatedcv", number = 10, repeats = 5)

      
      # train the model on training set
      logit_model = train(y ~ .,
                          data = train,
                          trControl = logit_control,
                          method = "glm",
                          family=binomial())
      
      
      # print cv scores
      summary(logit_model)
      logit_model$finalModel$coefficients
      logit_parameters = logit_model$bestTune
      
      train_pred_logit = data.frame(y=train$y, y_pred=predict(logit_model,train)) %>% mutate(y_pred2 = case_when(y_pred>0.4~1,T~0))
      test_pred_logit = data.frame(y=test$y, y_pred=predict(logit_model,test))  %>% mutate(y_pred2 = case_when(y_pred>0.4~1,T~0))
      
      #models_info_train = accuracy(train_pred$y,train_pred$y_pred)
      #models_info_test = accuracy(test_pred_logit$y,test_pred_logit$y_pred)
      models_info_test = accuracy(as.factor(test_pred_logit$y),as.factor(test_pred_logit$y_pred2))
      
      confusionMatrix(reference = as.factor(train_pred_logit$y),data = as.factor(train_pred_logit$y_pred2))
      confusionMatrix(reference = as.factor(test_pred_logit$y),data = as.factor(test_pred_logit$y_pred2))
      
      models_info_df_logit = data.frame(model = 'logit', 
                                        sqr_train = mean(glm.fits$residuals^2),
                                        sqr_test = mean((test_pred_logit$y - test_pred_logit$y_pred) ^ 2),
                                        accuracy = models_info_test$PCC,
                                        AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                        errotipoI  = models_info_test$typeI.error,
                                        errotipoII  = models_info_test$typeII.error,
                                        PLR  = models_info_test$plr,
                                        NLR  = models_info_test$nlr,
                                        Fscore =models_info_test$f.score,
                                        Info_gain= models_info_test$gain)
      
      df_info = bind_rows(df_info,models_info_df_logit)
      list_info[[model]]=list('train predictions'=train_pred_logit,
                              'train predictions'=test_pred_logit,
                              'model parameteres'=logit_parameters
      )
      
    } else if (model=="lda") {
      
      print(model)
      set.seed(seed)

      lda_ctrl <- trainControl(method = "repeatedcv",
                               repeats = 5, number = 10,
                               classProbs = TRUE
      )
      sparseLDAGridx  <-  expand.grid(diagonal=FALSE, lambda = c(0, 0.01, .1, 1, 10, 100))
      #set.seed(1) # to have reproducible results
      lda_model_val <- train(y ~ .,
                             data = train_factor,
                             method = "sda",
                             tuneGrid = sparseLDAGridx,
                             trControl = lda_ctrl,
                             metric = "Accuracy", # not needed it is so by default
                             #importance=TRUE,
                             preProc = c("center", "scale"))
      
      LDA_Parameters = lda_model_val$bestTune
      
      lda_model <- sda::sda(X_train,Y_train, diagonal = LDA_Parameters[1,1],  lambda = LDA_Parameters[1,2])
      
      lda_pred_train <- predict(lda_model, X_train)$class
      lda_pred_test <- predict(lda_model, X_test)$class
      
      train_pred_lda = data.frame(y=train$y, y_pred=lda_pred_train) %>% mutate(y_pred=case_when(y_pred=="1"~1,T~0))
      test_pred_lda = data.frame(y=test$y, y_pred=lda_pred_test) %>% mutate(y_pred=case_when(y_pred=="1"~1,T~0))
      
      models_info_test = accuracy(test_pred_lda$y,test_pred_lda$y_pred)
      models_info_test = accuracy(as.factor(test_pred_lda$y),as.factor(test_pred_lda$y_pred))
      
      confusionMatrix(reference = as.factor(train_pred_lda$y),data = as.factor(train_pred_lda$y_pred))
      confusionMatrix(reference = as.factor(test_pred_lda$y),data = as.factor(test_pred_lda$y_pred))
      
      models_info_df_lda = data.frame(model = 'LDA', 
                                      sqr_train = mean((train_pred_lda$y - train_pred_lda$y_pred) ^ 2),
                                      sqr_test = mean((test_pred_lda$y - test_pred_lda$y_pred) ^ 2),
                                      accuracy = models_info_test$PCC,
                                      AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                      errotipoI  = models_info_test$typeI.error,
                                      errotipoII  = models_info_test$typeII.error,
                                      PLR  = models_info_test$plr,
                                      NLR  = models_info_test$nlr,
                                      Fscore =models_info_test$f.score,
                                      Info_gain= models_info_test$gain)
      
      
      df_info = bind_rows(df_info,models_info_df_lda)
      list_info[[model]]=list('train predictions'=train_pred_lda,
                              'train predictions'=test_pred_lda,
                              'model parameters'=LDA_Parameters
      )
      
    } else  if (model=="knn") {
      
      print(model)
      set.seed(seed)
      
      
      knn_ctrl <- trainControl(method = "repeatedcv", repeats = 3, number = 10, classProbs = T) 
      knn_model <- train(y ~ .,
                         method     = "knn",
                         tuneGrid   = expand.grid(k = 1:10),
                         trControl  = knn_ctrl,
                         #metric     = "Accuracy",
                         data       = train)
      
      KNN_Parameters = knn_model$bestTune
      
      #knn_pred=knn(X_train,X_test,Y_train ,k=k, prob=T)      
      
      knn_pred_train <- predict(knn_model, X_train)
      knn_pred_test <- predict(knn_model, X_test)
      
      train_pred_knn = data.frame(y=train$y, y_pred=knn_pred_train) %>% mutate(y_pred2=case_when(y_pred>0.4~1,T~0))
      test_pred_knn = data.frame(y=test$y, y_pred=knn_pred_test) %>% mutate(y_pred2=case_when(y_pred>0.4~1,T~0))
      levels(test_pred_knn$y_pred2) <- c("0", "1")
      levels(train_pred_knn$y_pred2) <- c("0", "1")
      
      
      #models_info_test = accuracy(as.factor(test_pred_knn$y),as.factor(test_pred_knn$y_pred2))
      
      confusionMatrix(reference = as.factor(train_pred_knn$y),data = as.factor(train_pred_knn$y_pred2))
      confusionMatrix(reference = as.factor(test_pred_knn$y),data = as.factor(test_pred_knn$y_pred2))
      
      
      models_info_df_knn = data.frame(model = 'KNN', 
                                      sqr_train = mean((train_pred_knn$y - train_pred_knn$y_pred2)^2),
                                      sqr_test = mean((test_pred_knn$y - test_pred_knn$y_pred2)^2),
                                      accuracy = models_info_test$PCC,
                                      AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                      errotipoI  = models_info_test$typeI.error,
                                      errotipoII  = models_info_test$typeII.error,
                                      PLR  = models_info_test$plr,
                                      NLR  = models_info_test$nlr,
                                      Fscore =models_info_test$f.score,
                                      Info_gain= models_info_test$gain)
      
      
      df_info = bind_rows(df_info,models_info_df_knn)
      list_info[[model]]=list('train predictions'=train_pred_knn,
                              'train predictions'=test_pred_knn,
                              'model parameters'=KNN_Parameters
      )
      
    } else if (model=="rf") {
      #RANDOM FOREST
      print(model)
      set.seed(seed)
      
      # Create model with default paramters
      train_rf = train
      X_train_rf = train
      X_teste_rf = test
      
      names(train_rf) <- make.names(names(train_rf))
      names(X_teste_rf) <- make.names(names(X_teste_rf))
      names(X_train_rf) <- make.names(names(X_train_rf))
    
      rf_ctrl <- trainControl(method="repeatedcv", number=10, repeats = 3, search="grid")
      RFtunegrid <- expand.grid(.mtry=c(1,5,10,15,20))   #c(round(sqrt(ncol(train_rf))))
      modellist <- list()
      for (ntree in c(3,5,10,100,200)) {
        print(ntree)
        rf_model_tune <- train(as.factor(y)~., 
                          data=train_rf, 
                          method="rf", 
                          metric="Accuracy", 
                          tuneGrid=RFtunegrid, 
                          trControl=rf_ctrl, 
                          ntree=ntree)
        key <- toString(ntree)
        modellist[[key]] <- rf_model_tune
      }
      # compare results
      results <- resamples(modellist)
      summary(results)
      dotplot(results)
      
      
      summary_results = as.data.frame(summary(results)$statistics$Accuracy)[4] #%>% select('Mean')
      ntree_select = as.numeric(rownames(summary_results)[which(summary_results$Mean == max(summary_results))])
      mtry = rf_model_tune$bestTune[1,1]
      
      RF_Parameters = c(ntree_select, mtry)
      rf_model = randomForest(as.factor(y) ~.,data=train_rf, mtry=mtry,ntree=ntree_select, keep.forest=TRUE)
      


      #rf_pred_train <- predict(rf_model, X_train_rf)
      #rf_pred_test <- predict(rf_model, X_teste_rf)

      #prob
      rf_pred_test <- as.data.frame(predict(rf_model, X_teste_rf,type = "prob"))[,2]
      rf_pred_train <- as.data.frame(predict(rf_model, X_train_rf,type = "prob"))[,2]
      
      train_pred_rf = data.frame(y=train$y, y_pred=rf_pred_train) %>% mutate(y_pred2=case_when(y_pred>=0.4~1,T~0))
      test_pred_rf = data.frame(y=test$y, y_pred=rf_pred_test) %>% mutate(y_pred2=case_when(y_pred>=0.4~1,T~0))
      
      models_info_test = accuracy(as.factor(test_pred_rf$y),as.factor(test_pred_rf$y_pred2))
      
      confusionMatrix(reference = as.factor(train_pred_rf$y),data = as.factor(train_pred_rf$y_pred2))
      confusionMatrix(reference = as.factor(test_pred_rf$y),data = as.factor(test_pred_rf$y_pred2))
      
      models_info_df_rf = data.frame(model = 'RF', 
                                     sqr_train = mean((train_pred_rf$y - train_pred_rf$y_pred2) ^ 2),
                                     sqr_test = mean((test_pred_rf$y - test_pred_rf$y_pred2) ^ 2),
                                     accuracy = models_info_test$PCC,
                                     AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                     errotipoI  = models_info_test$typeI.error,
                                     errotipoII  = models_info_test$typeII.error,
                                     PLR  = models_info_test$plr,
                                     NLR  = models_info_test$nlr,
                                     Fscore =models_info_test$f.score,
                                     Info_gain= models_info_test$gain)
      
      
      df_info = bind_rows(df_info,models_info_df_rf)
      list_info[[model]]=list('train predictions'=train_pred_rf,
                            'train predictions'=test_pred_rf,
                            'model parameters'=RF_Parameters
      )
      
    } else if (model=="boosting") {
      
      
      #BOOSTING
      X_train_gbm = train %>% select(-'y')
      X_test_gbm = test %>% select(-'y')
      
      #gbm_model = gbm(y ~.,data=train, distribution="gaussian",n.trees=50, interaction.depth=4)
      
      # gbm_ctrl <- trainControl(method = "repeatedcv",number = 10,repeats = 3)
      
      gbm_ctrl <- trainControl(method = "cv", number = 10,)
      
      gbmGrid2 = expand.grid(interaction.depth = c(1, 3, 5, 7), 
                            n.trees = c(10,100), 
                            shrinkage = c(0.01, 0.1, 1),     #0, 0.01, .1, 1, 10    
                            n.minobsinnode = c(10, 20)      #5, 10, 20, 30
       )
      
      gbm_model <- train(y ~ ., 
                         data = train, 
                         method = "gbm",
                         distribution= "gaussian",
                         trControl = gbm_ctrl, 
                         verbose = FALSE, 
                         ## Now specify the exact models 
                         ## to evaluate:
                         tuneGrid = gbmGrid2)
      
      GBM_Parameters = gbm_model$bestTune
      ntree = GBM_Parameters[1,1]
      interdepth = GBM_Parameters[1,2]
      shrinkage = GBM_Parameters[1,3]
      nminobsin = GBM_Parameters[1,4]
      
      gbm_pred_train <- predict(gbm_model, X_train_gbm,n.trees=ntree, interaction.depth=interdepth, shrinkage=shrinkage, n.minobsinnode=nminobsin)
      gbm_pred_test <- predict(gbm_model, X_test_gbm,n.trees=ntree, interaction.depth=interdepth, shrinkage=shrinkage, n.minobsinnode=nminobsin)
      
      train_pred_gbm = data.frame(y=train$y, y_pred=gbm_pred_train) %>% mutate(y_pred2=case_when(y_pred>0.5~1,T~0))
      test_pred_gbm = data.frame(y=test$y, y_pred=gbm_pred_test) %>% mutate(y_pred2=case_when(y_pred>0.5~1,T~0))
      
      #models_info_test = accuracy(test_pred_gbm$y,test_pred_gbm$y_pred)
      models_info_test = accuracy(as.factor(test_pred_gbm$y),as.factor(test_pred_gbm$y_pred2))
      
      confusionMatrix(reference = as.factor(train_pred_gbm$y),data = as.factor(train_pred_gbm$y_pred2))
      confusionMatrix(reference = as.factor(test_pred_gbm$y),data = as.factor(test_pred_gbm$y_pred2))
      
      
      dim(test_pred_gbm)
      #dim(test_pred_gbm$y)
      
      models_info_df_gbm = data.frame(model = 'GBM', 
                                     sqr_train = mean((train_pred_gbm$y - train_pred_gbm$y_pred)^2),
                                     sqr_test = mean((test_pred_gbm$y - test_pred_gbm$y_pred)^2),
                                     accuracy = models_info_test$PCC,
                                     AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                     errotipoI  = models_info_test$typeI.error,
                                     errotipoII  = models_info_test$typeII.error,
                                     PLR  = models_info_test$plr,
                                     NLR  = models_info_test$nlr,
                                     Fscore =models_info_test$f.score,
                                     Info_gain= models_info_test$gain)
      
      df_info = bind_rows(df_info,models_info_df_gbm)
      list_info[[model]]=list('train predictions'=train_pred_gbm,
                            'train predictions'=test_pred_gbm,
                            'model parameters'=GBM_Parameters
      )
      
    } else if (model=="svmL") {
      
      #SVM
      #LINEAR
      
      svmL_tune=tune(svm , as.factor(y)~.,
                     data=train ,
                     kernel ="linear",
                     ranges=list(cost=c(0.1,1,10,100),
                                 gamma=c(0.5,1,2),
                                 epsilon=c(0.01,0.1,1)))
      
      
      # svmL_tune=tune(svm ,as.factor(y)~.,
      #                data=train ,
      #                kernel ="linear",
      #                ranges=list(cost=c(10),
      #                            gamma=c(0.5),
      #                            epilson=c(0.01)))
      
      
      svmL_bestmodel = svmL_tune$best.model
      
      svm_model=svm(as.factor(y)~., data=train ,
                    kernel ="linear", 
                    cost =svmL_tune$best.model$cost, 
                    gamma=svmL_tune$best.model$gamma,
                    epsilon=svmL_tune$best.model$epsilon,
                    scale=FALSE, probability=TRUE)
      
      # plot(svm_model , train)
      
      svmL_pred_train <- predict(svm_model, X_train, probability=TRUE, type='prob')
      svmL_pred_test <- predict(svm_model,  X_test, probability=TRUE)
      
      
      train_pred_svmL = data.frame(y=train$y, y_pred=svmL_pred_train) %>% mutate(y_pred2=case_when(y_pred=="1"~1,T~0))
      test_pred_svmL = data.frame(y=test$y, y_pred=svmL_pred_test) %>% mutate(y_pred2=case_when(y_pred=="1"~1,T~0))
      
      #models_info_test = accuracy(test_pred_svmL$y,test_pred_svmL$y_pred)   
      models_info_test = accuracy(as.factor(test_pred_svmL$y),as.factor(test_pred_svmL$y_pred2))
      
      confusionMatrix(reference = as.factor(train_pred_svmL$y),data = as.factor(train_pred_svmL$y_pred2))
      confusionMatrix(reference = as.factor(test_pred_svmL$y),data = as.factor(test_pred_svmL$y_pred2))
      
      
      models_info_df_svmL = data.frame(model = 'SVM Linear', 
                                       sqr_train = mean((train_pred_svmL$y - train_pred_svmL$y_pred2) ^ 2),
                                       sqr_test = mean((test_pred_svmL$y - test_pred_svmL$y_pred2) ^ 2),
                                       accuracy = models_info_test$PCC,
                                       AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                       errotipoI  = models_info_test$typeI.error,
                                       errotipoII  = models_info_test$typeII.error,
                                       PLR  = models_info_test$plr,
                                       NLR  = models_info_test$nlr,
                                       Fscore =models_info_test$f.score,
                                       Info_gain= models_info_test$gain)
      
      df_info = bind_rows(df_info,models_info_df_svmL)
      list_info[[model]]=list('train predictions'=test_pred_svmL,
                              'train predictions'=test_pred_svmL,
                              'model parameters'=svmL_bestmodel
      )
      
      } else if (model=="svmNL") {
        
        
        #NON LINEAR
        svmNL_tune=tune(svm , as.factor(y)~., 
                        data=train, kernel ="radial",
                        ranges=list(cost=c(0.1,1,10,100),
                                    gamma=c(0.5,1,2),
                                    epsilon=c(0.01,0.1,1)))
        
        svmNL_bestmodel = svmL_tune$best.model
        
        svmL_bestmodel = svmL_tune$best.model
        
        svm_model=svm(as.factor(y)~., data=train ,
                      kernel ="radial", 
                      cost =svmL_tune$best.model$cost, 
                      gamma=svmL_tune$best.model$gamma,
                      epsilon=svmL_tune$best.model$epsilon,
                      scale=FALSE, probability=TRUE)
        
        svmNL_pred_train <- predict(svmNL_bestmodel, X_train)
        svmNL_pred_test <- predict(svmNL_bestmodel, X_test)
        
        train_pred_svmNL = data.frame(y=train$y, y_pred=svmNL_pred_train) %>% mutate(y_pred2 = case_when(y_pred=="1"~1,T~0))
        test_pred_svmNL = data.frame(y=test$y, y_pred=svmNL_pred_test) %>% mutate(y_pred2 = case_when(y_pred=="1"~1,T~0))
        
        #models_info_test = accuracy(test_pred_svmNL$y,test_pred_svmNL$y_pred)
        models_info_test = accuracy(as.factor(test_pred_svmNL$y),as.factor(test_pred_svmNL$y_pred2))
        
        confusionMatrix(reference = as.factor(train_pred_svmNL$y),data = as.factor(train_pred_svmNL$y_pred2))
        confusionMatrix(reference = as.factor(test_pred_svmNL$y),data = as.factor(test_pred_svmNL$y_pred2))
        
        
        models_info_df_svmNL = data.frame(model = 'SVM Non-Linear', 
                                          sqr_train = mean((train_pred_svmNL$y - train_pred_svmNL$y_pred2) ^ 2),
                                          sqr_test = mean((test_pred_svmNL$y - test_pred_svmNL$y_pred2) ^ 2),
                                          accuracy = models_info_test$PCC,
                                          AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                          errotipoI  = models_info_test$typeI.error,
                                          errotipoII  = models_info_test$typeII.error,
                                          PLR  = models_info_test$plr,
                                          NLR  = models_info_test$nlr,
                                          Fscore =models_info_test$f.score,
                                          Info_gain= models_info_test$gain)
        
        df_info = bind_rows(df_info,models_info_df_svmNL)
        list_info[[model]]=list('train predictions'=test_pred_svmNL,
                                'train predictions'=test_pred_svmNL,
                                'model parameters'=svmNL_bestmodel
        )
        

      
     } else if(model=='bayes') {
      #a <- bayesreg(as.factor(y) ~ ., train, model = "logistic", prior = "horseshoe", n.samples = 10)
      
       # Create model with default paramters
       train_bay = train
       X_train_bay = train
       X_test_bay = test
       
       names(train_bay) <- make.names(names(train_bay))
       names(X_train_bay) <- make.names(names(X_train_bay))
       names(X_test_bay) <- make.names(names(X_test_bay))
      
      
      # bayes_ctrl <- trainControl(method = "cv", number = 10)
      bayes_ctrl <- trainControl(method="repeatedcv", number=10, repeats = 3, search="grid")
      bayes_model_train <- train(as.factor(y)~.,data=train_bay, method = "naive_bayes",trControl = bayes_ctrl)
      #bayes_model_train <- train(as.factor(y)~.,data=train_bay, method = "nb",trControl = bayes_ctrl)
      
      
      bayes_parameters = bayes_model_train$bestTune
    
      
      # model_bayes = naive_bayes(as.factor(y) ~.,data=train_rf, 
      #             fl=as.numeric(bayes_parameters[1]),
      #             usekernel=as.logical(bayes_parameters[2]), 
      #             adjust=as.numeric(bayes_parameters[3]))
      model_bayes = naive_bayes(as.factor(y) ~.,data=train_rf,
                                laplace=as.numeric(bayes_parameters[1]),
                                usekernel=as.logical(bayes_parameters[2]),
                                adjust=as.numeric(bayes_parameters[3]))
      
      bayes_train = predict(model_bayes, X_train, type='prob')[,2]
      bayes_test = predict(model_bayes, X_test, type='prob')[,2]
       
      train_bayes = data.frame(y=train$y, y_pred=bayes_train) %>% mutate(y_pred2=case_when(y_pred>=0.4~1,T~0))
      test_bayes = data.frame(y=test$y, y_pred=bayes_test) %>% mutate(y_pred2=case_when(y_pred>=0.4~1,T~0))
       
      #models_info_test = accuracy(test_pred_svmL$y,test_pred_svmL$y_pred)   
      models_info_test = accuracy(as.factor(test_bayes$y),as.factor(test_bayes$y_pred2))
       
      confusionMatrix(reference = as.factor(train_bayes$y),data = as.factor(train_bayes$y_pred2))
      confusionMatrix(reference = as.factor(test_bayes$y),data = as.factor(test_bayes$y_pred2))
       
       
      models_info_df_bayes = data.frame(model = 'Bayes Model', 
                                        sqr_train = mean((train_pred_svmL$y - train_pred_svmL$y_pred2) ^ 2),
                                        sqr_test = mean((test_bayes$y - test_bayes$y_pred2) ^ 2),
                                        accuracy = models_info_test$PCC,
                                        AUC = ifelse(length(models_info_test$AUC)!=0,models_info_test$AUC,0),
                                        errotipoI  = models_info_test$typeI.error,
                                        errotipoII  = models_info_test$typeII.error,
                                        PLR  = models_info_test$plr,
                                        NLR  = models_info_test$nlr,
                                        Fscore =models_info_test$f.score,
                                        Info_gain= models_info_test$gain)
       
      df_info = bind_rows(df_info,models_info_df_bayes)
      list_info[[model]]=list('train predictions'=train_pred_svmL,
                               'train predictions'=test_pred_svmL,
                               'model parameters'=bayes_parameters)
      
     } 
 
  }  
  
  return(list(df_info, list_info))
}





set_model_general = function(df_info, list_info, df_model, df_original) {
  
  
  df_model = df_banks %>% dplyr::select(-c(names(df_banks)[1:12],names(df_banks)[14:17],`2019`, `dummy_IB`, `dummy_II`)) 
  df_names = df_banks %>% dplyr::select(c(names(df_banks)[1:12],names(df_banks)[14:17],`2019`, `dummy_IB`, `dummy_II`)) 
  
  df_info_filter = df_info %>% select(model, sqr_train, sqr_test)
  model_picked = df_info_filter %>% filter(sqr_train==min(sqr_train)) %>% select(model) %>% .[[1]]
  

  
  if (model_picked=="RF") {
    
    
    df_rf = df_model
    X_rf = df_model %>% select(-y)

    names(df_rf) <- make.names(names(df_rf))
    names(X_rf) <- make.names(names(X_rf))

    ntree = list_info[["rf"]]$`model parameters`[1]
    # mtry = list_info[["rf"]]$`model parameters`[2]
    mtry=10
    
    rf_model = randomForest(as.factor(y) ~.,data=df_rf, mtry=mtry,ntree=ntree_select)
    
    #prob
    pred_rf_aux <- as.data.frame(predict(rf_model, X_rf,type = "prob"))[,2]

    pred_rf_df = data.frame(y=df_rf$y, y_pred=pred_rf_aux) %>% mutate(y_pred2=case_when(y_pred>=0.4~1,T~0))
    accur = accuracy(pred_rf_df$y,pred_rf_df$y_pred2)
    
    df_agg = cbind(df_names,pred_rf_df, X_rf)
    
    b=df_agg %>% filter(y_pred==0)
    
    hist(df_agg$y_pred)
  
  } else if(model_picked=='LDA'){
    
    
    print(model)
    set.seed(seed)
    
    Y_lda = df_model%>%dplyr::select('y') %>% as.matrix()
    X_lda = df_model%>%dplyr::select(-'y') %>% as.matrix()
    

    diagonal = list_info[["lda"]]$`model parameters`[1]
    lamba = list_info[["lda"]]$`model parameters`[2]
  
    lda_model <- sda(X_lda,Y_lda, diagonal = LDA_Parameters[1,1],  lambda = LDA_Parameters[1,2])
    
    lda_pred <- predict(lda_model, X_lda)$posterior[,2]
    
    pred_lda = data.frame(y=Y_lda, y_pred=lda_pred) %>% mutate(y_pred2=case_when(y_pred>=0.4~1,T~0))
    
    #models_info_train = accuracy(train_pred$y,train_pred$y_pred)
    models_info_test = accuracy(pred_lda$y,pred_lda$y_pred2)
    mean((Y_lda - pred_lda$y_pred2) ^ 2)
    df_agg2 = cbind(df_names,pred_lda, X_rf)

  }

  df_predict1 =  df_agg %>% 
    #select(IF, Data_X,y,y_pred,y_pred2, X05_17) %>% 
    mutate(percentile = percent_rank(y_pred)) %>%
    mutate(nota = 10 - 10*percentile)
  
  df_predict2 = df_predict1 %>% 
    select("IF","COD","TCB","SR","SR2","TD","TC","CID","UF","SEG","Data_Y","Data_X","y","y_pred","y_pred2", "percentile", "nota") %>%
    left_join(df_original %>% select(-'y'), by=c("IF"="IF","COD"="COD","TCB"="TCB","SR"="SR","SR2"="SR2","TD"="TD",
                                                 "TC"="TC","CID"="CID","UF"="UF","SEG"="SEG","Data_Y"="Data_Y","Data_X"="Data_X")) %>%
    mutate(nota=case_when(percentile==max(percentile)~0,T~nota))
  
  setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/")
  write.xlsx(list("DF predicted" = df_predict2, "DF predicted normalized" = df_predict1, "info"=df_info), file = "Models Predictions.xlsx")
  write.xlsx(list("DF predicted" = df_predict2, "DF predicted normalized" = df_predict1), file = "Models Predictions.xlsx")
  
  return (list("DF predicted" = df_predict2, "DF predicted normalized" = df_predict1))
}


# df_rating = data.frame(value = quantile(df_agg2$y_pred, probs = seq(0,10,.1)/10)) %>% 
#   rownames_to_column("percentil") %>% 
#   mutate(nota = sort(seq(0,10,.1),decreasing=T))


plot_rftree = function () {
  
  #**************************
  #return the rules of a tree
  #**************************
  getConds<-function(tree){
    #store all conditions into a list
    conds<-list()
    #start by the terminal nodes and find previous conditions
    id.leafs<-which(tree$status==-1)
    j<-0
    for(i in id.leafs){
      j<-j+1
      prevConds<-prevCond(tree,i)
      conds[[j]]<-prevConds$cond
      while(prevConds$id>1){
        prevConds<-prevCond(tree,prevConds$id)
        conds[[j]]<-paste(conds[[j]]," & ",prevConds$cond)
      }
      if(prevConds$id==1){
        conds[[j]]<-paste(conds[[j]]," => ",tree$prediction[i])
      }
    }
    return(conds)
  }
  
  #**************************
  #find the previous conditions in the tree
  #**************************
  prevCond<-function(tree,i){
    if(i %in% tree$right_daughter){
      id<-which(tree$right_daughter==i)
      cond<-paste(tree$split_var[id],">",tree$split_point[id])
    }
    if(i %in% tree$left_daughter){
      id<-which(tree$left_daughter==i)
      cond<-paste(tree$split_var[id],"<",tree$split_point[id])
    }
    
    return(list(cond=cond,id=id))
  }
  
  tree2 = data.frame(matrix(ncol=0,nrow=0))
  tree_list=list()
  for (ntree_plot in 1:10) {
    
    tree <- randomForest::getTree(rf_model, k = ntree_plot,labelVar = TRUE) %>%
      tibble::rownames_to_column() %>%
      # make leaf split points to NA, so the 0s won't get plotted
      mutate(`split point` = ifelse(is.na(prediction), `split point`, NA)) %>%
      mutate(`split point` = round(`split point`,2), tree_n = ntree_plot)
    
    tree2 = bind_rows(tree, tree2)
    
    colnames(tree)<- gsub(" ","_",colnames(tree))
    
    # prepare data frame for graph
    graph_frame <- data.frame(from = rep(tree$rowname, 2), to = c(tree$`left_daughter`, tree$`right_daughter`))
    
    # convert to graph and delete the last node that we don't want to plot
    graph <- graph_from_data_frame(graph_frame) %>%
      delete_vertices("0")
    
    # set node labels
    V(graph)$node_label <- as.character(tree$`split_var`)
    V(graph)$leaf_label <- as.character(tree$prediction)
    V(graph)$split <- as.character(round(tree$`split_point`, digits = 2))
    
    # plot
    
    rf_plot=ggraph(graph, 'dendrogram') + 
      theme_bw() +
      geom_edge_link() +
      geom_node_point() +
      geom_node_text(aes(label = node_label), na.rm = TRUE, repel = TRUE) +
      geom_node_label(aes(label = split), vjust = 2.5, na.rm = TRUE, fill = "white") +
      geom_node_label(aes(label = leaf_label, fill = leaf_label), na.rm = TRUE, 
                      repel = TRUE, colour = "white", fontface = "bold", show.legend = FALSE) +
      theme(panel.grid.minor = element_blank(),
            panel.grid.major = element_blank(),
            panel.background = element_blank(),
            plot.background = element_rect(fill = "white"),
            panel.border = element_blank(),
            axis.line = element_blank(),
            axis.text.x = element_blank(),
            axis.text.y = element_blank(),
            axis.ticks = element_blank(),
            axis.title.x = element_blank(),
            axis.title.y = element_blank(),
            plot.title = element_text(size = 18))
    #ggsave("myplot.png")
    
    ggsave(filename=paste0("rtree_",ntree_plot,".png"),plot=rf_plot,scale=2,width = 15, height = 5, dpi = 300, units = "in", device='png', limitsize = FALSE)
    print(paste0('Grafico feito para arvore',ntree_plot))
    tree_list[[ntree_plot]]=getConds(tree)
    print(paste0('Lista de arvores pronta pra',ntree_plot))
    
  }

  aux = tree2 %>% filter(!is.na(`split var`))
  
  words <- sort(rowSums(aux$`split var`),decreasing=TRUE) 
  
  
  hist(aux$`split var`)
  
  df_freq = lapply(aux, function(x) as.data.frame(table(x)))$`split var`
  df_merged = aux %>% left_join(df_freq, by=c("split var"="x"))
  tree_help = df_merged %>% distinct(`split var`, .keep_all=T) 
  colnames(tree_help)=gsub(' ','_',colnames(tree_help))  
  
  tree_help %>% mutate(split_var = case_when(str_extract(split_var, "^.{1}")=='X'~gsub('X','',split_var),T~split_var))
  
  
  ifelse(str_extract('Xpedro', "^.{1}")=='X',gsub('X','','Xpedro'),'Xpedro')
  wordcloud(words = a$`split var`, freq = a$Freq, min.freq = 1,max.words=1000, random.order=T, colors=brewer.pal(8, "Dark2"))
  str_sub(x, 2)
  
  
  
  #tree_num <- which(rf_model$forest$ndbigtree == min(rf_model$forest$ndbigtree))
  # get tree by index
  
  
  
}

############################################################### Rodando as funcoes #################################################################


setwd("/Users/pedrocampelo/Desktop/Work/FUNCEF/Credito Bancario/IF/")
load("model_result.RData")

df_list = open_df()
df_banks = df_list[[1]]
df_var = df_list[[2]]
rm(df_list)


# #CONFERIR LINHAS 
# df_row1 = as.data.frame(rowSums(is.na(df_model))) %>% rownames_to_column("row")
# names(df_row1)[2]='naRow'
# df_row1 = df_row1 %>% mutate('total'=length(df_filter3)) %>% mutate('ratio'=naRow/total) 
# rows = df_row1 %>% mutate(row=as.numeric(row)) %>% filter(ratio>0.75) %>% select('row') %>% as.list() %>% .[[1]]
# 
# 
# #CONFERIR COLUNAS 
 df_col1 = data.frame(colSums(df_model==0)) %>% rownames_to_column("var")
 names(df_col1)[2]='naCol'
 df_col1 %>% filter(naCol!=0)


#df_banks %>% filter(y==1)
 

#save.image(file="model_result_3trim_notscaled.RData") 
 
 
 
 
 
 
 
 

 


 