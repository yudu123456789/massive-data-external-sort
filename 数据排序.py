import os
import mmap
import heapq
import threading
import shutil
import logging
import tempfile
import psutil
import time
from typing import List, Generator, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SortConfig:
    MAX_MEMORY_MB = 1800
    CHUNK_SIZE_BYTES = 500 * 1024 * 1024
    MERGE_FAN_IN = 100
    BLOCK_SIZE = 16 * 1024 * 1024

class SafeChunkReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.queue = None
        self.stop_event = threading.Event()
        self.thread = None

    def __iter__(self):
        self.queue = queue.Queue(maxsize=4)
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        while True:
            item = self.queue.get()
            if item is None: break
            yield item

    def _read_loop(self):
        try:
            with open(self.filepath, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    try: mm.madvise(mmap.MADV_SEQUENTIAL)
                    except: pass
                    
                    pos = 0
                    while pos < mm.size():
                        if self.stop_event.is_set(): break
                        line = mm.readline()
                        if not line: break
                        self.queue.put(line)
                        pos += len(line)
        finally:
            self.queue.put(None)

    def close(self):
        self.stop_event.set()
        if self.thread: self.thread.join()

class ExternalSortEngine:
    def __init__(self, input_path: str, output_path: str):
        self.input_path = input_path
        self.output_path = output_path
        self.temp_dir = tempfile.mkdtemp(prefix="sort_engine_")
        self.chunks = []

    def _check_memory(self):
        proc = psutil.Process(os.getpid())
        mem = proc.memory_info().rss / (1024 * 1024)
        if mem > SortConfig.MAX_MEMORY_MB:
            raise MemoryError(f"Critical memory usage: {mem:.2f}MB")

    def split_phase(self):
        logging.info("Starting Phase 1: Adaptive Splitting...")
        chunk_idx = 0
        with open(self.input_path, 'rb') as f:
            while True:
                lines = f.readlines(SortConfig.CHUNK_SIZE_BYTES)
                if not lines: break
                
                lines.sort()
                chunk_path = os.path.join(self.temp_dir, f"chunk_{chunk_idx}.bin")
                with open(chunk_path, 'wb') as cf:
                    cf.writelines(lines)
                self.chunks.append(chunk_path)
                chunk_idx += 1
                self._check_memory()
                del lines
        logging.info(f"Split phase completed. Total chunks: {len(self.chunks)}")

    def _merge_recursive(self, chunk_files: List[str], depth: int = 0) -> str:
        if len(chunk_files) <= SortConfig.MERGE_FAN_IN:
            return self._merge_files(chunk_files, f"final_merge_{depth}.bin")
        
        intermediate_chunks = []
        for i in range(0, len(chunk_files), SortConfig.MERGE_FAN_IN):
            batch = chunk_files[i : i + SortConfig.MERGE_FAN_IN]
            out = self._merge_files(batch, f"intermediate_{depth}_{i}.bin")
            intermediate_chunks.append(out)
        return self._merge_recursive(intermediate_chunks, depth + 1)

    def _merge_files(self, files: List[str], output_name: str) -> str:
        out_path = os.path.join(self.temp_dir, output_name)
        readers = [SafeChunkReader(f) for f in files]
        heap = []
        
        for i, reader in enumerate(readers):
            it = iter(reader)
            try:
                first = next(it)
                heapq.heappush(heap, (first, i, it))
            except StopIteration:
                pass

        with open(out_path, 'wb') as out_f:
            while heap:
                line, idx, it = heapq.heappop(heap)
                out_f.write(line)
                try:
                    next_val = next(it)
                    heapq.heappush(heap, (next_val, idx, it))
                except StopIteration:
                    pass
        
        for r in readers: r.close()
        for f in files: os.remove(f)
        return out_path

    def run(self):
        try:
            self.split_phase()
            final_file = self._merge_recursive(self.chunks)
            shutil.move(final_file, self.output_path)
            logging.info("Sorting process completed successfully.")
        except Exception as e:
            logging.error(f"Fatal error during execution: {e}")
            raise
        finally:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    # 使用示例
    # 假设有一个 120GB 的 huge.log
    engine = ExternalSortEngine("huge.log", "sorted.log")
    engine.run()
