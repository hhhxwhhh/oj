#!/bin/sh

base=/OJ_FE

build_vendor_dll()
{
  if [ ! -e "${base}/build/vendor-manifest.json" ]
  then
      echo "Building vendor DLL..."
      npm run build:dll
      if [ $? -ne 0 ]; then
          echo "Failed to build vendor DLL"
          exit 1
      fi
  fi
}

cd $base

echo "Starting frontend build process..."

# 删除 package-lock.json 和清理 npm 缓存
echo "Removing package-lock.json and cleaning npm cache..."
rm -f package-lock.json
npm cache clean --force || true

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
  echo "ERROR: node_modules not found. Dependencies must be installed during Docker build."
  exit 1
fi

echo "Dependencies already installed during Docker build, skipping dependency installation..."

# 设置 git 提交哈希环境变量，避免构建错误
export COMMIT_ID="not-a-git-repo"

# 修复 simple-uploader 模块，避免构建错误
echo "Fixing simple-uploader module..."
cd /OJ_FE/simple-uploader
# 备份原始 package.json
cp package.json package.json.bak
# 移除 phantomjs 依赖，避免构建错误
sed -i.bak 's|"phantomjs": "^1.9.7"||' package.json

# 确保 lib 目录存在并包含正确的文件
if [ ! -d "/OJ_FE/simple-uploader/lib" ]; then
  echo "Creating lib directory with symbolic links..."
  mkdir -p /OJ_FE/simple-uploader/lib
fi

# 创建 uploader.js 文件的符号链接
if [ ! -f "/OJ_FE/simple-uploader/lib/uploader.js" ]; then
  ln -sf /OJ_FE/simple-uploader/dist/uploader.js /OJ_FE/simple-uploader/lib/uploader.js
fi

# 返回主目录
cd $base

# 修复 simple-hotkeys 模块，添加缺失的 main 字段
echo "Fixing simple-hotkeys module..."
cd /OJ_FE/simple-hotkeys
# 备份原始 package.json
cp package.json package.json.bak
# 添加 main 字段
sed -i.bak 's|"bugs": {|"main": "lib/hotkeys.js",\n  "bugs": {|' package.json

# 返回主目录
cd $base

# 删除无效的符号链接（使用 -f 参数忽略错误）
echo "Removing invalid symbolic links..."
rm -f /OJ_FE/node_modules/simple-module
rm -f /OJ_FE/node_modules/simple-hotkeys
rm -f /OJ_FE/node_modules/simple-uploader

# 创建正确的符号链接
echo "Creating correct symbolic links..."
ln -sf /OJ_FE/simple-module /OJ_FE/node_modules/simple-module
ln -sf /OJ_FE/simple-hotkeys /OJ_FE/node_modules/simple-hotkeys
ln -sf /OJ_FE/simple-uploader /OJ_FE/node_modules/simple-uploader

# 为嵌套依赖也创建符号链接
echo "Creating symbolic links for nested dependencies..."
# 确保目录存在
mkdir -p /OJ_FE/node_modules/tar-simditor-markdown/node_modules

# 删除可能存在的无效链接（如果是目录则删除整个目录）
rm -rf /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-module
rm -rf /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-hotkeys
rm -rf /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-uploader

# 创建嵌套依赖的符号链接
ln -sf /OJ_FE/simple-module /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-module
ln -sf /OJ_FE/simple-hotkeys /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-hotkeys
ln -sf /OJ_FE/simple-uploader /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-uploader

# 修改 webpack 配置，增强模块解析能力
echo "Enhancing webpack module resolution..."
cd /OJ_FE/build

# 备份原始文件
cp webpack.base.conf.js webpack.base.conf.js.bak

# 使用更简单的 sed 命令修改 webpack 配置
# 在 resolve 部分添加 modules 配置
sed -i.bak '/resolve: {/a\
    modules: [path.resolve(__dirname, "../node_modules"), path.resolve(__dirname, "../"), "node_modules"],' webpack.base.conf.js

