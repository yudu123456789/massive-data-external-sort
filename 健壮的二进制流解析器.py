def robust_read_chunk(file_handle, buffer_size: int = 1024 * 1024) -> Generator[bytes, None, None]:
    """
    确保读取动作永远停在换行符处，通过偏移量回溯或前向搜索
    解决 mmap 在 Buffer 边界切分导致的‘半行’问题。
    """
    buffer = b""
    while True:
        chunk = file_handle.read(buffer_size)
        if not chunk:
            if buffer: yield buffer
            break
        
        buffer += chunk
        # 寻找最后一个换行符
        last_newline = buffer.rfind(b'\n')
        
        if last_newline != -1:
            to_yield = buffer[:last_newline + 1]
            buffer = buffer[last_newline + 1:]
            yield to_yield
        else:
            # 说明这一行可能极长，超过了 buffer_size，需继续累积
            continue
