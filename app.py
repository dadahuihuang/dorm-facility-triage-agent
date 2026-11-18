import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath("src"))
from agent_router import triage
from database import insert_ticket, get_pending_tickets, update_ticket_by_human, get_all_tickets

st.set_page_config(page_title="宿舍设施智能报修", layout="wide")

# ================= 自定义 CSS 样式 =================
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 20px;
    }
    .chat-row.user-row { justify-content: flex-end; }
    .chat-row.agent-row { justify-content: flex-start; }
    
    .chat-bubble {
        max-width: 75%;
        padding: 12px 18px;
        border-radius: 15px;
        font-size: 1rem;
        line-height: 1.6;
        position: relative;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .user-bubble {
        background-color: #2b579a;
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .agent-bubble {
        background-color: #2d2d2d;
        color: #f0f0f0;
        border: 1px solid #404040;
        border-bottom-left-radius: 4px;
    }

    .metric-label { font-size: 0.9rem; color: #aaa; }
    .metric-value { font-size: 1.4rem; font-weight: bold; color: #fff; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# ================= 状态初始化 =================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_context" not in st.session_state:
    st.session_state.agent_context = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ================= 侧边栏 =================
with st.sidebar:
    st.title("系统控制台")
    
    if not st.session_state.is_admin:
        st.success("当前身份：学生用户")
        st.markdown("---")
        if st.button("清空当前对话", use_container_width=True):
            st.session_state.messages = []
            st.session_state.agent_context = None
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 管理员入口")
        admin_pwd = st.text_input("请输入管理员密码", type="password")
        if st.button("登录后台", use_container_width=True):
            if admin_pwd == "admin123":
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("密码错误")
    else:
        st.success("当前身份：后勤管理员")
        role = st.radio("视图切换：", ["学生报修端", "管理员复核台"])
        st.markdown("---")
        if st.button("退出管理员登录", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

if not st.session_state.is_admin:
    role = "学生报修端"

# ================= 视图一：学生报修端 =================
if role == "学生报修端":
    st.title("宿舍公共设施智能报修")
    st.write("请描述故障，系统将自动分诊并生成工单。")
    st.markdown("---")

    # 渲染历史对话记录
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-row user-row"><div class="chat-bubble user-bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-row agent-row"><div class="chat-bubble agent-bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
            
            if "tickets" in msg:
                for t in msg["tickets"]:
                    if t.get("high_risk", False):
                        st.error("高危预警：已标记为紧急情况")
                        
                    st.write("")
                    st.markdown("**系统结构化结论**")
                    
                    # 第一排
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f'<div class="metric-label">设施类别</div><div class="metric-value">{t["facility_label"]}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="metric-label">置信度</div><div class="metric-value">{t["confidence"]*100:.1f}%</div>', unsafe_allow_html=True)
                    status_text = "需人工复核" if t["need_human"] else "自动分诊"
                    c3.markdown(f'<div class="metric-label">状态</div><div class="metric-value">{status_text}</div>', unsafe_allow_html=True)
                    
                    # 🌟 第二排：加上了报修地点
                    c4, c5, c6 = st.columns(3)
                    c4.markdown(f'<div class="metric-label">报修地点</div><div class="metric-value">{t.get("location", "未提供")}</div>', unsafe_allow_html=True)
                    c5.markdown(f'<div class="metric-label">派单部门</div><div class="metric-value">{t["assigned_dept"]}</div>', unsafe_allow_html=True)
                    c6.markdown(f'<div class="metric-label">要求响应</div><div class="metric-value">{t["sla_target"]}</div>', unsafe_allow_html=True)
                    
                    if t.get("history_retrieval"):
                        st.info(f"历史参考：发现相似工单，建议方案 —— {t['history_retrieval']['solution']}")
                    if t.get("tool_alert"):
                        st.warning(f"外部工具预警：{t['tool_alert']}")
                        
                    with st.expander(f"查看完整工单草案 JSON ({t['facility_label']})"):
                        st.json(t)
                    st.markdown("---")

    # 初始欢迎语
    if len(st.session_state.messages) == 0:
        st.markdown("""
        <div class="chat-row agent-row">
            <div class="chat-bubble agent-bubble">
            你好，我是宿舍报修助手。请直接告诉我你遇到的故障（例如：三号楼二层走廊灯坏了）。
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 用户输入框
    if prompt := st.chat_input("请输入故障描述"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="chat-row user-row"><div class="chat-bubble user-bubble">{prompt}</div></div>', unsafe_allow_html=True)

        with st.spinner("正在分析..."):
            try:
                result = triage(raw_text=prompt, context=st.session_state.agent_context)
            except Exception as e:
                result = {"status": "error", "message": f"调用失败: {e}"}

            if result.get("status") == "error":
                st.error(result["message"])
                st.session_state.messages.append({"role": "assistant", "content": result["message"]})
            
            elif result.get("status") == "chitchat":
                st.markdown(f'<div class="chat-row agent-row"><div class="chat-bubble agent-bubble">{result["message"]}</div></div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": result["message"]})
            
            elif result.get("status") == "ask_for_location":
                st.markdown(f'<div class="chat-row agent-row"><div class="chat-bubble agent-bubble">{result["message"]}</div></div>', unsafe_allow_html=True)
                st.caption("请直接输入补充信息（如：3号楼2层）")
                st.session_state.messages.append({"role": "assistant", "content": result["message"]})
                st.session_state.agent_context = result
            
            elif result.get("status") == "success":
                tickets = result.get("tickets", [])
                st.session_state.agent_context = None 
                
                for ticket in tickets:
                    insert_ticket(ticket)
                
                response_text = result.get("ai_response", "工单已生成。")
                st.markdown(f'<div class="chat-row agent-row"><div class="chat-bubble agent-bubble">{response_text}</div></div>', unsafe_allow_html=True)
                
                for ticket in tickets:
                    if ticket.get("high_risk", False):
                        st.error("高危预警：已标记为紧急情况")
                        
                    st.write("")
                    st.markdown("**系统结构化结论**")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f'<div class="metric-label">设施类别</div><div class="metric-value">{ticket["facility_label"]}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="metric-label">置信度</div><div class="metric-value">{ticket["confidence"]*100:.1f}%</div>', unsafe_allow_html=True)
                    status_text = "需人工复核" if ticket["need_human"] else "自动分诊"
                    c3.markdown(f'<div class="metric-label">状态</div><div class="metric-value">{status_text}</div>', unsafe_allow_html=True)
                    
                    # 🌟 第二排：加上了报修地点
                    c4, c5, c6 = st.columns(3)
                    c4.markdown(f'<div class="metric-label">报修地点</div><div class="metric-value">{ticket.get("location", "未提供")}</div>', unsafe_allow_html=True)
                    c5.markdown(f'<div class="metric-label">派单部门</div><div class="metric-value">{ticket["assigned_dept"]}</div>', unsafe_allow_html=True)
                    c6.markdown(f'<div class="metric-label">要求响应</div><div class="metric-value">{ticket["sla_target"]}</div>', unsafe_allow_html=True)
                    
                    if ticket.get("history_retrieval"):
                        st.info(f"历史参考：发现相似工单，建议方案 —— {ticket['history_retrieval']['solution']}")
                    if ticket.get("tool_alert"):
                        st.warning(f"外部工具预警：{ticket['tool_alert']}")
                        
                    with st.expander(f"查看完整工单草案 JSON ({ticket['facility_label']})"):
                        st.json(ticket)
                    st.markdown("---")
                    
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text, 
                    "tickets": tickets 
                })

# ================= 视图二：管理员复核台 =================
elif role == "管理员复核台":
    st.title("后勤工单管理控制台")
    st.write("待人工复核及历史工单列表。")
    
    tab1, tab2 = st.tabs(["待人工复核工单", "所有历史工单"])
    
    with tab1:
        pending_df = get_pending_tickets()
        if pending_df.empty:
            st.success("当前没有待复核的疑难工单。")
        else:
            st.warning(f"当前有 {len(pending_df)} 条工单需要人工确认。")
            edited_df = st.data_editor(
                pending_df,
                column_config={
                    "id": st.column_config.NumberColumn("工单号", disabled=True),
                    "raw_text": st.column_config.TextColumn("原报修内容", disabled=True),
                    "location": st.column_config.TextColumn("报修地点", disabled=True), # 数据库里也有
                    "facility_label": st.column_config.SelectboxColumn("修改类别", options=["ELEC", "WATER", "HVAC", "FURN", "DOOR", "APPL", "STRUCT"], required=True),
                    "assigned_dept": st.column_config.SelectboxColumn("修改部门", options=["电工班", "水工班", "空调维修组", "木工班", "综合维修组", "厂家售后", "基建科"], required=True),
                    "confidence": st.column_config.NumberColumn("置信度", disabled=True),
                    "create_time": st.column_config.TextColumn("上报时间", disabled=True),
                },
                hide_index=True,
                key="pending_editor"
            )
            
            if st.button("保存修改并下发派单", type="primary"):
                for idx, row in edited_df.iterrows():
                    original_row = pending_df.loc[pending_df['id'] == row['id']].iloc[0]
                    if row['facility_label'] != original_row['facility_label'] or row['assigned_dept'] != original_row['assigned_dept']:
                        update_ticket_by_human(row['id'], row['facility_label'], row['assigned_dept'])
                st.success("修改已保存，工单已下发。")
                st.rerun()

    with tab2:
        all_df = get_all_tickets()
        st.dataframe(all_df, use_container_width=True)