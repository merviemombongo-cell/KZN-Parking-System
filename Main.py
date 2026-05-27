import sqlite3
import math
from datetime import datetime

def get_db_connection():
    return sqlite3.connect(r"D:\Richfield _IT\ASSIGNMENTS\KZN Parking System\parking_system.db")

def get_all_malls_dict():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT mall_id, name FROM malls")
        malls = {str(row[0]): row[1] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        malls = {
            "1": "Gateway Theatre of Shopping",
            "2": "Pavilion Shopping centre",
            "3": "La Lucia Mall",
        }
    finally:
        conn.close()
    return malls

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
            mall_names = get_all_malls_dict()
            print("Enter Mall ID for this Admin:")
            for m_id, name in mall_names.items():
                print(f"{m_id}. {name}")
            
            mall_id = int(input("Choice: "))
            mall_name = mall_names.get(str(mall_id), "Unknown Mall")
            
            if str(mall_id) not in mall_names:
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

    mall_names = get_all_malls_dict()

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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT mall_id, name, capacity, pricing_type, rate, max_cap FROM malls")
        malls_list = cursor.fetchall()
    except sqlite3.OperationalError:
        malls_list = []
    conn.close()

    print("\n--- Select a Mall ---")
    if not malls_list:

        print("1. Gateway Theatre of Shopping (Flat: R15, Capacity: 250)")
        print("2. Pavilion Shopping centre (Hourly: R10/hr, Capacity: 180)" )
        print("3. La Lucia Mall (R12/hr capped at R60, Capacity: 150)")
        malls_list = [
            (1, "Gateway Theatre of Shopping", 250, "Flat", 15.0, None),
            (2, "Pavilion Shopping centre", 180, "Hourly", 10.0, None),
            (3, "La Lucia Mall", 150, "Capped", 12.0, 60.0)
        ]
    else:
        for row in malls_list:
            if row[3] == "Flat":
                pricing_desc = f"Flat: R{int(row[4])}"
            elif row[3] == "Hourly":
                pricing_desc = f"Hourly: R{int(row[4])}/hr"
            else:
                pricing_desc = f"R{int(row[4])}/hr capped at R{int(row[5])}"
            print(f"{row[0]}. {row[1]} ({pricing_desc}, Capacity: {row[2]})")

    mall_choice = input("choice: ").strip()

    selected_mall = None
    for row in malls_list:
        if str(row[0]) == mall_choice:
            selected_mall = row
            break

    if selected_mall:
        full_mall_name = selected_mall[1]
        if "La Lucia" in full_mall_name:
            selected_mall_name = "La Lucia"
        else:
            selected_mall_name = full_mall_name.split()[0] 
        mall_capacity = selected_mall[2]
        pricing_type = selected_mall[3]
        rate_val = selected_mall[4]
        cap_val = selected_mall[5]
    else:
        selected_mall_name = "Unknown Mall"
        mall_capacity = 200
        pricing_type = "Hourly"
        rate_val = 10.0
        cap_val = None

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
            
            if active_count >= mall_capacity:
                print("\n[Entry Denied]: The mall has reached full capacity!")
                conn.close()
                continue
            conn.close()

            try:
                hours = int(input("How many hours will you be parked? "))
            except ValueError:
                print("Invalid input number. Defaulting to 1 hour.")
                hours = 1

            if pricing_type == "Flat":
                fee = rate_val
            elif pricing_type == "Hourly":
                fee = hours * rate_val
            elif pricing_type == "Capped":
                fee = min(hours * rate_val, cap_val)
            else:
                fee = hours * 10.0

            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO ParkingRecords (user_id, mall_id, total_fee, entry_time, hours_parked, status) 
                    VALUES (?, ?, ?, ?, ?, 'Active')
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

            pricing_text = f"{pricing_type} Structure Configured Rules Engine"
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
                current_exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT capacity, name FROM malls WHERE mall_id = ?", (mall_id,))
        mall_row = cursor.fetchone()
        max_capacity = mall_row[0] if mall_row else 200
        full_name = mall_row[1] if mall_row else "Unknown Mall"
    except sqlite3.OperationalError:
        max_capacity = 200
        full_name = "Unknown Mall"
    conn.close()

    while True:
        if "La Lucia" in full_name:
            short_name = "La Lucia"
        else:      
            short_name = full_name.split()[0]

        print(f"\nAdmin Menu - {short_name}")
        print("1 - View Vehicles Currently Parked")
        print("2 - Monitor Parking Capacity")
        print("3 - View occupancy & revenue report")
        print("4 - Logout")

        choice = input("Select an option: ").strip()
        
        if choice == "1":
            print(f"\n--- Vehicles currently parked @ {short_name} mall ---")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT Users.username, ParkingRecords.entry_time 
                FROM ParkingRecords
                JOIN Users ON ParkingRecords.user_id = Users.user_id
                WHERE ParkingRecords.mall_id = ? AND (ParkingRecords.status IS NULL OR ParkingRecords.status != 'Completed')
            """, (mall_id,))
            
            parked_vehicles = cursor.fetchall()
            conn.close()

            if not parked_vehicles:
                print("There is no parked vehicles.")
            else:
                for vehicle in parked_vehicles:
                    username, entry_time = vehicle
                    print(f"User: {username} | Entry: {entry_time}")
            
            input("\nPress enter to continue...")

        elif choice == "2":
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM ParkingRecords 
                WHERE mall_id = ? AND (status IS NULL OR status != 'Completed')
            """, (mall_id,))
            
            current_vehicles = cursor.fetchone()[0]
            conn.close()
            
            remaining_capacity = max_capacity - current_vehicles
            
            print(f"\nCurrent vehicles: {current_vehicles}")
            print(f"Remaining capacity: {remaining_capacity}")
            
            input("\nPress enter to continue...")

        elif choice == "3":
            import datetime
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM ParkingRecords 
                WHERE mall_id = ? AND entry_time LIKE ?
            """, (mall_id, f"{today_str}%"))
            total_entries_today = cursor.fetchone()[0]

            cursor.execute("""
                SELECT SUM(total_fee) FROM ParkingRecords 
                WHERE mall_id = ? AND status = 'Completed'
            """, (mall_id,))

            result_revenue = cursor.fetchone()[0]
            total_revenue = result_revenue if result_revenue is not None else 0.0
            conn.close()
            
            print(f"\n" + "="*60)
            print(f" Current status for {full_name}")
            print("="*60)
            print(f"Total vehicles parked today: {total_entries_today}")
            print(f"Total revenue earned: R {total_revenue:.2f}")

            if total_entries_today > 50:
                print("STATUS: High occupancy - Monitor exit gates")
            else:
                print("STATUS: Normal operations")
            print("="*60)
            input("\nPress enter to continue...")

        elif choice == "4":
            print("Logging out of admin session...")
            break
        else:
            print("Invaild option. Please try again.")
        
def owner_report():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mall_id, COUNT(record_id), SUM(total_fee), AVG(hours_parked)
        FROM ParkingRecords
        GROUP BY mall_id
    """)

    results = cursor.fetchall()
    conn.close()

    mall_names = get_all_malls_dict()

    print("\n" + "="*77)
    print(" OWNER OVERVIEW ".center(77))
    print("="*77)
    print(f"{'MALL NAME':<30} | {'VEHICLES':<6} | {'REVENUE':<12} | {'AVG DURATION (HRS)':<18}")
    print("="*77)

    grand_total_revenue = 0
    grand_total_vehicles = 0
    total_hours_sum = 0

    if not results and not mall_names:
        print("No parking records found,")
    else:
        order_map = {str(m_id): None for m_id in mall_names.keys()}
        for row in results:
            order_map[str(row[0])] = row

        for m_id in sorted(mall_names.keys(), key=int):
            row = order_map[m_id]
            m_name = mall_names.get(m_id, "Unknown")
            
            if row:
                m_vehicles = row[1]
                m_rev = row[2] if row[2] else 0.0
                m_avg_duration = row[3] if row[3] else 0.0
            else:
                m_vehicles = 0
                m_rev = 0.0
                m_avg_duration = 0.0

            print(f"{m_name:<30} | {m_vehicles:<8} | R{m_rev:<12.2f}| {m_avg_duration:<18.1f}")   

            grand_total_revenue += m_rev
            grand_total_vehicles += m_vehicles
            total_hours_sum += (m_avg_duration * m_vehicles)

    grand_avg_duration = (total_hours_sum / grand_total_vehicles) if grand_total_vehicles > 0 else 0.0          
   
    print("="*77)
    print(f"{'TOTAL SYSTEM':<30} | {grand_total_vehicles:<8} | R{grand_total_revenue:<12.2f}| {grand_avg_duration:<18.1f}")
    print("="*77)
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