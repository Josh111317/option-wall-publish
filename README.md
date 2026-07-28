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

- 页面访问：浏览器端每个 Streamlit 会话只发送一次
- 日期选择事件：`select_trade_date`
- Tab 点击事件：`view_tab`
- 下载事件：`download_result_file`
- 报告解锁事件：`view_report`
- 报告停留满 30 秒：`report_engaged`
- 使用专用按钮复制报告：`copy_report`
- 个人专栏阅读：`view_personal_column`

自动报告正文默认不下发到页面。访客点击“查看完整市场结构分析报告”后才会显示正文并记录
`view_report`；停留满 30 秒后记录 `report_engaged`；点击“复制完整报告”并成功写入剪贴板后记录
`copy_report`。这些统计都是匿名事件，不能识别访客姓名。

在 GA4 的“管理 → 数据显示 → 自定义定义”中创建以下事件级自定义维度：

| 维度名称 | 事件参数 |
| --- | --- |
| Tab 名称 | `tab_name` |
| 报告类型 | `report_type` |
| 交易日期 | `trade_date` |
| 标的 | `underlying` |
| 合约月份 | `contract_month` |
| 文件名 | `file_name` |
| 专栏标题 | `post_title` |

注册后通常需要等待一段时间，才能在 GA4“探索”中按这些参数拆分事件。建议建立：

- 内容使用：`view_tab`、`view_report`、`report_engaged`
- 报告复制：`copy_report`
- 文件下载：`download_result_file`
- 使用漏斗：`page_view → view_report → report_engaged → download_result_file`

可以把 `download_result_file`、`report_engaged` 标记为关键事件。

Streamlit Cloud 线上部署需要在 App secrets 中配置：

```toml
GA_API_SECRET = "你的 GA4 Measurement Protocol api_secret"
```

不要把 `GA_API_SECRET` 写入 GitHub 仓库。

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
