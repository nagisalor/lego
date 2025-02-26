import subprocess
import pkg_resources
import sys

def check_and_install_requirements(requirements_file='requirements.txt'):
    try:
        with open(requirements_file, 'r') as file:
            required_packages = file.read().splitlines()

        installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        missing_packages = [pkg for pkg in required_packages if pkg.split('==')[0] not in installed_packages]

        if missing_packages:
            print(f"Modules not installed: {', '.join(missing_packages)}")
            print("Installing required modules...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
            print("All modules have been successfully installed.")
        else:
            print("All modules in requirements.txt are already installed.")
    except FileNotFoundError:
        print(f"File {requirements_file} not found. Please ensure it is in the working directory.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

check_and_install_requirements()

import requests
from eth_account import Account
import time
from eth_account.messages import encode_defunct
import random

def get_proxy():
    try:
        with open('proxy.txt', 'r') as file:
            proxies = file.readlines()
            # Assuming the first line is for HTTP and the second line is for HTTPS
            http_proxy = proxies[0].strip()
            https_proxy = proxies[1].strip() if len(proxies) > 1 else http_proxy  # Default to http_proxy if not provided
            return {"http": http_proxy, "https": https_proxy}
    except FileNotFoundError:
        print("Error: 'proxy.txt' file not found.")
        return None
    except IndexError:
        print("Error: 'proxy.txt' file is improperly formatted.")
        return None

def get_ip_address(proxy=None):
    try:
        if proxy:
            response = requests.get('https://httpbin.org/ip', proxies=proxy, timeout=30)
        else:
            response = requests.get('https://httpbin.org/ip', timeout=30)
        return response.json()['origin']
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Error while fetching IP address: {e}")
        if proxy:
            print("Using direct connection instead of proxy.")
        return None

userAgent = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.2365.92",
]

def verif_kode_referral(invite_code):
    url = "https://referralapi.layeredge.io/api/referral/verify-referral-code"
    proxy = get_proxy()  # Get the proxy
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,id;q=0.8',
        'content-length': '26',
        'content-type': 'application/json',
        'origin': 'https://dashboard.layeredge.io',
        'priority': 'u=1, i',
        'referer': 'https://dashboard.layeredge.io/',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice(userAgent)
    }
    payload = {"invite_code": invite_code}
    response = requests.post(url, headers=headers, json=payload, proxies=proxy)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Received status code {response.status_code}")
        return None

def register_wallet(invite_code, wallet_address):
    url = f"https://referralapi.layeredge.io/api/referral/register-wallet/{invite_code}"
    proxy = get_proxy()  # Get the proxy
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,id;q=0.8',
        'content-length': '62',
        'content-type': 'application/json',
        'origin': 'https://dashboard.layeredge.io',
        'priority': 'u=1, i',
        'referer': 'https://dashboard.layeredge.io/',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice(userAgent)
    }
    payload = {"walletAddress": wallet_address}
    response = requests.post(url, headers=headers, json=payload, proxies=proxy)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Received status code {response.status_code}")
        return None

def node_activation(node_address, private_key, timestamp):
    message = f"Node activation request for {node_address} at {timestamp}"
    encoded_message = encode_defunct(text=message)
    signed_message = Account.sign_message(encoded_message, private_key)
    sign = signed_message.signature.hex()

    url = f"https://referralapi.layeredge.io/api/light-node/node-action/{node_address}/start"
    proxy = get_proxy()
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,id;q=0.8',
        'content-length': '169',
        'content-type': 'application/json',
        'origin': 'https://dashboard.layeredge.io',
        'priority': 'u=1, i',
        'referer': 'https://dashboard.layeredge.io/',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice(userAgent)
    }
    payload = {
        "sign": sign,
        "timestamp": timestamp
    }
    response = requests.post(url, headers=headers, json=payload, proxies=proxy)
    return response.json()

def generate_wallet_eth():
    account = Account.create()
    private_key = account._private_key.hex()
    return account.address, private_key

def main():
    print("""
    ==========================================================
     LayerEdge Auto Referral Bot v0.3 - by @AirdropFamilyIDN
    ==========================================================
    """)

    invite_code = input("Masukkan kode referral: ")
    iterations = int(input("Mau berapa Referral: "))
    use_proxy = input("Apakah ingin menggunakan proxy? (yes/no): ")
    
    while use_proxy.lower() not in ["yes", "no"]:
        print("Invalid input, please enter yes or no")
        use_proxy = input("Apakah ingin menggunakan proxy? (yes/no): ")
    
    if use_proxy.lower() == "yes":
        proxy = get_proxy()
    else:
        proxy = None

    success_count = 0
    failed_count = 0
    max_retries = 3  # Maximum number of retries

    for _ in range(iterations):
        wallet_address, private_key = generate_wallet_eth()
        print(f"\nProgress: {_ + 1}/{iterations}")

        for attempt in range(max_retries):
            try:
                if proxy:
                    ip_address = get_ip_address(proxy)
                    print(f"IP address: {ip_address}")

                print(f"Wallet address: {wallet_address}")
                response = verif_kode_referral(invite_code)

                if response is None or not response.get("data", {}).get("valid", False):
                    print(f"Kode referral tidak valid, {response.get('message', '') if response else 'Server error'}")
                    failed_count += 1
                    break  # Exit the retry loop for this wallet

                print("Kode referral valid")
                register_response = register_wallet(invite_code, wallet_address)

                if register_response and register_response.get("data", {}).get("walletAddress"):
                    print(f"Registered wallet address successfully: {register_response['data']['walletAddress']}")
                    timestamp = int(time.time() * 1000)
                    node_activation_response = node_activation(wallet_address, private_key, timestamp)
                    print(f"Node {wallet_address} activated successfully at {timestamp}")
                    success_count += 1

                    with open("wallets.json", "a") as file:
                        file.write(f"{wallet_address}:{private_key}\n")
                else:
                    raise Exception("Failed to register wallet")

                break  # Exit the retry loop if successful

            except Exception as e:
                print(f"Error: {e}")
                failed_count += 1
                with open("address_eror.txt", "a") as file:
                    file.write(wallet_address + "\n")
                with open("privatekey_eror.txt", "a") as file:
                    file.write(private_key + "\n")

                if attempt < max_retries - 1:
                    print(f"Retrying... (Attempt {attempt + 2}/{max_retries})")
                    time.sleep(5)  # Delay before retrying
                else:
                    print("Max retries reached. Moving to the next wallet.")

        sleeptime = random.randint(10, 13)
        for i in range(sleeptime):
            print(f"Menunggu... {sleeptime - i} detik tersisa", end='\r')
            time.sleep(1)
        print()

    print(f"\nTotal success: {success_count}, Total failed: {failed_count}")

if __name__ == "__main__":
    main()