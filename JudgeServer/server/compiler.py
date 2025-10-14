import _judger
import json
import os
import time 
import hashlib
import shutil
from config import COMPILER_LOG_PATH, COMPILER_USER_UID, COMPILER_GROUP_GID
from exception import CompileError
import shlex


class Compiler(object):
    def compile(self, compile_config, src_path, output_dir):
        # 强制所有Python相关命令使用系统Python而不是虚拟环境Python
        if "python" in compile_config.get("compile_command", "").lower():
            compile_config["compile_command"] = compile_config["compile_command"].replace(
                "/app/.venv/bin/python3", "/usr/bin/python3")
            print(f"Updated compile command to use system Python: {compile_config['compile_command']}")
        
        command = compile_config["compile_command"]
        exe_path = os.path.join(output_dir, compile_config["exe_name"])
        command = command.format(src_path=src_path, exe_dir=output_dir, exe_path=exe_path)
        compiler_out = os.path.join(output_dir, "compiler.out")
        _command = shlex.split(command)
        
        # 确保使用系统Python
        if _command and "/app/.venv/bin/python3" in _command[0]:
            _command[0] = "/usr/bin/python3"
            print(f"Forced Python path to system Python: {_command[0]}")
        print("=" * 60)
        print("COMPILER DEBUG INFO")
        print("=" * 60)
        print(f"Compile config: {json.dumps(compile_config, indent=2)}")
        print(f"Source path: {src_path}")
        print(f"Output directory: {output_dir}")
        print(f"Executable path: {exe_path}")
        print(f"Command: {command}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Final command: {' '.join(_command)}")
        
        # 检查源文件是否存在
        if os.path.exists(src_path):
            print(f"Source file exists, size: {os.path.getsize(src_path)} bytes")
            # 显示源文件内容
            with open(src_path, 'r', encoding='utf-8') as f:
                print("Source file content:")
                for i, line in enumerate(f):
                    if i >= 20:  # 显示前20行
                        print("  ...")
                        break
                    print(f"  {i+1:2d}: {line.rstrip()}")
        else:
            print("ERROR: Source file does not exist!")
            raise CompileError(f"Source file does not exist: {src_path}")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        os.chdir(output_dir)
        
        # 设置正确的环境变量以确保Python能在虚拟环境中正常工作
        env = compile_config.get("env", [])
        env.append("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
        env.append("LANG=C.UTF-8")
        env.append("LC_ALL=C.UTF-8")
        env.append("PYTHONNOUSERSITE=1")
        env.append("PYTHONUNBUFFERED=1")
        env.append("PYTHONHOME=/usr")
        env.append("PYTHONSAFEPATH=1")
        
        # 重要：不设置PYTHONNOZIPIMPORT=1，允许Python正常加载zip文件
        # 重要：不设置PYTHONPATH，让Python使用默认的sys.path配置
        
        # 完全移除运行时修复逻辑
        print(f"Environment variables: {env}")
        print(f"Command split into args: {_command}")
        
        # 检查编译器是否存在
        if not os.path.exists(_command[0]):
            print(f"ERROR: Compiler does not exist: {_command[0]}")
            raise CompileError(f"Compiler does not exist: {_command[0]}")
            
        print(f"Final command: {_command}")
        
        # 检测是否在ARM64架构上
        import platform
        is_arm64 = platform.machine() in ['aarch64', 'arm64']
        
        # 使用 root 权限进行编译
        print("Starting compilation with _judger.run...")
        result = _judger.run(max_cpu_time=compile_config["max_cpu_time"],
                             max_real_time=compile_config["max_real_time"],
                             max_memory=compile_config["max_memory"],
                             max_stack=128 * 1024 * 1024,
                             max_output_size=20 * 1024 * 1024,
                             max_process_number=_judger.UNLIMITED,
                             exe_path=_command[0],
                             input_path=src_path,
                             output_path=compiler_out,
                             error_path=compiler_out,
                             args=_command[1::],
                             env=env,
                             log_path=COMPILER_LOG_PATH,
                             # 如果是ARM64架构，使用ARM64 seccomp规则
                             seccomp_rule_name="arm64" if is_arm64 else None,
                             uid=0,    # 使用 root UID
                             gid=0)    # 使用 root GID

        
        print("Compiler command:", command)
        print("Compiler result:", json.dumps(result, indent=2))

        if result["result"] != _judger.RESULT_SUCCESS:
            error_message = "编译器运行时错误"
            
            # 添加详细调试信息
            error_message += f"\n• 执行命令: {command}"
            error_message += f"\n• 工作目录: {os.getcwd()}"
            error_message += f"\n• 环境变量: {env}"

            # 保留错误输出文件
            if os.path.exists(compiler_out):
                shutil.copy(compiler_out, f"/log/compiler_error_{time.time()}.log")

            # 添加系统调用追踪
            if result["result"] == _judger.RESULT_SYSTEM_ERROR:
                error_message += "\n\n系统调用追踪："
                error_message += f"\n• 最后系统调用: {result.get('last_syscall', '未知')}"
                error_message += f"\n• 退出信号: {result.get('signal', '未知')}"

            # 保存错误上下文
            try:
                with open(f"/log/error_ctx_{time.time()}.json", "w") as f:
                    json.dump({
                        "compile_config": compile_config,
                        "src_md5": hashlib.md5(open(src_path,"rb").read()).hexdigest()
                    }, f)
            except Exception as e:
                print(f"Failed to save error context: {e}")

            # 添加容器内调试命令
            error_message += "\n\n调试命令："
            error_message += "\ndocker exec -it oj-judge-dev cat /log/strace.log | tail -n 50"
            error_message += "\ndocker exec -it oj-judge-dev ls -l /judger/run"

            # 根据结果代码提供更具体的错误信息
            result_messages = {
                _judger.RESULT_WRONG_ANSWER: "Wrong Answer",
                _judger.RESULT_CPU_TIME_LIMIT_EXCEEDED: "CPU Time Limit Exceeded",
                _judger.RESULT_REAL_TIME_LIMIT_EXCEEDED: "Real Time Limit Exceeded",
                _judger.RESULT_MEMORY_LIMIT_EXCEEDED: "Memory Limit Exceeded",
                _judger.RESULT_RUNTIME_ERROR: "Runtime Error",
                _judger.RESULT_SYSTEM_ERROR: "System Error"
            }
            
            if result["result"] in result_messages:
                error_message += f" ({result_messages[result['result']]})"
            
            error_message += f", info: {json.dumps(result, indent=2)}"
            
            # 检查编译器输出文件
            if os.path.exists(compiler_out):
                try:
                    with open(compiler_out, encoding="utf-8") as f:
                        error = f.read().strip()
                        print("Compiler output file content:", error)
                        # 不删除输出文件，以便调试
                        if error:
                            error_message += f"\nCompiler output: {error}"
                except Exception as e:
                    error_message += f"\nError reading compiler output: {e}"
            else:
                print("No compiler output file found")
                error_message += "\nNo compiler output file generated"
                
            print(f"Final error message: {error_message}")
            raise CompileError(error_message)
        else:
            print(f"Compilation successful, executable at: {exe_path}")
            
            # 检查可执行文件是否创建成功
            if os.path.exists(exe_path):
                print(f"Executable file created successfully, size: {os.path.getsize(exe_path)} bytes")
            else:
                print("WARNING: Executable file not found after compilation")
                
            # 显示编译器输出（如果有）
            if os.path.exists(compiler_out):
                with open(compiler_out, encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        print("Compiler output (success):", content)
                # 成功时删除输出文件
                os.remove(compiler_out)
                
            print("=" * 60)
            print("END COMPILER DEBUG INFO")
            print("=" * 60)
            return exe_path