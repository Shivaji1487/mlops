import sqlite3

# यह 'production.db' नाम की फ़ाइल (डेटाबेस) बना देगा
conn = sqlite3.connect("production.db")

# 1. टेबल बनाना
conn.execute("""
CREATE TABLE IF NOT EXISTS customer_data (
    customer_id INTEGER,
    auto_renewal BOOLEAN,
    years_as_customer REAL,
    subscriptions INTEGER
)
""")

# 2. प्रैक्टिस के लिए थोड़ा मॉक डेटा डालना (ताकि SQL से डेटा खींचा जा सके)
conn.execute("INSERT INTO customer_data VALUES (101, 1, 4.0, 3)")
conn.execute("INSERT INTO customer_data VALUES (102, 1, 1.5, 6)")
conn.execute("INSERT INTO customer_data VALUES (103, 0, 2.0, 2)")

conn.commit()
conn.close()
print("✅ Database 'production.db' setup completed with mock data!")