# Vercel + Supabase 部署指南

## 部署步骤

### 第一步：配置Supabase数据库
1. 登录Supabase控制台: https://app.supabase.com
2. 选择项目: `jdsleruuwyinnkbzysyu`
3. 进入SQL Editor，运行 `supabase/migrations/20260313000000_init_tables.sql` 中的所有SQL语句
4. 确认所有表创建成功

### 第二步：部署到Vercel

#### 方法1：通过Vercel控制台部署（推荐）
1. Fork本项目到你的GitHub账户
2. 登录Vercel控制台: https://vercel.com
3. 点击 "New Project"，选择你Fork的仓库
4. 配置项目：
   - **Framework Preset**: 选择 "Other"
   - **Root Directory**: 保持默认
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('seyonec/ChemBERTa-zinc-base-v1'); AutoModel.from_pretrained('seyonec/ChemBERTa-zinc-base-v1')"
     ```
   - **Output Directory**: `.`
   - **Install Command**: `pip install -r requirements.txt`

5. 配置环境变量：
   | 变量名 | 值 |
   |--------|----|
   | `PYTHONPATH` | `.` |
   | `FLASK_ENV` | `production` |
   | `SUPABASE_URL` | `https://your-project.supabase.co` |
   | `SUPABASE_KEY` | `your-supabase-anon-key-here` |
   | `MAX_CONTENT_LENGTH` | `104857600` |

6. 点击 "Deploy" 开始部署

#### 方法2：使用Vercel CLI部署
```bash
# 安装Vercel CLI
npm install -g vercel

# 登录
vercel login

# 初始化项目
vercel init openclaw-drug

# 部署到生产环境
vercel deploy --prod \
  --env PYTHONPATH=. \
  --env FLASK_ENV=production \
  --env SUPABASE_URL=https://your-project.supabase.co \
  --env SUPABASE_KEY=your-supabase-anon-key-here
```

### 第三步：配置Vercel函数
在项目根目录创建 `api/index.py` 文件（已创建）：
```python
from web.app import app
handler = app.wsgi_app
```

### 第四步：验证部署
1. 部署完成后，Vercel会提供一个访问地址，例如：`https://openclaw-drug.vercel.app`
2. 访问该地址，确认Web界面正常加载
3. 测试各个功能模块是否正常工作

## 部署优化

### 1. 增加函数运行时间
在Vercel项目设置中，将函数最大运行时间调整为60秒（需要Pro计划）。

### 2. 配置缓存规则
添加缓存规则，缓存静态资源：
- 匹配路径: `/static/*`
- 缓存时间: 30天

### 3. 配置自定义域名
在Vercel控制台的"Domains"设置中添加你的自定义域名。

## 运行环境要求

### Vercel函数配置
- 运行时: Python 3.10
- 内存: 1024MB (默认)
- 最大执行时间: 60秒
- 临时磁盘空间: 512MB

### 冷启动优化
首次访问可能需要较长时间（30-60秒），因为需要加载AI模型。可以配置健康检查定期唤醒函数。

## 常见问题

### Q: 部署失败，提示内存不足？
A: Vercel免费版内存限制为1024MB，ChemBERTa模型加载需要约800MB内存，可能会导致OOM。可以考虑：
- 升级到Vercel Pro计划（2GB内存）
- 使用更小的模型版本
- 部署到其他支持更大内存的平台（如Fly.io、Render等）

### Q: 函数执行超时？
A: ADMET预测和虚拟筛选是计算密集型任务，可能需要较长时间。可以：
- 升级到Vercel Pro，延长函数执行时间到60秒
- 使用异步任务队列（如Supabase Edge Functions + pg_cron）
- 前端实现轮询查询任务状态

### Q: 如何处理大文件上传？
A: Vercel默认上传限制为4.5MB，要支持更大的文件：
- 使用Supabase Storage直接上传文件
- 前端先上传到Supabase Storage，然后将文件URL传给后端处理

## 替代部署方案

如果Vercel资源限制无法满足需求，可以考虑以下方案：

### 方案1: Fly.io部署
```bash
# 安装flyctl
curl -L https://fly.io/install.sh | sh

# 初始化项目
fly launch

# 部署
fly deploy
```

### 方案2: Render部署
1. 连接GitHub仓库
2. 配置构建命令: `pip install -r requirements.txt`
3. 配置启动命令: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 web.app:app`
4. 添加环境变量

### 方案3: 传统服务器部署
```bash
# 克隆代码
git clone <your-repo-url>
cd openclaw-drug

# 安装依赖
pip install -r requirements.txt

# 配置Nginx + Gunicorn
# 参考DEPLOYMENT.md中的生产部署指南
```

## 监控和维护

### Supabase监控
1. 进入Supabase控制台 → 项目 → 监控
2. 查看数据库查询性能、API调用次数、存储使用情况

### Vercel监控
1. 进入Vercel控制台 → 项目 → 函数
2. 查看函数调用次数、执行时间、错误率

### 日志查看
- Vercel函数日志: Vercel控制台 → 项目 → 函数 → 日志
- Supabase日志: Supabase控制台 → 项目 → 日志