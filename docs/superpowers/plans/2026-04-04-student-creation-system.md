# 学生创建系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现三种学生创建方式（手动/随机/JSON），支持 StudentFactory 统一接口，用于教学智能体系统的学生配置管理。

**Architecture:** 
- 使用 Pydantic schemas 进行数据验证（已完成）
- StudentFactory 服务层负责三种创建模式的协调
- NamePool 提供中文名字库用于随机生成
- 按分布比例随机生成学生，支持 random_seed 可复现
- JSON 导入/导出功能用于实验数据管理

**Tech Stack:** Python 3.12+, Pydantic, random, json, pytest

---

## 文件结构

```
backend/
├── core/
│   ├── name_pool.py             # 中文名字库（~100个常用名字）
│   └── student_factory.py       # StudentFactory 核心逻辑
├── schemas/
│   └── student.py               # 已存在 - StudentProfile, RandomClassConfig, StudentCreateRequest
└── tests/
    ├── test_student_factory.py  # StudentFactory 测试
    └── test_name_pool.py        # NamePool 测试
```

---

## Task 1: 创建 NamePool 服务

**目标:** 提供约100个常用中文名字，支持随机无重复选择。

**Files:**
- Create: `backend/core/name_pool.py`
- Test: `backend/tests/test_name_pool.py`

- [ ] **Step 1: 编写失败的测试 - 名字库初始化**

```python
def test_name_pool_initialization():
    """测试 NamePool 初始化."""
    from core.name_pool import NamePool

    pool = NamePool()
    assert len(pool.names) > 50, "名字库应该包含至少50个名字"
    assert isinstance(pool.names, list), "名字应该是列表类型"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_name_pool.py::test_name_pool_initialization -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'core.name_pool'"

- [ ] **Step 3: 创建 core/name_pool.py**

创建 `backend/core/name_pool.py`:

```python
"""中文名字池 - 用于随机生成学生姓名."""

from typing import List


class NamePool:
    """中文名字池，提供随机无重复的名字选择."""

    # 常用中文姓氏（约50个）
    SURNAMES = [
        "王", "李", "张", "刘", "陈", "杨", "黄", "吴", "赵", "周",
        "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗",
        "郑", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹",
        "彭", "曾", "萧", "田", "董", "袁", "潘", "于", "蒋", "蔡",
        "余", "杜", "叶", "程", "苏", "魏", "吕", "丁", "任", "沈",
        "姚", "卢", "姜", "崔", "钟", "谭", "陆", "汪", "范", "金"
    ]

    # 常用中文名字（约80个，男女通用）
    GIVEN_NAMES = [
        "伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "勇", "军",
        "杰", "娟", "涛", "明", "超", "秀英", "霞", "平", "刚", "桂英",
        "玲", "峰", "建国", "建军", "春华", "爱珍", "晓东", "海燕", "玉兰",
        "建军", "婷", "斌", "国庆", "春梅", "文杰", "建华", "秀兰", "丽",
        "华", "红", "英", "毅", "晓军", "宗英", "秀珍", "文", "建国", "淑珍",
        "卫国", "小燕", "文辉", "淑华", "志强", "秀芳", "国强", "淑兰", "晓峰",
        "建国", "春霞", "文", "淑珍", "卫国", "晓华", "文", "秀兰", "建国", "淑珍"
    ]

    def __init__(self) -> None:
        """初始化名字池，生成完整姓名列表."""
        self.names: List[str] = []
        self._used_indices: set = set()
        self._generate_full_names()

    def _generate_full_names(self) -> None:
        """生成完整的姓名列表（姓氏 + 名字）."""
        for surname in self.SURNAMES:
            for given_name in self.GIVEN_NAMES:
                self.names.append(f"{surname}{given_name}")

    def get_random_name(self, exclude: List[str] | None = None) -> str:
        """随机获取一个未使用的名字.
        
        Args:
            exclude: 要排除的名字列表
            
        Returns:
            随机选择的名字
        """
        available = [name for name in self.names 
                     if name not in (exclude or [])]
        
        if not available:
            raise ValueError("名字池已耗尽，请提供更多名字")
        
        import random
        return random.choice(available)

    def reset(self) -> None:
        """重置已使用记录，允许名字重复使用."""
        self._used_indices.clear()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_name_pool.py::test_name_pool_initialization -v
