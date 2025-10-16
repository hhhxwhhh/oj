# OnlineJudge 部署与测试

本项目是基于青岛大学 OnlineJudge 系统的完整部署和测试环境。系统包含前端、后端、判题服务器等多个组件。

## 项目结构

## 主要功能

- 在线代码判题系统
- 支持多种编程语言（C/C++、Java、Python等）
- 竞赛和练习模式
- 用户权限管理
- 题库管理
- 实时排名系统

## 部署说明

### 环境要求

- Docker & Docker Compose
- 至少 4GB 内存
- Linux 或 macOS 系统（推荐 Ubuntu 18.04+）

### 部署步骤
克隆项目代码：
git clone https://github.com/hhhxwhhh/oj.git

默认管理员账户：
用户名: root
密码: rootroot

前端访问地址：http://localhost:8081 


如果 Docker 构建失败：
清理构建缓存: docker builder prune -a
重新构建: docker-compose build --no-cache
检查网络连接和依赖源