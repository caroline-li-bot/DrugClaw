# 推送代码到GitHub指南

## 方法一：使用HTTPS推送（推荐）
```bash
cd /root/.openclaw/workspace/openclaw-drug

# 设置远程仓库（替换为你的GitHub token）
git remote set-url origin https://ghp_你的GitHub令牌@github.com/caroline-li-bot/openclaw-drug.git

# 推送代码
git push -u origin main
```

## 方法二：使用SSH推送
1. 生成SSH密钥（如果还没有）：
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

2. 把 `~/.ssh/id_ed25519.pub` 的内容添加到GitHub账户的SSH密钥中

3. 推送代码：
```bash
git remote set-url origin git@github.com:caroline-li-bot/openclaw-drug.git
git push -u origin main
```

## 已创建的GitHub仓库地址
🔗 **代码仓库**: https://github.com/caroline-li-bot/openclaw-drug

## 部署到Vercel步骤
1. 打开Vercel控制台：https://vercel.com
2. 点击 "Add New..." → "Project"
3. 选择刚刚创建的 `caroline-li-bot/openclaw-drug` 仓库
4. 配置项目：
   - **Project Name**: `openclaw-drug`
   - **Framework Preset**: 选择 `Other`
   - **Root Directory**: 保持默认
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('seyonec/ChemBERTa-zinc-base-v1'); AutoModel.from_pretrained('seyonec/ChemBERTa-zinc-base-v1')"
     ```
   - **Output Directory**: `.`
   - **Install Command**: `pip install -r requirements.txt`

5. 添加环境变量：
   | 变量名 | 值 |
   |--------|----|
   | `PYTHONPATH` | `.` |
   | `FLASK_ENV` | `production` |
   | `SUPABASE_URL` | `https://your-project.supabase.co` |
   | `SUPABASE_KEY` | `your-supabase-anon-key-here` |

6. 点击 "Deploy"

## 自定义域名配置
部署完成后，在Vercel项目设置中添加自定义域名：
- **域名**: `drug.openclaw.ai` （或者你想要的其他域名）
- Vercel会自动生成DNS记录，在你的域名解析服务商添加相应的CNAME记录即可

## 预期访问地址
- 🎉 **Vercel默认域名**: `https://openclaw-drug.vercel.app`
- 🌐 **自定义域名**: `https://drug.openclaw.ai`（配置完成后）

## 项目介绍更新
可以在GitHub仓库的About部分添加：
- **Description**: 药物研发全流程自动化助手，支持文献智能分析、ADMET性质预测、虚拟筛选，基于OpenClaw框架开发
- **Website**: 填写你的Vercel访问地址
- **Topics**: `drug-discovery`, `cheminformatics`, `virtual-screening`, `admet`, `ai-in-drug`, `openclaw`