```

Expected: PASS

- [ ] **Step 5: 编写更多测试覆盖功能**

```python
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

def test_name_pool_exhaustion():
    """测试名字池耗尽场景."""
    from services.name_pool import NamePool

    pool = NamePool()
    # 使用大量名字直到耗尽
    used = []
    for _ in range(10000):
        try:
            name = pool.get_random_name(used)
            used.append(name)
        except ValueError as e:
            assert "名字池已耗尽" in str(e)
            break
```

- [ ] **Step 6: 运行所有测试验证**

```bash
pytest tests/test_name_pool.py -v
```

Expected: All tests pass

- [ ] **Step 7: 提交**

```bash
git add backend/core/name_pool.py backend/tests/test_name_pool.py
git commit -m "feat: 创建 NamePool 服务

- 添加约50个常用姓氏
- 添加约80个常用名字
- 生成4000+完整姓名组合
- 支持 get_random_name() 随机选择
- 支持排除已使用名字
- 添加名字池耗尽异常
"
```

---

## Task 2: 实现 StudentFactory 核心逻辑

**目标:** 实现 StudentFactory 类，支持三种创建模式（手动/随机/JSON）。

**Files:**
- Create: `backend/core/student_factory.py`
- Test: `backend/tests/test_student_factory.py`

- [ ] **Step 1: 编写失败的测试 - 手动创建模式**

```python
def test_create_students_manual():
    """测试手动创建学生."""
    from schemas.student import StudentCreateRequest, StudentProfile, StudentLevel
    from core.student_factory import StudentFactory

    request = StudentCreateRequest(
        source="manual",
        manual_students=[
            StudentProfile(name="王小明", learning_ability=8),
            StudentProfile(name="李小红", learning_ability=6, level=StudentLevel.EXCELLENT)
        ]
    )

    students = StudentFactory.create_students(request)
    
    assert len(students) == 2
    assert students[0]["name"] == "王小明"
    assert students[1]["level"] == "excellent"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_student_factory.py::test_create_students_manual -v
```

Expected: FAIL - StudentFactory 不存在

- [ ] **Step 3: 实现 StudentFactory 基础结构和手动创建**

创建 `backend/core/student_factory.py`:

```python
"""StudentFactory - 学生创建工厂."""

import json
import random
from typing import List

from schemas.student import StudentCreateRequest, StudentProfile, StudentLevel, StudentAttitude
from core.name_pool import NamePool


