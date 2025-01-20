import requests
import random
import os
import threading
from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime
from fake_useragent import UserAgent
from colorama import init, Fore, Style

init(autoreset=True)

def get_headers():
    ua = UserAgent()
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://earn.taker.xyz',
        'Referer': 'https://earn.taker.xyz/',
        'User-Agent': ua.random
    }

def format_console_output(timestamp, current, total, status, address, referral, status_color=Fore.BLUE):
    return (
        f"[ "
        f"{Style.DIM}{timestamp}{Style.RESET_ALL} "
        f"] [ "
        f"{Fore.YELLOW}{current}/{total}{Fore.WHITE} ] [ "
        f"{status_color}{status}{Fore.WHITE} ] "
        f"{Fore.BLUE}Address: {Fore.YELLOW}{address} "
        f"{Fore.MAGENTA}[ {Fore.GREEN}{referral}{Fore.MAGENTA} ]"
    )

def load_proxies():
    if not os.path.exists('proxies.txt'):
        return []
    with open('proxies.txt', 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def get_random_proxy(proxies):
    if not proxies:
        return None
    return random.choice(proxies)

def generate_wallet():
    w3 = Web3()
    acct = w3.eth.account.create()
    return acct.key.hex(), acct.address

def sign_message(private_key, message):
    w3 = Web3()
    message_hash = encode_defunct(text=message)
    signed_message = w3.eth.account.sign_message(message_hash, private_key)
    return signed_message.signature.hex()

def save_account(private_key, address, referral_code):
    with open('accounts.txt', 'a') as f:
        f.write(f"Wallet Privatekey: {private_key}\n")
        f.write(f"Wallet Address: {address}\n")
        f.write(f"Referred to: {referral_code}\n")
        f.write("-" * 85 + "\n")

def create_account(referral_code, account_number, total_accounts, proxies):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    private_key, address = generate_wallet()

    request_headers = get_headers()
    proxy = get_random_proxy(proxies)
    proxies_dict = {'http': proxy, 'https': proxy} if proxy else None

    try:
        nonce_response = requests.post(
            'https://lightmining-api.taker.xyz/wallet/generateNonce',
            headers=request_headers,
            json={"walletAddress": address},
            proxies=proxies_dict,
            timeout=None
        )

        if nonce_response.status_code != 200:
            print(f"{Fore.RED}Failed to get nonce. Status code: {nonce_response.status_code}")
            return False

        response_data = nonce_response.json()
        if not response_data or 'data' not in response_data or 'nonce' not in response_data['data']:
            print(f"{Fore.RED}Invalid nonce response format: {response_data}")
            return False

        message = response_data['data']['nonce']
        signature = sign_message(private_key, message)

        login_response = requests.post(
            'https://lightmining-api.taker.xyz/wallet/login',
            headers=request_headers,
            json={
                "address": address,
                "signature": signature,
                "message": message,
                "invitationCode": referral_code
            },
            proxies=proxies_dict,
            timeout=None
        )

        if login_response.status_code == 200:
            response_data = login_response.json()
            if not response_data or 'data' not in response_data or 'token' not in response_data['data']:
                print(f"{Fore.RED}Invalid login response format: {response_data}")
                return False

            print(format_console_output(timestamp, account_number, total_accounts, "SUCCESS", address, referral_code, Fore.GREEN))
            save_account(private_key, address, referral_code)
            return True
        else:
            print(format_console_output(timestamp, account_number, total_accounts, "LOGIN FAILED", address, referral_code, Fore.RED))
            print(f"{Fore.RED}Login failed with status code: {login_response.status_code}")
            return False

    except Exception as e:
        print(format_console_output(timestamp, account_number, total_accounts, "ERROR", address, referral_code, Fore.RED))
        print(f"{Fore.RED}Error details: {str(e)}")
        return False

def print_header():
    header = """
╔══════════════════════════════════════════╗
║   make dua that i get married to a pretty arab lady. AMEEN ║
╚══════════════════════════════════════════╝"""
    print(f"{Fore.CYAN}{header}{Style.RESET_ALL}")

def worker_thread(referral_code, account_number, total_accounts, proxies, success_counter):
    if create_account(referral_code, account_number, total_accounts, proxies):
        success_counter.append(1)

def main():
    print_header()
    referral_code = input(f"{Fore.YELLOW}Enter referral code: {Style.RESET_ALL}")
    try:
        num_accounts = int(input(f"{Fore.YELLOW}Enter the number of referrals you need: {Style.RESET_ALL}"))
        if num_accounts <= 0:
            print(f"{Fore.RED}Please enter a positive number.")
            return
    except ValueError:
        print(f"{Fore.RED}Invalid input. Please enter a valid number.")
        return

    print()

    proxies = load_proxies()
    if not proxies:
        print(f"{Fore.YELLOW}No proxies found in proxies.txt, running without proxies")

    threads = []
    success_counter = []
    batch_size = 2000  # Set the batch size to 2000 threads per batch
    for i in range(1, num_accounts + 1):
        thread = threading.Thread(target=worker_thread, args=(referral_code, i, num_accounts, proxies, success_counter))
        threads.append(thread)
        thread.start()

        if len(threads) >= batch_size:
            for thread in threads:
                thread.join()  # Wait for all threads in this batch to finish
            threads = []  # Reset the thread list for the next batch

    for thread in threads:
        thread.join()  # Wait for any remaining threads to finish

    print(f"\n{Fore.CYAN}[✓] All Process Completed!{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Total: {Fore.YELLOW}{num_accounts} {Fore.WHITE}| "
          f"Success: {Fore.GREEN}{len(success_counter)} {Fore.WHITE}| "
          f"Failed: {Fore.RED}{num_accounts - len(success_counter)}")

if __name__ == "__main__":
    main()
