# 部署指南

## 快速启动

### 方法1: 一键启动脚本（推荐）
```bash
./start_web.sh
```

脚本会自动创建虚拟环境、安装依赖、启动服务。

### 方法2: 手动启动
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r web/requirements.txt

# 启动服务
python web/app.py --host 0.0.0.0 --port 7890
```

### 方法3: Docker部署
```bash
# 构建镜像
docker build -t openclaw-drug -f web/Dockerfile .

# 运行容器
docker run -p 7890:7890 openclaw-drug
```

## 访问地址
服务启动后访问：http://localhost:7890

## 功能说明

### 📚 文献分析
- **功能**: 自动搜索PubMed数据库的文献，分析研究热点，提取关键发现
- **输入**: 关键词、最大文献数量、时间范围
- **输出**: 研究热点统计、关键发现、完整分析报告

### 🧪 ADMET预测
- **功能**: 预测化合物的吸收、分布、代谢、排泄和毒性性质
- **支持模式**:
  - 单模式：输入单个SMILES字符串
  - 批量模式：上传CSV文件（包含smiles列）
- **输出**: 综合评分、开发决策建议、详细性质报告

### 🔍 虚拟筛选
- **功能**: 自动化分子对接，从化合物库中筛选活性化合物
- **输入**: 
  - 靶点PDB文件
  - 化合物库CSV文件（包含smiles列）
  - 结合位点坐标和盒子大小
- **输出**: 候选化合物列表、结合能排序、筛选报告

## 系统要求

### 最低配置
- CPU: 4核
- 内存: 8GB
- 硬盘: 20GB可用空间
- 操作系统: Linux/macOS/Windows

### 推荐配置
- CPU: 8核+
- 内存: 16GB+
- GPU: NVIDIA GPU (可选，加速AI预测)
- 硬盘: 50GB+ SSD

## 依赖说明

### 基础依赖
- Python 3.9+
- RDKit (化学信息学库)
- Flask (Web框架)
- Pandas/Numpy (数据处理)
- PyTorch (深度学习框架)
- Transformers (HuggingFace Transformers)

### 可选依赖
- AutoDock Vina (分子对接)
- MGLTools (配体/受体制备)
- PyMOL (分子可视化)

## 环境变量配置

```bash
# 可选配置
export PUBMED_EMAIL="your@email.com"  # PubMed API访问邮箱
export VINA_PATH="/path/to/vina"      # AutoDock Vina路径
export MGLTOOLS_PATH="/path/to/mgltools"  # MGLTools路径
```

## 常见问题

### Q: 首次启动很慢？
A: 首次启动会自动下载ChemBERTa等AI模型，大小约1GB，下载完成后后续启动会很快。

### Q: 虚拟筛选功能不可用？
A: 虚拟筛选需要安装AutoDock Vina和MGLTools，请参考官方文档安装：
- AutoDock Vina: https://vina.scripps.edu/
- MGLTools: https://ccsb.scripps.edu/mgltools/

### Q: 文献分析返回结果太少？
A: 可以调大"最大文献数量"参数，或者扩大时间范围。PubMed API有访问频率限制，短时间大量请求可能会被限流。

### Q: 如何上传大的化合物库？
A: 系统默认最大上传限制是100MB，如果需要更大的文件，可以修改`web/app.py`中的`MAX_CONTENT_LENGTH`配置。

## 生产部署建议

### 使用Gunicorn
```bash
gunicorn --bind 0.0.0.0:7890 --workers 4 --timeout 120 web.app:app
```

### Nginx反向代理配置
```nginx
server {
    listen 80;
    server_name drug.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:7890;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
        proxy_read_timeout 300;
    }
}
```

### 配置HTTPS (Let's Encrypt)
```bash
sudo certbot --nginx -d drug.yourdomain.com
```