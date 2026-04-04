"""StudentFactory 测试."""

import pytest

from core.student_factory import StudentFactory
from schemas.student import RandomClassConfig, StudentCreateRequest, StudentLevel, StudentProfile


def test_create_students_manual():
    """测试手动创建学生."""
    request = StudentCreateRequest(
        source="manual",
        manual_students=[
            StudentProfile(name="王小明", learning_ability=8),
            StudentProfile(name="李小红", learning_ability=6, level=StudentLevel.EXCELLENT),
        ],
    )

    students = StudentFactory.create_students(request)

    assert len(students) == 2
    assert students[0]["name"] == "王小明"
    assert students[1]["level"] == "excellent"


def test_create_students_random():
    """测试随机生成学生."""
    request = StudentCreateRequest(
        source="random",
        random_config=RandomClassConfig(
            total_students=10,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            random_seed=42,  # 固定种子以验证可复现性
        ),
    )

    students = StudentFactory.create_students(request)

    assert len(students) == 10

    # 验证水平分布大致符合预期（允许一定误差）
    level_counts = {"excellent": 0, "average": 0, "basic": 0}
    for student in students:
        level_counts[student["level"]] += 1

    # 验证：10个学生中，分布应该是 3/5/2 左右
    assert 2 <= level_counts["excellent"] <= 4  # 30% → ~3
    assert 4 <= level_counts["average"] <= 6  # 50% → ~5
    assert 1 <= level_counts["basic"] <= 3  # 20% → ~2


def test_create_students_json():
    """测试 JSON 导入学生."""
    json_data = """
    [
        {"name": "测试学生1", "learning_ability": 5},
        {"name": "测试学生2", "learning_ability": 7, "level": "excellent"}
    ]
    """

    request = StudentCreateRequest(source="json", json_data=json_data)

    students = StudentFactory.create_students(request)

    assert len(students) == 2
    assert students[0]["name"] == "测试学生1"
    assert students[1]["level"] == "excellent"


def test_export_students():
    """测试导出学生为 JSON."""
    students = [{"name": "张三", "learning_ability": 8}, {"name": "李四", "learning_ability": 6}]

    json_str = StudentFactory.export_students(students)

    import json

    parsed = json.loads(json_str)
    assert len(parsed) == 2


# ==================== 边界情况测试 (Task 3) ====================


class TestStudentFactoryErrors:
    """测试 StudentFactory 错误处理."""

    def test_manual_empty_students(self):
        """测试手动创建 - 空列表."""
        request = StudentCreateRequest(source="manual", manual_students=[])

        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "手动创建模式需要提供学生列表" in str(exc_info.value)

    def test_manual_too_many_students(self):
        """测试手动创建 - 超过8个学生."""
        students = [StudentProfile(name=f"学生{i}", learning_ability=5) for i in range(9)]
        request = StudentCreateRequest(source="manual", manual_students=students)

        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "最多支持8个学生" in str(exc_info.value)

    def test_manual_invalid_learning_ability(self):
        """测试手动创建 - 学习能力超出范围."""
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            StudentProfile(name="测试", learning_ability=11)

    def test_random_invalid_distribution(self):
        """测试随机生成 - 分布总和不为1."""
        # Pydantic 在 schema 层面验证分布总和
        with pytest.raises(Exception) as exc_info:  # Pydantic ValidationError
            RandomClassConfig(
                total_students=10,
                level_distribution={"excellent": 0.5, "average": 0.6},  # 总和1.1
            )
        assert "分布比例总和必须为1.0" in str(exc_info.value)

    def test_random_too_few_students(self):
        """测试随机生成 - 学生数少于2."""
        # Pydantic 在 schema 层面验证学生数量
        with pytest.raises(Exception) as exc_info:  # Pydantic ValidationError
            RandomClassConfig(total_students=1)
        assert "greater than or equal to 2" in str(exc_info.value)

    def test_random_too_many_students(self):
        """测试随机生成 - 学生数超过50."""
        # Pydantic 在 schema 层面验证学生数量
        with pytest.raises(Exception) as exc_info:  # Pydantic ValidationError
            RandomClassConfig(total_students=51)
        assert "less than or equal to 50" in str(exc_info.value)

    def test_json_invalid_json(self):
        """测试 JSON 导入 - 无效 JSON."""
        request = StudentCreateRequest(source="json", json_data="{invalid json")

        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "JSON 格式错误" in str(exc_info.value)

    def test_json_not_list(self):
        """测试 JSON 导入 - 不是列表."""
        request = StudentCreateRequest(
            source="json", json_data='{"name": "单个学生", "learning_ability": 5}'
        )

        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "应该是学生列表" in str(exc_info.value)

    def test_unsupported_source(self):
        """测试不支持的创建类型."""
        request = StudentCreateRequest(source="invalid")

        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "不支持的创建类型" in str(exc_info.value)


