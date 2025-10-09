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

# 在根目录创建符号链接，确保任何相对路径引用都能找到模块
echo "Creating symbolic links in root directory..."
cd /
ln -sf /OJ_FE/simple-module simple-module
ln -sf /OJ_FE/simple-hotkeys simple-hotkeys
ln -sf /OJ_FE/simple-uploader simple-uploader
cd $base

# 在项目根目录创建 node_modules 目录（如果不存在）
mkdir -p /OJ_FE/node_modules

# 直接在 node_modules 中创建符号链接
echo "Creating direct symbolic links in node_modules..."
ln -sf /OJ_FE/simple-module /OJ_FE/node_modules/simple-module
ln -sf /OJ_FE/simple-hotkeys /OJ_FE/node_modules/simple-hotkeys
ln -sf /OJ_FE/simple-uploader /OJ_FE/node_modules/simple-uploader

# 为嵌套依赖也创建符号链接
echo "Creating symbolic links for nested dependencies..."
mkdir -p /OJ_FE/node_modules/tar-simditor-markdown/node_modules
ln -sf /OJ_FE/simple-module /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-module
ln -sf /OJ_FE/simple-hotkeys /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-hotkeys
ln -sf /OJ_FE/simple-uploader /OJ_FE/node_modules/tar-simditor-markdown/node_modules/simple-uploader

# 修改 webpack 配置，增强模块解析能力
echo "Enhancing webpack module resolution..."
cd /OJ_FE/build

# 备份原始文件
cp webpack.base.conf.js webpack.base.conf.js.bak

# 使用更简单的 sed 命令修改 webpack 配置
# 在 resolve: { 后面添加 modules 配置
sed -i.bak '/resolve: {/a\
    modules: [path.resolve(__dirname, "../node_modules"), path.resolve(__dirname, "../"), "node_modules"],' webpack.base.conf.js

# 在 alias: { 后面添加别名配置
sed -i.bak '/alias: {/a\
      "simple-module": path.resolve(__dirname, "../simple-module"),\
      "simple-hotkeys": path.resolve(__dirname, "../simple-hotkeys"),\
      "simple-uploader": path.resolve(__dirname, "../simple-uploader"),' webpack.base.conf.js

# 返回工作目录
cd /OJ_FE

# 直接修改 tar-simditor 源代码，使用模块名而不是路径
echo "Patching tar-simditor source files with module names..."
# 备份并修改主 tar-simditor
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

# 创建一个临时的 webpack 配置文件来覆盖默认配置
echo "Creating temporary webpack config override..."
cat > /OJ_FE/webpack.config.override.js << 'EOF'
const path = require('path');

module.exports = {
  resolve: {
    modules: [
      path.resolve(__dirname, "node_modules"),
      path.resolve(__dirname, "."),
      "node_modules"
    ],
    alias: {
      "simple-module": path.resolve(__dirname, "simple-module"),
      "simple-hotkeys": path.resolve(__dirname, "simple-hotkeys"),
      "simple-uploader": path.resolve(__dirname, "simple-uploader")
    }
  }
};
EOF

echo "Building vendor DLL if needed..."
build_vendor_dll

echo "Running build process..."
# 移除 NODE_OPTIONS 以避免 OpenSSL 错误
if [ -f package.json.bak ]; then
  rm package.json.bak
fi
sed -i.bak 's/NODE_OPTIONS=--openssl-legacy-provider //g' package.json

# 在运行时进行构建，使用 NODE_PATH 环境变量增强模块解析
NODE_PATH="/OJ_FE/node_modules:/OJ_FE" npm run build
if [ $? -ne 0 ]; then
    echo "Build error, please check node version and package.json"
    # 恢复原始文件以便下次重试
    if [ -f /OJ_FE/build/webpack.base.conf.js.bak ]; then
      mv /OJ_FE/build/webpack.base.conf.js.bak /OJ_FE/build/webpack.base.conf.js
    fi
    # 恢复 tar-simditor 文件
    if [ -f /OJ_FE/node_modules/tar-simditor/lib/simditor.js.bak ]; then
      mv /OJ_FE/node_modules/tar-simditor/lib/simditor.js.bak /OJ_FE/node_modules/tar-simditor/lib/simditor.js
    fi
    if [ -f /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js.bak ]; then
      mv /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js.bak /OJ_FE/node_modules/tar-simditor-markdown/node_modules/tar-simditor/lib/simditor.js
    fi
    exit 1
fi

echo "Build completed successfully"

# 检查 dist 目录是否存在
if [ ! -d "/OJ_FE/dist" ]; then
    echo "ERROR: dist directory not found after build"
    exit 1
fi

echo "Starting nginx..."
exec nginx -c /OJ_FE/deploy/nginx.conf