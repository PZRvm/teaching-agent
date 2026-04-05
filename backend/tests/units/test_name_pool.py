"""NamePool 测试."""


def test_name_pool_initialization():
    """测试 NamePool 初始化."""
    from core.name_pool import NamePool

    pool = NamePool()
    assert len(pool.names) > 50, "名字库应该包含至少50个名字"
    assert isinstance(pool.names, list), "名字应该是列表类型"


def test_get_random_name():
    """测试随机获取名字."""
    from core.name_pool import NamePool

    pool = NamePool()
    name1 = pool.get_random_name()
    name2 = pool.get_random_name([name1])  # 排除已使用的

    assert isinstance(name1, str)
    assert isinstance(name2, str)
    assert len(name1) > 1
    assert len(name2) > 1
