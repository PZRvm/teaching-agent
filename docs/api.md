# API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 用户模块

### 获取用户列表

```http
GET /users/
```

**响应示例：**
```json
[
  {"username": "Rick"},
  {"username": "Morty"}
]
```

---

### 获取当前用户

```http
GET /users/me
```

**响应示例：**
```json
{
  "username": "fakecurrentuser"
}
```

---

### 获取指定用户

```http
GET /users/{username}
```

**路径参数：**
- `username` (string) - 用户名

**响应示例：**
```json
{
  "username": "rick"
}
```

---

## 智能体模块（待实现）

---

## 对话模块（待实现）
