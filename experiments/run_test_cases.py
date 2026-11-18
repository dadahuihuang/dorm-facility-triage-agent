# -*- coding: utf-8 -*-
"""
离线验收脚本：复刻 app.py 的调用方式，跑完 7 个验收用例并输出测试记录。

用法（在项目根目录）：
    python experiments/run_test_cases.py

说明：
- 上下文传递与 app.py 完全一致：上一轮 ask_for_location 的整个 result 作为 context；success 后清空。
- 不会写入 tickets.db（避免污染演示数据）；如需入库，打开 WRITE_DB 开关。
- 依赖 .env 中的 ZHIPU_API_KEY（大模型播报/追问）。
"""
import sys
import os
import io
import json
import logging

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.abspath("src"))

logging.getLogger("jieba").setLevel(logging.ERROR)

from agent_router import triage  # noqa: E402

WRITE_DB = False

CASES = [
    {
        "id": "TC-01",
        "name": "标准首轮报修（正则清洗/高置信/自动派单）",
        "turns": ["你好！ 5栋三楼305宿舍灯坏了！麻烦快点"],
        "check": lambda rs: (
            rs[-1]["status"] == "success"
            and len(rs[-1].get("tickets", [])) == 1
            and rs[-1]["tickets"][0]["facility_label"] == "ELEC"
            and rs[-1]["tickets"][0]["confidence"] > 0.9
            and "305" in rs[-1]["tickets"][0].get("location", "")
            and rs[-1]["tickets"][0]["need_human"] is False
        ),
    },
    {
        "id": "TC-02",
        "name": "多轮追问 + 室内强制房间号",
        "turns": ["空调不制冷", "在3栋2楼", "201"],
        "check": lambda rs: (
            rs[0]["status"] == "ask_for_location"
            and rs[1]["status"] == "ask_for_location"
            and rs[2]["status"] == "success"
            and rs[2]["tickets"][0]["facility_label"] == "HVAC"
            and "201" in rs[2]["tickets"][0].get("location", "")
        ),
    },
    {
        "id": "TC-03",
        "name": "多故障/多位置拆单（缺房间号先追问）",
        "turns": ["3栋2楼走廊灯坏了，4栋4楼寝室门锁也打不开了", "402"],
        "check": lambda rs: (
            # 第 1 轮：公区那条直接出单，寝室那条因缺房间号必须追问
            rs[0]["status"] == "ask_for_location"
            and len(rs[0].get("pending_tickets", [])) == 1
            and rs[1]["status"] == "success"
            and len(rs[1].get("tickets", [])) == 2
            and {t["facility_label"] for t in rs[1]["tickets"]} == {"ELEC", "DOOR"}
            and any(t["facility_label"] == "DOOR" and "402" in t.get("location", "")
                    for t in rs[1]["tickets"])
        ),
    },
    {
        "id": "TC-04",
        "name": "高危规则兜底（冒烟/焦味）",
        "turns": ["3栋301电线冒烟了，有焦味"],
        "check": lambda rs: (
            rs[-1]["status"] == "success"
            and rs[-1]["tickets"][0]["high_risk"] is True
            and rs[-1]["tickets"][0]["need_human"] is True
            and "15分钟" in rs[-1]["tickets"][0]["sla_target"]
        ),
    },
    {
        "id": "TC-05",
        "name": "意图打断 + 闲聊防污染",
        "turns": ["马桶堵了", "哎，今天上课太累了", "1栋2楼走廊厕所"],
        "check": lambda rs: (
            rs[0]["status"] == "ask_for_location"
            and rs[2]["status"] == "success"
            and rs[2]["tickets"][0]["facility_label"] == "WATER"
        ),
    },
    {
        "id": "TC-06",
        "name": "低置信度转人工复核",
        "turns": ["那个东西有点问题，一直响", "2栋2楼201"],
        "check": lambda rs: (
            rs[-1]["status"] == "success"
            and rs[-1]["tickets"][0]["need_human"] is True
        ),
    },
    {
        "id": "TC-07",
        "name": "垃圾输入/边界控制",
        "turns": ["你好，给我讲个笑话", "?????"],
        "check": lambda rs: all(r["status"] == "chitchat" for r in rs),
    },
]


def brief(result):
    """把一次 triage 结果压成便于阅读的摘要。"""
    st = result.get("status")
    if st in ("chitchat", "error"):
        return {"status": st, "message": (result.get("message") or "")[:80]}
    if st == "ask_for_location":
        return {
            "status": st,
            "faults": result.get("faults"),
            "building": result.get("building"),
            "room": result.get("room"),
            "area": result.get("area"),
            "loc_type": result.get("loc_type"),
            "pending_tickets": len(result.get("pending_tickets", [])),
            "message": (result.get("message") or "")[:100],
        }
    tickets = []
    for t in result.get("tickets", []):
        tickets.append({
            "label": t["facility_label"],
            "conf": t["confidence"],
            "location": t.get("location"),
            "dept": t["assigned_dept"],
            "sla": t["sla_target"],
            "high_risk": t["high_risk"],
            "need_human": t["need_human"],
            "reason": t["reason"],
            "summary": t.get("summary"),
            "history": bool(t.get("history_retrieval")),
            "tool_alert": t.get("tool_alert"),
        })
    return {"status": st, "n_tickets": len(tickets), "tickets": tickets,
            "ai_response": (result.get("ai_response") or "")[:120]}


def main():
    records = []
    for case in CASES:
        print("\n" + "=" * 70)
        print(f"{case['id']} {case['name']}")
        print("=" * 70)
        ctx = None
        results = []
        for turn_no, text in enumerate(case["turns"], 1):
            print(f"\n[第 {turn_no} 轮] 用户: {text}")
            try:
                result = triage(raw_text=text, context=ctx)
            except Exception as e:  # noqa: BLE001
                result = {"status": "error", "message": f"调用异常: {e}"}
            results.append(result)
            print("   → " + json.dumps(brief(result), ensure_ascii=False))

            if result.get("status") == "ask_for_location":
                ctx = result
            elif result.get("status") == "success":
                ctx = None
                if WRITE_DB:
                    from database import insert_ticket
                    for t in result.get("tickets", []):
                        insert_ticket(t)

        try:
            passed = bool(case["check"](results))
        except Exception as e:  # noqa: BLE001
            passed = False
            print(f"   [校验异常] {e}")
        print(f"\n   >>> 结果: {'PASS' if passed else 'FAIL'}")
        records.append({"case": case, "results": results, "passed": passed})

    out_dir = "experiments"
    with open(os.path.join(out_dir, "test_cases_raw.json"), "w", encoding="utf-8") as f:
        json.dump(
            [{"id": r["case"]["id"], "name": r["case"]["name"],
              "passed": r["passed"], "turns": r["case"]["turns"],
              "results": [brief(x) for x in r["results"]]} for r in records],
            f, ensure_ascii=False, indent=2,
        )

    print("\n" + "=" * 70)
    total = len(records)
    ok = sum(1 for r in records if r["passed"])
    print(f"通过 {ok}/{total}")
    for r in records:
        print(f"  {r['case']['id']} {'PASS' if r['passed'] else 'FAIL'}  {r['case']['name']}")


if __name__ == "__main__":
    main()
