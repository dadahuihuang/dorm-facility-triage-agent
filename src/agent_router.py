import os
import joblib
import jieba
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from zhipuai import ZhipuAI
from dotenv import load_dotenv

load_dotenv()


def _get_api_key():
    """优先读环境变量/.env；部署到 Streamlit Cloud 时改读 st.secrets。"""
    key = os.getenv("ZHIPU_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("ZHIPU_API_KEY")
    except Exception:
        return None


_API_KEY = _get_api_key()
# 没有密钥时不构造客户端，所有播报走兜底文案，分类与规则功能照常可用
client = ZhipuAI(api_key=_API_KEY) if _API_KEY else None

vectorizer = joblib.load("models/vectorizer.pkl")
model = joblib.load("models/lr_model.pkl")

history_df = pd.read_csv("data/history_tickets.csv", encoding="utf-8-sig")
history_texts = [" ".join(jieba.cut(str(t))) for t in history_df['text']]
history_vectorizer = TfidfVectorizer()
history_matrix = history_vectorizer.fit_transform(history_texts)

def check_weather_tool(location=""):
    return {"weather": "暴雨", "alert": "当前有暴雨预警，请优先处理漏水工单！"}

# 高危词库：只保留真正涉及人身安全/重大财产损失的情形。
# 注意："打不开/进不去"已移除——门锁损坏、钥匙忘带属于普通维修，误报会挤占紧急通道。
HIGH_RISK_KEYWORDS = ["漏电", "触电", "冒烟", "冒火", "着火", "焦味", "火花", "漏气", "燃气味", "爆裂",
                      "水漫", "积水", "淹", "反锁", "被困", "困在", "出不去", "要塌", "塌了", "砸到人", "裸露"]

dispatch_rules = {
    "ELEC": {"dept": "电工班", "sla": "2小时内"},
    "WATER": {"dept": "水工班", "sla": "4小时内"},
    "HVAC": {"dept": "空调维修组", "sla": "8小时内"},
    "FURN": {"dept": "木工班", "sla": "24小时内"},
    "DOOR": {"dept": "综合维修组", "sla": "12小时内"},
    "APPL": {"dept": "厂家售后", "sla": "48小时内"},
    "STRUCT": {"dept": "基建科", "sla": "24小时内"}
}

def extract_info(text):
    building = ""
    b_match = re.search(r'([一二三四五六七八九十\d]+[号栋]楼?)', text)
    if b_match: building = b_match.group(1)

    room = ""
    # 优先寻找严格的 3-4 位数字房间号
    r_match_num = re.search(r'(\d{3,4})', text)
    if r_match_num:
        room = r_match_num.group(1)
    else:
        # 如果没有3-4位数字，才去找楼层（比如 2楼、二楼）
        r_match = re.search(r'([\d一二三四五六七八九十]+[层楼]?\s*[\d一二三四五六七八九十]+[室房]?)', text)
        if r_match:
            room = r_match.group(1).replace(" ", "")
        else:
            r_match2 = re.search(r'([一二三四五六七八九十]+[层楼])|(\d{3,4}[室房]?)', text)
            if r_match2: room = r_match2.group(0)

    area = ""
    a_match = re.search(r'([一二三四五六七八九十\d]+[层楼])|(走廊|楼梯间|厕所|卫生间|阳台|洗衣房|洗漱间|大厅|楼道)', text)
    if a_match: area = a_match.group(0)

    # 公区描述（走廊/厕所/洗衣房…）可能不止一个，全部保留，避免师傅上门找不到具体位置
    for mark in re.findall(r'走廊|楼梯间|厕所|卫生间|阳台|洗衣房|洗漱间|大厅|楼道', text):
        if mark not in area and mark not in room:
            area = f"{area}{mark}"

    if area and area in room:
        area = ""
    # 反过来：如果房间号其实只是楼层（2楼），而它已包含在区域描述里，就清掉避免“2楼...2楼”重复
    if room and area and room in area:
        room = ""

    indoor_words = ["寝室", "宿舍", "房间", "床", "桌", "柜", "室内", "空调", "马桶", "插座", "热水器", "饮水机", "灯"]
    public_words = ["走廊", "楼梯", "公共", "洗衣房", "洗漱间", "大厅", "门禁", "楼道", "路灯", "电梯", "井盖", "外墙"]
    
    loc_type = "unknown"
    if any(w in text for w in public_words): loc_type = "public"
    elif any(w in text for w in indoor_words): loc_type = "indoor"

    fault = text
    for entity in [building, room, area]:
        if entity: fault = fault.replace(entity, "")
    fault = re.sub(r'[，,、。！!？?\s]+', '', fault)
    if not fault: fault = text
        
    return building, room, area, fault, loc_type

# 真正“私有、必须精确到房间”的设备。
# 注意：马桶/寝室可能位于公共卫生间或整层寝室，不能一律强制房间号，否则公区报修会被卡死。
STRONG_INDOOR = ["空调", "床", "衣柜", "书桌", "淋浴", "热水器", "插座", "饮水机", "台灯", "床头灯"]

def is_location_complete(building, room, area, loc_type, fault_text):
    has_building = bool(building)
    # 房间号必须有纯数字，且至少3位（比如 302, 1002）
    has_real_room = bool(re.search(r'\d{3,4}', room))
    has_area = bool(area) or bool(re.search(r'[层楼]', room))

    # 室内场景（寝室/宿舍/床/空调…）：必须精确到房间号，师傅才能敲门
    if loc_type == "indoor":
        return has_building and has_real_room
    # 公区场景（走廊/厕所/洗衣房…）：楼栋 + 楼层或房间号即可
    if loc_type == "public":
        return has_building and (has_area or has_real_room)
    # 场景未知但提到私有设备时，同样按室内处理
    if any(w in fault_text for w in STRONG_INDOOR):
        return has_building and has_real_room
    return has_building and (has_area or has_real_room)

def clean_text_for_ml(text):
    clean = re.sub(r'[^\u4e00-\u9fa5]', '', str(text))
    clean = re.sub(r'[一二三四五六七八九十]+[号栋楼区层]', '', clean)
    stop_words = ["你好", "您好", "麻烦", "请", "谢谢", "急", "帮", "帮忙", "报修", "有个", "一个", "这里", "那里"]
    for word in stop_words:
        clean = clean.replace(word, "")
    return clean.strip()

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF\uFE0F\u200D]"
)

