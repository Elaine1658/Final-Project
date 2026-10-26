import json
import sqlite3
from pathlib import Path
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'dining.db'
mcp = FastMCP('campus-dining-data')

def _rows(sql, args=()):
    with sqlite3.connect(DB) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(sql, args).fetchall()]

def get_sales_history(meal: str | None = None):
    if meal:
        return _rows('SELECT * FROM sales_history WHERE meal=? ORDER BY service_date', (meal,))
    return _rows('SELECT * FROM sales_history ORDER BY service_date, meal')

def get_inventory():
    return _rows('SELECT * FROM inventory ORDER BY meal')

def get_dining_context():
    return _rows('SELECT * FROM dining_context ORDER BY id DESC LIMIT 1')[0]

@mcp.tool()
def sales_history(meal: str = '') -> str:
    """Return recent meal sales, preparation, and waste data."""
    return json.dumps(get_sales_history(meal or None), indent=2)

@mcp.tool()
def inventory_snapshot() -> str:
    """Return available prepared inventory, unit cost, and expiry days."""
    return json.dumps(get_inventory(), indent=2)

@mcp.tool()
def campus_context() -> str:
    """Return tomorrow's weather, event attendance, and context confidence."""
    return json.dumps(get_dining_context(), indent=2)

if __name__ == '__main__':
    mcp.run(transport='stdio')
