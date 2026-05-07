import sqlite3
from datetime import datetime

def get_db_connection():
    return sqlite3.connect('parking_system.db')

def register_user():
    print("\n--- Register New Account ---")
    username =input("Enter username: ")
    password =input("Enter password: ")
    print("Select Role: 1. Customer 2. Admin 3. Owner")
    role_choice =input("Choice: ")

    role_map ={"1": "Customer", "2": "Admin", "3": "Owner"}
    role = role_map.get(role_choice, "Customer")

    mall_id = None
    if role == "Admin":
        mall_id = input("Enter Mall ID for this Admin (1. Gateway Theatre of Shopping, 2: Pavilion Shopping centre, 3: La Lucia Mall): ")

    try:
        conn =get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (username, password, role, assigned_mall_id) VALUES (?, ?, ?, ?)", (username, password, role, mall_id))
        conn.commit()
        conn.close()
        print("Registration successful! You can now log in.")
    except sqlite3.IntegrityError:
        print("Error: Username already exists.")

def login():
    print("\n--- Login ---")
    username = input("Username: ")
    password =input("Password: ")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role, username FROM Users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user
    else:
        print("Invalid username or password.")
        return None
    
def view_customer_history(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mall_id, total_fee, entry_time
        FROM ParkingRecords
        WHERE user_id = ?
        ORDER BY entry_time DESC
    """, (user_id,))

    records =  cursor.fetchall()
    if records:
        print("\n--- Your Parking History ---")
        for row in records:
            print(f"Mall ID: {row[0]} | Fee: R{row[1]} | Date: {row[2]}")
    else:
        print("No parking history found.")
    conn.close()

    print("\n" + "="*70)
    print(f"{'MALL NAME' :<30} {'FEE':<10} {'DATE & TIME'}")
    print("-"*70)

    if not records:
        print("No transaction found in your account.")
    else:
        for row in records:
            current_mall_id = str(row[0])
            mall_names = {
                "1": "Gateway Theatre of Shopping",
                "2": "Pavilion Shopping centre",
                "3": "La Lucia Mall",
            }
            name = mall_names.get(current_mall_id, "Unknown")
            print(f"{name:<30} R{row[1]:<9} {row[2]}")

    print("="*70)

def customer_menu(user_id):
    while True:
        print("\n--- Customer Portal ---")
        print("1. Park Vechile")
        print("2. View parking history")
        print("3. Log out")

        user_selection = input("Select an option: ")

        if user_selection == "1":
            print("\n--- Select a Mall ---")
            print("1. Gateway Theatre of Shopping (Flat rate: R20)")
            print("2. Pavilion Shopping centre (Hourly: R10/hr)" )
            print("3. La Lucia Mall (Capped: R15/hr, Max R50)")
            mall_choice =input("choice: ")
            hours = int(input("How amny hours wiil you be parked? "))

            fee = 0 
            if mall_choice =="1": fee = 20
            elif mall_choice == "2": fee = hours *10
            elif mall_choice == "3": fee = min(hours *15, 50)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ParkingRecords (user_id, mall_id, total_fee, entry_time) VALUES (?, ?, ?, ?)",
                           (user_id, mall_choice, fee, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
            conn.commit()
            conn.close()
            print(f"Success! R{fee} recored.")
            pass
        elif user_selection == "2":
            view_customer_history(user_id)
        elif user_selection == "3":
            print("Logging out...")
            break
        else:
            print("Invaild option.")

def admin_menu():
    print("\n--- Admin Dashboard ---")
    print("Functionality: View mall occupancy reports.")

def owner_menu():
    print("\n--- Owner Dashboard ---")
    print("Funtionality: Update pricing rates,")

def admin_dashboard(mall_id):
    while True:   
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
           SELECT COUNT(record_id), SUM(total_fee)
            FROM ParkingRecords
            WHERE mall_id = ?
        """, (mall_id,))
        
        result = cursor.fetchone()
        total_cars = result[0] if result[0] else 0
        total_revenue = result[1] if result[1] else 0.0
        conn.close()
        
        mall_name = {
            '1': 'Gateway Theatre of Shopping',
            '2': 'Pavilion SHopping Centre',
            '3': 'La Lucia Mall'
        }
        name = mall_name.get(str(mall_id), "Unknown Mall")
          
        print(f"\n===============================")
        print(f" ADMIN DASHBOARD: {mall_name}")
        print(f"===============================")
        print(f"1. View occupancy & revenue report")
        print(f"2. Log out")
        print(f"==============================")

        choice = input("Select an option: ")

        if choice == "1":
            print(f"\n--- Current status for {mall_name} ---")
            print(f"Total vehicles parked: {total_cars}")
            print(f"Total revenue earned: R {total_revenue:.2f}")
            if total_cars > 50:
                print("STATUS: High occupancy - Monitor exit gates")
            else:
                print("STATUS: Normal operations")
            input("\nPress enter to continue...")
        elif choice == "2":
            print("Logging out of admin session...")
            break
        else:
            print("Invaild option. Please try again.")
        
def owner_report():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mall_id, COUNT(record_id), SUM(total_fee)
        FROM ParkingRecords
        GROUP BY mall_id
    """)

    results = cursor.fetchall()
    conn.close()

    mall_name = {
        '1': 'Gateway Theatre of shopping',
        '2': 'Pavilion Shopping Centre',
        '3': 'La Lucia Mall'
    }

    print("\n" + "="*60)
    print("               OWNER OVERVIEW               ")
    print("="*60)
    print(f"{'MALL NAME':<30} | {'CARS':<6} | {'REVENUE'}")
    print("="*60)

    grand_total_revenue = 0
    grand_total_cars = 0

    if not results:
        print("No parking records found,")
    else:
        for row in results:
            m_name = mall_name.get(str(row[0]), "Unknown")
            m_cars = row[1]
            m_rev = row[2] if row[2] else 0.0

            print(f"{m_name:<30} | {m_cars:<6} | R{m_rev:<10.2f}")

            grand_total_revenue += m_rev
            grand_total_cars += m_cars

    print("="*60)
    print(f"{'TOTAL SYSTEM':<30} | {grand_total_cars:<6} | R{grand_total_revenue:<10.2f}")
    print("="*60)
    input("\nPress enter to return to main menu...")
def main():
    while True:
        print("\n=================================")
        print("  KZN PARKING MANAGEMENT SYSTEM ")
        print("=================================")
        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("Select an option: ")
        
        if choice == "1":
            user = login()
            if user:
                user_id, role, mall_id = user
                
                print(f"\nWelcome back, {role}!")

                if role == "Customer":
                    customer_menu(user_id)
                elif role == "Admin":
                    if mall_id:
                        admin_dashboard(mall_id)
                    else:
                        print("Error: This Admin has no assigned mall.")
                elif role == "Owner":
                    owner_report()

        elif choice == "2":
            register_user()
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid option, pleses try again.")

if __name__ =="__main__":
    main()