import sqlite3

conn = sqlite3.connect('datatalk_demo.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    salary INTEGER,
    hire_date TEXT
)
''')

c.execute('DELETE FROM employees')

employees = [
    (1, 'Alice Smith', 'Engineering', 120000, '2021-01-15'),
    (2, 'Bob Johnson', 'Engineering', 110000, '2021-03-22'),
    (3, 'Charlie Brown', 'Product', 105000, '2020-11-01'),
    (4, 'Diana Prince', 'Sales', 95000, '2022-05-10'),
    (5, 'Evan Wright', 'Marketing', 85000, '2023-02-14'),
    (6, 'Fiona Gallagher', 'HR', 75000, '2019-08-30'),
]

c.executemany('INSERT INTO employees VALUES (?,?,?,?,?)', employees)

c.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT,
    budget INTEGER,
    department TEXT
)
''')

c.execute('DELETE FROM projects')

projects = [
    (1, 'Project Alpha', 500000, 'Engineering'),
    (2, 'Project Beta', 300000, 'Product'),
    (3, 'Project Gamma', 150000, 'Marketing'),
]

c.executemany('INSERT INTO projects VALUES (?,?,?,?)', projects)

conn.commit()
conn.close()
print("Demo database seeded successfully.")
