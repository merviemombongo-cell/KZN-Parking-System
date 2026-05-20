import sqlite3
import math
from datetime import datetime

def get_db_connection():
    return sqlite3.connect(r"D:\Richfield _IT\ASSIGNMENTS\KZN Parking System\parking_system.db")

def register_user():
    print("\n--- Register New Account ---")
    username =input("Enter username: ")
    password =input("Enter password: ")
    print("Select Role: 1. Customer 2. Admin 3. Owner")
    role_choice = input("Choice: ")

    role_map = {"1": "Customer", "2": "Admin", "3": "Owner"}
    role = role_map.get(role_choice, "Customer")

    mall_id = None
    mall_name = "No Mall (Customer)"

    if role == "Admin":
        try:
            mall_id = int(input("""Enter Mall ID for this Admin:
1. Gateway Theatre of Shopping
2. Pavilion Shopping centre
3. La Lucia Mall
Choice: """))
        
            if mall_id == 1:
                mall_name = "Gateway Theatre of Shopping"
            elif mall_id == 2:
                mall_name = "Pavilion Shopping centre"
            elif mall_id == 3:
                mall_name = "La Lucia Mall"
            else:
                mall_name = "Unknown Mall"
                print("Invalid selection. Please assign a valid Mall ID.")
    
        except ValueError:
            mall_id = None
            print("Invalid input, defaulting to no mall.")

    try:
        conn =get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (username, password, role, mall_id) VALUES (?, ?, ?, ?)", (username, password, role, mall_id))
        
        conn.commit()
        conn.close()

        if role == "Customer":
            print(f"Registration successful! Account for {username} registered successfully.")
        elif role == "Admin":
            print(f"Registration successful! {username} allocated to {mall_name}.")
        elif role == "Owner":
            print(f"Registration successful! {username} has access to all three malls.")
        
    
    except sqlite3.IntegrityError:
        print("Error: Username already exists.")

def login():
    print("\n--- Login ---")
    username = input("Username: ")
    password =input("Password: ")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role, mall_id FROM Users WHERE username=? AND password=?", (username, password))
    
    user = cursor.fetchone()
    conn.close()
    if user:
        return user
    else:
        print("Invalid username or password.")
        return None
    
