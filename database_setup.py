import sqlite3
#This python file creates the parking system database, which will be where all the data of my program is stored. 
def init_db ():
    conn =sqlite3.connect("parking_system.db") #This is where my files are located.
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")

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
            mall_id INTEGER, -- Only used for admins
            FOREIGN KEY (mall_id) REFERENCES malls(mall_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ParkingRecords (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mall_id INTEGER NOT NULL,
            entry_time DATETIME NOT NULL,
            exit_time DATETIME,
            hours_parked REAL DEFAULT 0,  
            total_fee REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active', -- 'Active' means car is still in mall 
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (mall_id) REFERENCES malls(mall_id) 
        ) 
    ''')
    
    malls_data =[
        ('Gateway Theatre of Shopping', 250, 'Flat', 15.0, None),
        ('Pavilion Shopping Centre', 180, 'Hourly', 10.0, None),
        ('La Lucia Mall', 150, 'Capped', 12.0, 60.0)
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO malls (name, capacity, pricing_type, rate, cap_limit)
        VALUES (?, ?, ?, ?, ?)
    ''', malls_data)

    conn.commit()
    conn.close()
    print("Database structure created and KZN malls loaded successfull!")

if __name__ == "__main__":
    init_db() 
