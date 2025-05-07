import time
import threading
import argparse
import sys
import os
import signal
from pypresence import Presence

CLIENT_ID = ""  # Add your Discord application client ID here
RPC = Presence(CLIENT_ID)
rpc_connected = False
active = False

def start_presence(machine_name="Unknown", tools=["terminal"]):
    global RPC, rpc_connected, active
    try:
        if not rpc_connected:
            RPC.connect()
            rpc_connected = True
        
        tools_str = ', '.join([t.title() for t in tools])
        
        # Get the first tool for small image
        first_icon = tools[0] if tools else "terminal"
        # Convert tool name to lowercase for asset matching
        first_icon = first_icon.lower()
        
        # Use a default if the tool isn't recognized
        valid_tool_icons = ["terminal", "burp", "nmap", "metasploit", "wireshark", "ffuf", "gobuster", "dirb"]
        if first_icon not in valid_tool_icons:
            first_icon = "terminal"
            
        print(f"[DEBUG] Using icon: {first_icon}")
        
        # Update the presence with more frequent refreshes
        RPC.update(
            state=f"Using {tools_str}",
            details=f"HTB Machine: {machine_name}",
            large_image="htb_logo",
            small_image=first_icon,
            start=time.time(),
            # Adding buttons to make presence more engaging
            buttons=[
                {"label": "HackTheBox", "url": "https://www.hackthebox.com/"},
                {"label": "Join Discord", "url": "https://discord.gg/hackthebox"}
            ]
        )
        print(f"[+] Presence started for '{machine_name}' using tools: {tools_str}")
        active = True
    except Exception as e:
        print(f"[-] Error: {e}")
        print(f"[-] Debug info: rpc_connected={rpc_connected}, active={active}")

def presence_loop():
    global active
    while active:
        try:
            time.sleep(10)  # Reduced from 15 to 10 seconds for more frequent updates
            if active:  # Check if still active before updating
                # We need to repeat the full update to prevent details from disappearing
                if 'last_machine' in globals() and 'last_tools' in globals():
                    tools_str = ', '.join([t.title() for t in last_tools])
                    first_icon = last_tools[0] if last_tools else "terminal"
                    # Convert tool name to lowercase for asset matching
                    first_icon = first_icon.lower()
                    
                    # Use a default if the tool isn't recognized
                    valid_tool_icons = ["terminal", "burp", "nmap", "metasploit", "wireshark", "ffuf", "gobuster", "dirb"]
                    if first_icon not in valid_tool_icons:
                        first_icon = "terminal"
                    
                    RPC.update(
                        state=f"Using {tools_str}",
                        details=f"HTB Machine: {last_machine}",
                        large_image="htb_logo",
                        small_image=first_icon,
                        start=globals().get('start_time', time.time()),
                        buttons=[
                            {"label": "HackTheBox", "url": "https://www.hackthebox.com/"},
                            {"label": "Join Discord", "url": "https://discord.gg/hackthebox"}
                        ]
                    )
        except Exception as e:
            print(f"[-] Error in presence loop: {e}")
            break

def stop_presence():
    global active, rpc_connected
    try:
        if rpc_connected:
            RPC.clear()
            RPC.close()
    except Exception as e:
        print(f"[-] Error closing presence: {e}")
    
    active = False
    rpc_connected = False
    print("[+] Presence stopped.")

def interactive_menu():
    print("== HackTheBox Discord Presence CLI ==")
    machine = input("Enter HTB Machine Name: ").strip()
    print("Enter tools (comma-separated, e.g. burp,nmap,ffuf):")
    tools_input = input("Tools: ").strip()
    tools = [t.strip().lower() for t in tools_input.split(",") if t.strip()]
    if not tools:
        tools = ["terminal"]
    
    # Store machine and tools globally for the presence loop
    global last_machine, last_tools, start_time
    last_machine = machine
    last_tools = tools
    start_time = time.time()
    
    start_presence(machine, tools)
    t = threading.Thread(target=presence_loop, daemon=True)
    t.start()
    
    try:
        print("Presence active. Press Ctrl+C to stop.")
        # Use a better approach than blocking on input()
        while active:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_presence()
        print("Terminal released. You can continue working.")

