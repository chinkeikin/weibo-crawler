# 微博爬虫 API 服务

基于 [weibo-crawler](https://github.com/dataabc/weibo-crawler) 的 HTTP API 服务，提供 RESTful API 接口管理爬虫配置和执行爬取任务。

## 功能特性

- ✅ **HTTP API 服务**：基于 FastAPI 构建，自动生成 API 文档
- ✅ **配置管理**：通过 API 动态修改 `config.json` 配置
- ✅ **用户管理**：通过 API 添加/删除需要爬取的微博用户
- ✅ **定时爬取**：可配置的定时任务，自动爬取用户微博
- ✅ **任务管理**：查询爬取任务状态和进度
- ✅ **数据查询**：查询已爬取的微博数据（从 SQLite 数据库）
- ✅ **API 认证**：管理接口需要 Token 认证
- ✅ **IPv4/IPv6 双栈支持**
- ✅ **systemd 系统服务**（开机自启）

## 快速开始

### 1. 安装依赖

```bash
# 安装系统依赖
sudo bash install.sh
```

### 2. 配置 API Token（可选）

创建 `.env` 文件：

```bash
echo "API_TOKEN=your_secret_token_here" > .env
```

### 3. 配置爬虫（config.json）

确保 `config.json` 文件存在并配置正确。API 服务会读取和更新这个文件。

### 4. 启动服务

```bash
# 启动服务
sudo systemctl start weibo-crawler-api

# 查看状态
sudo systemctl status weibo-crawler-api

# 设置开机自启
sudo systemctl enable weibo-crawler-api
```

### 5. 访问 API 文档

浏览器打开：http://localhost:8000/docs

## API 接口

### 查询接口（无需认证）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/weibos` | GET | 查询微博内容 |
| `/api/users` | GET | 查询用户列表 |
| `/api/config` | GET | 查询系统配置 |
| `/api/task/{task_id}` | GET | 查询任务状态 |
| `/api/health` | GET | 健康检查 |

### 管理接口（需要认证）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/users/add` | POST | 添加用户并立即爬取 |
| `/api/users/delete` | POST | 删除用户 |
| `/api/config/update` | POST | 更新配置 |
| `/api/crawl/trigger` | POST | 手动触发爬取 |

**认证方式：** Header 添加 `Authorization: Bearer <token>`

## 使用示例

### 1. 添加用户

```bash
curl -X POST "http://localhost:8000/api/users/add" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["1669879400", "1223178222"]}'
```

### 2. 查询微博

```bash
curl "http://localhost:8000/api/weibos?user_ids=1669879400&limit=10"
```

### 3. 更新配置

```bash
curl -X POST "http://localhost:8000/api/config/update" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "only_crawl_original": 1,
    "cookie": "your_weibo_cookie_here"
  }'
```

### 4. 手动触发爬取

```bash
curl -X POST "http://localhost:8000/api/crawl/trigger?user_ids=1669879400" \
  -H "Authorization: Bearer your_token_here"
```

## 配置说明

API 服务会读取和更新 `config.json` 文件。主要配置项：

- `user_id_list`: 用户ID列表（文件路径或列表）
- `only_crawl_original`: 是否只爬取原创微博（0/1）
- `since_date`: 爬取天数或日期
- `cookie`: 微博 Cookie
- `original_pic_download`: 是否下载原创图片（0/1）
- `original_video_download`: 是否下载原创视频（0/1）
- `download_comment`: 是否下载评论（0/1）
- `download_repost`: 是否下载转发（0/1）

详细配置说明请参考原项目 README.md。

## 数据存储

爬取的数据存储在 SQLite 数据库中（默认路径：`./weibo/weibodata.db`），可通过 `/api/weibos` 接口查询。

## 服务管理

```bash
# 启动
sudo systemctl start weibo-crawler-api

# 停止
sudo systemctl stop weibo-crawler-api

# 重启
sudo systemctl restart weibo-crawler-api

# 查看日志
sudo journalctl -u weibo-crawler-api -f
```

## 注意事项

1. **配置同步**：API 修改的配置会直接写入 `config.json`，请确保文件可写
2. **并发控制**：同时只能运行一个爬取任务，新任务会等待
3. **数据路径**：数据库路径由爬虫配置决定，默认在 `./weibo/` 目录
4. **Cookie 配置**：建议通过 API 配置 Cookie，避免手动编辑文件

## 项目结构

```
weibo-crawler/
├── weibo.py              # 爬虫核心代码（原项目）
├── config.json           # 配置文件（API 会读取/更新）
├── api_service/          # API 服务层（新增）
│   ├── main.py          # FastAPI 入口
│   ├── config_manager.py # 配置管理
│   ├── crawler_service.py # 爬虫服务
│   ├── scheduler.py     # 定时任务
│   └── api/             # API 路由
├── run_api.py           # 启动脚本
└── install.sh           # 安装脚本
```

## 技术栈

- **FastAPI** - Web 框架
- **APScheduler** - 定时任务调度
- **SQLite** - 数据存储（由爬虫写入）
- **weibo-crawler** - 爬虫核心（原项目）

## 开源协议

MIT License

## 致谢

本项目基于 [dataabc/weibo-crawler](https://github.com/dataabc/weibo-crawler)，感谢原作者的贡献。