# 在 alias 部分添加别名配置
sed -i.bak '/alias: {/a\
      "simple-module": path.resolve(__dirname, "../simple-module"),\
      "simple-hotkeys": path.resolve(__dirname, "../simple-hotkeys"),\
      "simple-uploader": path.resolve(__dirname, "../simple-uploader"),' webpack.base.conf.js

# 返回工作目录
cd /OJ_FE

# 直接修改 tar-simditor 源代码，使用模块名而不是路径
echo "Patching tar-simditor source files..."
# 修改主 tar-simditor
if [ -f "/OJ_FE/node_modules/tar-simditor/lib/simditor.js" ]; then
  cp /OJ_FE/node_modules/tar-simditor/lib/simditor.js /OJ_FE/node_modules/tar-simditor/lib/simditor.js.bak
  sed -i.bak 's|"../../simple-module"|"simple-module"|g' /OJ_FE/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|"../../simple-hotkeys"|"simple-hotkeys"|g' /OJ_FE/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|"../../simple-uploader"|"simple-uploader"|g' /OJ_FE/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|require("../../simple-module")|require("simple-module")|g' /OJ_FE/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|require("../../simple-hotkeys")|require("simple-hotkeys")|g' /OJ_FE/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|require("../../simple-uploader")|require("simple-uploader")|g' /OJ_FE/node_modules/tar-simditor/lib/simditor.js
fi

# 修改嵌套的 tar-simditor
if [ -f "/OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js" ]; then
  cp /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js.bak
  sed -i.bak 's|"../../simple-module"|"simple-module"|g' /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|"../../simple-hotkeys"|"simple-hotkeys"|g' /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|"../../simple-uploader"|"simple-uploader"|g' /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|require("../../simple-module")|require("simple-module")|g' /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|require("../../simple-hotkeys")|require("simple-hotkeys")|g' /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
  sed -i.bak 's|require("../../simple-uploader")|require("simple-uploader")|g' /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
fi

echo "Building vendor DLL if needed..."
build_vendor_dll

echo "Running build process..."
# 移除 NODE_OPTIONS 以避免 OpenSSL 错误
if [ -f package.json.bak ]; then
  rm package.json.bak
fi
sed -i.bak 's/NODE_OPTIONS=--openssl-legacy-provider //g' package.json

# 在运行时进行构建，使用增强的模块解析
NODE_PATH="/OJ_FE/node_modules:/OJ_FE:/node_modules" npm run build
if [ $? -ne 0 ]; then
    echo "Build error, please check node version and package.json"
    # 恢复原始文件以便下次重试
    if [ -f /OJ_FE/build/webpack.base.conf.js.bak ]; then
      mv /OJ_FE/build/webpack.base.conf.js.bak /OJ_FE/build/webpack.base.conf.js
    fi
    # 恢复 simple-uploader 和 simple-hotkeys 的 package.json
    if [ -f /OJ_FE/simple-uploader/package.json.bak ]; then
      mv /OJ_FE/simple-uploader/package.json.bak /OJ_FE/simple-uploader/package.json
    fi
    if [ -f /OJ_FE/simple-hotkeys/package.json.bak ]; then
      mv /OJ_FE/simple-hotkeys/package.json.bak /OJ_FE/simple-hotkeys/package.json
    fi
    exit 1
fi

echo "Build completed successfully"

# 检查 dist 目录是否存在
if [ ! -d "/OJ_FE/dist" ]; then
    echo "ERROR: dist directory not found after build"
    exit 1
fi

# 修复 nginx 配置文件
echo "Fixing nginx configuration..."
cd /OJ_FE/deploy
# 备份原始 nginx 配置
cp nginx.conf nginx.conf.bak

# 直接修改 proxy_pass 指令，使用 IP 地址而不是 upstream 名称
sed -i.bak 's|proxy_pass http://oj-backend-dev:8000;|proxy_pass http://127.0.0.1:8000;|g' nginx.conf

echo "Starting nginx..."
exec nginx -c /OJ_FE/deploy/nginx.conf