def strip_emoji(text):
    """大模型偶尔无视提示词输出 Emoji，这里做兜底清洗。"""
    if not text:
        return text
    return _EMOJI_RE.sub("", text).strip()

def call_llm(system_prompt, user_prompt):
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        )
        return strip_emoji(response.choices[0].message.content) or None
    except Exception as e:
        return None

def generate_ticket_summary(raw_text, label):
    prompt = f"用户报修了：【{raw_text}】，系统分类为：【{label}】。请用10个字以内，非常规范的专业术语总结这个故障。只输出总结内容。"
    return call_llm("你是一个工单总结系统。", prompt) or "设施故障报修"

def process_single_fault(text, location_text):
    clean_input = clean_text_for_ml(text)
    if len(clean_input) < 2: clean_input = text
        
    X = vectorizer.transform([clean_input])
    probs = model.predict_proba(X)[0]
    top2_idx = probs.argsort()[-2:][::-1]
    pred_label = model.classes_[top2_idx[0]]
    confidence = probs[top2_idx[0]]
    margin = confidence - probs[top2_idx[1]]
    
    query_vec = history_vectorizer.transform([" ".join(jieba.cut(str(clean_input)))])
    sim_scores = cosine_similarity(query_vec, history_matrix)[0]
    top_idx = sim_scores.argmax()
    sim_score = sim_scores[top_idx]
    history_match = None
    if sim_score > 0.3:
        history_match = {
            "match_text": history_df.iloc[top_idx]['text'],
            "dept": history_df.iloc[top_idx]['dept'],
            "solution": history_df.iloc[top_idx]['solution']
        }

    high_risk = any(kw in text for kw in HIGH_RISK_KEYWORDS)
    tool_warning = None
    if pred_label == "WATER" and (high_risk or "堵" in text):
        weather_info = check_weather_tool(location_text)
        if weather_info["weather"] == "暴雨":
            tool_warning = weather_info["alert"]

    need_human = False
    reason = "系统自动分诊"
    if high_risk:
        need_human = True
        reason = "命中高危规则，情况紧急"
    elif confidence < 0.6:
        if margin > 0.3: reason = "模型置信度偏低，但预测结果绝对占优，自动放行"
        else:
            need_human = True
            reason = "系统置信度较低，需进一步确认"

    dispatcher = dispatch_rules.get(pred_label, {"dept": "总务处", "sla": "24小时内"})
    current_sla = "15分钟（紧急）" if high_risk else dispatcher["sla"]
    
    return {
        "raw_text": text, "location": location_text, "summary": generate_ticket_summary(text, pred_label),
        "facility_label": pred_label, "confidence": round(float(confidence), 3), "high_risk": high_risk,
        "need_human": need_human, "reason": reason, "history_retrieval": history_match,
        "tool_alert": tool_warning, "assigned_dept": dispatcher["dept"], "sla_target": current_sla
    }

