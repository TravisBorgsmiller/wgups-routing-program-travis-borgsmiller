# Student ID: 011697233
# File: main.py
# WGUPS Routing Program - Task 2 Implementation
# Uses Nearest Neighbor Algorithm to deliver all packages under 140 miles.

import csv
import datetime


class ChainingHashTable:
    """Custom hash table utilizing direct chaining with lists and tuples."""
    def __init__(self, initial_capacity=40):
        self.capacity = initial_capacity
        self.table = [[] for _ in range(initial_capacity)]
        self.size = 0

    def _hash(self, key):
        return int(key) % self.capacity

    def insert(self, key, item):
        bucket_index = self._hash(key)
        bucket = self.table[bucket_index]
        for i, pair in enumerate(bucket):
            if pair[0] == key:
                bucket[i] = (key, item)
                return True
        bucket.append((key, item))
        self.size += 1
        return True

    def lookup(self, key):
        bucket_index = self._hash(key)
        bucket = self.table[bucket_index]
        for pair in bucket:
            if pair[0] == key:
                return pair[1]
        return None


class Package:
    """Represents a package and tracks its real-time delivery state."""
    def __init__(self, pkg_id, address, city, state, zip_code, deadline, weight, notes):
        self.pkg_id = int(pkg_id)
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight
        self.notes = notes
        
        # Delivery state tracking
        self.departure_time = None
        self.delivery_time = None
        self.truck_id = None
        self.status = "At the Hub"

    def status_at_time(self, query_time):
        """Calculates dynamic status and handles address correction for Package #9."""
        # Handle Package #9 address correction logic
        current_address = self.address
        current_zip = self.zip_code
        if self.pkg_id == 9:
            correction_time = datetime.timedelta(hours=10, minutes=20)
            if query_time < correction_time:
                current_address = "300 State St"
                current_zip = "84103"
            else:
                current_address = "410 S State St"
                current_zip = "84111"

        # Delayed flight packages before 9:05 AM are labeled 'Delayed'
        delayed_ids = [6, 25, 28, 32]
        delayed_arrival = datetime.timedelta(hours=9, minutes=5)
        if self.pkg_id in delayed_ids and query_time < delayed_arrival:
            return "Delayed (Flight)", current_address, current_zip

        # Evaluate physical transit state
        if self.delivery_time and query_time >= self.delivery_time:
            return f"Delivered at {self.delivery_time}", current_address, current_zip
        elif self.departure_time and query_time >= self.departure_time:
            return "En Route", current_address, current_zip
        else:
            return "At the Hub", current_address, current_zip

    def __str__(self):
        return (f"Package ID: {self.pkg_id:2d} | Truck: {self.truck_id} | "
                f"Address: {self.address:<35} | {self.city}, {self.state} {self.zip_code} | "
                f"Deadline: {self.deadline:<8} | Weight: {self.weight:2d}kg | "
                f"Status: {self.status}")


class Truck:
    """Represents a delivery vehicle with route and mileage tracking."""
    def __init__(self, truck_id, departure_time):
        self.truck_id = truck_id
        self.departure_time = departure_time
        self.current_time = departure_time
        self.current_address_idx = 0  # Starts at HUB (index 0)
        self.packages = []
        self.route = []
        self.total_miles = 0.0


# ----------------------------------------------------------------------
# DATA LOADING FUNCTIONS
# ----------------------------------------------------------------------

def load_address_data(filename='addresses.csv'):
    """Reads address names and maps address strings to unique integer indices."""
    address_list = []
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            address_list.append(row[2].strip().lower())
    return address_list


def load_distance_data(filename='distances.csv'):
    """Reads distance matrix between all 27 Salt Lake City locations."""
    distance_matrix = []
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            distance_matrix.append([float(val) for val in row])
    return distance_matrix


def load_package_data(filename='packages.csv', hash_table=None):
    """Loads packages into custom hash table."""
    if hash_table is None:
        hash_table = ChainingHashTable()
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            pkg = Package(
                pkg_id=row[0],
                address=row[1],
                city=row[2],
                state=row[3],
                zip_code=row[4],
                deadline=row[5],
                weight=int(row[6]),
                notes=row[7] if len(row) > 7 else ""
            )
            hash_table.insert(pkg.pkg_id, pkg)
    return hash_table


