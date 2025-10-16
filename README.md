.
├── JudgeServer/              # 判题服务器
│   ├── Judger/               # 判题核心组件
│   ├── client/               # 客户端SDK
│   ├── server/               # 服务器端实现
│   └── tests/                # 测试用例
├── Judger/                   # 判题核心引擎
│   ├── bindings/             # 多语言绑定
│   ├── demo/                 # 示例程序
│   ├── src/                  # 核心源码
│   └── tests/                # 测试用例
├── OnlineJudge/              # 后端管理系统 (Django)
│   ├── account/              # 用户账户模块
│   ├── announcement/         # 公告模块
│   ├── contest/              # 竞赛模块
│   ├── judge/                # 判题模块
│   ├── problem/              # 题目模块
│   ├── submission/           # 提交模块
│   └── utils/                # 工具模块
├── OnlineJudgeDeploy/        # Docker 部署配置
│   ├── data/                 # 数据持久化目录
│   └── docker-compose.yml    # Docker 编排文件
├── OnlineJudgeFE/            # 前端界面 (Vue.js)
│   ├── src/                  # 源代码
│   ├── build/                # 构建配置
│   └── package.json          # 依赖配置
└── README.md                 # 项目说明文件


默认管理员账户：
用户名: root
密码: rootroot

前端访问地址：http://localhost:8081 

如果 Docker 构建失败：
清理构建缓存: docker builder prune -a
重新构建: docker-compose build --no-cache
检查网络连接和依赖源