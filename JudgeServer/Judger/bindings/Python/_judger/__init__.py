import json
import subprocess

UNLIMITED = -1
VERSION = 0x020101

RESULT_SUCCESS = 0
RESULT_WRONG_ANSWER = -1
RESULT_CPU_TIME_LIMIT_EXCEEDED = 1
RESULT_REAL_TIME_LIMIT_EXCEEDED = 2
RESULT_MEMORY_LIMIT_EXCEEDED = 3
RESULT_RUNTIME_ERROR = 4
RESULT_SYSTEM_ERROR = 5

ERROR_INVALID_CONFIG = -1
ERROR_FORK_FAILED = -2
ERROR_PTHREAD_FAILED = -3
ERROR_WAIT_FAILED = -4
ERROR_ROOT_REQUIRED = -5
ERROR_LOAD_SECCOMP_FAILED = -6
ERROR_SETRLIMIT_FAILED = -7
ERROR_DUP2_FAILED = -8
ERROR_SETUID_FAILED = -9
ERROR_EXECVE_FAILED = -10
ERROR_SPJ_ERROR = -11


def run(max_cpu_time,
        max_real_time,
        max_memory,
        max_stack,
        max_output_size,
        max_process_number,
        exe_path,
        input_path,
        output_path,
        error_path,
        args,
        env,
        log_path,
        seccomp_rule_name,
        uid,
        gid,
        memory_limit_check_only=0):
    str_list_vars = ["args", "env"]
    int_vars = ["max_cpu_time", "max_real_time",
                "max_memory", "max_stack", "max_output_size",
                "max_process_number", "uid", "gid", "memory_limit_check_only"]
    str_vars = ["exe_path", "input_path", "output_path", "error_path", "log_path"]

    proc_args = ["/usr/lib/judger/libjudger.so"]

    for var in str_list_vars:
        value = vars()[var]
        if not isinstance(value, list):
            raise ValueError("{} must be a list".format(var))
        for item in value:
            if not isinstance(item, str):
                raise ValueError("{} item must be a string".format(var))
            proc_args.append("--{}={}".format(var, item))

    for var in int_vars:
        value = vars()[var]
        if not isinstance(value, int):
            raise ValueError("{} must be a int".format(var))
        if value != UNLIMITED:
            proc_args.append("--{}={}".format(var, value))

    for var in str_vars:
        value = vars()[var]
        if not isinstance(value, str):
            raise ValueError("{} must be a string".format(var))
        proc_args.append("--{}={}".format(var, value))

    if not isinstance(seccomp_rule_name, str) and seccomp_rule_name is not None:
        raise ValueError("seccomp_rule_name must be a string or None")
    if seccomp_rule_name:
        proc_args.append("--seccomp_rule={}".format(seccomp_rule_name))

    print("Judger command:", " ".join(proc_args))  # 调试信息
    proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    print("Judger stdout:", repr(out))  # 调试信息
    print("Judger stderr:", repr(err))  # 调试信息
    print("Judger return code:", proc.returncode)  # 调试信息
    
    # 检查stderr中的错误信息
    if err:
        err_msg = err.decode('utf-8')
        print("Error output from judger:", err_msg)  # 调试信息
        # 不再直接抛出异常，而是继续处理
    
    # 检查返回码
    if proc.returncode != 0:
        print("Judger process exited with non-zero return code:", proc.returncode)
        
    if not out:
        # 如果没有输出，尝试从stderr获取信息
        if err:
            err_msg = err.decode('utf-8')
            # 如果stderr包含JSON格式的错误信息，就返回它
            try:
                error_result = json.loads(err_msg)
                return error_result
            except json.JSONDecodeError:
                # 如果不是JSON格式，构造一个错误结果
                return {
                    "result": RESULT_SYSTEM_ERROR,
                    "error": "Judger returned empty output. Stderr: " + err_msg,
                    "return_code": proc.returncode
                }
        else:
            # 如果stdout和stderr都为空
            return {
                "result": RESULT_SYSTEM_ERROR,
                "error": "Judger returned empty output with no error message",
                "return_code": proc.returncode
            }
    
    try:
        return json.loads(out.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError("Judger output is not valid JSON: {}".format(out.decode("utf-8"))) from e