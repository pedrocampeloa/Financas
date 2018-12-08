#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 20 01:02:48 2018

@author: pedrocampelo
"""

#BLACKSCHOLHES EQUATION

 import math

    def d1 (S0,X, r, vol,T):
        return (math.log(S0/X) + (r+0.5*(vol**2))*T)/(vol*(T**(1/2)))

    def d2(d1,vol,T):
        return d1(S0,X, r, vol,T)-(vol*(T**(1/2)))

    def Nd1 (d1, xbarra, dp):                      #normalizando d1
        return (d1(S0,X, r, vol,T)-xbarra)/dp      

    def Nd2 (d2, d1, xbarra,dp):                 #normalizando d2
        return (d2(d1,vol,T)-xbarra)/dp      

    def C(Nd1, S0, Nd2, X, r, T):
        return Nd1(d1, xbarra, dp)*S0 -Nd2(d2, d1, xbarra,dp)*X*math.exp(-r*T)
    
if __name__=='__main__':

    #BlackScholes Parameters

    S0=300            #fluxo de caixa futuro descontado (DFC)
    X=300             #custo inicial
    vol=0.3           #fator de volatilidade anual
    r=0.05            #taxa de juros contínua
    T=5               #tempo do projeto

    xbarra=-1.277       
    dp=2.557   
    
    print(C(Nd1, S0, Nd2, X, r, T))
    112.8121315637216
    
    
    
    
  #MONTE CARLO SIMULATION  
 
    #MonteCarlo Parameters
S0=300          #DFC
X=300           #custo inicial
vol=0.3         #fator de volatilidade anual
r=0.05          #taxa de juros contínua
T=5             #tempo do projeto
ts_bs=0.5       #incremento no tempo 
  
  
colunas = ['S0','S1','S2','S3','S4','S5']
df=pd.DataFrame(columns=colunas, index=list(range(1000)))

df['S0']=np.ones((1000,1))*S0 
df['S1']=df['S0'] + df['S0']*(r*ts_bs + vol*e1*((ts_bs*1)**(1/2)))  #T=1
df['S2']=df['S1'] + df['S1']*(r*ts_bs + vol*e2*((ts_bs*2)**(1/2)))  #T=2
df['S3']=df['S2'] + df['S2']*(r*ts_bs + vol*e3*((ts_bs*3)**(1/2)))  #T=3
df['S4']=df['S3'] + df['S3']*(r*ts_bs + vol*e4*((ts_bs*4)**(1/2)))  #T=4
df['S5']=df['S4'] + df['S4']*(r*ts_bs + vol*e5*((ts_bs*5)**(1/2)))  #T=5
df['S']=df['S5']-X              #Descontar do preço inicial
df['S'][df['S'] < 0] = 0        #Retirar os valores negativos
df['SS']=df['S']/ math.exp(T*r) #Trazer para o valor presente

print (df.head())
print (df['SS'].mean())





#BINOMIAL METHOD


#Binomial Parameters
S0=300          #DFC
X=300           #custo inicial
vol=0.3         #fator de volatilidade anual
r=0.05          #taxa de juros contínua
T=5             #tempo do projeto
ts_bm=1         #incremento no tempo

import math 

def u(t):
    return math.exp(vol*(ts_bm*t)**(1/2))

def d(t):
    return 1/u(t)

def p(t):
    return (math.exp(r*ts_bm*t)-d(t))/(u(t)-d(t))

S0u = S0*u(1)
S0d = S0*d(1)
S1= [S0u,S0d]

S0uu=S0u*u(1)
S0ud=S0u*d(1)
S0dd=S0d*d(1)    
S2 = [S0uu, S0ud, S0dd] 

S0uuu=S0uu*u(1)
S0uud=S0ud*u(1)
S0udd=S0ud*d(1)
S0ddd=S0dd*d(1)
S3 = [S0uuu, S0uud, S0udd, S0ddd]

S0uuuu=S0uuu*u(1)
S0uuud=S0uuu*d(1)
S0uudd=S0uud*d(1)
S0uddd=S0udd*d(1)
S0dddd=S0ddd*d(1)
S4 = [S0uuuu,S0uuud,S0uudd,S0uddd,S0dddd]

S0uuuuu=S0uuuu*u(1)
S0uuuud=S0uuuu*d(1)
S0uuudd=S0uuud*d(1)
S0uuddd=S0uudd*d(1)
S0udddd=S0uddd*d(1)
S0ddddd=S0dddd*d(1)
S5 = [S0uuuuu,S0uuuud,S0uuudd,S0uuddd,S0udddd, S0ddddd]


#Indução Reversa
I5 = [S0uuuuu - X,S0uuuud -X,S0uuudd - X,S0uuddd-X,S0udddd-X, S0ddddd-X]

def replace_neg(old_list):
    new_list = []
    for i in old_list:
        if i < 0:
             new_list.append(0)
        else:
            new_list.append(i)
    return new_list

I5 = replace_neg(I5)

I0uuuuu=I5[0]
I0uuuud=I5[1]
I0uuudd=I5[2]
I0uuddd=I5[3]
I0udddd=I5[4]
I0ddddd=I5[5]

I0uuuu=(p(1)*I0uuuuu + (1-p(1))*I0uuuud)*math.exp(-r*ts_bm*1)
I0uuud=(p(1)*I0uuuud + (1-p(1))*I0uuudd)*math.exp(-r*ts_bm*1)
I0uudd=(p(1)*I0uuudd + (1-p(1))*I0uuddd)*math.exp(-r*ts_bm*1)
I0uddd=(p(1)*I0uuddd + (1-p(1))*I0udddd)*math.exp(-r*ts_bm*1)
I0dddd=(p(1)*I0udddd + (1-p(1))*I0ddddd)*math.exp(-r*ts_bm*1)
I4 = [I0uuuu, I0uuud, I0uudd, I0uddd, I0dddd]

I0uuu=(p(1)*I0uuuu + (1-p(1))*I0uuud)*math.exp(-r*ts_bm*1)
I0uud=(p(1)*I0uuud + (1-p(1))*I0uudd)*math.exp(-r*ts_bm*1)
I0udd=(p(1)*I0uudd + (1-p(1))*I0uddd)*math.exp(-r*ts_bm*1)
I0ddd=(p(1)*I0uddd + (1-p(1))*I0dddd)*math.exp(-r*ts_bm*1)
I3= [I0uuu, I0uud, I0udd, I0ddd]

I0uu=(p(1)*I0uuu + (1-p(1))*I0uud)*math.exp(-r*ts_bm*1)
I0ud=(p(1)*I0uud + (1-p(1))*I0udd)*math.exp(-r*ts_bm*1)
I0dd=(p(1)*I0udd + (1-p(1))*I0ddd)*math.exp(-r*ts_bm*1)
I2 = [I0uu, I0ud, I0dd]

I0u = (p(1)*I0uu + (1-p(1))*I0ud)*math.exp(-r*ts_bm*1)
I0d = (p(1)*I0ud + (1-p(1))*I0dd)*math.exp(-r*ts_bm*1)
I1 = [I0u, I0d]

I0 = (p(1)*I0u + (1-p(1))*I0d)*math.exp(-r*ts_bm*1)

print (I0)


#TENTATIVA plot



import matplotlib.pyplot as plt

c = [[(S0), (S0d)],
     [(S0), (S0u)],
     [(S0d), (S0dd)],
     [(S0d), (S0ud)],
     [(S0u), (S0ud)],
     [(S0u), (S0uu)],
     [(S0dd), (S0ddd)],
     [(S0dd), (S0udd)],
     [(S0ud), (S0uddd)],
     [(S0ud), (S0uud)],
     [(S0uu), (S0uud)],
     [(S0uu), (S0uuu)],
     [(S0ddd), (S0dddd)],
     [(S0ddd), (S0uddd)],
     [(S0udd), (S0uddd)],
     [(S0udd), (S0uudd)],
     [(S0uud), (S0uudd)],
     [(S0uud), (S0uuud)],
     [(S0uuu), (S0uuud)],
     [(S0uuu), (S0uuuu)],
     [(S0dddd), (S0ddddd)],
     [(S0dddd), (S0udddd)],
     [(S0uddd), (S0udddd)],
     [(S0uddd), (S0uuddd)],
     [(S0uudd), (S0uuddd)],
     [(S0uudd), (S0uuudd)],
     [(S0uuud), (S0uuudd)],
     [(S0uuud), (S0uuuud)],
     [(S0uuuu), (S0uuuud)],
     [(S0uuuu), (S0uuuuu)]]

import numpy as np

def binom_tree_call (T,N,t, r, vol, r, X, array_out=False):
    dt=T/N
    u=np.exp(vol*(dt)**(1/2))
    u=1/u
    p=(np.exp(r*dt)-d/(u-d)
    price_tree = np.zeros([N+1,N+1])    
    
    for i in range (N+1):
        for j in range (i+1):
            price_tree[j,i]=S0*(d**j)*(u**(i-j))
    
    
    option = np.zeros([N+1,N+1])
    option[:,N]=np.maximum(np.zeros(N+1),price_tree[:,N]-X)
    
    for i in np.arrange(N-1, -1, -1):
        for j in np.arrange(0,i+1):
            option[j,i]=np.exp(-r*dt)*(p*option[j,i+1]+(1-p)*option[j+i,i+1])
            
    if array_out:
      return [option[0,0], price_tree, option]
    else:
        return option[0,0]
    

    
#Binomial Parameters
S0=300          #DFC
X=300           #custo inicial
vol=0.3         #fator de volatilidade anual
r=0.05          #taxa de juros contínua
T=5             #tempo do projeto
ts_bm=1         #incremento no tempo

import math 

def u(t):
    return math.exp(vol*(ts_bm*t)**(1/2))

def d(t):
    return 1/u(t)

def p(t):
    return (math.exp(r*ts_bm*t)-d(t))/(u(t)-d(t))    
    
    
    
    
    
    
    
