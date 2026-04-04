"""StudentFactory - 学生创建工厂."""

import json
import random

from core.name_pool import NamePool
from schemas.student import (
    RandomClassConfig,
    StudentCreateRequest,
    StudentProfile,
)


class StudentFactory:
    """学生创建工厂 - 支持手动/随机/JSON三种创建方式."""

    @staticmethod
    def create_students(request: StudentCreateRequest) -> list[dict]:
        """根据请求类型创建学生.

        Args:
            request: 学生创建请求

        Returns:
            学生字典列表

        Raises:
            ValueError: 不支持的创建类型或请求参数无效
        """
        if request.source == "manual":
            return StudentFactory._create_manual(request.manual_students)
        elif request.source == "random":
            return StudentFactory._create_random(request.random_config)
        elif request.source == "json":
            return StudentFactory._create_from_json(request.json_data)
        else:
            raise ValueError(f"不支持的创建类型: {request.source}")

    @staticmethod
    def _create_manual(students: "list[StudentProfile] | None") -> list[dict]:
        """手动创建学生.

        Args:
            students: 学生配置列表

        Returns:
            学生字典列表
        """
        if not students:
            raise ValueError("手动创建模式需要提供学生列表")

        if len(students) < 2:
            raise ValueError("手动创建至少需要2个学生")

        if len(students) > 8:
            raise ValueError("手动创建最多支持8个学生")

        result = []
        for profile in students:
            result.append(
                {
                    "name": profile.name,
                    "gender": profile.gender,
                    "level": profile.level.value,
                    "attitude": profile.attitude.value,
                    "learning_ability": profile.learning_ability,
                    "background": profile.background,
                    "special_traits": profile.special_traits or [],
                }
            )

        return result

    @staticmethod
    def _create_random(config: "RandomClassConfig | None") -> list[dict]:
        """随机生成学生.

        Args:
            config: 随机班级配置

        Returns:
            学生字典列表
        """
        if not config:
            raise ValueError("随机生成模式需要提供 RandomClassConfig")

        total = config.total_students
        level_dist = config.level_distribution
        attitude_dist = config.attitude_distribution

        # 使用本地随机生成器，避免污染全局状态
        rng = random.Random(config.random_seed)

        # 生成学生
        students = []
        name_pool = NamePool()
        used_names = []

        # 按分布生成各水平学生
        for _ in range(total):
            # 随机选择水平
            level = StudentFactory._random_choice_by_distribution(level_dist, rng)
            attitude = StudentFactory._random_choice_by_distribution(attitude_dist, rng)
            learning_ability = StudentFactory._generate_learning_ability(level, rng)

            # 随机选择名字（不重复）
            name = name_pool.get_random_name(used_names, rng)
            used_names.append(name)

            # 随机性别
            gender = rng.choice(["男", "女"])

            students.append(
                {
                    "name": name,
                    "gender": gender,
                    "level": level,
                    "attitude": attitude,
                    "learning_ability": learning_ability,
                    "background": None,
                    "special_traits": [],
                }
            )

        return students

    @staticmethod
    def _create_from_json(json_data: str | None) -> list[dict]:
        """从 JSON 导入学生.

        Args:
            json_data: JSON 字符串

        Returns:
            学生字典列表

        Raises:
            ValueError: JSON 格式错误或验证失败
        """
        if not json_data:
            raise ValueError("JSON 导入模式需要提供 JSON 数据")

        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 格式错误: {e}") from None

        if not isinstance(data, list):
            raise ValueError("JSON 数据应该是学生列表")

        if len(data) < 2:
            raise ValueError("至少需要2个学生")

        if len(data) > 50:
            raise ValueError("JSON 导入最多支持50个学生")

        # 使用 Pydantic 验证每个学生数据
        students = []
        for item in data:
            try:
                profile = StudentProfile(**item)
            except Exception as e:
                raise ValueError(f"学生数据验证失败: {e}") from None

            students.append(
                {
                    "name": profile.name,
                    "gender": profile.gender,
                    "level": profile.level.value,
                    "attitude": profile.attitude.value,
                    "learning_ability": profile.learning_ability,
                    "background": profile.background,
                    "special_traits": profile.special_traits or [],
                }
            )

        return students

    @staticmethod
    def _random_choice_by_distribution(distribution: dict, rng: random.Random) -> str:
        """根据分布比例随机选择.

        Args:
            distribution: 分布字典，如 {"excellent": 0.3, "average": 0.5, "basic": 0.2}
            rng: 随机数生成器

        Returns:
            选中的键值
        """
        rand_val = rng.random()
        cumulative = 0.0

        for key, prob in distribution.items():
            cumulative += prob
            if rand_val <= cumulative:
                return key

        # 处理浮点数精度问题
        return list(distribution.keys())[-1]

    @staticmethod
    def _generate_learning_ability(level: str, rng: random.Random) -> int:
        """根据学生水平生成学习能力.

        Args:
            level: 学生水平
            rng: 随机数生成器

        Returns:
            学习能力值 (1-10)
        """
        base_range = {"excellent": (7, 10), "average": (4, 7), "basic": (1, 4)}

        min_val, max_val = base_range.get(level, (4, 7))
        return rng.randint(min_val, max_val)

    @staticmethod
    def export_students(students: list[dict]) -> str:
        """导出学生为 JSON 格式.

        Args:
            students: 学生字典列表

        Returns:
            JSON 字符串
        """
        return json.dumps(students, ensure_ascii=False, indent=2)
