import os
import random
import pandas as pd

random.seed(42)

# 1. 基础种子数据 (保留50条)
base_data = [
    [1, "走廊那个声控灯不亮了晚上回宿舍黑漆漆的", "某栋某层走廊", "public", "ELEC", 0, "real", "", "公共区域照明"],
    [2, "宿舍吸顶灯一直闪关了重开还是闪", "某宿舍", "in_room", "ELEC", 0, "synthetic", "", ""],
    [3, "进门左边墙上的插座没电手机充电没反应", "某宿舍", "in_room", "ELEC", 0, "synthetic", "", ""],
    [4, "楼梯间的灯坏了好几盏晚上下楼看不清", "某栋楼梯间", "public", "ELEC", 0, "synthetic", "", ""],
    [5, "灯太暗了看书眼睛疼能不能换亮一点的", "某宿舍", "in_room", "ELEC", 0, "real", "", ""],
    [6, "宿舍电闸老是跳开个吹风机就跳", "某宿舍", "in_room", "ELEC", 1, "synthetic", "", "电气风险"],
    [7, "阳台灯不亮了开关按了没反应", "某宿舍阳台", "in_room", "ELEC", 0, "synthetic", "", ""],
    [8, "走廊应急照明灯掉下来了电线露在外面", "某栋某层走廊", "public", "ELEC", 1, "real", "", "电线裸露高危"],
    [9, "卫生间洗手池水龙头漏水关紧后还在滴水", "某宿舍卫生间", "in_room", "WATER", 0, "real", "", ""],
    [10, "厕所堵了冲不下去水快漫出来了", "某宿舍卫生间", "in_room", "WATER", 1, "synthetic", "", "积水风险"],
    [11, "淋浴花洒不出热水等了好久还是凉的", "某宿舍淋浴间", "in_room", "WATER", 0, "synthetic", "", ""],
    [12, "阳台地漏堵了洗衣服的水下不去", "某宿舍阳台", "in_room", "WATER", 0, "synthetic", "", ""],
    [13, "公共厕所味道特别大像是下水道反味", "某栋公共卫生间", "public", "WATER", 0, "real", "", ""],
    [14, "水龙头水压太大了开就溅一身可能要装个滤网", "某宿舍卫生间", "in_room", "WATER", 0, "real", "", ""],
    [15, "宿舍马桶一直流水按了冲水按钮弹不回来", "某宿舍卫生间", "in_room", "WATER", 0, "synthetic", "", ""],
    [16, "楼道水管好像爆了地上全是水", "某栋某层楼道", "public", "WATER", 1, "synthetic", "", "水管爆裂高危"],
    [17, "洗澡间下水道堵了积水到脚踝", "某栋公共淋浴间", "public", "WATER", 0, "synthetic", "", ""],
    [18, "空调不制热吹的是冷风晚上被冻醒", "某宿舍", "in_room", "HVAC", 0, "real", "", ""],
    [19, "空调开起来咔咔乱响感觉要炸了一样", "某宿舍", "in_room", "HVAC", 1, "real", "", "异响可能高危"],
    [20, "宿舍风扇不转了按开关没反应", "某宿舍", "in_room", "HVAC", 0, "synthetic", "", ""],
    [21, "空调漏水滴到床上了", "某宿舍", "in_room", "HVAC", 0, "synthetic", "", ""],
    [22, "卫生间排气扇坏了洗完澡全是雾气散不掉", "某宿舍卫生间", "in_room", "HVAC", 0, "synthetic", "", ""],
    [23, "空调遥控器按了没反应不知道是遥控器坏了还是空调坏了", "某宿舍", "in_room", "HVAC", 0, "synthetic", "", "对象不明"],
    [24, "靠近卫生间的床太摇晃了上铺下床感觉床会翻", "某宿舍", "in_room", "FURN", 1, "real", "", "床体坍塌风险"],
    [25, "书桌抽屉把手断了拉不开", "某宿舍", "in_room", "FURN", 0, "real", "", ""],
    [26, "衣柜左边柜门关不上锁和卡扣对不齐", "某宿舍", "in_room", "FURN", 0, "real", "", ""],
    [27, "床板断了睡上去会塌", "某宿舍", "in_room", "FURN", 1, "synthetic", "", "床体坍塌风险"],
    [28, "椅子腿松了坐上去吱吱响感觉要散架", "某宿舍", "in_room", "FURN", 0, "synthetic", "", ""],
    [29, "爬上铺的梯子松掉了踩上去晃得厉害", "某宿舍", "in_room", "FURN", 1, "real", "", "攀爬风险"],
    [30, "衣柜门合不上有一条大缝衣服都落灰", "某宿舍", "in_room", "FURN", 0, "real", "", ""],
    [31, "桌子晃得厉害写字的时候不稳", "某宿舍", "in_room", "FURN", 0, "synthetic", "", ""],
    [32, "柜子最下面那个抽屉的滑轮坏了拉不出来", "某宿舍", "in_room", "FURN", 0, "real", "", ""],
    [33, "宿舍门锁非常不好开很怕哪天进不了门", "某宿舍", "in_room", "DOOR", 0, "real", "", ""],
    [34, "钥匙断在锁里面了现在门打不开", "某宿舍", "in_room", "DOOR", 1, "real", "", "无法进出高危"],
    [35, "阳台门和纱窗都很难推纱窗还有缝关不严", "某宿舍阳台", "in_room", "DOOR", 0, "real", "", ""],
    [36, "窗户把手松了关窗的时候合不拢", "某宿舍", "in_room", "DOOR", 0, "synthetic", "", ""],
    [37, "厕所门反锁了从外面打不开", "某栋公共卫生间", "public", "DOOR", 1, "real", "", "无法进出高危"],
    [38, "窗帘杆弯了窗帘快掉下来了", "某宿舍", "in_room", "DOOR", 0, "real", "", ""],
    [39, "单元门门禁刷卡没反应要等别人开门才能进", "某栋单元门", "public", "DOOR", 0, "synthetic", "", ""],
    [40, "门关上的时候声音巨大哐的一声整层楼都能听到", "某宿舍", "in_room", "DOOR", 0, "real", "", ""],
    [41, "公共洗衣机不脱水衣服拿出来还是湿的", "某栋洗衣房", "public", "APPL", 0, "synthetic", "", ""],
    [42, "走廊饮水机不出热水了只有冷水", "某栋某层走廊", "public", "APPL", 0, "synthetic", "", ""],
    [43, "烘干机投了币不转钱扣了机器没反应", "某栋洗衣房", "public", "APPL", 0, "synthetic", "", ""],
    [44, "宿舍饮水机漏水底座下面一滩水", "某宿舍", "in_room", "APPL", 0, "synthetic", "", "漏水接近电气需注意"],
    [45, "公共吹风机插上电没反应换了个插座也不行", "某栋公共洗漱间", "public", "APPL", 0, "synthetic", "", ""],
    [46, "洗衣机排水管掉了水直接排到地上", "某栋洗衣房", "public", "APPL", 0, "synthetic", "", ""],
    [47, "宿舍门口走廊天花板墙皮脱落掉了一地灰", "某栋某层走廊", "public", "STRUCT", 0, "real", "", ""],
    [48, "浴室瓷砖破了两块边角很锋利", "某宿舍卫生间", "in_room", "STRUCT", 0, "real", "", ""],
    [49, "灯坏了", "unknown", "unknown", "ELEC", 0, "real", "", "描述过短边界样例"],
    [50, "水龙头漏水床也有问题门也不好关", "unknown", "unknown", "WATER", 0, "synthetic", "", "多故障混合边界样例"]
]
columns = ["id", "raw_text", "location_text", "location_type", "facility_label", "high_risk_gold", "source_type", "split", "notes"]
df_base = pd.DataFrame(base_data, columns=columns)

