# option-wall-publish

只读发布版 Option Wall Dashboard。

这个仓库只展示已经由本地主系统导出的结果，不提供 Excel/CSV 上传，不读取 Access 数据库，也不重新计算期权指标。

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

如果普通推送失败，可以在当前目录手动执行：

```bash
git push --force-with-lease origin main
```

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
- 留言反馈
- 下载结果

## Google Analytics

`publish_app.py` 中已经接入 GA4：

```text
G-9VW3TM6793
```

当前记录：

- 页面访问
- 日期选择事件：`select_trade_date`
- Tab 点击事件：`view_tab`
- 下载事件：`download_result_file`

## 留言反馈

默认预留了 Google Form / 腾讯问卷 / 飞书表单嵌入位。

创建表单后，把公开填写链接填入 `publish_app.py`：

```python
FEEDBACK_FORM_URL = "你的表单公开链接"
```

## 打赏支持

可以把二维码图片放入：

```text
assets/wechat_reward.png
assets/alipay_reward.png
```

也可以在 `publish_app.py` 填入链接：

```python
DONATION_LINKS = {
    "爱发电": "你的链接",
    "Buy Me a Coffee": "你的链接",
}
```

打赏是自愿支持，不影响结果浏览和文件下载。
