# Agent 安装与上报示例（Linux）

本 repo 目前提供一个 Python Agent 示例：`agent/agent.py`  
可采集 CPU/Memory/Disk 并上报到 Backend 的 `/ingest/metrics`，同时可上报简易日志到 `/ingest/logs`。

## 1) 安装（建议使用 venv）

```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 设置环境变量

```bash
export AIOPS_BACKEND_URL="http://<backend-ip>:8000"
export AIOPS_HOSTNAME="$(hostname)"
export AIOPS_OS="linux"
export AIOPS_INTERVAL_SEC="10"
```

## 3) 直接启动

```bash
python agent.py
```

## 4) systemd（示例）

创建 `/etc/systemd/system/aiops-agent.service`：

```ini
[Unit]
Description=AIOps Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/aiops/agent
Environment=AIOPS_BACKEND_URL=http://<backend-ip>:8000
Environment=AIOPS_INTERVAL_SEC=10
ExecStart=/opt/aiops/agent/.venv/bin/python /opt/aiops/agent/agent.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用与启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aiops-agent
sudo systemctl status aiops-agent
```

