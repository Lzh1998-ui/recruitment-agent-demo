# Recruitment Agent

AI 驱动的招聘管理系统，基于 Streamlit 构建。

## 功能

- 候选人管理（添加/查看/编辑/删除）
- 简历上传与 AI 解析
- 职位管理
- AI 智能匹配（多维度评分）
- 面试安排与跟进
- 招聘漏斗统计
- Excel 导出

## 快速开始

### 1. 安装依赖

双击运行 `install.bat`，或手动执行：

```bash
python -m pip install -r requirements.txt
```

### 2. 启动系统

双击运行 `start.bat`，浏览器自动打开 `http://localhost:8501`

### 3. 配置 AI（首次使用）

首次启动会弹出配置向导，填入 AI API Key 即可：
- 支持 DeepSeek、OpenAI、SiliconFlow 等兼容 API
- API Base URL 和模型名称均可自定义

## 配置说明

配置文件：`settings.json`（自动创建）

| 字段 | 说明 | 示例 |
|------|------|------|
| `api_key` | AI API Key | `sk-...` |
| `api_base` | API 接口地址 | `https://api.deepseek.com/v1` |
| `model` | 模型名称 | `deepseek-chat` |
| `company_name` | 公司名称（可选）| `某科技有限公司` |

也可在系统界面点击侧边栏「⚙️ 系统设置」随时修改。

## 环境要求

- Python 3.9+
- Windows / macOS / Linux

## 目录结构

```
recruitment_agent/
├── app.py              # 主程序（Streamlit）
├── db.py               # 数据库操作
├── config.py           # 配置文件
├── ai_match.py         # AI 匹配引擎
├── match_engine.py     # 规则匹配引擎
├── resume_parser.py    # 简历解析
├── excel_export.py     # Excel 导出
├── requirements.txt    # 依赖清单
├── install.bat        # 依赖安装脚本（Windows）
├── start.bat          # 启动脚本（Windows）
├── settings.json       # 用户配置（自动生成）
├── recruitment.db     # SQLite 数据库（自动生成）
└── resumes/           # 简历文件存储目录
```

## 常见问题

**Q: 启动后提示「未找到 Python」**
A: 请先安装 Python 3.9+，安装时勾选「Add Python to PATH」

**Q: AI 匹配不工作**
A: 检查 `settings.json` 中的 `api_key` 是否正确，或在「系统设置」页面测试连接。

**Q: 如何迁移数据？**
A: 直接复制整个文件夹即可，`recruitment.db` 包含所有数据。
