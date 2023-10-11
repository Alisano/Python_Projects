from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning
from os import environ
import numpy as np
import matplotlib.pyplot as plt
from time import time
import math as m
from scipy.ndimage import convolve
from scipy.sparse.csgraph import laplacian
import yaml
from scipy.constants import m_e, pi
from scipy.constants import elementary_charge as q
from random import triangular
from numpy import linalg, gradient
from numba import njit, float64, types, boolean
from numba.experimental import jitclass
from numba.extending import as_numba_type
from warnings import simplefilter