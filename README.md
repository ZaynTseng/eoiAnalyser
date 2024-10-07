# 澳洲189签证邀请数据分析工具

## 项目简介

这个项目是一个用于分析澳大利亚189技术移民签证邀请数据的工具。它使用 Streamlit 创建了一个交互式的 web
应用，允许用户可视化和探索不同职业、EOI 状态和时间段的邀请数据。

## 功能特点

- 自动加载本地 `/data/` 目录中的所有 CSV 数据文件
- 交互式选择职业、EOI 状态、积分和时间段
- 使用 Plotly 生成动态的横向条形图，展示不同时间段的邀请数量
- 支持多个时间段的数据对比

## 安装说明

1. 克隆此仓库：
   ```
   git clone https://github.com/ZaynTseng/eoiAnalyser.git
   cd eoiAnalyser
   ```

2. 创建并激活虚拟环境（推荐）：
   ```
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
   ```

3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

## 使用方法

1. 将您的 CSV 数据文件放入项目根目录下的 `/data/` 文件夹中。

2. 运行 Streamlit 应用：
   ```
   streamlit run main.py
   ```

3. 在浏览器中打开显示的本地 URL（通常是 http://localhost:8501）。

4. 使用侧边栏的选项来筛选和探索数据。

## 数据格式要求

请确保您的 CSV 文件包含以下列：

- `Occupation`：职业名称
- `EOI Status`：EOI 状态
- `Points`：申请人的积分
- `As At Month`：数据的月份（格式：MM/YYYY）
- `Count EOIs`：EOI 的数量

## 贡献指南

欢迎对本项目进行贡献！如果您有任何改进意见或发现了 bug，请创建一个 issue 或提交一个 pull request。

## 关于作者

本项目由 [ZaynTseng](https://github.com/ZaynTseng) 开发和维护。

## 许可证

本项目采用 MIT 许可证。详情请参见 [LICENSE](LICENSE) 文件。