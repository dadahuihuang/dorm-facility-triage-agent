# -*- coding: utf-8 -*-
"""生成《复用组件清单与许可证说明》docx，供导出 PDF 作为提交材料④。"""
import os

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'docs', '复用组件清单与许可证说明.docx')

doc = docx.Document()

# 页面与边距（A4，窄边距以容纳 6 列表格）
for s in doc.sections:
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.left_margin = Cm(1.6)
    s.right_margin = Cm(1.6)
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(2.0)

# 全局字体
style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')


def set_cn(run, name='宋体', size=10.5, bold=False):
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)


def para(text, size=10.5, bold=False, align=None, space_after=6, first_indent=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.5
    if first_indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    if align:
        p.alignment = align
    r = p.add_run(text)
    set_cn(r, size=size, bold=bold)
    return p


def heading(text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    set_cn(r, name='黑体', size=15 if level == 1 else 12, bold=True)
    return p


def make_table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        r = hdr[i].paragraphs[0].add_run(h)
        set_cn(r, size=9.5, bold=True)
        hdr[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ''
            r = cells[i].paragraphs[0].add_run(str(val))
            set_cn(r, size=8.5)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    return t


# ================= 标题 =================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
r = p.add_run('复用组件清单与许可证说明')
set_cn(r, name='黑体', size=20, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('——宿舍楼公共设施报修文本分诊与低置信复核 Agent')
set_cn(r, size=11)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('课程：机器学习　　姓名：唐辉　　学号：028123179　　日期：2026.11.18')
set_cn(r, size=10)

para('本文档为课程期末项目提交材料④，列出项目复用的全部第三方组件及其许可证、来源、用途，'
     '并说明自研部分与数据处理方式。所有组件均以依赖形式调用，未修改其源码。', size=10)

# ================= 一、第三方组件 =================
heading('一、第三方组件清单', 1)

rows = [
    ['1', 'scikit-learn', '1.9.1', 'https://scikit-learn.org/', 'BSD-3-Clause',
     'TF-IDF 特征提取、逻辑回归/朴素贝叶斯训练、F1 与混淆矩阵评估'],
    ['2', 'jieba', '0.42.1', 'https://github.com/fxsjy/jieba', 'MIT',
     '历史工单检索时的中文分词（分类模型不依赖分词）'],
    ['3', 'pandas', '3.1.1', 'https://pandas.pydata.org/', 'BSD-3-Clause',
     '读取 CSV、按类别分层划分数据集、结果汇总'],
    ['4', 'Streamlit', '1.67.0', 'https://streamlit.io/', 'Apache-2.0',
     '构建学生报修端与管理员复核台网页界面'],
    ['5', 'zhipuai SDK', '2.1.5.20250825', 'https://open.bigmodel.cn/', '官方 SDK 许可',
     '调用 GLM-4-Flash 生成客服播报文本'],
    ['6', 'python-dotenv', '1.2.4', 'https://github.com/theskumar/python-dotenv', 'BSD-3-Clause',
     '从 .env 读取 API Key，避免密钥硬编码'],
    ['7', 'joblib', '1.6.0', 'https://joblib.readthedocs.io/', 'BSD-3-Clause',
     '序列化与加载 vectorizer.pkl、lr_model.pkl'],
    ['8', 'NumPy', '2.5.5', 'https://numpy.org/', 'BSD-3-Clause',
     'scikit-learn 的底层数值依赖'],
]
make_table(['#', '组件', '版本', '来源链接', '许可证', '本项目用途'], rows,
           [0.8, 2.6, 2.6, 4.9, 2.3, 4.6])

para('')

# ================= 二、许可证要点 =================
heading('二、许可证要点与合规说明', 1)
para('BSD-3-Clause：允许商业使用与修改，要求保留版权声明与免责声明，且不得以原作者名义为衍生作品背书。')
para('MIT：允许商业使用与修改，要求保留版权声明与许可声明。')
para('Apache-2.0：允许商业使用与修改，要求保留版权与许可声明；若修改文件需标注，并附 NOTICE 文件（如有）。')
para('本项目未修改上述组件的源代码，仅通过公开 API 调用并做参数配置，因此保留本清单并注明版本与许可证即满足署名义务。'
     '各组件的完整许可证文本可在其官方仓库的 LICENSE 文件中查阅。')

# ================= 三、自研部分 =================
heading('三、自研部分（不涉及第三方代码）', 1)
rows2 = [
    ['数据集生成', 'make_csv.py', '7 类模板、错别字注入、混合故障拼接、去重与分层划分'],
    ['文本清洗', 'src/train.py、src/agent_router.py', '去标点/位置实体/客套词，训练与推理共用同一函数'],
    ['位置抽取与场景校验', 'src/agent_router.py', '楼栋/楼层/房间号/公区抽取，室内强制房间号'],
    ['多轮状态与拆单', 'src/agent_router.py', '上下文合并、部分出单、补齐后合并出单'],
    ['高危规则与派单映射', 'src/agent_router.py', '关键词表、7 个部门映射、SLA 设定'],
    ['工单库与人工复核', 'database.py、app.py', 'SQLite 表设计、待复核列表、人工改派与下发'],
    ['验收与诊断脚本', 'experiments/', '7 个端到端用例、清洗消融、混淆矩阵、规则查全率'],
]
make_table(['模块', '文件', '说明'], rows2, [3.4, 5.2, 10.4])

para('')

# ================= 四、数据说明 =================
heading('四、数据来源与隐私处理', 1)
para('数据集共 2934 条，由 23 条人工整理的真实报修素材与 2911 条模板合成样本组成。'
     '真实素材已改写表达并去除姓名、学号与具体房号；位置信息统一抽象为“某宿舍”“某栋某层走廊”等形式。')
para('项目未使用任何需授权才能分发的第三方数据集，data/history_tickets.csv 为自建模拟历史工单，不含真实用户信息。')

# ================= 五、密钥与安全 =================
heading('五、密钥管理与安全', 1)
para('ZHIPU_API_KEY 仅存放于本地 .env 文件，仓库 .gitignore 已排除 .env、data/tickets.db 等敏感或运行时文件；'
     '源码中不存在硬编码密钥，报告与截图亦不含密钥内容。')

# ================= 六、免责声明 =================
heading('六、免责声明', 1)
para('上述第三方组件按其原始许可证“按原样”提供，作者不对使用本系统造成的任何直接或间接损失负责。'
     '本清单仅用于课程作业的合规说明。')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
print('saved:', OUT)
