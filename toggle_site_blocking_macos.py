import sys
import subprocess
import time
import os

TIME_DELAY = 5
HOSTS_FILE = "/etc/hosts"
BLOCKED_IP = "127.0.0.1"

# Multiline string containing site aliases
SITE_ALIASES = """
twitter=twitter.com, www.twitter.com, x.com, www.x.com
facebook=facebook.com, www.facebook.com
x=twitter.com, www.twitter.com, x.com, www.x.com
"""

def read_site_aliases():
    aliases = {}
    for line in SITE_ALIASES.strip().split('\n'):
        if line.strip() and not line.startswith('#'):
            parts = line.strip().split('=')
            if len(parts) == 2:
                key = parts[0].strip()
                values = [v.strip() for v in parts[1].split(',')]
                aliases[key] = values
    return aliases

def is_site_blocked(site):
    with open(HOSTS_FILE, 'r') as f:
        for line in f:
            if line.strip().startswith(BLOCKED_IP) and site in line:
                return True
    return False

def toggle_block_site(site):
    aliases = read_site_aliases()
    sites_to_toggle = aliases.get(site, [site, f"www.{site}"])
    
    with open(HOSTS_FILE, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if not any(site in line for site in sites_to_toggle):
            new_lines.append(line)
    
    if not is_site_blocked(sites_to_toggle[0]):
        for site in sites_to_toggle:
            new_lines.append(f"{BLOCKED_IP} {site}\n")
    
    # Use sudo to write to the hosts file
    with open('temp_hosts', 'w') as f:
        f.writelines(new_lines)
    
    os.system(f"sudo mv temp_hosts {HOSTS_FILE}")
    
    flush_dns_cache()

def list_blocked_sites():
    with open(HOSTS_FILE, 'r') as f:
        for line in f:
            if line.strip().startswith(BLOCKED_IP):
                print(line.strip())

def flush_dns_cache():
    try:
        subprocess.run(['sudo', 'dscacheutil', '-flushcache'], check=True)
        subprocess.run(['sudo', 'killall', '-HUP', 'mDNSResponder'], check=True)
        print("DNS cache flushed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while flushing DNS cache: {e}")
        print("You may need to flush the DNS cache manually.")

def main():
    if len(sys.argv) != 2:
        print("Usage: sudo python toggle_site_blocking.py <site|list>")
        sys.exit(1)

    if os.geteuid() != 0:
        print("This script must be run with sudo privileges.")
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "list":
        list_blocked_sites()
    else:
        aliases = read_site_aliases()
        sites_to_toggle = aliases.get(command, [command, f"www.{command}"])
        
        if is_site_blocked(sites_to_toggle[0]):
            print(f"Unblocking {command} in {TIME_DELAY} seconds...")
            for remaining in range(TIME_DELAY, 0, -1):
                sys.stdout.write(f"\rTime remaining: {remaining} seconds")
                sys.stdout.flush()
                time.sleep(1)
            print("\nTime is up! Unblocking the site now.")
        else:
            print(f"Blocking {command} now.")
        
        toggle_block_site(command)

if __name__ == "__main__":
    main()