# ================= 核心逻辑 =================
def triage(raw_text, location_text="unknown", context=None, tau=0.6):
    try:
        current_input = str(raw_text).strip()
        
        # 多位置拆分机制：首句就含多个带位置信息的故障时也要能拆（不再要求 context 非空）
        comma_parts = [p.strip() for p in re.split(r'[，,]', current_input) if len(p.strip()) > 1]
        is_multi_location = len(comma_parts) > 1 and all(re.search(r'\d|[一二三四五六七八九十]', p) for p in comma_parts)
        
        if is_multi_location:
            all_tickets = []
            pending_ask = None
            for part in comma_parts:
                sub_result = triage(part, location_text, context, tau)
                if sub_result.get("status") == "success":
                    all_tickets.extend(sub_result.get("tickets", []))
                elif sub_result.get("status") == "ask_for_location":
                    pending_ask = sub_result

            # 有一部分位置不完整（如“4栋4楼寝室门锁”缺房间号）：
            # 已完整的先记下来，缺位置的继续追问，补齐后再一并出单，绝不给没房间号的寝室出单
            if pending_ask:
                pending_ask["pending_tickets"] = all_tickets
                if all_tickets:
                    done_loc = "、".join(t.get("location", "") for t in all_tickets)
                    pending_ask["message"] = (
                        f"其中「{done_loc}」的报修已为您生成工单；"
                        + (pending_ask.get("message") or "另一处还需要补充具体位置。")
                    )
                return pending_ask

            if all_tickets:
                depts = list(set([t["assigned_dept"] for t in all_tickets]))
                report_prompt = f"""
                你是一个高情商的校园报修客服。
                系统刚刚为您生成了 {len(all_tickets)} 张独立的报修工单，涉及部门：{', '.join(depts)}。
                请热情地告知用户：由于您上报了多个位置，系统已为您拆分为 {len(all_tickets)} 张工单并分别派单。
                严禁使用任何 Emoji。
                """
                ai_response = call_llm("你是一个认真负责的校园报修客服。", report_prompt)
                return {
                    "status": "success",
                    "tickets": all_tickets,
                    "ai_response": ai_response or "已为您生成多张工单。"
                }

        saved_faults = context.get("faults", "") if context else ""
        saved_building = context.get("building", "") if context else ""
        saved_room = context.get("room", "") if context else ""
        saved_area = context.get("area", "") if context else ""
        saved_loc_type = context.get("loc_type", "unknown") if context else "unknown"
        
        cur_b, cur_r, cur_a, cur_fault, cur_type = extract_info(current_input)
        
        final_faults = saved_faults
        final_building = saved_building or cur_b
        final_room = saved_room or cur_r
        final_area = saved_area or cur_a
        final_loc_type = cur_type if cur_type != "unknown" else saved_loc_type
        
        fault_words = ["坏", "漏", "堵", "响", "跳", "不亮", "不动", "断", "松", "裂", "漫", "冒", "等", "修", "门", "灯", "水", "冷", "热", "卡", "掉", "脏", "臭", "没反应"]
        device_words = ["空调", "马桶", "水管", "洗衣机", "饮水机", "天花板", "床", "柜子", "电扇", "插头"]
        has_fault_word = any(k in current_input for k in fault_words) or any(d in current_input for d in device_words)
        
        if has_fault_word:
            if cur_b or cur_r or cur_a:
                final_faults = cur_fault
            elif not final_faults:
                final_faults = cur_fault
            elif cur_fault not in final_faults and final_faults not in cur_fault:
                final_faults = f"{final_faults}，还有{cur_fault}"

        if not context and not has_fault_word and not (cur_b or cur_r or cur_a) and len(current_input) < 10:
            reply = call_llm(
                "你是高校宿舍智能报修助手。无论用户说什么，都只能用一两句话回应，并礼貌地把话题拉回“宿舍设施报修”。"
                "不要讲笑话、不要讲故事、不要扮演其他角色、不要回答与报修无关的知识性问题。严禁使用任何 Emoji。",
                current_input,
            )
            return {"status": "chitchat", "message": reply or "你好！我是宿舍报修助手，请问宿舍里什么设施出问题了？"}

        if not final_faults:
            prompt = f"用户说：'{current_input}'。没有提到具体故障。请热情引导用户描述哪里坏了。严禁使用 Emoji。"
            ai_msg = call_llm("你是高校宿舍报修助手。", prompt)
            return {"status": "ask_for_location", "message": ai_msg or "请问具体是哪里坏了呢？", "faults": "", "building": final_building, "room": final_room, "area": final_area, "loc_type": final_loc_type}
            
        # 🌟 调用强校验
        if not is_location_complete(final_building, final_room, final_area, final_loc_type, final_faults):
            if final_loc_type == "indoor" or any(w in final_faults for w in STRONG_INDOOR):
                need_info = "具体的房间号（例如402室）"
            elif final_loc_type == "public":
                need_info = "具体的楼层或公共区域（例如3层走廊）"
            else:
                need_info = "具体的房间号（例如302室）或楼层区域"

            prompt = f"用户报修了：'{final_faults}'。目前已知位置：'{final_building}{final_room}{final_area}'。为了精准定位，请温和地追问用户：{need_info}。严禁使用 Emoji。"
            ai_msg = call_llm("你是高校宿舍报修助手。", prompt)
            
            return {
                "status": "ask_for_location", 
                "message": ai_msg or f"为了师傅能准确定位，请问{need_info}是多少呢？", 
                "faults": final_faults, "building": final_building, 
                "room": final_room, "area": final_area, "loc_type": final_loc_type
            }

        # 状态完备，生成工单
        if final_area and final_area in final_room:
            final_area = ""
            
        final_location = f"{final_building}{final_area}{final_room}".strip()
        
        fault_parts = re.split(r'，|,|、|还有|和', final_faults)
        fault_parts = [p.strip() for p in fault_parts if len(p.strip()) > 1]
        
        # 多位置拆单时，之前已完整的那部分工单先挂起在 context 里，这里一并出单
        pending_tickets = context.get("pending_tickets", []) if context else []
        tickets = list(pending_tickets)
        unique_parts = list(dict.fromkeys(fault_parts))
        for part in unique_parts:
            tickets.append(process_single_fault(part, final_location))

        depts = list(set([t["assigned_dept"] for t in tickets]))
        need_human_count = sum(1 for t in tickets if t.get("need_human"))
        is_multi = "是" if len(tickets) > 1 else "否"
        
        report_prompt = f"""
        你是一个高情商的校园宿舍报修系统前台客服。
        系统刚刚为你生成了一份全新的报修工单。
        
        【工单数据】
        - 故障数量：{len(tickets)} 个
        - 涉及部门：{', '.join(depts)}
        - 报修地点：{final_location}
        - 需人工复核的工单数：{need_human_count}
        
        【严格播报要求】
        1. 必须明确告诉用户，系统已经记录了报修地点（即：{final_location}）。
        2. 绝对不能说“师傅已经修好”、“已经到达”。使用将来时态。
        3. 绝对不要提及“置信度”、“SLA”等技术术语。严禁使用任何 Emoji。
        4. 如果包含多个故障，告诉用户：“系统已将您的报修拆分为 {len(tickets)} 张工单，并派发给 {', '.join(depts)}。”
        5. 如果只有一个故障且无需人工复核，告诉用户已自动派单。
        6. 如果“需人工复核的工单数”大于 0，必须明确说明“已转交人工客服进一步确认/加急跟进”，
           严禁说“已自动派单”“已安排师傅上门”。
        7. 热情、贴心、分段落输出。
        """
        ai_response = call_llm("你是一个认真负责的校园报修客服。", report_prompt)

        # 大模型偶尔仍会串词，这里做最后一道一致性兜底
        if need_human_count and ai_response and "人工" not in ai_response:
            ai_response = ai_response.rstrip() + "\n\n由于部分信息尚不确定，该工单已转交人工客服进一步确认，请保持电话畅通。"

        return {
            "status": "success", "tickets": tickets, 
            "ai_response": ai_response if ai_response else "工单已成功生成。"
        }
    
    except Exception as e:
        print(f"Triage 核心逻辑异常: {e}")
        return {"status": "error", "message": "系统内部处理出错，请稍后重试。"}