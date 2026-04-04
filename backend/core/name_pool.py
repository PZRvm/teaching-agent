"""中文名字池 - 用于随机生成学生姓名."""



class NamePool:
    """中文名字池，提供随机无重复的名字选择."""

    # 常用中文姓氏（约50个）
    SURNAMES = [
        "王",
        "李",
        "张",
        "刘",
        "陈",
        "杨",
        "黄",
        "吴",
        "赵",
        "周",
        "徐",
        "孙",
        "马",
        "朱",
        "胡",
        "郭",
        "何",
        "高",
        "林",
        "罗",
        "郑",
        "梁",
        "谢",
        "宋",
        "唐",
        "许",
        "韩",
        "冯",
        "邓",
        "曹",
        "彭",
        "曾",
        "萧",
        "田",
        "董",
        "袁",
        "潘",
        "于",
        "蒋",
        "蔡",
        "余",
        "杜",
        "叶",
        "程",
        "苏",
        "魏",
        "吕",
        "丁",
        "任",
        "沈",
        "姚",
        "卢",
        "姜",
        "崔",
        "钟",
        "谭",
        "陆",
        "汪",
        "范",
        "金",
    ]

    # 常用中文名字（约80个，男女通用）
    GIVEN_NAMES = [
        "伟",
        "芳",
        "娜",
        "敏",
        "静",
        "强",
        "磊",
        "洋",
        "勇",
        "军",
        "杰",
        "娟",
        "涛",
        "明",
        "超",
        "秀英",
        "霞",
        "平",
        "刚",
        "桂英",
        "玲",
        "峰",
        "建国",
        "建军",
        "春华",
        "爱珍",
        "晓东",
        "海燕",
        "玉兰",
        "建军",
        "婷",
        "斌",
        "国庆",
        "春梅",
        "文杰",
        "建华",
        "秀兰",
        "丽",
        "华",
        "红",
        "英",
        "毅",
        "晓军",
        "宗英",
        "秀珍",
        "文",
        "建国",
        "淑珍",
        "卫国",
        "小燕",
        "文辉",
        "淑华",
        "志强",
        "秀芳",
        "国强",
        "淑兰",
        "晓峰",
        "建国",
        "春霞",
        "文",
        "淑珍",
        "卫国",
        "晓华",
        "文",
        "秀兰",
        "建国",
        "淑珍",
    ]

    def __init__(self) -> None:
        """初始化名字池，生成完整姓名列表."""
        self.names: list[str] = []
        self._used_indices: set = set()
        self._generate_full_names()

    def _generate_full_names(self) -> None:
        """生成完整的姓名列表（姓氏 + 名字）."""
        for surname in self.SURNAMES:
            for given_name in self.GIVEN_NAMES:
                self.names.append(f"{surname}{given_name}")

    def get_random_name(self, exclude: list[str] | None = None) -> str:
        """随机获取一个未使用的名字.

        Args:
            exclude: 要排除的名字列表

        Returns:
            随机选择的名字
        """
        import random

        available = [name for name in self.names if name not in (exclude or [])]

        if not available:
            raise ValueError("名字池已耗尽，请提供更多名字")

        return random.choice(available)
