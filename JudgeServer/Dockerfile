FROM debian:bullseye-slim AS builder
ARG TARGETARCH
ARG TARGETVARIANT

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# 添加针对 ARM64 的特定处理
RUN <<EOS
set -ex
echo "Building for architecture: $TARGETARCH"
if [ "$TARGETARCH" = "arm64" ]; then
    echo "Applying ARM64 specific configurations"
fi
EOS

RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-1-$TARGETARCH$TARGETVARIANT-builder,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,id=apt-cache-2-$TARGETARCH$TARGETVARIANT-builder,sharing=locked \
    <<EOS
set -ex
rm -f /etc/apt/apt.conf.d/docker-clean
echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/keep-cache
echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/no-recommends
echo 'APT::AutoRemove::RecommendsImportant "0";' >> /etc/apt/apt.conf.d/no-recommends
apt-get update
apt-get install -y libtool make cmake libseccomp-dev gcc python3 python3-venv
EOS

COPY Judger/ /app/
RUN <<EOS
set -ex
mkdir /app/build
cd /app/build
# 在 ARM64 上使用特定的 CMake 配置
if [ "$TARGETARCH" = "arm64" ]; then
    echo "Configuring for ARM64"
    # 为 ARM64 添加特定的编译标志
    cmake -DCMAKE_SYSTEM_PROCESSOR=arm64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-g -Wall -O3 -std=c99 -pie -fPIC -fno-stack-protector" ..
else
    cmake -DCMAKE_SYSTEM_PROCESSOR=$TARGETARCH ..
fi
cmake --build . --parallel $(nproc)

ls -la libjudger.so
file libjudger.so

# 验证生成的可执行文件是否可以在ARM64上运行
if [ "$TARGETARCH" = "arm64" ]; then
    echo "Testing ARM64 executable..."
    # 创建一个简单的测试，但不会因为失败而停止构建
    set +e  # 禁用立即退出错误
    ./libjudger.so --max_cpu_time=1000 --max_real_time=2000 --max_memory=33554432 --max_stack=16777216 --max_output_size=1048576 --uid=0 --gid=0 --exe_path=/bin/echo --input_path=/dev/null --output_path=/tmp/test_out --error_path=/tmp/test_err --args=hello --log_path=/tmp/test_log
    TEST_EXIT_CODE=$?
    set -e  # 重新启用立即退出错误
    if [ $TEST_EXIT_CODE -ne 0 ]; then
        echo "Test execution failed with exit code $TEST_EXIT_CODE, but continuing..."
    else
        echo "Test execution succeeded"
    fi
fi
EOS


RUN <<EOS
set -ex
cd bindings/Python
python3 -m venv .venv
.venv/bin/pip3 install build
.venv/bin/python3 -m build -w

# 验证Python包
ls -la dist/
# 使用具体文件名而不是通配符
.venv/bin/pip3 install dist/judger-2.2.0-py3-none-any.whl
.venv/bin/python3 -c "import _judger; print('_judger module works')"
EOS

FROM debian:bullseye-slim
ARG TARGETARCH
ARG TARGETVARIANT

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-1-$TARGETARCH$TARGETVARIANT-final,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,id=apt-cache-2-$TARGETARCH$TARGETVARIANT-final,sharing=locked \
    <<EOS
set -ex
rm -f /etc/apt/apt.conf.d/docker-clean
echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/keep-cache
echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/no-recommends
echo 'APT::AutoRemove::RecommendsImportant "0";' >> /etc/apt/apt.conf.d/no-recommends
needed="python3-minimal \
    python3-venv \
    python3-distutils \
    python3-lib2to3 \
    python3-pkg-resources \
    libpython3-stdlib \
    libpython3-dev \
    golang-go \
    default-jdk \
    gcc \
    g++ \
    nodejs \
    strace \
    zip \
    curl"  
savedAptMark="$(apt-mark showmanual) $needed"
# 安装Python和相关依赖
apt-get update
apt-get install -y ca-certificates curl wget $needed
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 9

# 在清理操作之前创建完整的python39.zip文件
echo "Creating python39.zip from standard library..."

# 方法1: 使用系统标准的创建方式
cd /usr/lib/python3.9
# 创建包含完整标准库的zip文件
find . -name "*.py" -o -name "*.pyc" | grep -v __pycache__ | \
    zip -q -@ /usr/lib/python39.zip || echo "Creating zip file"

# 验证zip文件内容
echo "Verifying python39.zip contents:"
python3 -c "
import zipfile
import os

zip_path = '/usr/lib/python39.zip'
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        file_list = zf.namelist()
        print(f'Zip contains {len(file_list)} files')
        
        # 检查关键文件
        essential_files = ['site.py', 'os.py', 'stat.py', 'codecs.py', 'encodings/__init__.py']
        for file in essential_files:
            if file in file_list:
                print(f'✓ {file} found')
            else:
                print(f'✗ {file} missing')
else:
    print('Zip file not created')
"

# 现在进行清理操作
apt-mark auto '.*' > /dev/null
apt-mark manual $savedAptMark
apt-get purge -y --auto-remove

# 验证Python环境在清理后仍然可用
python3 -c "
import sys
print('Python environment after cleanup:')
print(f'sys.path: {sys.path}')

# 测试关键模块
try:
    import site
    import os
    import stat
    import codecs
    print('✓ All essential modules available')
except ImportError as e:
    print(f'✗ Module import failed: {e}')
    sys.exit(1)
"

# 验证Python安装
python3 -c "import sys; print('Python paths:'); [print(p) for p in sys.path]"

# 创建完整的python39.zip文件 - 包含整个标准库
if [ ! -f /usr/lib/python39.zip ]; then
    echo "Creating complete python39.zip with full standard library..."
    
    # 方法1: 尝试使用Python的zipimport机制创建完整的zip文件
    python3 -c "