# ----------------------------------------------------------------------
# HELPER ROUTING FUNCTIONS
# ----------------------------------------------------------------------

def get_address_index(address_str, address_list):
    """Matches raw package address string to distance matrix index."""
    cleaned = address_str.strip().lower()
    for idx, addr in enumerate(address_list):
        if addr in cleaned or cleaned in addr:
            return idx
    # Specific edge conditions
    if "5383" in cleaned:
        return 24
    if "6351" in cleaned:
        return 26
    raise ValueError(f"Address '{address_str}' not matched in distance list.")


def distance_between(idx1, idx2, distance_matrix):
    """Retrieves bidirectional distance between two address indices."""
    return distance_matrix[idx1][idx2]


# ----------------------------------------------------------------------
# NEAREST NEIGHBOR ROUTING ALGORITHM
# ----------------------------------------------------------------------

def deliver_truck_packages(truck, distance_matrix, address_list, hash_table):
    """
    Executes delivery using a greedy Nearest Neighbor algorithm.
    Finds unvisited package at minimum distance, advances truck clock at 18 mph,
    records delivery timestamps, and returns to hub.
    """
    unvisited = [hash_table.lookup(pid) for pid in truck.packages]
    
    # Set package departure time and truck ID
    for pkg in unvisited:
        pkg.departure_time = truck.departure_time
        pkg.truck_id = truck.truck_id

    current_idx = truck.current_address_idx

    while unvisited:
        nearest_pkg = None
        min_dist = float('inf')

        for pkg in unvisited:
            # Check package 9 address update
            pkg_addr = "410 S State St" if pkg.pkg_id == 9 else pkg.address
            dest_idx = get_address_index(pkg_addr, address_list)
            dist = distance_between(current_idx, dest_idx, distance_matrix)
            if dist < min_dist:
                min_dist = dist
                nearest_pkg = pkg

        # Advance truck position and time
        pkg_addr = "410 S State St" if nearest_pkg.pkg_id == 9 else nearest_pkg.address
        dest_idx = get_address_index(pkg_addr, address_list)
        transit_hours = min_dist / 18.0
        truck.current_time += datetime.timedelta(hours=transit_hours)
        truck.total_miles += min_dist
        truck.current_address_idx = dest_idx

        # Update package state
        nearest_pkg.delivery_time = truck.current_time
        nearest_pkg.status = f"Delivered at {nearest_pkg.delivery_time}"
        truck.route.append(nearest_pkg.pkg_id)
        unvisited.remove(nearest_pkg)
        current_idx = dest_idx

    # Return truck to Hub (Index 0)
    return_dist = distance_between(current_idx, 0, distance_matrix)
    truck.total_miles += return_dist
    truck.current_time += datetime.timedelta(hours=return_dist / 18.0)
    truck.current_address_idx = 0


# ----------------------------------------------------------------------
# MAIN EXECUTION & CLI
# ----------------------------------------------------------------------

