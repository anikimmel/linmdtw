from DTW import *
from DTWGPU import *
from AlignmentTools import *
import numpy as np
import matplotlib.pyplot as plt
import time
import json
import scipy.io as sio

def test_alignment_accuracy():
    from SyntheticCurves import getTorusKnot, getRandomRigidTransformation
    np.random.seed(0)

    M = 500
    N = 400
    #Ground truth path
    t1 = np.linspace(0, 1, M)
    t2 = np.linspace(0, 1, N)**2

    # Time-ordered point clouds
    dim = 20
    X = np.zeros((M, dim))
    X[:, 0:3] = getTorusKnot(5, 3, t1)
    Y = np.zeros((N, dim))
    Y[:, 0:3] = getTorusKnot(5, 3, t2)
    R, T = getRandomRigidTransformation(dim, np.std(X))
    X = X.dot(R) + T[None, :]
    Y = Y.dot(R) + T[None, :]
    X = np.array(X, dtype=np.float32)
    Y = np.array(Y, dtype=np.float32)

    res = DTW_Backtrace(X, Y)

    t2 = t2*(M-1)
    t1 = (N-1)*np.linspace(0, 1, len(t2))
    PGT = np.zeros((len(t1), 2))
    PGT[:, 0] = t2
    PGT[:, 1] = t1
    P = np.array(res['path'])
    score = computeAlignmentError(PGT, P, doPlot = True)
    plt.show()

def test_ordinary_vs_diag_alignment():
    # Setup point clouds
    from AlignmentTools import getCSM
    M = 800
    t = 2*np.pi*np.linspace(0, 1, M)**2
    X = np.zeros((M, 2))
    X[:, 0] = np.cos(t)
    X[:, 1] = np.sin(2*t)
    N = 1199
    t = 2*np.pi*np.linspace(0, 1, N)
    Y = np.zeros((N, 2))
    Y[:, 0] = 1.1*np.cos(t)
    Y[:, 1] = 1.1*np.sin(2*t)
    X = X*1000
    Y = Y*1000

    # Do ordinary DTW as a reference
    X = np.array(X, dtype=np.float32)
    Y = np.array(Y, dtype=np.float32)

    res = DTW_Backtrace(X, Y)
    path = res['path']
    cost = res['cost']
    plt.imshow(res['P'])
    plt.show()
    print("Cost ordinary: ", cost)

    # Do parallel DTW
    cost = DTWDiag(X, Y)['cost']
    print("Cost diagonal: ", cost)
    path2 = DTWDiag_Backtrace(X, Y, cost)
    
    path2 = np.array(path2)
    path = np.array(path)

    print(np.allclose(path, path2))
    D = getCSM(X, Y)
    print("Cost path ordinary: ", np.sum(D[path[:, 0], path[:, 1]]))
    print("Cost path diagonal: ", np.sum(D[path2[:, 0], path2[:, 1]]))

    plt.scatter(path[:, 0], path[:, 1])
    plt.scatter(path2[:, 0], path2[:, 1], 100, marker='x')
    plt.show()


def test_timing(dim = 20):
    import timeit
    from SyntheticCurves import getTorusKnot, getRandomRigidTransformation
    initParallelAlgorithms()
    np.random.seed(0)


    # Run cython code
    trials = 10
    reps = 100
    MAX_SIZE = 20000
    sizes = np.round(np.linspace(0, 1, 101)[1::]*MAX_SIZE)
    allsizes = []
    cytimes = []
    nbtimes = []
    for N in sizes:
        N = int(N)
        WarpDict = getWarpDictionary(N)
        t1 = np.linspace(0, 1, N)
        X1 = np.zeros((N, dim))
        X1[:, 0:3] = getTorusKnot(5, 3, t1)
        for trial in range(trials):
            global X
            global Y
            t2 = getWarpingPath(WarpDict, 3, False)
            Y = np.zeros((N, dim))
            Y[:, 0:3] = getTorusKnot(5, 3, t2)
            R, T = getRandomRigidTransformation(dim, np.std(X1))
            X = np.array(X1.dot(R) + T[None, :], dtype=np.float32)
            Y = np.array(Y.dot(R) + T[None, :], dtype=np.float32)
            print("Doing %i x %i trial %i"%(N, N, trial+1))
            cytime = timeit.timeit("DTW(X, Y)", number=reps, globals=globals())
            nbtime = timeit.timeit("DTWPar_GPU(X, Y)", number=reps, globals=globals())
            cytimes.append(cytime)
            nbtimes.append(nbtime)
            allsizes.append(N)
            json.dump({"cytimes":cytimes, "nbtimes":nbtimes, "allsizes":allsizes}, open("timings.txt", "w"))

if __name__ == '__main__':
    #test_ordinary_vs_diag_alignment()
    #test_alignment_accuracy()
    test_timing()