# 2. 扩充词典
templates = {
    "ELEC": {"obj": ["走廊灯", "宿舍灯", "插座", "开关", "电线", "电闸", "应急灯", "台灯"], "act": ["不亮了", "一直闪", "坏了", "没电", "烧黑了", "接触不良", "跳闸", "掉下来了", "灯罩破了"], "risk": ["漏电", "冒火花", "有焦味", "电线裸露"]},
    "WATER": {"obj": ["水龙头", "厕所", "下水道", "花洒", "马桶", "洗手池", "地漏", "水管"], "act": ["漏水", "堵了", "不出水", "水很小", "一直流水", "反味", "水发黄", "关不紧"], "risk": ["爆裂", "水漫出来了", "漏到楼下了"]},
    "HVAC": {"obj": ["空调", "风扇", "排气扇", "外机"], "act": ["不制冷", "不制热", "噪音很大", "漏水", "不转了", "遥控没反应", "扇叶断了"], "risk": ["冒烟", "外壳带电", "着火"]},
    "FURN": {"obj": ["床板", "床架", "书桌", "椅子", "衣柜", "抽屉", "梯子", "柜门"], "act": ["摇晃", "散架了", "拉不开", "关不上", "螺丝掉光", "坏了", "少了一块", "断了"], "risk": ["要塌了", "掉下来砸到人", "钉子扎人"]},
    "DOOR": {"obj": ["门", "窗户", "纱窗", "钥匙", "门禁", "玻璃", "窗帘"], "act": ["打不开", "关不上", "卡住", "插不进", "锁坏了", "推不动", "把手掉了", "碎了"], "risk": ["反锁了出不去", "玻璃砸下来了", "关不严漏风"]},
    "APPL": {"obj": ["洗衣机", "饮水机", "烘干机", "吹风机", "微波炉"], "act": ["不工作", "不出水", "漏水", "投币没反应", "发出怪声", "漏电", "跳闸"], "risk": ["触电", "冒烟"]},
    "STRUCT": {"obj": ["天花板", "墙面", "地板", "瓷砖", "墙皮"], "act": ["脱落", "渗水", "裂缝", "破了", "发霉", "空鼓"], "risk": ["砸下来", "掉灰严重", "钢筋露出来了"]}
}

