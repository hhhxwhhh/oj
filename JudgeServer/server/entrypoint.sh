#!/bin/sh
set -ex

rm -rf /judger/*
mkdir -p /judger/run /judger/spj

chown compiler:code /judger/run
chmod 777 /judger/run

chown compiler:spj /judger/spj
chmod 710 /judger/spj

# 确保日志目录存在且有正确的权限
mkdir -p /log
chmod 777 /log

# 检查_judger模块是否可以被导入
if ! .venv/bin/python3 -c "import _judger; print('_judger module loaded successfully, version:', _judger.VERSION)" 2>&1; then
    echo "Error: _judger module cannot be imported. Sandbox functionality will be disabled."
    exit 1
fi

# 检查libjudger.so是否存在且可访问
if [ ! -f "/usr/lib/judger/libjudger.so" ]; then
    echo "Error: libjudger.so not found"
    exit 1
fi

# 检查必需的用户是否存在
if ! id code >/dev/null 2>&1 || ! id compiler >/dev/null 2>&1 || ! id spj >/dev/null 2>&1; then
    echo "Error: Required users not found"
    exit 1
fi

# 等待后端服务启动的函数
wait_for_backend() {
    echo "Waiting for backend service to be ready..."
    # 等待最多180秒
    for i in $(seq 1 60); do
        # 使用 curl 检查后端服务是否就绪
        if curl -s -o /dev/null -w "%{http_code}" http://oj-backend-dev:8000/api/judge_server_heartbeat/ | grep -q "405\|403\|200"; then
            echo "Backend service is ready"
            return 0
        fi
        echo "Waiting for backend service... ($i/60)"
        sleep 3
    done
    echo "Backend service did not become ready in time"
    return 1
}

# 等待后端服务启动
if [ -z "$DISABLE_HEARTBEAT" ]; then
    wait_for_backend || echo "Warning: Could not connect to backend, continuing anyway..."
fi

CPU_CORE_NUM="$(nproc)"
if [ "$CPU_CORE_NUM" -lt 2 ]; then
    export WORKER_NUM=2;
else
    export WORKER_NUM="$CPU_CORE_NUM";
fi

exec .venv/bin/gunicorn server:app --workers $WORKER_NUM --threads 4 --error-logfile /log/gunicorn.log --bind 0.0.0.0:8080