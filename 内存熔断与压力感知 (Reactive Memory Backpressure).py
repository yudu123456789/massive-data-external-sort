import psutil
import time
import threading

class BackpressureMonitor:
    def __init__(self, limit_mb: int = 1800):
        self.limit_mb = limit_mb
        self.paused = threading.Event()
        self.paused.set() # 初始状态为运行
        
    def check_and_wait(self):
        """插入在读取循环中，实时感知内存压力"""
        while not self.paused.is_set():
            time.sleep(0.5)
            
        mem_usage = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        if mem_usage > self.limit_mb * 0.8:
            logging.warning("Memory pressure high, triggering backpressure...")
            self.paused.clear() # 暂停生产者
            
        if mem_usage < self.limit_mb * 0.5:
            self.paused.set() # 恢复生产者
