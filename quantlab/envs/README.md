# 框架環境隔離(REQ-A0-PAR-003)

PyTorch / TensorFlow / JAX 各綁不同 CUDA/cuDNN 版本,塞同一 venv 易衝突。
每框架一份獨立環境定義,各自建 venv 或容器映像;平行排程器提交 job 時挑對應環境。

| Lane | 定義 | 隔離 venv(建議) |
|---|---|---|
| PyTorch | [pytorch.txt](./pytorch.txt) | `.venv-torch` |
| TensorFlow | [tensorflow.txt](./tensorflow.txt) | `.venv-tf` |
| JAX | [jax.txt](./jax.txt) | `.venv-jax` |

> 此為環境定義(declaration);實際各 lane 安裝與 GPU 驗證屬真機 / 容器執行,
> 不在單一開發 venv 內進行。回測 harness 對框架無感,只透過 Strategy Protocol 互動。