def main():
    parser = argparse.ArgumentParser(description="HackTheBox Discord Presence")
    parser.add_argument('--machine', help='HTB Machine name')
    parser.add_argument('--tools', nargs='+', help='List of tools (e.g. burp nmap ffuf)', default=["terminal"])
    parser.add_argument('--background', action='store_true', help='Run in background without blocking terminal')
    parser.add_argument('--status', action='store_true', help='Check if presence is running')
    args = parser.parse_args()

    # Check status if requested
    if args.status:
        try:
            with open(f"{os.path.expanduser('~')}/.htb_presence_pid", "r") as f:
                pid = f.read().strip()
                if os.path.exists(f"/proc/{pid}"):
                    print(f"[+] HTB Presence is running (PID: {pid})")
                else:
                    print("[-] HTB Presence is not running")
        except:
            print("[-] HTB Presence is not running")
        return

    if args.machine:
        # Store machine and tools globally for the presence loop
        global last_machine, last_tools, start_time
        last_machine = args.machine
        last_tools = args.tools
        start_time = time.time()
        
        start_presence(args.machine, args.tools)
        
        if args.background:
            # If in background mode, fork a new process
            try:
                pid = os.fork()
                if pid > 0:
                    # Parent process exits
                    print(f"[+] Running in background (PID: {pid}). Use 'htbpresence --stop' to terminate.")
                    # Save PID to file for later termination
                    with open(f"{os.path.expanduser('~')}/.htb_presence_pid", "w") as f:
                        f.write(str(pid))
                    sys.exit(0)
                else:
                    # Child process continues with presence
                    # Detach from terminal
                    os.setsid()
                    # Close file descriptors
                    os.close(0)
                    os.close(1)
                    os.close(2)
                    # Continue with presence loop without daemon thread
                    while active:
                        try:
                            if active and rpc_connected:
                                tools_str = ', '.join([t.title() for t in last_tools])
                                first_icon = last_tools[0] if last_tools else "terminal"
                                # Convert tool name to lowercase for asset matching
                                first_icon = first_icon.lower()
                                
                                # Use a default if the tool isn't recognized
                                valid_tool_icons = ["terminal", "burp", "nmap", "metasploit", "wireshark", "ffuf", "gobuster", "dirb"]
                                if first_icon not in valid_tool_icons:
                                    first_icon = "terminal"
                                
                                RPC.update(
                                    state=f"Using {tools_str}",
                                    details=f"HTB Machine: {last_machine}",
                                    large_image="htb_logo",
                                    small_image=first_icon,
                                    start=start_time,
                                    buttons=[
                                        {"label": "HackTheBox", "url": "https://www.hackthebox.com/"},
                                        {"label": "Join Discord", "url": "https://discord.gg/hackthebox"}
                                    ]
                                )
                            time.sleep(10)
                        except Exception as e:
                            # Can't print in detached process
                            time.sleep(30)
                            try:
                                if not rpc_connected:
                                    RPC.connect()
                                    rpc_connected = True
                            except:
                                pass
            except OSError:
                print("[-] Failed to start background process")
                stop_presence()
        else:
            # Regular foreground mode
            t = threading.Thread(target=presence_loop, daemon=True)
            t.start()
            try:
                print("Presence active. Press Ctrl+C to stop.")
                while active:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            finally:
                stop_presence()
                print("Terminal released. You can continue working.")
    else:
        interactive_menu()

if __name__ == "__main__":
    # Add a way to stop background processes
    if len(sys.argv) > 1 and sys.argv[1] == "--stop":
        # Try to read PID from file and kill process
        try:
            with open(f"{os.path.expanduser('~')}/.htb_presence_pid", "r") as f:
                pid = int(f.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"[+] Background presence stopped (PID: {pid}).")
                    # Remove PID file
                    os.remove(f"{os.path.expanduser('~')}/.htb_presence_pid")
                except ProcessLookupError:
                    print("[+] No active process found. Cleaning up...")
                    os.remove(f"{os.path.expanduser('~')}/.htb_presence_pid")
                except Exception as e:
                    print(f"[-] Error stopping presence: {e}")
        except FileNotFoundError:
            # No PID file, try to clear directly
            try:
                RPC.connect()
                RPC.clear()
                RPC.close()
                print("[+] Active presence cleared.")
            except:
                print("[+] No active presence found.")
        sys.exit(0)
    
    main()
