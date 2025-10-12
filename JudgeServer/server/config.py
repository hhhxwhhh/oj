import os
import pwd

import grp

JUDGER_WORKSPACE_BASE = "/judger/run"
LOG_BASE = "/log"

COMPILER_LOG_PATH = os.path.join(LOG_BASE, "compile.log")
JUDGER_RUN_LOG_PATH = os.path.join(LOG_BASE, "judger.log")
SERVER_LOG_PATH = os.path.join(LOG_BASE, "judge_server.log")

RUN_USER_UID = pwd.getpwnam("code").pw_uid
RUN_GROUP_GID = grp.getgrnam("code").gr_gid

COMPILER_USER_UID = pwd.getpwnam("compiler").pw_uid
COMPILER_GROUP_GID = grp.getgrnam("compiler").gr_gid

SPJ_USER_UID = pwd.getpwnam("spj").pw_uid
SPJ_GROUP_GID = grp.getgrnam("spj").gr_gid

TEST_CASE_DIR = "/test_case"
SPJ_SRC_DIR = "/judger/spj"
SPJ_EXE_DIR = "/judger/spj"

# 从环境变量获取Token，默认为开发Token
token = os.environ.get("TOKEN", "5a1b3c9f4e7d8a2b6c0e1f5d9a3b7c4e") #测试用的token 无任何实际意义
