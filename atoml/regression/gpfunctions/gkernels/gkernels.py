# created on 11/9/17 at 13:02
# by @jagarridotorres (jagt@stanford.edu)

import numpy as np
from atoml.regression.gpfunctions.gkernels import squared_exponential_kernel as squared_exponential
from atoml.regression.gpfunctions.gkernels import linear_kernel as linear
from atoml.regression.gpfunctions.gkernels import constant_kernel as constant

# To build k_little:
def k_little(kernel_type, l,train,test):
    k_little = eval(str(kernel_type)).kernel_klittle(l,test,train)
    return k_little

# To build kgd_tilde:
def kgd_tilde(kernel_type, l, train, test):
    l = np.array(l)
    size1 = np.shape(train)
    size2 = np.shape(test)
    kgd = np.zeros((size1[0]*size1[1],size2[0]))
    for j in range(len(test)):
        kgd_thistest = np.zeros(size1[0]*size1[1])
        for i in range(len(train)):
            kgd_thistest[i*size1[1]:(i+1)*size1[1]] = eval(str(
            kernel_type)).kernel_kgd(
            l,test[j],train[i])
        kgd[:,j] = kgd_thistest
    return kgd


#########################################
############    bigKs    ################
#########################################

# To build big_k:
def bigk(kernel_type, l, train):
    bigk = eval(str(kernel_type)).kernel_bigk(l,train)
    return bigk


# To build big_kgd:
def big_kgd(kernel_type, l,train):
    l = np.array(l)
    size = np.shape(train)
    big_kgd = np.zeros((size[0],size[0]*size[1]))
    for i in range(len(train)):
        basis_vect1 = np.zeros(size[0])
        basis_vect1[i] = 1.0
        for j in range(len(train)):
            basis_vect2 = np.zeros(size[0])
            basis_vect2[j] = 1.0
            k_gd = eval(str(kernel_type)).kernel_kgd(l, train[i],train[j])
            prekron = np.outer(basis_vect1,np.transpose(basis_vect2))
            kron = np.kron(prekron,k_gd)
            big_kgd = big_kgd + kron
    return big_kgd


# To build big_kdd:
def big_kdd(kernel_type, l, train):
    l = np.array(l)
    size = np.shape(train)
    big_kdd = np.zeros((size[0]*size[1],size[0]*size[1]))
    for i in range(len(train)):
        basis_vect1 = np.zeros(size[0])
        basis_vect1[i] = 1.0
        for j in range(len(train)):
            basis_vect2 = np.zeros(size[0])
            basis_vect2[j] = 1.0
            k_dd = eval(str(kernel_type)).kernel_kdd(l, train[i],train[j])
            prekron = np.outer(basis_vect1,np.transpose(basis_vect2))
            kron = np.kron(prekron,k_dd)
            big_kdd = big_kdd + kron
    return big_kdd


#########################################
#######  k TILDE and bigK TILDE    ######
#########################################

# To build k_tilde:
def k_tilde(kernel_type, l,test,train):
    l = np.array(l)
    k_tilde = []
    k_tilde = np.vstack([k_little(kernel_type, l,train,test),kgd_tilde(
    kernel_type, l,
    train,test)])
    return k_tilde.T

# To build bigK_tilde:
def bigk_tilde(kernel_type, l,train):
    l = np.array(l)
    bigk_tilde = []
    bigk_tilde = np.block([[bigk(kernel_type, l,train),big_kgd(kernel_type, l,
    train)],
    [np.transpose(
    big_kgd(kernel_type, l,train)),big_kdd(kernel_type, l,train)]])
    return bigk_tilde

#########################################
#########################################