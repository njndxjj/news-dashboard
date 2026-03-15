#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Snowflake 分布式 ID 生成器
- 64 位整数结构：1 位符号 + 41 位时间戳 + 10 位机器 ID + 12 位序列号
- 保证全局唯一、趋势递增、高性能
- 支持多服务器部署，每台服务器配置不同的 worker_id
"""

import time
import threading
import os

class SnowflakeIDGenerator:
    """Snowflake 分布式 ID 生成器"""

    # 时间戳起始点（2024-01-01 00:00:00 UTC，单位毫秒）
    EPOCH = 1704067200000

    # 位分配
    TIMESTAMP_BITS = 41  # 时间戳占 41 位（可用约 69 年）
    WORKER_BITS = 10     # 机器 ID 占 10 位（最多 1024 台服务器）
    SEQUENCE_BITS = 12   # 序列号占 12 位（每毫秒最多 4096 个 ID）

    # 位移量
    WORKER_SHIFT = SEQUENCE_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_BITS

    # 最大值
    MAX_WORKER_ID = (1 << WORKER_BITS) - 1  # 1023
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095

    def __init__(self, worker_id=None):
        """
        初始化生成器

        Args:
            worker_id: 机器 ID（0-1023），可从环境变量获取或自动生成
        """
        self.lock = threading.Lock()

        # 从环境变量获取 worker_id，或从进程 ID 派生
        if worker_id is None:
            env_worker_id = os.environ.get('SNOWFLAKE_WORKER_ID')
            if env_worker_id:
                worker_id = int(env_worker_id)
            else:
                # 使用进程 ID 派生（适合单机多进程场景）
                worker_id = os.getpid() % 1024

        if not (0 <= worker_id <= self.MAX_WORKER_ID):
            raise ValueError(f'worker_id 必须在 0-{self.MAX_WORKER_ID} 之间')

        self.worker_id = worker_id
        self.sequence = 0
        self.last_timestamp = -1

        print(f"✅ Snowflake 生成器已初始化 - Worker ID: {worker_id}")

    def _get_timestamp_ms(self):
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)

    def _wait_next_millisecond(self, last_timestamp):
        """等待到下一毫秒"""
        timestamp = self._get_timestamp_ms()
        while timestamp <= last_timestamp:
            timestamp = self._get_timestamp_ms()
        return timestamp

    def generate(self):
        """
        生成一个全局唯一的 64 位整数 ID

        Returns:
            int: 64 位整数 ID

        结构:
            - 1 位：未使用（符号位）
            - 41 位：时间戳毫秒数（从 EPOCH 开始，可用约 69 年）
            - 10 位：机器 ID（0-1023，支持 1024 台服务器）
            - 12 位：序列号（0-4095，每毫秒最多生成 4096 个 ID）
        """
        with self.lock:
            timestamp = self._get_timestamp_ms()

            # 如果当前时间小于上次生成时间，说明时钟回拨，抛出异常
            if timestamp < self.last_timestamp:
                raise RuntimeError(
                    f'时钟回拨！检测到时间倒流 {self.last_timestamp - timestamp}ms'
                )

            # 同一毫秒内，序列号递增
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    # 当前毫秒的序列号已用完，等待下一毫秒
                    timestamp = self._wait_next_millisecond(self.last_timestamp)
            else:
                # 新毫秒，重置序列号
                self.sequence = 0

            # 组合 ID
            id_value = (
                ((timestamp - self.EPOCH) << self.TIMESTAMP_SHIFT) |
                (self.worker_id << self.WORKER_SHIFT) |
                self.sequence
            )

            self.last_timestamp = timestamp
            return id_value

    def generate_uuid(self):
        """
        生成 UUID 格式的 ID（字符串，兼容现有数据库字段）

        Returns:
            str: UUID 格式字符串（如：550e8400-e29b-41d4-a716-446655440000）
        """
        snowflake_id = self.generate()
        # 将 64 位整数转换为 32 位十六进制字符串，填充为标准 UUID 格式
        hex_str = f'{snowflake_id:0>32x}'
        # 插入 UUID 格式的分隔符
        return f'{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}'

    def parse_id(self, id_value):
        """
        解析 Snowflake ID，提取时间戳、机器 ID、序列号

        Args:
            id_value: 64 位整数 ID 或 UUID 字符串

        Returns:
            dict: {
                'timestamp': 时间戳（毫秒）,
                'datetime': 可读日期时间,
                'worker_id': 机器 ID,
                'sequence': 序列号
            }
        """
        if isinstance(id_value, str):
            # 如果是 UUID 字符串，转换回整数
            hex_str = id_value.replace('-', '')
            id_value = int(hex_str, 16)

        sequence = id_value & self.MAX_SEQUENCE
        worker_id = (id_value >> self.WORKER_SHIFT) & self.MAX_WORKER_ID
        timestamp = ((id_value >> self.TIMESTAMP_SHIFT) & ((1 << self.TIMESTAMP_BITS) - 1)) + self.EPOCH

        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp / 1000.0)

        return {
            'timestamp': timestamp,
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'worker_id': worker_id,
            'sequence': sequence
        }


# 全局单例（懒加载）
_generator = None
_generator_lock = threading.Lock()


def get_generator(worker_id=None):
    """
    获取全局 Snowflake 生成器单例

    Args:
        worker_id: 机器 ID（可选，首次调用时指定）

    Returns:
        SnowflakeIDGenerator: 全局生成器实例
    """
    global _generator
    if _generator is None:
        with _generator_lock:
            if _generator is None:
                _generator = SnowflakeIDGenerator(worker_id)
    return _generator


def generate_id():
    """生成一个整数 ID"""
    return get_generator().generate()


def generate_uuid():
    """生成一个 UUID 格式的 ID（兼容现有数据库）"""
    return get_generator().generate_uuid()


# 测试代码
if __name__ == '__main__':
    print('Snowflake ID 生成器测试')
    print('=' * 50)

    generator = SnowflakeIDGenerator(worker_id=1)

    # 生成 10 个 ID 测试
    print('\n生成 10 个 ID：')
    ids = []
    for i in range(10):
        int_id = generator.generate()
        uuid = generator.generate_uuid()
        ids.append(int_id)
        print(f'  [{i+1}] 整数：{int_id} | UUID: {uuid}')

    # 测试解析功能
    print('\n解析第一个 ID：')
    parsed = generator.parse_id(ids[0])
    for key, value in parsed.items():
        print(f'  {key}: {value}')

    # 测试并发（多线程）- 使用全局单例
    print('\n并发测试（10 线程 × 100 次，使用全局单例）：')
    import threading

    all_ids = []
    lock = threading.Lock()

    def worker():
        # 使用全局单例生成器
        gen = get_generator(worker_id=1)
        for _ in range(100):
            uid = gen.generate_uuid()
            with lock:
                all_ids.append(uid)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 检查唯一性
    unique_ids = set(all_ids)
    print(f'  生成总数：{len(all_ids)}')
    print(f'  唯一数量：{len(unique_ids)}')
    print(f'  唯一性：{"✅ 通过" if len(all_ids) == len(unique_ids) else "❌ 失败"}')

    # 显示前 5 个 ID
    print('\n前 5 个生成的 UUID：')
    for i, uid in enumerate(all_ids[:5], 1):
        print(f'  [{i}] {uid}')
