# option-wall-publish

只读发布版 Option Wall Dashboard。

这个仓库只展示已经由本地主系统导出的结果，不提供上传文件，不读取 Access 数据库，也不重新计算期权指标。

## 本地预览

```bash
streamlit run publish_app.py
```

Windows 可以双击：

```text
start_publish_dashboard.bat
```

默认读取：

```text
daily_data/
```

## 每日更新流程

1. 在本地主系统 `option_wall_system/app.py` 完成计算。
2. 在主系统“导出结果”中点击一键保存，结果会写入：

```text
D:\codex\options\option_wall_publish\daily_data
```

3. 本地预览 `publish_app.py`。
4. 双击 `publish_update.bat`，提交并推送当天 `daily_data` 到 GitHub。

## 云端部署

Streamlit Community Cloud 中选择：

```text
publish_app.py
```

依赖见：

```text
requirements.txt
```

## 展示内容

- 今日总览
- ETF Gamma Wall
- 分价位结构
- Wall 可信度
- 现价位置分析
- 多标的对比
- 自动报告
- 下载结果