def main():
    address_list = load_address_data('addresses.csv')
    distance_matrix = load_distance_data('distances.csv')
    package_table = load_package_data('packages.csv')

    # Truck 1: Leaves at 8:00 AM with mutual constraint packages & morning deadlines
    truck1 = Truck(truck_id=1, departure_time=datetime.timedelta(hours=8, minutes=0))
    truck1.packages = [13, 14, 15, 16, 19, 20, 1, 29, 30, 31, 34, 37, 40, 2, 4, 7]

    # Truck 2: Leaves at 9:05 AM (waiting for delayed flight packages; handles Truck 2 only packages)
    truck2 = Truck(truck_id=2, departure_time=datetime.timedelta(hours=9, minutes=5))
    truck2.packages = [3, 18, 36, 38, 6, 25, 28, 32, 26, 27, 33, 35]

    # Deliver Truck 1 & Truck 2
    deliver_truck_packages(truck1, distance_matrix, address_list, package_table)
    deliver_truck_packages(truck2, distance_matrix, address_list, package_table)

    # Truck 3: Leaves after Truck 1 returns and after 10:20 AM (when Pkg 9 address is corrected)
    truck3_start = max(truck1.current_time, datetime.timedelta(hours=10, minutes=20))
    truck3 = Truck(truck_id=3, departure_time=truck3_start)
    truck3.packages = [5, 8, 9, 10, 11, 12, 17, 21, 22, 23, 24, 39]

    # Deliver Truck 3
    deliver_truck_packages(truck3, distance_matrix, address_list, package_table)

    total_mileage = truck1.total_miles + truck2.total_miles + truck3.total_miles

    # Command Line Interface
    print("=" * 80)
    print("         WESTERN GOVERNORS UNIVERSITY PARCEL SERVICE (WGUPS)")
    print("=" * 80)
    print(f"Total Mileage Traveled by All Trucks: {total_mileage:.2f} miles")
    print(f"  * Truck 1 Distance: {truck1.total_miles:.2f} miles | Finished at: {truck1.current_time}")
    print(f"  * Truck 2 Distance: {truck2.total_miles:.2f} miles | Finished at: {truck2.current_time}")
    print(f"  * Truck 3 Distance: {truck3.total_miles:.2f} miles | Finished at: {truck3.current_time}")
    print("=" * 80)

    while True:
        print("\nSelect an Option:")
        print("1. View Status of All Packages at a Specific Time")
        print("2. Lookup a Single Package by ID at a Specific Time")
        print("3. Exit Program")
        choice = input("Enter choice (1-3): ").strip()

        if choice == '1':
            time_str = input("Enter time in HH:MM:SS format (e.g., 09:00:00): ").strip()
            try:
                h, m, s = map(int, time_str.split(':'))
                user_time = datetime.timedelta(hours=h, minutes=m, seconds=s)
            except ValueError:
                print("Invalid time format. Please use HH:MM:SS.")
                continue

            print(f"\n================ PACKAGE STATUS SNAPSHOT AT {user_time} ================")
            print(f"{'ID':<4}{'Truck':<7}{'Address':<32}{'Deadline':<10}{'City':<18}{'Zip':<7}{'Weight':<8}{'Status'}")
            print("-" * 105)
            for pid in range(1, 41):
                pkg = package_table.lookup(pid)
                status, addr, z_code = pkg.status_at_time(user_time)
                print(f"{pkg.pkg_id:<4}{pkg.truck_id:<7}{addr:<32}{pkg.deadline:<10}{pkg.city:<18}{z_code:<7}{pkg.weight:<8}{status}")
            print("=" * 105)

        elif choice == '2':
            pid_str = input("Enter Package ID (1-40): ").strip()
            time_str = input("Enter time in HH:MM:SS format (e.g., 10:00:00): ").strip()
            try:
                pid = int(pid_str)
                h, m, s = map(int, time_str.split(':'))
                user_time = datetime.timedelta(hours=h, minutes=m, seconds=s)
            except ValueError:
                print("Invalid input values. Try again.")
                continue

            pkg = package_table.lookup(pid)
            if not pkg:
                print("Package not found.")
                continue

            status, addr, z_code = pkg.status_at_time(user_time)
            print("\n---------------- PACKAGE DETAILS ----------------")
            print(f"Package ID:        {pkg.pkg_id}")
            print(f"Assigned Truck:    {pkg.truck_id}")
            print(f"Delivery Address:  {addr}")
            print(f"City, State, Zip:  {pkg.city}, {pkg.state} {z_code}")
            print(f"Delivery Deadline: {pkg.deadline}")
            print(f"Weight:            {pkg.weight} kg")
            print(f"Special Notes:     {pkg.notes if pkg.notes else 'None'}")
            print(f"Status at {user_time}: {status}")
            print("-------------------------------------------------")

        elif choice == '3':
            print("Exiting WGUPS Delivery Management System. Goodbye!")
            break
        else:
            print("Invalid option. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()