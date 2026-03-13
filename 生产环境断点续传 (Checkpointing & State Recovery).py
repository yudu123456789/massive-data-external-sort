import json
import os

class CheckpointManager:
    def __init__(self, workspace: str):
        self.state_file = os.path.join(workspace, "task_state.json")
    
    def save(self, completed_chunks: List[str]):
        with open(self.state_file, 'w') as f:
            json.dump({"completed": completed_chunks}, f)
            f.flush()
            os.fsync(f.fileno()) # 强制物理刷盘，确保断电不丢数据

    def load(self) -> List[str]:
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f).get("completed", [])
        return []

# 使用方式
# 在 Split 阶段，每完成一个 Chunk 写入，更新 Checkpoint
# 在启动时，扫描 workspace 目录下已存在的 .bin 文件，排除掉未完成的 Chunk