# 扩充语料干扰词
prefixes = ["", "麻烦来看看，", "急！", "你好，", "报修：", "阿姨，", "师傅，", "救命，", "不知道咋回事，", "帮帮忙，", "请问，"]
suffixes = ["", "谢谢。", "很急！", "麻烦尽快处理。", "在线等。", "不知道能不能修。", "影响生活了。", "拜托了。"]
locations = ["某栋某层走廊", "某宿舍", "公共卫生间", "某宿舍阳台", "某栋楼梯间", "洗衣房", "洗漱间", "某宿舍卫生间"]

# 错别字与拼音谐音替换库（模拟真实输入）
typo_dict = {
    "灯": ["等", "登"], "插座": ["插坐", "查座"], "水管": ["谁管", "水关"], 
    "漏水": ["露水", "楼水"], "堵了": ["赌了", "堵啦"], "空调": ["空条", "控调"],
    "门锁": ["门索", "们锁"], "钥匙": ["要匙", "药匙"], "坏了": ["怀了", "还了"],
    "宿舍": ["宿社", "缩舍"], "走廊": ["走狼", "走朗"]
}

def inject_typo(text):
    """随机注入错别字增强鲁棒性"""
    if random.random() < 0.15: # 15%概率触发错别字
        for correct, typos in typo_dict.items():
            if correct in text:
                text = text.replace(correct, random.choice(typos), 1)
                break
    return text

syn_data = []
current_id = 51

# 3. 生成海量数据 (约 5000+ 条)
for label, t in templates.items():
    # 普通工单 (每个类别 300 条)
    for _ in range(300):
        loc = random.choice(locations) if random.random() > 0.3 else ""
        obj = random.choice(t["obj"])
        act = random.choice(t["act"])
        
        # 随机句式组装
        patterns = [f"{loc}的{obj}{act}", f"{obj}{act}", f"{loc} {obj} {act}"]
        text = random.choice(patterns)
        
        # 前后缀叠加
        if random.random() > 0.5: text = random.choice(prefixes) + text
        if random.random() > 0.5: text = text + random.choice(suffixes)
        
        # 注入错别字
        text = inject_typo(text)
        
        syn_data.append([current_id, text, loc if loc else "unknown", "unknown", label, 0, "synthetic", "", "增强数据"])
        current_id += 1
        
    # 高危工单 (每个类别 80 条)
    for _ in range(80):
        loc = random.choice(locations) if random.random() > 0.3 else ""
        obj = random.choice(t["obj"])
        risk = random.choice(t["risk"])
        
        patterns = [f"{loc}的{obj}{risk}了", f"{obj}{risk}！", f"快来人啊 {obj} {risk}了"]
        text = random.choice(patterns)
        text = inject_typo(text)
        
        syn_data.append([current_id, text, loc if loc else "unknown", "unknown", label, 1, "synthetic", "", "高危增强"])
        current_id += 1

# 4. 生成 500 条“长难句 / 多故障混合”样本（极其考验模型）
all_objs = [(obj, label) for label, t in templates.items() for obj in t["obj"]]
for _ in range(500):
    # 随机抽取两个不同类别的故障进行拼接
    item1, item2 = random.sample(all_objs, 2)
    obj1, label1 = item1
    obj2, label2 = item2
    
    act1 = random.choice(templates[label1]["act"])
    act2 = random.choice(templates[label2]["act"])
    
    # 拼接成一句话，主标签取第一个出现的故障
    text = f"{obj1}{act1}，而且{obj2}{act2}，麻烦都来看看"
    syn_data.append([current_id, text, "unknown", "unknown", label1, 0, "synthetic", "", f"混合故障_副标签_{label2}"])
    current_id += 1

# 5. 合并、去重、打乱、划分
df_syn = pd.DataFrame(syn_data, columns=columns)
df_all = pd.concat([df_base, df_syn], ignore_index=True)
df_all = df_all.drop_duplicates(subset=['raw_text']) # 去除完全重复的句子
df_all = df_all.sample(frac=1, random_state=42).reset_index(drop=True) # 彻底打乱

# 分层划分 (70/15/15)
train_idx, val_idx, test_idx = [], [], []
for label in df_all['facility_label'].unique():
    indices = df_all[df_all['facility_label'] == label].index.tolist()
    n = len(indices)
    train_idx.extend(indices[:int(n*0.7)])
    val_idx.extend(indices[int(n*0.7):int(n*0.85)])
    test_idx.extend(indices[int(n*0.85):])

df_all.loc[train_idx, 'split'] = 'train'
df_all.loc[val_idx, 'split'] = 'val'
df_all.loc[test_idx, 'split'] = 'test'

# 6. 保存
os.makedirs("data", exist_ok=True)
df_all.to_csv("data/annotations.csv", index=False, encoding="utf-8-sig")
print(f"数据集生成完毕！共 {len(df_all)} 条数据（已去重）。")
print(df_all['facility_label'].value_counts())
print("数据集划分：\n", df_all['split'].value_counts())