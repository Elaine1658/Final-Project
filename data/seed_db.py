from pathlib import Path
import sqlite3

DB = Path(__file__).with_name("dining.db")
DB.parent.mkdir(exist_ok=True)
with sqlite3.connect(DB) as db:
    db.executescript("""
    DROP TABLE IF EXISTS sales_history;
    DROP TABLE IF EXISTS inventory;
    DROP TABLE IF EXISTS dining_context;
    CREATE TABLE sales_history (
      id INTEGER PRIMARY KEY, service_date TEXT, meal TEXT, day_type TEXT,
      weather TEXT, event_size INTEGER, prepared INTEGER, sold INTEGER, wasted INTEGER
    );
    CREATE TABLE inventory (
      meal TEXT PRIMARY KEY, on_hand INTEGER, unit_cost REAL, expiry_days INTEGER,
      ingredient_note TEXT
    );
    CREATE TABLE dining_context (
      id INTEGER PRIMARY KEY, service_date TEXT, weather TEXT, event_name TEXT,
      expected_attendance INTEGER, confidence REAL
    );
    """)
    rows = [
      (1,'2026-10-19','Grilled chicken bowl','weekday','clear',0,120,108,12),
      (2,'2026-10-20','Grilled chicken bowl','weekday','rain',0,120,96,24),
      (3,'2026-10-21','Grilled chicken bowl','weekday','clear',0,120,113,7),
      (4,'2026-10-22','Grilled chicken bowl','weekday','clear',250,170,161,9),
      (5,'2026-10-19','Vegetarian pasta','weekday','clear',0,75,64,11),
      (6,'2026-10-20','Vegetarian pasta','weekday','rain',0,75,59,16),
      (7,'2026-10-21','Vegetarian pasta','weekday','clear',0,75,70,5),
      (8,'2026-10-22','Vegetarian pasta','weekday','clear',250,100,91,9),
      (9,'2026-10-19','Soup and sandwich','weekday','clear',0,60,52,8),
      (10,'2026-10-20','Soup and sandwich','weekday','rain',0,60,58,2),
      (11,'2026-10-21','Soup and sandwich','weekday','clear',0,60,55,5),
      (12,'2026-10-22','Soup and sandwich','weekday','clear',250,80,73,7),
    ]
    db.executemany('INSERT INTO sales_history VALUES (?,?,?,?,?,?,?,?,?)', rows)
    db.executemany('INSERT INTO inventory VALUES (?,?,?,?,?)', [
      ('Grilled chicken bowl', 145, 4.20, 3, 'Chicken and rice; fresh prep'),
      ('Vegetarian pasta', 82, 2.10, 5, 'Pasta and vegetables'),
      ('Soup and sandwich', 48, 2.60, 1, 'Soup base expires tomorrow'),
      ('Fruit cup', 90, 1.15, 2, 'Ready-to-serve fruit'),
    ])
    db.execute('INSERT INTO dining_context VALUES (?,?,?,?,?,?)', (1,'2026-10-23','rain','Yale Family Weekend',350,0.78))
print(DB)
