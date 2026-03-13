def safe_parse_line(raw_bytes: bytes) -> Optional[str]:
    """工业级解析：处理编码异常，过滤空行与超大异常行"""
    try:
        line = raw_bytes.decode('utf-8').strip()
        if not line: return None
        if len(line) > 1024 * 1024: # 异常行过滤（单行超过1MB视为语料污染）
            logging.warning(f"Skipping anomalously long line: {len(line)} bytes")
            return None
        return line
    except UnicodeDecodeError:
        return None # 跳过非法编码行

# 在归并循环中使用：
# line_str = safe_parse_line(raw_bytes)
# if line_str: heap.push(...)
