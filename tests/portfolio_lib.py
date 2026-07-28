import numpy as np


def min_variance_weights(sigma: np.ndarray) -> np.ndarray:
    ones = np.ones(len(sigma))
    sigma_inv = np.linalg.inv(sigma)
    w = sigma_inv @ ones
    return w / (ones @ sigma_inv @ ones)


def tangency_weights(mu: np.ndarray, sigma: np.ndarray, rf: float) -> np.ndarray:
    excess = mu - rf
    sigma_inv = np.linalg.inv(sigma)
    w = sigma_inv @ excess
    return w / (np.ones(len(mu)) @ sigma_inv @ excess)
