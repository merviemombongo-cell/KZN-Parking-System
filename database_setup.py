import sqlite3

def init_db ():
    conn =sqlite3.connect('parking_system.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS malls (
            mall_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            pricing_type TEXT NOT NULL, -- 'Flat', 'Hourly', or 'Capped'
            rate REAL NOT NULL,
            cap_limit REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL, -- 'Customer', 'Admin', or 'Owner'
            assigned_mall_id INTEFER, -- Only used for admins
            FOREIGN KEY (assigned_mall_id) REFERENCES Malls(mall_id)
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ParkingRecords (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mall_id INTEGER NOT NULL,
            entry_time DATETIME NOT NULL,
            exit_time DATETIME,
            total_fee REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active', -- 'Active' means car is still in mall 
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (mall_id) REFERENCES Malls(mall_id) 
        ) 
    ''')
    
    malls_data =[
        ('Gateway Theatre of Shopping', 250, 'Flat', 15.0, None),
        ('Pavilion Shopping Centre', 180, 'Hourly', 10.0, None),
        ('La Lucia Mall', 150, 'Capped', 12.0, 60.0)
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO Malls (name, capacity, pricing_type, rate, cap_limit)
        VALUES (?, ?, ?, ?, ?)
    ''', malls_data)

    conn.commit()
    conn.close()
    print("Database structure created and KZN malls loaded successfull!")

if __name__ == "__main__":
    init_db() 
