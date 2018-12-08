#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 16:51:00 2018

@author: pedrocampelo
"""


    import numpy as np  
    import matplotlib.pyplot as plt  
    import os
    
    os.getcwd()   
    os.chdir('/Users/pedrocampelo/Downloads')
    cwd = os.getcwd()
    cwd
    
#MINIMIZAR 9x + 8y
    

    
    x = np.linspace(-10,10)                 #Referência
    
    x7 = np.linspace(-0.48,0.5)
    x8 = np.linspace(-0.25,0.75)
    x9 = np.linspace(-0,1)
    x10 = np.linspace(0.5,1.2)
    
    y10 = x10*(-9/8) + (17/8)
    y9 = x9*(-9/8) + (12/8)
    y8 = x8*(-9/8) + (6/8)
    y7 = x7*(-9/8)                               
    y6 = x*(-9/8) - (5/8)
    

    plt.axis([-0.5, 1.25, -0.5, 1.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x10, y10, color='red')    
    plt.plot(x9, y9, color='red')
    plt.plot(x8, y8, color='red')
    plt.plot(x7, y7, color='red')
    plt.plot(x, y6, color='red')
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimizar (9x + 8y)')
    plt.annotate('.', xy=(0, 0), xytext=(0.2, 0.3),
                 arrowprops=dict(facecolor='black', shrink=0.15),
             )

    plt.annotate('.', xy=(0.3, 0.5), xytext=(0.5, 0.8),
                 arrowprops=dict(facecolor='black', shrink=0.15),
             )    
    plt.annotate('.', xy=(0.6, 0.9), xytext=(0.79, 1.2),
                 arrowprops=dict(facecolor='black', shrink=0.15),
             )  
    plt.annotate('.', xy=(-0.26, -0.39), xytext=(-0.08, -0.12),
                 arrowprops=dict(facecolor='black', shrink=0.15),
             )     
    #plt.grid()    
    plt.show()
    
    plt.savefig('grafico.png')    




                                    #Restrição 1 (Verde):
    

    y1=x*(1/2) - (3/2) 

    plt.axis([-2, 6, -3, 5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x, y1, color='green')
    plt.fill_between(x,y1, 10, color='lightgrey', alpha=0.5)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrição 1')
    #plt.grid()    
    plt.show()
    
    
                                #Juntando com a maximização 
                                #1) Com 4 
    x11 = np.linspace(-2,3.5)
    x12 = np.linspace(-2,4.5)
    
    y11 = x11*(-9/8) + (27/8)
    y12 = x12*(-9/8) 
    
    xp1 = 0
    yp1 = 0
    
    ymax=np.maximum(y1, 0)
    xaux = np.array([-10.        ,  -9.59183673,  -9.18367347,  -8.7755102 ,
        -8.36734694,  -7.95918367,  -7.55102041,  -7.14285714,
        -6.73469388,  -6.32653061,  -5.91836735,  -5.51020408,
        -5.10204082,  -4.69387755,  -4.28571429,  -3.87755102,
        -3.46938776,  -3.06122449,  -2.65306122,  -2.24489796,
        -1.83673469,  -1.42857143,  -1.02040816,  -0.6122449 ,
        -0.20408163,   0.0000001,   0.6122449 ,   1.02040816,
         1.42857143,   1.83673469,   2.24489796,   2.65306122,
         3.06122449,   3.46938776,   3.87755102,   4.28571429,
         4.69387755,   5.10204082,   5.51020408,   5.91836735,
         6.32653061,   6.73469388,   7.14285714,   7.55102041,
         7.95918367,   8.36734694,   8.7755102 ,   9.18367347,
         9.59183673,  10.        ])
    
    
    
                     
    plt.axis([-1, 5, -1, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x11, y11, color='red')    
    plt.plot(x12, y12, color='red')
    plt.plot(xp1, yp1, 'ro') 
    plt.plot(x, y1, color='green')
    plt.fill_between(xaux, ymax,10,where=xaux>=0, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 1')
    plt.annotate('.', xy=(0.5, 0.5), xytext=(1.5, 1.5),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             )  
    #plt.grid()    
    plt.show()
    
    

    

    
    #2) sem 4

    x13 = np.linspace(-5,2.5)
    x14 = np.linspace(-4.5,4.5)

    
    y13 = x13*(-9/8) + (4/8)
    y14 = x14*(-9/8) - (35/8)
    
    xp1 = 0
    yp1 = 0    
    


    plt.axis([-5, 3, -4, 2])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x13, y13, color='red')    
    plt.plot(x14, y14, color='red')
    plt.plot(x, y1, color='green')
    plt.fill_between(x,y1, 10, color='lightgrey', alpha=0.5)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 1')
    plt.annotate('.', xy=(-1.5, -1.5), xytext=(-0.5, -0.7),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             ) 
    plt.annotate('.', xy=(-4, -3), xytext=(-3, -2.2),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             )
    #plt.grid()    
    plt.show()

    
    
                        #Restrição 2 (Amarela):


    y2=x*(3/4) - (5/4)

    plt.axis([-2, 6, -3, 2])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x, y2, color='yellow')
    plt.fill_between(x, y2, -3, color='lightgrey', alpha=0.5)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrição 2')    
    #plt.grid()    
    plt.show()   
    
    
                        #Juntando com a maximização


    #1) com 4
    
    x21 = np.linspace(-2,4.3)
    x22 = np.linspace(-0.5,4)
    
    y21 = x21*(-9/8) + (35/8)
    y22 = x22*(-9/8) + (15/8)
    
    xp2 = (5/3)
    yp2 = 0
    

                     
    plt.axis([-1, 5, -1, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x21, y21, color='red')    
    plt.plot(x22, y22, color='red')
    plt.plot(xp2, yp2, 'ro') 
    plt.plot(x, y2, color='yellow')
    plt.fill_between(x, y2, 0, where=x>=(5/3),color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 2')
    plt.annotate('.', xy=(1, 1), xytext=(1.7, 1.7),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             )  
    #plt.grid()    
    plt.show()
    


    #2) sem 4                
    
    x23 = np.linspace(-2,2)
    x24 = np.linspace(-5,5)
    
    y23 = x24*(-9/8) - (35/8)
    y24 = x23*(-9/8) + (4/8)
    
    xp2 = (5/3)
    yp2 = 0

                     
    plt.axis([-4, 4, -4, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x23, y24, color='red')    
    plt.plot(x24, y23, color='red')
    #plt.plot(xp2, yp2, 'ro') 
    plt.plot(x, y2, color='yellow')
    plt.fill_between(x, y2, -10, color='lightgrey', alpha=0.5)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 2')
    plt.annotate('.', xy=(-1.2, -1.5), xytext=(-0.5, -0.7),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             ) 
    plt.annotate('.', xy=(-3.5, -3.5), xytext=(-2.5, -2.5),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             )  
    #plt.grid()    
    plt.show()
    
                        #Restrição 3:(Azul)

    
    y3=x*(6/7) - (8/7)
         
    plt.axis([-2, 4, -3, 4])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x, y3, color='blue')
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrição 3')
    #plt.grid()    
    plt.show()
    
                            #Juntando com a maximização

   
    #1) com 4
    
    x31 = np.linspace(-0.2,2.7)
    x32 = np.linspace(-.4,4)
    
    y31 = x31*(-9/8) + (23/8)
    y32 = x32*(-9/8) + (12/8)
    
    xp3 = (4/3)
    yp3 = 0
                     
    plt.axis([-0.5, 3, -0.5, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x31, y31, color='red')    
    plt.plot(x32, y32, color='red')
    plt.plot(xp3, yp3, 'ro') 
    plt.plot(x, y3, color='blue') 
    plt.fill_between(xv5, yv5, 10, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 3')
    plt.annotate('.', xy=(0.7, 0.9), xytext=(1, 1.5),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()

    
    #2) sem 4               MUDAR PARAMETROS DA MINIMIZACAO

    
        
    x33 = np.linspace(-3.4,5)
    x34 = np.linspace(-1.2,2.3)
    
    y33 = x33*(-9/8) - (35/8)
    y34 = x34*(-9/8) + (4/8)
    

    
                     
    plt.axis([-4, 3, -4, 2])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x33, y33, color='red')    
    plt.plot(x34, y34, color='red')
    plt.plot(x, y3, color='blue') 
    #plt.fill_between(xv5, yv5, 10, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 3')
    plt.annotate('.', xy=(-1.2, -1.5), xytext=(-0.5, -0.7),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             ) 
    plt.annotate('.', xy=(-3.5, -3.5), xytext=(-2.5, -2.5),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             )    
    #plt.grid()    
    plt.show()
    
    
                            #Restrições 4:
    
    xv5 = list(range(9))
    yv5 = [0,0,0,0,0,0,0,0,0]
    
    
    plt.axis([-0.5, 4, -0.5, 4])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.fill_between(xv5, yv5, 10, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrição 4')
    #plt.grid()    
    plt.show() 
    
    
    
                            #Juntando com a maximização


    x41 = np.linspace(-0.5,3.5)
    x42 = np.linspace(-2,4.5)
    
    y41 = x41*(-9/8) + (27/8)
    y42 = x42*(-9/8)
    
    xp1 = 0
    yp1 = 0
                     
    plt.axis([-1, 4, -1, 4])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x41, y41, color='red')    
    plt.plot(x42, y42, color='red')
    plt.plot(xp1, yp1, 'ro') 
    plt.fill_between(xv5, yv5, 10, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrição 4')
    plt.annotate('.', xy=(0.3, 0.3), xytext=(1.2, 1.7),
                 arrowprops=dict(facecolor='black', shrink=0.05),
             )  
    #plt.grid()    
    plt.show() 
    
    

    
    
                            #Juntando as restrições
    
    yv1 = [0, -0.5, -1, -1.5, -2]
    xv1 = [-1,-1,-1,-1,-1]
    yv2 = [-2,-2,-2,-2,-2]
    xv2 = [0, -0.25, -0.5, -0.75, -1]
    xv3 = [-1]
    yv3 = [-2]
    
    
    
                                  #1 e 2  
  
    plt.axis([-2.5, 5, -3, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xv3, yv3, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y2, color='yellow')
    plt.fill_between(x,  y1, y2,where=x>=-1, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrições 1 e 2')
    #plt.grid()    
    plt.show()     
   
    
                        #Juntando com a maximização
                        
                        
                        #1) sem 4 
                        
    x121 = np.linspace(-2,4)
    x122 = np.linspace(-1.2,1.6)
    
    y121 = x121*(-9/8) - (25/8)
    y122 = x122*(-9/8) + (4/8)
    
    xp4 = -1
    yp4 = -2
    
                     
    plt.axis([-1.5, 2, -2.5, 2])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x121, y121, color='red')    
    plt.plot(x122, y122, color='red')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xp4, yp4, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y2, color='yellow')
    #plt.plot(x, y3, color='blue') 
    plt.fill_between(x,  y1, y2,where=x>=-1, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrições 1 e 2')
    plt.annotate('.', xy=(-0.5, -1), xytext=(0, 0),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()



        #2) com 4
        
    x123 = np.linspace(-2,2.8)
    x124 = np.linspace(-0.5,2.6)
    
    y123 = x123*(-9/8) + (23/8)
    y124 = x124*(-9/8) + (15/8)   
        
    xp2 = (5/3)
    yp2 = 0
        
    plt.axis([-1.2, 3, -2.2, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x123, y123, color='red')    
    plt.plot(x124, y124, color='red')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xp2, yp2, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y2, color='yellow')
    #plt.plot(x, y3, color='blue') 
    plt.fill_between(x,y2, 0, where= y2>=-0.1,color='lightgrey', alpha=2)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrições 1 e 2')
    plt.annotate('.', xy=(0.9, 1), xytext=(1.2, 1.5),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()

    
    
    
    
                                    #1 e 3

    plt.axis([-2, 4, -3, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xv3, yv3, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y3, color='blue')
    plt.fill_between(x,y1, 3, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrições 1 e 3')
    #plt.grid()    
    plt.show()      
    
    
                            #Juntando com a maximização

        #1) com 4


    x131 = np.linspace(-2,3.4)
    x132 = np.linspace(-0.8,2.9)
    
    y131 = x131*(-9/8) + (23/8)
    y132 = x132*(-9/8) + (12/8)
    
    xp2 = (4/3)
    yp2 = 0
    
    ymax=np.maximum(y1, 0)
    xaux = np.array([-10.        ,  -9.59183673,  -9.18367347,  -8.7755102 ,
        -8.36734694,  -7.95918367,  -7.55102041,  -7.14285714,
        -6.73469388,  -6.32653061,  -5.91836735,  -5.51020408,
        -5.10204082,  -4.69387755,  -4.28571429,  -3.87755102,
        -3.46938776,  -3.06122449,  -2.65306122,  -2.24489796,
        -1.83673469,  -1.42857143,  -1.02040816,  -0.6122449 ,
        -0.20408163,   0.000001,   0.6122449 ,   1.02040816,
         1.42857143,   1.83673469,   2.24489796,   2.65306122,
         3.06122449,   3.46938776,   3.87755102,   4.28571429,
         4.69387755,   5.10204082,   5.51020408,   5.91836735,
         6.32653061,   6.73469388,   7.14285714,   7.55102041,
         7.95918367,   8.36734694,   8.7755102 ,   9.18367347,
         9.59183673,  10.        ])
                     
    plt.axis([-1.5, 4, -2.5, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x131, y131, color='red')    
    plt.plot(x132, y132, color='red')
    plt.plot(x, y1, color='green')
    plt.plot(x, y3, color='blue') 
    plt.plot(xp3, yp3, 'ro') 
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xv3, yv3, 'ro') 
    plt.fill_between(xaux, ymax,10,where=xaux>=0, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrições 1 e 3')
    plt.annotate('.', xy=(0.7, 0.9), xytext=(1, 1.5),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()



            #1) sem 4

    x133 = np.linspace(-2,4)
    x134 = np.linspace(-2,4)
    
    y133 = x133*(-9/8) - (25/8)
    y134 = x134*(-9/8) + (4/8)
    
    

    xp4 = -1
    yp4 = -2
             
    plt.axis([-2, 4, -3, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x133, y133, color='red')    
    plt.plot(x134, y134, color='red')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y3, color='blue') 
    plt.plot(xp4, yp4, 'ro') 
    plt.fill_between(x,y1, 3, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrições 1 e 3')
    plt.annotate('.', xy=(-0.5, -1), xytext=(0, 0),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()

    
    
    
    
                                    #2 e 3 
    
   
    plt.axis([-2, 4, -3, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xv3, yv3, 'ro') 
    plt.plot(x, y2, color='yellow')
    plt.plot(x, y3, color='blue')
    plt.fill_between(x,y2, -3, color='lightgrey', alpha=2)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrições 2 e 3')
    #plt.grid()    
    plt.show()      
    
                                #Juntando com a maximização

    
    
                #1) sem 4 (solução: x1=x2=-infinito)


    x231 = np.linspace(-3.5,1.1)
    x232 = np.linspace(-4.5,5)
   
    y231 = x231*(-9/8) - (25/8)
    y232 = x232*(-9/8) - (50/8)
  
    xp4 = -1
    yp4 = -2   

    plt.axis([-5, 3, -5, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(x231, y231, color='red')    
    plt.plot(x232, y232, color='red')
    plt.plot(xv3, yv3, 'ro') 
    plt.plot(x, y2, color='yellow')
    plt.plot(x, y3, color='blue')
    plt.fill_between(x,y2, -10, color='lightgrey', alpha=2)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrições 2 e 3')
    plt.annotate('.', xy=(-2.2, -2.5), xytext=(-1.4, -1.8),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show() 
    
    
    
                    #1) com 4 (sem solução)
                    
                    
    plt.axis([-1.1, 4, -2.1, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xv3, yv3, 'ro') 
    plt.plot(x, y2, color='yellow')
    plt.plot(x, y3, color='blue')
    plt.fill_between(x, y2, 0, where=x>=(5/3),color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrições 2 e 3')
    #plt.grid()    
    plt.show()               

    
    


                                    #as 3

    plt.axis([-1.5, 4, -2.5, 2.5])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xv3, yv3, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y2, color='yellow')
    plt.plot(x, y3, color='blue')  
    plt.fill_between(x,y1, y2, color='lightgrey', alpha=2)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrições 1, 2 e 3')
    #plt.grid()    
    plt.show()    


                            #Juntando com a maximização
                            
                            #1) com 4
       
    x1231 = np.linspace(-2,4)
    x1232 = np.linspace(-2,4)
    
    y1231 = x1231*(-9/8) + (23/8)
    y1232 = x1232*(-9/8) + (12/8)
    
                     
    plt.axis([-1.5, 3, -2.5, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x1231, y1231, color='red')    
    plt.plot(x1232, y1232, color='red')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xp3, yp3, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y2, color='yellow')
    plt.plot(x, y3, color='blue') 
    plt.fill_between(x,y2, 0, where= y2>=-0.1,color='lightgrey', alpha=2)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimização e Restrições 1, 2 e 3')
    plt.annotate('.', xy=(0.7, 0.9), xytext=(1, 1.5),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()
    

    
    

                            #1) sem 4

    x1233 = np.linspace(-2,4)
    x1234 = np.linspace(-1.1,1.7)
    
    y1233 = x1233*(-9/8) - (25/8)
    y1234 = x1234*(-9/8) + (4/8)
    
    xp4 = -1
    yp4 = -2
    
                     
    plt.axis([-1.5, 2, -2.5, 2])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.plot(x1233, y1233, color='red')    
    plt.plot(x1234, y1234, color='red')
    plt.plot(xv1, yv1, 'r--', color='black')
    plt.plot(xv2, yv2, 'r--', color='black') 
    plt.plot(xp4, yp4, 'ro') 
    plt.plot(x, y1, color='green')
    plt.plot(x, y2, color='yellow')
    plt.plot(x, y3, color='blue') 
    plt.fill_between(x,  y1, y2,where=x>=-1, color='lightgrey', alpha=0.5 )
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Minimizar (9x + 8y)')
    plt.annotate('.', xy=(-0.5, -1), xytext=(0, 0),
                 arrowprops=dict(facecolor='black', shrink=1),
             )  
    #plt.grid()    
    plt.show()


#COMENTARIO


MAX 3X + Y 
S.A
Y=X-1
Y=-3X+1
Y=-X+(1/2)
Y=(1/2)


    x = np.linspace(-10,10)                
   
    y1=x-1
    y2=-3*x+1
    y3=-2*x+(1/2)

    yp = (-1/2)
    xp = (1/2)
    
    plt.axis([-3, 3, -3, 3])
    plt.axhline(0, color='black')
    plt.axvline(0, color='black')
    plt.axhline((-1/2), color='blue') 
    plt.plot(x, y1, color='blue')  
    plt.plot(x, y2, color='blue')    
    plt.plot(x, y3, color='blue')    
    plt.plot(xp, yp, 'ro') 
    #plt.fill_between(x, y2, y3, color='lightgrey', alpha=2)
    plt.xlabel('eixo x')
    plt.ylabel('eixo y')
    plt.title('Restrições 1 a 4')
    #plt.grid() 
    plt.savefig('grafico1.png')    
    plt.show() 



    '"""

    


    
    
    
    