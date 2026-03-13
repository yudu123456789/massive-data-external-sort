def read_with_dedup_lookahead(file_handle) -> Generator:
    """
    不仅读取行，还进行预读对比。如果连续多行相同，
    则在内存中聚合，输出 (key, count) 结构，大幅减少归并次数。
    """
    last_line = None
    count = 0
    for line in file_handle:
        if line == last_line:
            count += 1
        else:
            if last_line is not None:
                yield (last_line, count)
            last_line = line
            count = 1
    yield (last_line, count)
