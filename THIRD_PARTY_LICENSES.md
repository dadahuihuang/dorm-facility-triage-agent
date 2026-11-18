# 复用组件清单与许可证说明

本项目为课程作业，复用了以下开源组件。所有组件均为原样调用（未修改其源码），仅通过参数配置与包装函数集成。

## 一、第三方组件

| # | 组件 | 版本 | 来源 | 许可证 | 本项目用途 | 集成方式 |
|---|---|---|---|---|---|---|
| 1 | scikit-learn | 1.9.1 | https://scikit-learn.org/ | BSD-3-Clause | `TfidfVectorizer` 特征提取、`LogisticRegression` / `MultinomialNB` 训练、`f1_score` / `confusion_matrix` 评估 | 直接调用 API，参数配置 |
| 2 | jieba | 0.42.1 | https://github.com/fxsjy/jieba | MIT | 历史工单检索时对文本分词（分类模型本身不使用分词） | 直接调用 `jieba.cut` |
| 3 | pandas | 3.1.1 | https://pandas.pydata.org/ | BSD-3-Clause | 读取 CSV、按类别分层划分数据集、汇总结果 | 直接调用 API |
| 4 | Streamlit | 1.67.0 | https://streamlit.io/ | Apache-2.0 | 构建学生报修端与管理员复核台网页 | 直接调用组件，自定义 CSS |
| 5 | zhipuai SDK | 2.1.5.20250825 | https://open.bigmodel.cn/ | 官方 SDK 许可 | 调用 GLM-4-Flash 生成客服播报文本 | 直接调用 `ZhipuAI().chat.completions.create` |
| 6 | python-dotenv | 1.2.4 | https://github.com/theskumar/python-dotenv | BSD-3-Clause | 从 `.env` 读取 `ZHIPU_API_KEY`，避免密钥硬编码 | 直接调用 `load_dotenv` |
| 7 | joblib | 1.6.0 | https://joblib.readthedocs.io/ | BSD-3-Clause | 序列化 `vectorizer.pkl` 与 `lr_model.pkl` | 直接调用 `dump` / `load` |
| 8 | NumPy | 2.5.5 | https://numpy.org/ | BSD-3-Clause | scikit-learn 的底层依赖，用于概率数组运算 | 间接依赖 |

### 各许可证要点

- **BSD-3-Clause**：允许商用与修改，要求保留版权声明与免责声明，不得使用原作者名义为衍生作品背书。
- **MIT**：允许商用与修改，要求保留版权声明与许可声明。
- **Apache-2.0**：允许商用与修改，需保留版权与许可声明，修改文件需标注，附 NOTICE（如有）。

本项目未修改上述组件的源码，仅以依赖形式调用，因此按要求在仓库中保留本清单即可满足署名义务。

## 二、自研部分

以下模块由本人独立编写，不涉及第三方代码：

| 模块 | 文件 | 说明 |
|---|---|---|
| 数据集生成 | `make_csv.py` | 7 类模板、错别字注入、混合故障拼接、去重与分层划分 |
| 文本清洗 | `src/train.py`、`src/agent_router.py` | 去标点/位置实体/客套词，训练与推理共用 |
| 位置抽取与场景校验 | `src/agent_router.py` | 楼栋/楼层/房间号/公区抽取，室内强制房间号 |
| 多轮状态与拆单 | `src/agent_router.py` | 上下文合并、部分出单、补齐后合并 |
| 高危规则与派单映射 | `src/agent_router.py` | 关键词表、7 部门映射、SLA |
| 工单库与人工复核 | `database.py`、`app.py` | SQLite 表设计、待复核列表、人工改派 |
| 验收测试 | `experiments/run_test_cases.py` | 7 个端到端用例与自动判定 |

## 三、数据说明

- 数据集共 2934 条：23 条人工整理的真实报修素材（已改写，去除姓名、学号、房号）+ 2911 条模板合成样本。
- 未使用任何需授权才能分发的第三方数据集，不涉及个人隐私数据。
- `data/history_tickets.csv` 为自建的模拟历史工单，不含真实用户信息。

## 四、密钥与安全

`ZHIPU_API_KEY` 仅存放于本地 `.env`，`.gitignore` 已排除 `.env`、`data/tickets.db` 等敏感/运行时文件。源码中不存在硬编码密钥，报告与截图中亦不含密钥。

## 五、免责声明

本项目的第三方组件按其原始许可证"按原样"提供，作者不对使用本系统造成的任何直接或间接损失负责。课程作业用途之外的使用请自行评估合规性。
