"""quantlab — portfolio-grade 個人 quant 研究 lab(Epic A0 地基)。

與既有 invest_algorithms/(FastAPI + algo_pyramid)並存不互改。
子套件:contracts / data / engine / parallel / tracking。
框架隔離鐵律:engine / data 不得 import torch/tensorflow/jax(NFR-A0-FWAGN-001)。
"""
