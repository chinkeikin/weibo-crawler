# 合并策略说明

## 为什么大部分不会冲突？

### ✅ 不会冲突的文件（新增文件）

我**只新增了文件**，没有修改原项目的核心代码：

```
新增文件（不会冲突）：
├── api_service/          # 全新的 API 服务层
│   ├── main.py
│   ├── config_manager.py
│   ├── crawler_service.py
│   ├── scheduler.py
│   └── api/
├── run_api.py           # 新的启动脚本
├── install.sh           # 新的安装脚本
├── requirements-api.txt # 新的依赖文件（分离）
└── API_README.md        # 新的文档
```

**原因**：Git 合并时，新增文件不会产生冲突，只会被添加。

### ✅ 原项目文件（未修改）

以下文件**完全没有修改**，合并时不会有任何冲突：

```
原项目文件（未修改）：
├── weibo.py             # 爬虫核心（只调用，不修改）
├── const.py             # 常量配置（只读取，不修改）
├── __main__.py          # 主入口（保留原功能）
├── util/                # 工具类（只调用，不修改）
├── requirements.txt     # 依赖文件（已恢复，不修改）
└── config.json          # 配置文件（运行时修改，不提交）
```

**原因**：
- 我们没有修改这些文件的源码
- 只是**调用**它们的功能
- Git 合并时，原仓库的更新会直接应用

### ⚠️ 已解决的问题：requirements.txt

**之前**：修改了 `requirements.txt`，可能产生冲突

**现在**：✅ **已解决**
- 恢复了原项目的 `requirements.txt`（不修改）
- 创建了独立的 `requirements-api.txt`（新增文件）
- 安装脚本会安装两个依赖文件

**结果**：✅ **完全不会冲突**

## 如何保证不冲突？

### 核心原则

1. **不修改原项目文件**
   - ✅ `weibo.py` - 只调用，不修改
   - ✅ `const.py` - 只读取，不修改
   - ✅ `requirements.txt` - 不修改
   - ✅ `config.json` - 运行时修改，不提交到 Git

2. **只新增文件**
   - ✅ `api_service/` - 全新的 API 层
   - ✅ `requirements-api.txt` - 独立的依赖文件
   - ✅ `run_api.py` - 新的启动脚本

3. **运行时文件不提交**
   - ✅ `config.json.bak` - 备份文件
   - ✅ `*.db` - 数据库文件
   - ✅ `log/` - 日志文件

### 合并流程

```bash
# 1. 添加原仓库为 upstream
git remote add upstream https://github.com/dataabc/weibo-crawler.git

# 2. 获取原仓库更新
git fetch upstream

# 3. 合并更新（通常不会有冲突）
git merge upstream/master

# 4. 如果有冲突，通常是：
#    - 原仓库新增了文件 → 自动添加 ✅
#    - 原仓库更新了文件 → 自动更新 ✅
#    - 我们的新增文件 → 保留 ✅
```

### 实际场景分析

#### 场景1：原仓库更新了 weibo.py

**结果**：✅ **不会冲突**
- **原因**：我们没有修改 weibo.py
- **处理**：直接合并，我们的代码调用更新后的 weibo.py
- **影响**：✅ 自动获得原仓库的 bug 修复和新功能

#### 场景2：原仓库更新了 requirements.txt

**结果**：✅ **不会冲突**
- **原因**：我们没有修改 requirements.txt
- **处理**：直接合并，原仓库的依赖更新会自动应用
- **影响**：✅ 自动获得依赖更新

#### 场景3：原仓库新增了文件

**结果**：✅ **不会冲突**
- **原因**：新增文件不会冲突
- **处理**：自动添加新文件
- **影响**：✅ 自动获得新功能

#### 场景4：原仓库更新了 config.json 结构

**结果**：✅ **不会冲突**
- **原因**：config.json 已添加到 .gitignore，不跟踪
- **处理**：本地配置文件不受影响
- **影响**：✅ 需要手动更新本地配置（如果需要）

## 配置管理说明

### config.json 的处理

**重要**：`config.json` 是**运行时配置文件**，不是源码文件。

**设计**：
1. ✅ 不提交到 Git（添加到 .gitignore）
2. ✅ API 服务会读取和更新它（运行时操作）
3. ✅ 每次更新前自动备份（config.json.bak）

**好处**：
- ✅ 不会与 Git 合并冲突
- ✅ 每个环境可以有不同配置
- ✅ 配置修改不会影响代码合并

### 依赖管理

**分离策略**：
```
requirements.txt        # 原项目依赖（不修改）
requirements-api.txt    # API 服务依赖（新增）
```

**安装顺序**：
```bash
pip install -r requirements.txt      # 先安装原项目依赖
pip install -r requirements-api.txt  # 再安装 API 依赖
```

**好处**：
- ✅ 依赖清晰分离
- ✅ 可以独立管理版本
- ✅ 完全避免冲突

## 最佳实践总结

### ✅ 推荐做法

1. **保持原项目文件不变**
   ```bash
   # 不要修改这些文件
   - weibo.py
   - const.py
   - requirements.txt
   - __main__.py
   ```

2. **只新增文件**
   ```bash
   # 只添加新文件
   - api_service/
   - requirements-api.txt
   - run_api.py
   ```

3. **运行时文件不提交**
   ```bash
   # .gitignore 中已配置
   - config.json.bak
   - *.db
   - log/
   ```

4. **定期合并原仓库更新**
   ```bash
   git fetch upstream
   git merge upstream/master
   ```

### ❌ 避免的做法

1. **不要修改原项目核心文件**
   - ❌ 修改 weibo.py
   - ❌ 修改 const.py
   - ❌ 修改 requirements.txt

2. **不要提交运行时文件**
   - ❌ 提交 config.json
   - ❌ 提交数据库文件
   - ❌ 提交日志文件

## 验证方法

### 测试合并

```bash
# 1. 添加原仓库
git remote add upstream https://github.com/dataabc/weibo-crawler.git

# 2. 测试合并（不会真正合并）
git fetch upstream
git merge --no-commit --no-ff upstream/master

# 3. 查看是否有冲突
git status

# 4. 取消测试合并
git merge --abort
```

**预期结果**：
- ✅ 没有冲突
- ✅ 原仓库的更新会自动应用
- ✅ 我们的新增文件会保留

## 总结

**为什么不会冲突？**

1. ✅ **只新增文件**，不修改原文件
2. ✅ **分离依赖**，requirements.txt 不修改
3. ✅ **运行时配置不提交**，config.json 不跟踪

**如何保证不冲突？**

1. ✅ **遵循最佳实践**（只新增，不修改）
2. ✅ **使用分离的依赖文件**
3. ✅ **不提交运行时文件**

**结果**：

- ✅ 合并原仓库更新时**完全不会冲突**
- ✅ 自动获得原仓库的 bug 修复和新功能
- ✅ 我们的 API 服务代码**完全保留**
- ✅ 可以轻松同步原仓库更新