def view_customer_history(user_id, mall_choice):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT mall_id, hours_parked, total_fee, entry_time, exit_time, status
            FROM ParkingRecords
            WHERE user_id = ? AND mall_id = ?
            ORDER BY entry_time DESC
        """, (user_id, mall_choice))

        records =  cursor.fetchall()

    except sqlite3.OperationalError as e:
        print(f"\n[Database Error]: {e}")
        print("Please ensure your database_setup.py has been run and the tables exist.")
        conn.close()
        return    

    print("\n" + "="*98)
    print(" Your Parking History ".center(98))
    print("="*98)

    
    print(f"{'MALL NAME':<32}{'HOURS':<10}{'FEE':<12}{'ENTRY TIME':<22}{'EXIT TIME':<19}")
    print("-"*98)

    mall_names = {
        "1": "Gateway Theatre of Shopping",
        "2": "Pavilion Shopping centre",
        "3": "La Lucia Mall",
    }

    if not records:
        print("No parking transactions found in your account.".center(98))
        print("="*98)
        return

    for row in records:
        current_mall_id = str(row[0])
        mall_name = mall_names.get(current_mall_id, f"Mall {current_mall_id}")
        
        hours_val = row[1]
        hours = str(int(hours_val)) if isinstance(hours_val, (int, float)) else "0"
             
        fee_val = row[2]
        entry_time = row[3] if row[3] is not None else "N/A"
        exit_time = row[4] if row[4] is not None else "Still Parked"
        status_val = row[5]

        if status_val != 'Completed':
            fee_display = "Unpaid"
        else:
            fee_display = f"R{fee_val:.2f}" if isinstance(fee_val, (int, float)) else f"R{fee_val}"
        
        print(f"{mall_name:<32}{hours:<10}{fee_display:<12}{entry_time:<22}{exit_time:<19}")
                
    print("="*98)
    conn.close()
def pay_outstanding(user_id, mall_choice):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT record_id, total_fee, hours_parked 
            FROM ParkingRecords 
            WHERE user_id = ? AND mall_id = ? AND (status IS NULL OR status != 'Completed')
            ORDER BY entry_time DESC LIMIT 1
        """, (user_id, mall_choice))
        
        record = cursor.fetchone()
        
        if not record:
            print("\nOutstanding balance clean! You have no unpaid records here.")
            conn.close()
            return
            
        record_id, fee, hours = record
        
        print("\n" + "="*50)
        print("Outstanding Parking Balance".center(50))
        print("="*50)
        print(f"Hours Logged: {int(hours)} hrs")
        print(f"Total Due:    R{fee:.2f}")
        print("="*50)
        
        confirm = input("\nProcess payment for this outstanding fee? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            import datetime
            current_exit_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE ParkingRecords 
                SET status = 'Completed', exit_time = ? 
                WHERE record_id = ?
            """, (current_exit_time, record_id))
            
            conn.commit()
            print("\nPayment complete! Your history has been updated.")
        else:
            print("\nPayment skipped. Record remains unpaid.")
            
    except sqlite3.OperationalError as e:
        print(f"\n[Database Error]: {e}")
    finally:
        conn.close()

def customer_menu(user_id):
    print("\n--- Select a Mall ---")
    print("1. Gateway Theatre of Shopping (Flat: R15, Capacity: 250)")
    print("2. Pavilion Shopping centre (Hourly: R10/hr, Capacity: 180)" )
    print("3. La Lucia Mall (R12/hr capped at R60, Capacity: 150)")
    mall_choice =input("choice: ").strip()

    mall_names = {
        "1": "Gateway",
        "2": "Pavilion",
        "3": "LaLucia"
    }
    selected_mall_name = mall_names.get(mall_choice, "Unknown Mall")

    while True:
        print(f"\nCustomer Menu - {selected_mall_name}")
        print("1 - Vehicle Entry")
        print("2 - Vehicle Exit")
        print("3 - View History")
        print("4 - Pay Outstanding")
        print("5 - Logout")

        user_selection = input("Select an option: ").strip()

        if user_selection == "1":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ParkingRecords WHERE mall_id = ? AND status = 'Active'", (mall_choice,))
            active_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT capacity FROM Malls WHERE mall_id = ?", (mall_choice,))
            mall_cap_row = cursor.fetchone()
            conn.close()
            
            if mall_cap_row and active_count >= mall_cap_row[0]:
                print("\n[Entry Denied]: The mall has reached full capacity!")
                continue

            try:
                hours = int(input("How many hours will you be parked? "))
            except ValueError:
                print("Invalid input number. Defaulting to 1 hour.")
                hours = 1

            fee = 0 
            if mall_choice =="1": 
                fee = 20
            elif mall_choice == "2": 
                fee = hours * 10
            elif mall_choice == "3": 
                fee = min(hours * 15, 50)

            try:
                import datetime
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO ParkingRecords (user_id, mall_id, total_fee, entry_time, hours_parked) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, mall_choice, fee, current_time, hours))
                                     
                conn.commit()
                print("\nVehicle entry recorded successfully!")

            except sqlite3.OperationalError as e:
                print(f"\n[Database Error] Could not write to disk: {e}")
                print("Tip: Close DB Browser or any external SQLite extensions and try again.")
            finally:
                if conn:
                    conn.close()    

        elif user_selection == "2":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT record_id, hours_parked, total_fee 
                FROM ParkingRecords 
                WHERE user_id = ? AND mall_id = ? AND status = 'Active'
                ORDER BY entry_time DESC LIMIT 1
            """, (user_id, mall_choice))
            record = cursor.fetchone()
            
            if not record:
                print("\nNo active vehicle entry found for this mall session.")
                conn.close()
                continue
                
            record_id, hours_parked, total_fee = record
            conn.close()

            pricing_text = ""
            if mall_choice == "1":
                pricing_text = "Flat Rate (R15 per visit) - regardless of duration"
            elif mall_choice == "2":
                pricing_text = "Hourly Rate (R10 per hour)"
            elif mall_choice == "3":
                pricing_text = "Hourly Rate with Cap (R12 per hour, max R60)"
                
            print(f"\nDuration (hours): {int(hours_parked)}")
            print(f"Pricing Applied: {pricing_text}")
            print(f"Amount Due: R {int(total_fee)}")
            
            confirm = input("Confirm payment (yes/no): ").strip().lower()
            if confirm == "yes":
                import datetime
                current_exit_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("UPDATE ParkingRecords SET status = 'Completed', exit_time = ? WHERE record_id = ?", (current_exit_time, record_id,))
                conn.commit()
                conn.close()
                print("Payment successful! Drive safely.")
            else:
                print("Payment pending.")

        elif user_selection == "3":
            view_customer_history(user_id, mall_choice)
        elif user_selection == "4":
            pay_outstanding(user_id, mall_choice)
        elif user_selection == "5":
            print("Logging out...")
            break
        else:
            print("Invaild option.")

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
            1: 'Gateway Theatre of Shopping',
            2: 'Pavilion SHopping Centre',
            3: 'La Lucia Mall'
        }
        name = mall_name.get(int(mall_id), "Unknown Mall")
          
        print(f"\n=============================================")
        print(f" ADMIN DASHBOARD: {name}")
        print(f"=============================================")
        print(f"1. View occupancy & revenue report")
        print(f"2. Log out")

        choice = input("Select an option: ")

        if choice == "1":
            print(f"\n===============================================")
            print(f" Current status for {name}")
            print(f"===============================================")
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
    print(" OWNER OVERVIEW ".center(60))
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
                        print("\nError: This Admin has no assigned mall. Please contact the owner.")
                elif role == "Owner":
                    owner_report()

        elif choice == "2":
            register_user()
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please try again.")

if __name__ =="__main__":
    main()