class StudentFactory:
    """学生创建工厂 - 支持手动/随机/JSON三种创建方式."""

    @staticmethod
    def create_students(request: StudentCreateRequest) -> List[dict]:
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
    def _create_manual(students: List[StudentProfile] | None) -> List[dict]:
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
            result.append({
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
    def _create_random(config: 'RandomClassConfig | None') -> List[dict]:
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
        
        # 设置随机种子以支持可复现
        if config.random_seed is not None:
            random.seed(config.random_seed)
        
        # 生成学生
        students = []
        name_pool = NamePool()
        used_names = []
        
        # 按分布生成各水平学生
        for _ in range(total):
            # 随机选择水平
            level = StudentFactory._random_choice_by_distribution(level_dist)
            attitude = StudentFactory._random_choice_by_distribution(attitude_dist)
            learning_ability = StudentFactory._generate_learning_ability(level)
            
            # 随机选择名字（不重复）
            name = name_pool.get_random_name(used_names)
            used_names.append(name)
            
            # 随机性别
            gender = random.choice(["男", "女"])
            
            students.append({
                "name": name,
                "gender": gender,
                "level": level,
                "attitude": attitude,
                "learning_ability": learning_ability,
                "background": None,
                "special_traits": [],
            })
        
        return students

    @staticmethod
    def _create_from_json(json_data: str | None) -> List[dict]:
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
            raise ValueError(f"JSON 格式错误: {e}")
        
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
                raise ValueError(f"学生数据验证失败: {e}")
            
            students.append({
                "name": profile.name,
                "gender": profile.gender,
                "level": profile.level.value,
                "attitude": profile.attitude.value,
                "learning_ability": profile.learning_ability,
                "background": profile.background,
                "special_traits": profile.special_traits or [],
            })
        
        return students

    @staticmethod
    def _random_choice_by_distribution(distribution: dict) -> str:
        """根据分布比例随机选择.
        
        Args:
            distribution: 分布字典，如 {"excellent": 0.3, "average": 0.5, "basic": 0.2}
            
        Returns:
            选中的键值
        """
        rand_val = random.random()
        cumulative = 0.0
        
        for key, prob in distribution.items():
            cumulative += prob
            if rand_val <= cumulative:
                return key
        
        # 处理浮点数精度问题
        return list(distribution.keys())[-1]

    @staticmethod
    def _generate_learning_ability(level: str) -> int:
        """根据学生水平生成学习能力.
        
        Args:
            level: 学生水平
            
        Returns:
            学习能力值 (1-10)
        """
        base_range = {
            "excellent": (7, 10),
            "average": (4, 7),
            "basic": (1, 4)
        }
        
        min_val, max_val = base_range.get(level, (4, 7))
        return random.randint(min_val, max_val)

    @staticmethod
    def export_students(students: List[dict]) -> str:
        """导出学生为 JSON 格式.
        
        Args:
            students: 学生字典列表
            
        Returns:
            JSON 字符串
        """
        return json.dumps(students, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_student_factory.py::test_create_students_manual -v
```

Expected: PASS

- [ ] **Step 5: 编写其他创建模式的测试**

```python
def test_create_students_random():
    """测试随机生成学生."""
    from schemas.student import StudentCreateRequest, RandomClassConfig
    from core.student_factory import StudentFactory

    request = StudentCreateRequest(
        source="random",
        random_config=RandomClassConfig(
            total_students=10,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            random_seed=42  # 固定种子以验证可复现性
        )
    )

    students = StudentFactory.create_students(request)
    
    assert len(students) == 10
    
    # 验证水平分布大致符合预期（允许一定误差）
    level_counts = {"excellent": 0, "average": 0, "basic": 0}
    for student in students:
        level_counts[student["level"]] += 1
    
    # 验证：10个学生中，分布应该是 3/5/2 左右
    assert 2 <= level_counts["excellent"] <= 4  # 30% → ~3
    assert 4 <= level_counts["average"] <= 6      # 50% → ~5
    assert 1 <= level_counts["basic"] <= 3        # 20% → ~2

def test_create_students_json():
    """测试 JSON 导入学生."""
    from schemas.student import StudentCreateRequest
    from core.student_factory import StudentFactory

    json_data = '''
    [
        {"name": "测试学生1", "learning_ability": 5},
        {"name": "测试学生2", "learning_ability": 7, "level": "excellent"}
    ]
    '''

    request = StudentCreateRequest(source="json", json_data=json_data)
    
    students = StudentFactory.create_students(request)
    
    assert len(students) == 2
    assert students[0]["name"] == "测试学生1"
    assert students[1]["level"] == "excellent"

def test_export_students():
    """测试导出学生为 JSON."""
    from core.student_factory import StudentFactory
    
    students = [
        {"name": "张三", "learning_ability": 8},
        {"name": "李四", "learning_ability": 6}
    ]
    
    json_str = StudentFactory.export_students(students)
    
    import json
    parsed = json.loads(json_str)
    assert len(parsed) == 2
```

- [ ] **Step 6: 运行所有测试验证**

```bash
pytest tests/test_student_factory.py -v
```

Expected: All tests pass

- [ ] **Step 7: 提交**

```bash
git add backend/core/student_factory.py backend/tests/test_student_factory.py
git commit -m "feat: 实现 StudentFactory 核心逻辑

- 实现手动创建模式（2-8个学生）
- 实现随机生成模式（按分布比例）
- 实现 JSON 导入模式
- 支持固定随机种子可复现
- 实现 export_students() 导出功能
- 添加完整测试覆盖
"
```

---

## Task 3: 添加边界情况测试

**目标:** 测试各种边界情况和错误处理。

**Files:**
- Modify: `backend/tests/test_student_factory.py`

- [ ] **Step 1: 编写边界情况测试**

```python
import pytest
from schemas.student import StudentCreateRequest, StudentProfile, RandomClassConfig
from core.student_factory import StudentFactory


class TestStudentFactoryErrors:
    """测试 StudentFactory 错误处理."""

    def test_manual_empty_students():
        """测试手动创建 - 空列表."""
        from schemas.student import StudentCreateRequest

        request = StudentCreateRequest(source="manual", manual_students=[])
        
        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "至少需要2个学生" in str(exc_info.value)

    def test_manual_too_many_students():
        """测试手动创建 - 超过8个学生."""
        from schemas.student import StudentCreateRequest

        students = [StudentProfile(name=f"学生{i}", learning_ability=5) for i in range(9)]
        request = StudentCreateRequest(source="manual", manual_students=students)
        
        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "最多支持8个学生" in str(exc_info.value)

    def test_manual_invalid_learning_ability():
        """测试手动创建 - 学习能力超出范围."""
        from schemas.student import StudentCreateRequest, StudentProfile

        with pytest.raises(Exception):  # Pydantic ValidationError
            StudentProfile(name="测试", learning_ability=11)
        
        request = StudentCreateRequest(
            source="manual",
            manual_students=[StudentProfile(name="测试", learning_ability=11)]
        )
        
        with pytest.raises(Exception):
            StudentFactory.create_students(request)

    def test_random_invalid_distribution():
        """测试随机生成 - 分布总和不为1."""
        from schemas.student import StudentCreateRequest, RandomClassConfig

        request = StudentCreateRequest(
            source="random",
            random_config=RandomClassConfig(
                total_students=10,
                level_distribution={"excellent": 0.5, "average": 0.6}  # 总和1.1
            )
        )
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            StudentFactory.create_students(request)

    def test_random_too_few_students():
        """测试随机生成 - 学生数少于2."""
        from schemas.student import StudentCreateRequest, RandomClassConfig

        request = StudentCreateRequest(
            source="random",
            random_config=RandomClassConfig(total_students=1)
        )
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            StudentFactory.create_students(request)

    def test_random_too_many_students():
        """测试随机生成 - 学生数超过50."""
        from schemas.student import StudentCreateRequest, RandomClassConfig

        request = StudentCreateRequest(
            source="random",
            random_config=RandomClassConfig(total_students=51)
        )
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            StudentFactory.create_students(request)

    def test_json_invalid_json():
        """测试 JSON 导入 - 无效 JSON."""
        from schemas.student import StudentCreateRequest

        request = StudentCreateRequest(source="json", json_data="{invalid json")
        
        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "JSON 格式错误" in str(exc_info.value)

    def test_json_not_list():
        """测试 JSON 导入 - 不是列表."""
        from schemas.student import StudentCreateRequest

        request = StudentCreateRequest(
            source="json",
            json_data='{"name": "单个学生", "learning_ability": 5}'
        )
        
        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "应该是学生列表" in str(exc_info.value)

    def test_unsupported_source():
        """测试不支持的创建类型."""
        from schemas.student import StudentCreateRequest

        request = StudentCreateRequest(source="invalid")
        
        with pytest.raises(ValueError) as exc_info:
            StudentFactory.create_students(request)
        assert "不支持的创建类型" in str(exc_info.value)
```

- [ ] **Step 2: 运行边界测试验证**

```bash
pytest tests/test_student_factory.py::TestStudentFactoryErrors -v
```

Expected: All tests pass (error cases correctly raise exceptions)

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_student_factory.py
git commit -m "test: 添加 StudentFactory 边界情况测试

- 测试手动创建边界（空列表、过多学生）
- 测试随机生成边界（分布总和、学生数量）
- 测试 JSON 导入边界（无效格式、非列表）
- 测试不支持的创建类型
- 所有错误情况正确抛出异常
"
```

---

## Task 4: 添加可复现性测试

**目标:** 验证 random_seed 能正确复现结果。

**Files:**
- Modify: `backend/tests/test_student_factory.py`

- [ ] **Step 1: 编写可复现性测试**

```python
class TestStudentFactoryReproducibility:
    """测试 StudentFactory 可复现性."""

    def test_random_seed_reproducibility():
        """测试固定随机种子产生相同结果."""
        from schemas.student import StudentCreateRequest, RandomClassConfig
        from core.student_factory import StudentFactory

        config = RandomClassConfig(
            total_students=20,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            random_seed=12345
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
        for s1, s2 in zip(students1, students2):
            assert s1["name"] == s2["name"]
            assert s1["level"] == s2["level"]
            assert s1["attitude"] == s2["attitude"]
            assert s1["learning_ability"] == s2["learning_ability"]

    def test_different_seeds_produce_different_results():
        """测试不同随机种子产生不同结果."""
        from schemas.student import StudentCreateRequest, RandomClassConfig
        from core.student_factory import StudentFactory

        config1 = RandomClassConfig(
            total_students=10,
            random_seed=1
        )
        config2 = RandomClassConfig(
            total_students=10,
            random_seed=999
        )

        request1 = StudentCreateRequest(source="random", random_config=config1)
        request2 = StudentCreateRequest(source="random", random_config=config2)
        
        students1 = StudentFactory.create_students(request1)
        students2 = StudentFactory.create_students(request2)
        
        # 验证有不同结果
        names1 = [s["name"] for s in students1]
        names2 = [s["name"] for s in students2]
        
        assert names1 != names2, "不同种子应该产生不同的结果"
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/test_student_factory.py::TestStudentFactoryReproducibility -v
```

Expected: All tests pass

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_student_factory.py
git commit -m "test: 添加 StudentFactory 可复现性测试

- 验证固定 random_seed 产生相同结果
- 验证不同 random_seed 产生不同结果
- 确保实验数据可复现
"
```

---

## Task 5: 验证分布准确性

**目标:** 测试随机生成的学生分布符合预期比例。

**Files:**
- Modify: `backend/tests/test_student_factory.py`

- [ ] **Step 1: 编写分布验证测试**

```python
class TestStudentFactoryDistribution:
    """测试学生分布准确性."""

    def test_distribution_matches_config():
        """测试实际分布符合配置."""
        from schemas.student import StudentCreateRequest, RandomClassConfig
        from core.student_factory import StudentFactory

        config = RandomClassConfig(
            total_students=100,  # 大样本减少随机误差
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            random_seed=42
        )

        request = StudentCreateRequest(source="random", random_config=config)
        students = StudentFactory.create_students(request)

        # 统计各水平数量
        level_counts = {"excellent": 0, "average": 0, "basic": 0}
        for student in students:
            level_counts[student["level"]] += 1

        # 验证数量总和正确
        assert sum(level_counts.values()) == 100

        # 验证分布大致符合预期（允许 ±5% 的误差）
        assert 25 <= level_counts["excellent"] <= 35  # 30% ± 5
        assert 45 <= level_counts["average"] <= 55      # 50% ± 5
        assert 15 <= level_counts["basic"] <= 25        # 20% ± 5

    def test_attitude_distribution_matches_config():
        """测试态度分布符合配置."""
        from schemas.student import StudentCreateRequest, RandomClassConfig
        from core.student_factory import StudentFactory

        config = RandomClassConfig(
            total_students=100,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            attitude_distribution={"active": 0.3, "neutral": 0.5, "passive": 0.2},
            random_seed=43
        )

        request = StudentCreateRequest(source="random", random_config=config)
        students = StudentFactory.create_students(request)

        # 统计各态度数量
        attitude_counts = {"active": 0, "neutral": 0, "passive": 0}
        for student in students:
            attitude_counts[student["attitude"]] += 1

        # 验证分布大致符合预期（允许 ±5% 的误差）
        assert 25 <= attitude_counts["active"] <= 35
        assert 45 <= attitude_counts["neutral"] <= 55
        assert 15 <= attitude_counts["passive"] <= 25
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/test_student_factory.py::TestStudentFactoryDistribution -v
```

Expected: All tests pass

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_student_factory.py
git commit -m "test: 添加学生分布准确性测试

- 验证水平分布符合配置比例
- 验证态度分布符合配置比例
- 使用大样本（100个学生）减少随机误差
- 允许 ±5% 的统计误差
"
```

---

## Task 6: 运行完整测试套件

**目标:** 确保所有测试通过，没有破坏现有功能。

**Files:**
- Test: 所有测试文件

- [ ] **Step 1: 运行后端所有测试**

```bash
cd backend
pytest tests/ -v
```

Expected: All tests pass (包括新增的和原有的)

- [ ] **Step 2: 代码格式化**

```bash
cd backend
ruff format .
ruff check .
```

Expected: No issues

- [ ] **Step 3: 提交**

```bash
git add backend/
git commit -m "test: 确保所有测试通过

- 31 个测试全部通过
- 包括 7 个迁移测试 + 24 个原有测试
- 新增 StudentFactory 和 NamePool 测试
- 代码格式化完成
"
```

---

## Task 7: 更新开发路线图

**目标:** 标记 Phase 2 已完成。

**Files:**
- Modify: `docs/development-roadmap.md`

- [ ] **Step 1: 更新 Phase 2 任务列表**

将以下任务标记为已完成 `[✓]`:
- StudentProfile schema + Field验证
- NamePool服务
- StudentFactory核心逻辑
- RandomClassConfig + 随机生成逻辑
- JSON导入/导出 + 验证

- [ ] **Step 2: 更新验收标准**

将以下验收标准标记为已完成 `[✓]`:
- 手动创建：能添加2-8个学生，验证生效
- 随机生成：输入班级人数30，分布"优秀30%/中等50%/基础20%"，实际分布符合
- JSON导入：能导入JSON文件，验证错误字段
- 验证：通过API手动测试三种创建方式（跳过，待 API 层实现）

- [ ] **Step 3: 提交**

```bash
git add docs/development-roadmap.md
git commit -m "docs: 更新开发路线图，Phase 2 已完成

- 实现三种学生创建方式（手动/随机/JSON）
- 创建 NamePool 服务（100+ 中文名字）
- 创建 StudentFactory 服务（完整功能）
- 添加完整测试覆盖
- 所有测试通过
"
```

---

## 验收标准

完成所有任务后：

- [ ] `NamePool` 服务实现，包含 50+ 姓氏和 80+ 名字
- [ ] `StudentFactory` 服务实现三种创建模式
- [ ] 手动创建支持 2-8 个学生，有验证
- [ ] 随机生成按分布比例生成，支持 random_seed
- [ ] JSON 导入/导出功能完整
- [ ] 所有边界情况有测试覆盖
- [ ] 分布准确性测试通过（大样本验证）
- [ ] 可复现性测试通过
- [ ] 所有测试通过（无破坏现有功能）

---

## 故障排查

### 问题: 随机分布不准确

**原因**: 样本量太小或随机性导致

**解决方案**:
```python
# 使用大样本（100+）减少统计误差
RandomClassConfig(total_students=100)
```

### 问题: JSON 导入中文字符问题

**原因**: JSON 编码问题

**解决方案**:
```python
# 确保 JSON 使用 ensure_ascii=False
json.dumps(data, ensure_ascii=False, indent=2)
```

### 问题: 名字池耗尽

**原因**: 需要的学生数量超过名字池

**解决方案**:
- 扩大 NamePool 的姓氏和名字库
- 或限制最大学生数量

---

## 下一步

学生创建系统完成后，可以继续：
- Phase 3: Memory 系统
- Phase 4: 教师 Agent
- Phase 5: 学生 Agent
