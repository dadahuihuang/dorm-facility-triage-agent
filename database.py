import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "data/tickets.db"

def init_db():
    """初始化数据库，创建工单表"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            create_time TEXT,
            raw_text TEXT,
            location TEXT,
            facility_label TEXT,
            confidence REAL,
            high_risk INTEGER,
            need_human INTEGER,
            assigned_dept TEXT,
            sla_target TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_ticket(ticket):
    """将新生成的工单插入数据库"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 如果不需要人工复核，直接设定为已自动派单；否则待人工复核
    status = "待人工复核" if ticket['need_human'] else "已自动派单"
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute('''
        INSERT INTO tickets (create_time, raw_text, location, facility_label, confidence, high_risk, need_human, assigned_dept, sla_target, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        create_time, ticket['raw_text'], ticket['location'], ticket['facility_label'],
        ticket['confidence'], int(ticket['high_risk']), int(ticket['need_human']),
        ticket['assigned_dept'], ticket['sla_target'], status
    ))
    conn.commit()
    conn.close()

def get_pending_tickets():
    """获取所有待人工复核的工单"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM tickets WHERE status = '待人工复核' ORDER BY create_time DESC", conn)
    conn.close()
    return df

def update_ticket_by_human(ticket_id, new_label, new_dept):
    """管理员人工复核后更新工单状态"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE tickets 
        SET facility_label = ?, assigned_dept = ?, status = '已人工确认派单'
        WHERE id = ?
    ''', (new_label, new_dept, ticket_id))
    conn.commit()
    conn.close()

def get_all_tickets():
    """获取所有历史工单"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY create_time DESC", conn)
    conn.close()
    return df