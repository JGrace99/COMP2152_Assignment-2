"""
Author: Jack Grace
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime

import socket
import threading
import sqlite3
import os
import platform
import sys
import datetime

# TODO: Print Python version and OS name (Step iii)

print(f"Python Version: {platform.python_version()}")
print(f"Operating System: {os.name}")

# TODO: Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores

# List of protocols and their respective port numbers
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"

class NetworkTool:
    def __init__(self, target):
        print("Network tool created!")
        self.__target = target
    
    # Q3: What is the benefit of using @property and @target.setter?
    # @property lets you access a method like a plain attribute,
    # while @target.setter intercepts assignments to add logic such as validation.
    # Together they let you control how an attribute is read and written without changing the interface.
    @property
    def target(self):
        return self.__target
    
    # Complex setter
    @target.setter
    def target(self, new_target):
        if new_target:
            self.__target = new_target
            print(f"New target set!: {new_target}")
        else:
            print("Error: Target cannot be empty")
    
    # Destructor
    def __del__(self):
        print("NetworkTool instance destroyed")

# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner inherits from NetworkTool and automatically gets the target property, its validation logic,
# and the destructor without rewriting them.
# PortScanner gets these features from NetworkTool through class inheritance, so there is no need to redefine them.
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def scan_port(self, port):
        # Q4: What would happen without try-except here?
        # If a socket operation fails, an unhandled socket error would crash the thread.
        # However, each port runs on its own thread, so it would only kill that one thread silently.
        # Incomplete results would arise with no traceback, and the socket would never be closed
        # since the finally block requires try-except to work.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))

            if result == 0:
                status = "Open"
            else:
                status = "Closed"
            
            # Checks list of common ports.
            # Gets the service name / name of port

            service_name = common_ports.get(port, "Unknown")
            
            self.lock.acquire()
            self.scan_results.append((port, status, service_name))
            self.lock.release()

        except socket.error as se:
            print(f"Error scanning port {port}: {se}")
        finally:
            sock.close()

    def get_open_ports(self):
        # Creating new list from tuples using a conditional list comprehension 
        return [(port, status, service_name) for port, status, service_name in self.scan_results if status == "Open"]

    # Q2: Why do we use threading instead of scanning one port at a time?
    # Each port scan blocks while waiting for a connection timeout, so scanning sequentially
    # would make a 1024-port scan take over 17 minutes (1 second timeout * 1024 ports / 60 seconds).
    # Threading lets all ports be attempted concurrently, reducing total scan time to roughly one timeout period.
    def scan_range(self, start_port, end_port):
        threads = []
        # end_port + 1 since range in start inclusive - end exclusive
        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def __del__(self):
        print("PortScanner instance destroyed")
        return super().__del__()

# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
DB_NAME = "scan_history.db"
def save_results(target, results):

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS scans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT, 
                        port INTEGER, 
                        status TEXT, 
                        service TEXT, 
                        scan_date TEXT
                    )
                """)
        
        for result in results:
            cursor.execute("INSERT INTO scans (target, port, status, service, scan_date) VALUES (?, ?, ?, ?, ?)",
                            (target, result[0], result[1], result[2], str(datetime.datetime.now())))
        conn.commit()

    except sqlite3.Error as e:
        print(f"Database Error: {e}")
    finally:
        conn.close()

def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()
        print("--- Past Scans ---")
        for row in rows:
            print(f"[{row[5]}] {row[1]} : Port {row[2]} ({row[4]}) - {row[3]}")

    except sqlite3.Error as e:
        print(f"No past scans found.")
    finally:
        conn.close()

# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."

    gathering = True

    while(gathering):
        try:
            target_ip = input("Enter a Target IP Address: ")

            if not target_ip:
                target_ip = "127.0.0.1"

            start_point = int(input("Enter a starting port number (1 - 1024): "))
            if not (start_point >= 1 and start_point <= 1024):
                raise Exception("Port must be between 1 and 1024.")

            end_point = int(input(f"Enter an ending port number ({start_point} - 1024): "))
            if not (end_point >= start_point and end_point <= 1024):
                raise Exception("Port must be between 1 and 1024.")

            gathering = False

        except ValueError:
            print("Invalid input. Please enter a valid integer.")
        except Exception as e:
            print(e)

    # TODO: After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()

    port_scanner = PortScanner(target_ip)

    print(f"Scanning {target_ip} from port {start_point} to {end_point}...")
    port_scanner.scan_range(start_point, end_point)

    print(f"--- Scan Results for {target_ip} ---")

    scans = port_scanner.get_open_ports()
    for scan in scans:
        print(f"Port {scan[0]}: {scan[1]} ({scan[2]})")

    print("------")
    print(f"Total open ports found: {len(scans)}")  

    save_results(target_ip, port_scanner.scan_results)

    get_history = True

    while(get_history):
        answer = input("Would you like to see past scan history? (yes/no): ")
        if answer.lower() == "yes":
            load_past_scans()
            break
        elif answer.lower() == "no":
            break
        else:
            print("Please enter a valid input!")

# Q5: New Feature Proposal
# A save_to_csv(filename, results) function could write open port scan results to a .csv file
# using Python's built-in csv module. It would use a list comprehension to filter only open ports,
# then write a header row followed by each port, status, and service name.
# This gives users a portable, human-readable export they can open in Excel or other tools.
# Diagram: See diagram_101577863.png in the repository root
