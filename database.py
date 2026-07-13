import sqlite3, os

# Use explicit env var first, then /data (Railway persistent volume), then local file.
# To persist data on Railway: add a Volume mounted at /data in the Railway dashboard.
DB_PATH = (
    os.environ.get('DATABASE_PATH')
    or ('/data/ops_hub.db' if os.path.isdir('/data') else None)
    or os.path.join(os.path.dirname(__file__), 'ops_hub.db')
)

STATUSES = ('live', 'progress', 'idea')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        url        TEXT NOT NULL,
        category   TEXT NOT NULL,
        status     TEXT NOT NULL DEFAULT 'idea',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()

    c.execute('SELECT COUNT(*) FROM links')
    if c.fetchone()[0] == 0:
        c.execute(
            'INSERT INTO links (name, url, category, status) VALUES (?, ?, ?, ?)',
            (
                'Warehouse inventory',
                'https://memory-block-warehouse-production.up.railway.app',
                'Memory Block · Australia',
                'live',
            ),
        )
        conn.commit()
    conn.close()


def get_all_links():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM links ORDER BY category, name').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_link(link_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM links WHERE id = ?', (link_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_link(name, url, category, status):
    conn = get_conn()
    cur = conn.execute(
        'INSERT INTO links (name, url, category, status) VALUES (?, ?, ?, ?)',
        (name, url, category, status),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return get_link(new_id)


def update_link(link_id, name, url, category, status):
    conn = get_conn()
    conn.execute(
        'UPDATE links SET name = ?, url = ?, category = ?, status = ? WHERE id = ?',
        (name, url, category, status, link_id),
    )
    conn.commit()
    conn.close()
    return get_link(link_id)


def delete_link(link_id):
    conn = get_conn()
    cur = conn.execute('DELETE FROM links WHERE id = ?', (link_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted
