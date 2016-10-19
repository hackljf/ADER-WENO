""" Implements the WENO method used in Dumbser et al (DOI 10.1016/j.cma.2013.09.022)
"""
from itertools import product

from numpy import multiply, zeros, floor, ceil
from scipy.linalg import solve

from options import rc, λc, λs, ε, ndim, N, n
from .weno_matrices import coefficient_matrices, oscillation_indicator
from auxiliary.functions import extend


Mc = coefficient_matrices()
Σ = oscillation_indicator()

if N%2:
    nStencils = 4
    lamList = [λc, λc, λs, λs]
else:
    nStencils = 3
    lamList = [λc, λs, λs]


def coeffs(uList):
    """ Calculate coefficients of basis polynomials and weights
    """
    wList = [solve(Mc[i], uList[i], overwrite_b=1, check_finite=0) for i in range(nStencils)]
    σList = [((w.T).dot(Σ).dot(w)).diagonal() for w in wList]
    oList = [lamList[i]  / (abs(σList[i]) + ε)**rc for i in range(nStencils)]
    oSum = zeros(n)
    numerator = zeros([N+1, n])
    for i in range(nStencils):
        oSum += oList[i]
        numerator += multiply(wList[i], oList[i])
    return numerator / oSum

def reconstruct(u):
    """ Find reconstruction coefficients of u to order N+1
    """
    nx, ny, nz = u.shape[:3]
    floorHalfN = int(floor(N/2))
    ceilHalfN = int(ceil(N/2))

    Wx = zeros([nx, ny, nz, N+1, n])
    tempu = extend(u, N, 0)
    for i, j, k in product(range(nx), range(ny), range(nz)):
        ii = i + N
        if nStencils==3:
            u1 = tempu[ii-floorHalfN : ii+floorHalfN+1, j, k]
            u2 = tempu[ii-N : ii+1, j, k]
            u3 = tempu[ii : ii+N+1, j, k]
            Wx[i, j, k] = coeffs([u1, u2, u3])
        else:
            u1 = tempu[ii-floorHalfN : ii+ceilHalfN+1, j, k]
            u2 = tempu[ii-ceilHalfN : ii+floorHalfN+1, j, k]
            u3 = tempu[ii-N : ii+1, j, k]
            u4 = tempu[ii : ii+N+1, j, k]
            Wx[i, j, k] = coeffs([u1, u2, u3, u4])
    if ndim==1:
        return Wx

    Wxy = zeros([nx, ny, nz, N+1, N+1, n])
    tempWx = extend(Wx, N, 1)
    for i, j, k in product(range(nx), range(ny), range(nz)):
        jj = j + N
        for a in range(N+1):
            if nStencils==3:
                w1 = tempWx[i, jj-floorHalfN : jj+floorHalfN+1, k, a]
                w2 = tempWx[i, jj-N : jj+1, k, a]
                w3 = tempWx[i, jj : jj+N+1, k, a]
                Wxy[i, j, k, a] = coeffs([w1, w2, w3])
            else:
                w1 = tempWx[i, jj-floorHalfN : jj+ceilHalfN+1, k, a]
                w2 = tempWx[i, jj-ceilHalfN : jj+floorHalfN+1, k, a]
                w3 = tempWx[i, jj-N : jj+1, k, a]
                w4 = tempWx[i, jj : jj+N+1, k, a]
                Wxy[i, j, k, a] = coeffs([w1, w2, w3, w4])
    if ndim==2:
        return Wxy

    Wxyz = zeros([nx, ny, nz, N+1, N+1, N+1, n])
    tempWxy = extend(Wxy, N, 2)
    for i, j, k in product(range(nx), range(ny), range(nz)):
        kk = k + N
        for a, b in product(range(N+1), range(N+1)):
            if nStencils==3:
                w1 = tempWxy[i, j, kk-floorHalfN : kk+floorHalfN+1, a, b]
                w2 = tempWxy[i, j, kk-N : kk+1, a, b]
                w3 = tempWxy[i, j, kk : kk+N+1, a, b]
                Wxyz[i, j, k, a, b] = coeffs([w1, w2, w3])
            else:
                w1 = tempWxy[i, j, kk-floorHalfN : kk+ceilHalfN+1, a, b]
                w2 = tempWxy[i, j, kk-ceilHalfN : kk+floorHalfN+1, a, b]
                w3 = tempWxy[i, j, kk-N : kk+1, a, b]
                w4 = tempWxy[i, j, kk : kk+N+1, a, b]
                Wxyz[i, j, k, a, b] = coeffs([w1, w2, w3, w4])
    if ndim==3:
        return Wxyz
