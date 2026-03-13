import sys
import resource

def verify_system_constraints():
    """
    在程序启动时执行，确保环境符合生产标准
    """
    # 1. 检查打开文件描述符限制
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft_limit < 500:
        logging.warning(f"File descriptor limit {soft_limit} is too low. Potential Merge Failure.")
        
    # 2. 检查可用磁盘空间
    total, used, free = shutil.disk_usage("/")
    if free < 150 * 1024 * 1024 * 1024: # 150GB 冗余
        raise OSError("Insufficient disk space for external merge sort.")
        
    # 3. 内存锁定策略
    # 在 Linux 上锁定进程内存以防被 OS Swap 交换出去，导致性能暴跌
    try:
        resource.mlockall(resource.MCL_CURRENT | resource.MCL_FUTURE)
    except AttributeError:
        pass # 非 Linux 系统跳过
