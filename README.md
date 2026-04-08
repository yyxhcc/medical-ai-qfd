# Medical AI QFD - 多智能体质量功能展开系统

基于急症室（A&E）等候时间数据的多智能体QFD质量功能展开分析系统。

## 项目简介

本项目采用多智能体系统架构，通过四个专业化的智能体对急症室运营数据进行全面分析，最终转化为QFD质量屋指标，为医疗服务优化提供数据驱动的决策支持。

## 项目结构

```
medical-ai-qfd/
├── data/
│   └── raw/                          # 原始数据目录
│       └── monthly_ae_activity_202601.csv
├── output/
│   ├── figures/                      # 图表输出目录
│   ├── qfd_analysis_report.md        # 学术报告
│   └── analysis_results.json         # 分析结果数据
├── src/
│   ├── agent_time.py                 # 流程时序智能体
│   ├── agent_satisfaction.py         # 满意度分析智能体
│   ├── agent_operation.py            # 业务运营智能体
│   ├── agent_qfd.py                  # QFD质量屋智能体
│   └── workflow.py                   # 总工作流
├── requirements.txt                   # Python依赖
└── README.md                          # 项目说明
```

## 智能体说明

### 1. Agent Time - 流程时序智能体

**功能**：清洗等候时间数据，识别拥堵瓶颈

- 数据清洗与预处理
- 4小时、8小时、12小时等候率分析
- 识别表现最差的医疗机构
- 生成等候时间分布图

### 2. Agent Satisfaction - 满意度分析智能体

**功能**：挖掘诉求、统计短板、需求分层

- 患者需求层级划分（Critical/High/Medium/Good）
- 部门绩效短板识别
- 高流量低绩效区域定位
- 极端等候时间案例分析

### 3. Agent Operation - 业务运营智能体

**功能**：整合业务数据，识别流程断点

- 多维度业务数据整合
- 效率评分计算
- 区域卫生局（HBT）对比分析
- 流程断点识别

### 4. Agent QFD - QFD质量屋智能体

**功能**：把结果转为QFD质量屋指标

- 质量屋（House of Quality）构建
- 客户需求与技术需求映射
- 权重计算与优先级排序
- 改进建议生成

## 安装说明

### 环境要求

- Python 3.8 或更高版本

### 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行完整工作流

一键运行所有智能体并生成报告：

```bash
cd src
python workflow.py
```

### 单独运行智能体

每个智能体也可以单独运行：

```bash
cd src

# 流程时序分析
python agent_time.py

# 满意度分析
python agent_satisfaction.py

# 业务运营分析
python agent_operation.py

# QFD质量屋分析
python agent_qfd.py
```

## 输出说明

运行完成后，将在 `output/` 目录生成以下内容：

### 图表（output/figures/）

Kieran Healy 学术风格图表，包含8个PDF/PNG格式图表：

1. `figure1_time_bottlenecks` - 拥堵瓶颈识别
2. `figure2_wait_distribution` - 等候时间分布
3. `figure3_demand_tiers` - 需求层级划分
4. `figure4_department_analysis` - 部门分析
5. `figure5_operation_efficiency` - 运营效率
6. `figure6_regional_comparison` - 区域对比
7. `figure7_qfd_weights` - QFD权重与绩效
8. `figure8_qfd_relationship_matrix` - QFD关系矩阵

### 报告（output/）

- `qfd_analysis_report.md` - 完整的学术风格分析报告
- `analysis_results.json` - JSON格式的分析结果数据

## QFD质量屋指标

### 客户需求（Customer Requirements）

1. 等候时间 < 4小时（重要度：10）
2. 等候时间 < 8小时（重要度：8）
3. 等候时间 < 12小时（重要度：9）
4. 高流量处理能力（重要度：7）
5. 部门效率（重要度：8）

### 技术需求（Technical Requirements）

1. 4小时达标率
2. 8小时等候减少
3. 12小时等候减少
4. 流量优化
5. 部门标准化

## 数据来源

- 数据集：Monthly Accident and Emergency Activity
- 数据文件：`data/raw/monthly_ae_activity_202601.csv`

## 论文引用

图表采用 Kieran Healy 学术风格，可直接用于论文发表。

## 许可证

MIT License
