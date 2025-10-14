#include <stdio.h>
#include <seccomp.h>
#include <linux/audit.h>
#include <sys/syscall.h>
#include "../runner.h"

int arm64_seccomp_rules(struct config *_config) {
    scmp_filter_ctx ctx;
    
    ctx = seccomp_init(SCMP_ACT_ERRNO(1));  // 改为返回错误而不是直接杀死进程
    if (!ctx) {
        return LOAD_SECCOMP_FAILED;
    }

    // 添加 ARM64 专用规则 - 更全面的系统调用列表
    int allowed_syscalls[] = {
        SCMP_SYS(read), SCMP_SYS(write), SCMP_SYS(open), SCMP_SYS(close),
        SCMP_SYS(stat), SCMP_SYS(fstat), SCMP_SYS(lseek), SCMP_SYS(mmap),
        SCMP_SYS(mprotect), SCMP_SYS(munmap), SCMP_SYS(brk), SCMP_SYS(rt_sigaction),
        SCMP_SYS(rt_sigprocmask), SCMP_SYS(rt_sigreturn), SCMP_SYS(ioctl),
        SCMP_SYS(pread64), SCMP_SYS(pwrite64), SCMP_SYS(readv), SCMP_SYS(writev),
        SCMP_SYS(access), SCMP_SYS(pipe), SCMP_SYS(select), SCMP_SYS(sched_yield),
        SCMP_SYS(mremap), SCMP_SYS(msync), SCMP_SYS(mincore), SCMP_SYS(madvise),
        SCMP_SYS(shmget), SCMP_SYS(shmat), SCMP_SYS(shmctl), SCMP_SYS(dup),
        SCMP_SYS(dup2), SCMP_SYS(pause), SCMP_SYS(nanosleep), SCMP_SYS(getitimer),
        SCMP_SYS(setitimer), SCMP_SYS(getpid), SCMP_SYS(sendfile), SCMP_SYS(socket),
        SCMP_SYS(connect), SCMP_SYS(accept), SCMP_SYS(sendto), SCMP_SYS(recvfrom),
        SCMP_SYS(bind), SCMP_SYS(listen), SCMP_SYS(shutdown), SCMP_SYS(getsockopt),
        SCMP_SYS(setsockopt), SCMP_SYS(getsockname), SCMP_SYS(getpeername),
        SCMP_SYS(socketpair), SCMP_SYS(clone), SCMP_SYS(fork), SCMP_SYS(vfork),
        SCMP_SYS(execve), SCMP_SYS(exit), SCMP_SYS(exit_group), SCMP_SYS(wait4), SCMP_SYS(kill),
        SCMP_SYS(uname), SCMP_SYS(fcntl), SCMP_SYS(flock), SCMP_SYS(fsync),
        SCMP_SYS(fdatasync), SCMP_SYS(ftruncate), SCMP_SYS(getdents), SCMP_SYS(getcwd),
        SCMP_SYS(chdir), SCMP_SYS(fchdir), SCMP_SYS(rename), SCMP_SYS(mkdir),
        SCMP_SYS(rmdir), SCMP_SYS(creat), SCMP_SYS(link), SCMP_SYS(unlink),
        SCMP_SYS(symlink), SCMP_SYS(readlink), SCMP_SYS(chmod), SCMP_SYS(fchmod),
        SCMP_SYS(chown), SCMP_SYS(fchown), SCMP_SYS(lchown), SCMP_SYS(umask),
        SCMP_SYS(gettimeofday), SCMP_SYS(getrlimit), SCMP_SYS(getrusage),
        SCMP_SYS(sysinfo), SCMP_SYS(times), SCMP_SYS(ptrace), SCMP_SYS(getuid),
        SCMP_SYS(syslog), SCMP_SYS(getgid), SCMP_SYS(setuid), SCMP_SYS(setgid),
        SCMP_SYS(geteuid), SCMP_SYS(getegid), SCMP_SYS(setpgid), SCMP_SYS(getppid),
        SCMP_SYS(getpgrp), SCMP_SYS(setsid), SCMP_SYS(setreuid), SCMP_SYS(setregid),
        SCMP_SYS(getgroups), SCMP_SYS(setgroups), SCMP_SYS(setresuid),
        SCMP_SYS(getresuid), SCMP_SYS(setresgid), SCMP_SYS(getresgid),
        SCMP_SYS(getpgid), SCMP_SYS(setfsuid), SCMP_SYS(setfsgid), SCMP_SYS(getsid),
        SCMP_SYS(capget), SCMP_SYS(capset), SCMP_SYS(rt_sigpending),
        SCMP_SYS(rt_sigtimedwait), SCMP_SYS(rt_sigqueueinfo), SCMP_SYS(rt_sigsuspend),
        SCMP_SYS(sigaltstack), SCMP_SYS(utime), SCMP_SYS(mknod), SCMP_SYS(uselib),
        SCMP_SYS(personality), SCMP_SYS(ustat), SCMP_SYS(statfs), SCMP_SYS(fstatfs),
        SCMP_SYS(sysfs), SCMP_SYS(getpriority), SCMP_SYS(setpriority),
        SCMP_SYS(sched_setparam), SCMP_SYS(sched_getparam), SCMP_SYS(sched_setscheduler),
        SCMP_SYS(sched_getscheduler), SCMP_SYS(sched_get_priority_max),
        SCMP_SYS(sched_get_priority_min), SCMP_SYS(sched_rr_get_interval),
        SCMP_SYS(mlock), SCMP_SYS(munlock), SCMP_SYS(mlockall), SCMP_SYS(munlockall),
        SCMP_SYS(vhangup), SCMP_SYS(prctl), SCMP_SYS(adjtimex), SCMP_SYS(settimeofday),
        SCMP_SYS(gettid), SCMP_SYS(readahead), SCMP_SYS(setxattr), SCMP_SYS(lsetxattr),
        SCMP_SYS(fsetxattr), SCMP_SYS(getxattr), SCMP_SYS(lgetxattr), SCMP_SYS(fgetxattr),
        SCMP_SYS(listxattr), SCMP_SYS(llistxattr), SCMP_SYS(flistxattr),
        SCMP_SYS(removexattr), SCMP_SYS(lremovexattr), SCMP_SYS(fremovexattr),
        SCMP_SYS(tkill), SCMP_SYS(time), SCMP_SYS(futex), SCMP_SYS(sched_setaffinity),
        SCMP_SYS(sched_getaffinity), SCMP_SYS(epoll_create), SCMP_SYS(epoll_ctl),
        SCMP_SYS(epoll_wait), SCMP_SYS(epoll_pwait), SCMP_SYS(semget), SCMP_SYS(semctl), 
        SCMP_SYS(semop), SCMP_SYS(semctl), SCMP_SYS(msgget), SCMP_SYS(msgsnd), 
        SCMP_SYS(msgrcv), SCMP_SYS(msgctl), SCMP_SYS(shmdt), SCMP_SYS(fadvise64),
        SCMP_SYS(timer_create), SCMP_SYS(timer_settime), SCMP_SYS(timer_gettime),
        SCMP_SYS(timer_getoverrun), SCMP_SYS(timer_delete), SCMP_SYS(clock_settime),
        SCMP_SYS(clock_gettime), SCMP_SYS(clock_getres), SCMP_SYS(clock_nanosleep),
        SCMP_SYS(utimes), SCMP_SYS(mq_open), SCMP_SYS(mq_unlink), SCMP_SYS(mq_timedsend),
        SCMP_SYS(mq_timedreceive), SCMP_SYS(mq_notify), SCMP_SYS(mq_getsetattr),
        SCMP_SYS(kexec_load), SCMP_SYS(waitid), SCMP_SYS(add_key), SCMP_SYS(request_key),
        SCMP_SYS(keyctl), SCMP_SYS(ioprio_set), SCMP_SYS(ioprio_get), SCMP_SYS(inotify_init),
        SCMP_SYS(inotify_add_watch), SCMP_SYS(inotify_rm_watch), SCMP_SYS(migrate_pages),
        SCMP_SYS(openat), SCMP_SYS(mkdirat), SCMP_SYS(mknodat), SCMP_SYS(fchownat),
        SCMP_SYS(futimesat), SCMP_SYS(newfstatat), SCMP_SYS(unlinkat), SCMP_SYS(renameat),
        SCMP_SYS(linkat), SCMP_SYS(symlinkat), SCMP_SYS(readlinkat), SCMP_SYS(fchmodat),
        SCMP_SYS(faccessat), SCMP_SYS(pselect6), SCMP_SYS(ppoll), SCMP_SYS(set_robust_list),
        SCMP_SYS(get_robust_list), SCMP_SYS(splice), SCMP_SYS(tee), SCMP_SYS(sync_file_range),
        SCMP_SYS(vmsplice), SCMP_SYS(move_pages), SCMP_SYS(utimensat), SCMP_SYS(epoll_pwait),
        SCMP_SYS(signalfd), SCMP_SYS(timerfd_create), SCMP_SYS(eventfd), SCMP_SYS(fallocate),
        SCMP_SYS(timerfd_settime), SCMP_SYS(timerfd_gettime), SCMP_SYS(accept4), 
        SCMP_SYS(signalfd4), SCMP_SYS(eventfd2), SCMP_SYS(epoll_create1), SCMP_SYS(dup3),
        SCMP_SYS(pipe2), SCMP_SYS(inotify_init1), SCMP_SYS(preadv), SCMP_SYS(pwritev),
        SCMP_SYS(rt_tgsigqueueinfo), SCMP_SYS(fanotify_init), SCMP_SYS(fanotify_mark),
        SCMP_SYS(prlimit64), SCMP_SYS(name_to_handle_at), SCMP_SYS(open_by_handle_at),
        SCMP_SYS(clock_adjtime), SCMP_SYS(syncfs), SCMP_SYS(sendmmsg), SCMP_SYS(setns),
        SCMP_SYS(getcpu), SCMP_SYS(process_vm_readv), SCMP_SYS(process_vm_writev),
        SCMP_SYS(kcmp), SCMP_SYS(finit_module), SCMP_SYS(sched_setattr), 
        SCMP_SYS(sched_getattr), SCMP_SYS(renameat2), SCMP_SYS(seccomp),
        SCMP_SYS(getrandom), SCMP_SYS(memfd_create), SCMP_SYS(kexec_file_load),
        SCMP_SYS(bpf), SCMP_SYS(execveat), SCMP_SYS(userfaultfd), SCMP_SYS(membarrier),
        SCMP_SYS(mlock2), SCMP_SYS(copy_file_range), SCMP_SYS(preadv2), SCMP_SYS(pwritev2),
        SCMP_SYS(pkey_mprotect), SCMP_SYS(pkey_alloc), SCMP_SYS(pkey_free),
        SCMP_SYS(statx), SCMP_SYS(io_pgetevents), SCMP_SYS(rseq), SCMP_SYS(kexec_file_load)
    };

    int num_syscalls = sizeof(allowed_syscalls) / sizeof(allowed_syscalls[0]);
    
    for (int i = 0; i < num_syscalls; i++) {
        if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, allowed_syscalls[i], 0) != 0) {
            seccomp_release(ctx);
            return LOAD_SECCOMP_FAILED;
        }
    }

    // 加载 seccomp 过滤器
    if (seccomp_load(ctx) != 0) {
        seccomp_release(ctx);
        return LOAD_SECCOMP_FAILED;
    }
    
    seccomp_release(ctx);
    return SUCCESS;
}