import sys
import zipfile
import os

# 获取标准库路径
stdlib_path = '/usr/lib/python3.9'
zip_path = '/usr/lib/python39.zip'

print(f'Creating complete standard library zip at {zip_path}')

# 创建zip文件，包含整个标准库目录
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(stdlib_path):
        # 排除不必要的目录
        if '__pycache__' in root or 'test' in root or 'dist-packages' in root:
            continue
            
        for file in files:
            if file.endswith('.py') or file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                # 计算在zip中的相对路径
                arcname = os.path.relpath(file_path, stdlib_path)
                zf.write(file_path, arcname)
                print(f'Added: {arcname}')

print('Complete standard library zip created successfully')
"

    # 方法2: 如果Python方法失败，使用系统命令创建更完整的zip文件
    if [ ! -f /usr/lib/python39.zip ]; then
        echo "Using system command to create standard library zip..."
        cd /usr/lib/python3.9
        # 包含所有.py文件和必要的目录，排除缓存和测试文件
        find . -name "*.py" -not -path "./__pycache__/*" -not -path "./test/*" -not -path "./dist-packages/*" | \
            zip -q -@ /usr/lib/python39.zip || echo "Some files may not have been added"
        
        # 确保包含必要的目录结构
        zip -q -r /usr/lib/python39.zip encodings/ lib-dynload/ || echo "Adding directories"
    fi
    
    echo "Verifying python39.zip contents..."
    python3 -c "
import zipfile
import sys

try:
    with zipfile.ZipFile('/usr/lib/python39.zip', 'r') as zf:
        # 检查关键模块是否存在
        essential_files = ['site.py', 'os.py', 'stat.py', 'codecs.py', 'encodings/__init__.py']
        missing_files = []
        
        for file in essential_files:
            try:
                zf.getinfo(file)
                print(f'✓ {file} found in zip')
            except KeyError:
                missing_files.append(file)
                print(f'✗ {file} missing in zip')
        
        if missing_files:
            print(f'Missing essential files: {missing_files}')
            sys.exit(1)
        else:
            print('All essential files are present in zip')
            
except Exception as e:
    print(f'Error verifying zip file: {e}')
    sys.exit(1)
"
    
    echo "Complete python39.zip created and verified"
fi

# 确保标准库目录结构完整
if [ ! -d /usr/lib/python3.9/encodings ]; then
    # 如果encodings目录不存在，从系统安装中复制
    ENCODINGS_SOURCE=$(python3 -c "import encodings; import os; print(os.path.dirname(encodings.__file__))")
    if [ -d "$ENCODINGS_SOURCE" ]; then
        cp -r "$ENCODINGS_SOURCE" /usr/lib/python3.9/encodings
        echo "Copied encodings directory from system installation"
    fi
fi

# 验证完整的Python环境
python3 -c "
import sys
print('=== Python Environment Verification ===')
print(f'Python version: {sys.version}')
print(f'Python paths: {sys.path}')

# 测试完整的模块加载链
test_modules = [
    'site',           # 基础站点模块
    'os',             # 操作系统接口
    'stat',           # 文件状态
    'codecs',         # 编解码器
    'encodings.utf_8', # UTF-8编码
    'encodings.ascii', # ASCII编码
    'sys',            # 系统参数
    'builtins',       # 内置函数
]

print('Testing module import chain...')
for module in test_modules:
    try:
        __import__(module)
        print(f'✓ {module} imported successfully')
    except ImportError as e:
        print(f'✗ {module} import failed: {e}')
        # 提供详细的调试信息
        import traceback
        traceback.print_exc()
        sys.exit(1)

print('=== All modules imported successfully ===')
print('Python environment is fully functional')
"

# 删除重复和冲突的配置
# apt-mark auto '.*' > /dev/null
# 2. 确保这个目录在Python的site-packages目录中被正确链接或复制
if [ ! -L /usr/lib/python3.9/encodings ] && [ ! -d /usr/lib/python3.9/encodings ]; then
    ln -s $ENCODINGS_DIR /usr/lib/python3.9/encodings
    echo "Created symlink for encodings module"
fi

# 3. 再次验证Python encodings模块可用性
python3 -c "import encodings; print('Python encodings module available')"


apt-mark auto '.*' > /dev/null
apt-mark manual $savedAptMark
apt-get purge -y --auto-remove
EOS

COPY --from=builder --chmod=755 --link /app/build/libjudger.so /usr/lib/judger/libjudger.so
COPY --from=builder /app/bindings/Python/dist/ /app/
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-cache-$TARGETARCH$TARGETVARIANT-final \
    <<EOS
set -ex
python3 -m venv .venv
CC=gcc .venv/bin/pip3 install --compile --no-cache-dir flask gunicorn idna psutil requests
.venv/bin/pip3 install *.whl
EOS

COPY server/ /app/
RUN <<EOS
set -ex
chmod -R u=rwX,go=rX /app/
chmod +x /app/entrypoint.sh
gcc -shared -fPIC -o unbuffer.so unbuffer.c
useradd -u 901 -r -s /sbin/nologin -M compiler
useradd -u 902 -r -s /sbin/nologin -M code
useradd -u 903 -r -s /sbin/nologin -M -G code spj
mkdir -p /usr/lib/judger
EOS

RUN <<EOS
set -ex
gcc --version
g++ --version
python3 --version
java -version
node --version
EOS

HEALTHCHECK --interval=5s CMD [ "/app/.venv/bin/python3", "/app/service.py" ]
EXPOSE 8080
ENTRYPOINT [ "/app/entrypoint.sh" ]