import os
import heapq
from typing import List

class HierarchicalMerger:
    """递归归并器，将 O(N) 扇入归并转为 O(log N) 层级归并，规避 FD 限制"""
    def __init__(self, fan_in: int = 100):
        self.fan_in = fan_in

    def merge_all(self, chunk_files: List[str]) -> str:
        current_level_files = chunk_files
        
        while len(current_level_files) > 1:
            next_level_files = []
            # 每一轮处理一个批次，确保同时打开的文件句柄数 <= fan_in + 1
            for i in range(0, len(current_level_files), self.fan_in):
                batch = current_level_files[i : i + self.fan_in]
                if len(batch) == 1:
                    next_level_files.append(batch[0])
                else:
                    output = f"merged_level_{len(next_level_files)}.tmp"
                    self._merge_batch(batch, output)
                    # 及时回收已合并的源文件
                    for f in batch: os.remove(f)
                    next_level_files.append(output)
            current_level_files = next_level_files
            
        return current_level_files[0]

    def _merge_batch(self, input_files: List[str], output_file: str):
        # 此处调用前面定义过的归并逻辑
        pass