# ==================== 可复现性测试 (Task 4) ====================


class TestStudentFactoryReproducibility:
    """测试 StudentFactory 可复现性."""

    def test_random_seed_reproducibility(self):
        """测试固定随机种子产生相同结果."""
        config = RandomClassConfig(
            total_students=20,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            random_seed=12345,
        )

        # 第一次生成
        request1 = StudentCreateRequest(source="random", random_config=config)
        students1 = StudentFactory.create_students(request1)

        # 重置并第二次生成
        request2 = StudentCreateRequest(source="random", random_config=config)
        students2 = StudentFactory.create_students(request2)

        # 验证结果相同
        assert len(students1) == len(students2) == 20

        # 验证每个学生属性相同
        for s1, s2 in zip(students1, students2, strict=False):
            assert s1["name"] == s2["name"]
            assert s1["level"] == s2["level"]
            assert s1["attitude"] == s2["attitude"]
            assert s1["learning_ability"] == s2["learning_ability"]

    def test_different_seeds_produce_different_results(self):
        """测试不同随机种子产生不同结果."""
        config1 = RandomClassConfig(total_students=10, random_seed=1)
        config2 = RandomClassConfig(total_students=10, random_seed=999)

        request1 = StudentCreateRequest(source="random", random_config=config1)
        request2 = StudentCreateRequest(source="random", random_config=config2)

        students1 = StudentFactory.create_students(request1)
        students2 = StudentFactory.create_students(request2)

        # 验证有不同结果
        names1 = [s["name"] for s in students1]
        names2 = [s["name"] for s in students2]

        assert names1 != names2, "不同种子应该产生不同的结果"


# ==================== 分布准确性测试 (Task 5) ====================


class TestStudentFactoryDistribution:
    """测试学生分布准确性."""

    def test_distribution_matches_config(self):
        """测试实际分布符合配置."""
        config = RandomClassConfig(
            total_students=50,  # 最大值
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            random_seed=42,
        )

        request = StudentCreateRequest(source="random", random_config=config)
        students = StudentFactory.create_students(request)

        # 统计各水平数量
        level_counts = {"excellent": 0, "average": 0, "basic": 0}
        for student in students:
            level_counts[student["level"]] += 1

        # 验证数量总和正确
        assert sum(level_counts.values()) == 50

        # 验证分布大致符合预期（允许 ±6% 的误差，因为样本较小）
        assert 9 <= level_counts["excellent"] <= 21  # 30% ± 6 (15±6)
        assert 19 <= level_counts["average"] <= 31  # 50% ± 6 (25±6)
        assert 5 <= level_counts["basic"] <= 15  # 20% ± 6 (10±5)

    def test_attitude_distribution_matches_config(self):
        """测试态度分布符合配置."""
        config = RandomClassConfig(
            total_students=50,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            attitude_distribution={"active": 0.3, "neutral": 0.5, "passive": 0.2},
            random_seed=43,
        )

        request = StudentCreateRequest(source="random", random_config=config)
        students = StudentFactory.create_students(request)

        # 统计各态度数量
        attitude_counts = {"active": 0, "neutral": 0, "passive": 0}
        for student in students:
            attitude_counts[student["attitude"]] += 1

        # 验证分布大致符合预期（允许 ±6% 的误差）
        assert 9 <= attitude_counts["active"] <= 21
        assert 19 <= attitude_counts["neutral"] <= 31
        assert 5 <= attitude_counts["passive"] <= 15
