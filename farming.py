import asyncio
import aiohttp
import logging
import random
import time
import aiofiles
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import signal
import pytz
from datetime import datetime
from colorama import Fore, Style

from colorama import init
init()


# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="LayerEdge Farming | [%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Utility Functions
async def delay(seconds):
    await asyncio.sleep(seconds)

async def save_to_file(filename, data):
    try:
        async with aiofiles.open(filename, 'a', encoding='utf-8') as f:
            await f.write(f"{data}\n")
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save data to {filename}: {e}")

async def read_file(pathFile):
    try:
        async with aiofiles.open(pathFile, 'r', encoding='utf-8') as f:
            datas = await f.readlines()
        return [data.strip() for data in datas if data.strip()]
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return []

# Enhanced Request Handler
class RequestHandler:
    @staticmethod
    async def make_request(config, retries=3, backoff_ms=2000):
        async with aiohttp.ClientSession() as session:
            for attempt in range(retries):
                try:
                    # logger.info(f"Making request to {config['url']} with payload: {config.get('json')}")
                    async with session.request(
                        config['method'].upper(), 
                        config['url'], 
                        headers=config.get('headers'),
                        json=config.get('json')
                    ) as response:
                        if response.status == 502:
                            #logger.error(f"Received 502 Bad Gateway. Attempt {attempt + 1}/{retries}. Retrying...")
                            await delay(backoff_ms / 1000)
                            continue  # Retry on 502
                        if response.status == 405:
                            response_text = await response.text()
                            response_data = json.loads(response_text)
                            if response_data.get('message') == "can not claim node points twice in 24 hours, come back after 24 hours!":
                                return None  # Stop retrying on 405
                        if response.status != 200:
                            response_text = await response.text()
                            #logger.error(f"Request failed with status {response.status}")
                            return None
                        response_data = await response.json()
                        return response_data
                except Exception as e:
                    #logger.error(f"Request failed: {e}")
                    await delay(backoff_ms / 1000)
        return None

# LayerEdgeConnection Class
class LayerEdgeConnection:
    def __init__(self, private_key):
        self.wallet = Account.from_key(private_key)

    async def make_request(self, method, url, config={}):
        final_config = {
            'method': method,
            'url': url,
            'headers': {
                'accept': 'application/json, text/plain, */*',
                'content-type': 'application/json',
                'origin': 'https://dashboard.layeredge.io',
                'referer': 'https://dashboard.layeredge.io/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            },
            **config
        }
        return await RequestHandler.make_request(final_config)

    async def connect_node(self):
        if await self.is_node_running():
            logger.info(f"{Fore.GREEN}Node already running: {self.wallet.address}{Style.RESET_ALL}")
            return True

        for attempt in range(3):
            timestamp = int(time.time())
            message = encode_defunct(text=f"Node activation request for {self.wallet.address} at {timestamp}")
            sign = Account.sign_message(message, self.wallet.key).signature.hex()

            response = await self.make_request(
                "POST",
                f"https://referralapi.layeredge.io/api/light-node/node-action/{self.wallet.address}/start",
                {'json': {'sign': sign, 'timestamp': timestamp}}
            )

            if response and response.get("statusCode") == 200 and response.get("message") == "node action executed successfully" and response.get("data", {}).get("startTimestamp"):
                logger.info(f"{Fore.GREEN}Connected Node Successfully: {self.wallet.address}{Style.RESET_ALL}")
                return True
            else:
                logger.info(f"{Fore.RED}Failed to connect Node: {self.wallet.address}{Style.RESET_ALL}")
                await asyncio.sleep(10)
        return False

    async def is_node_running(self):
        response = await self.make_request(
            "GET",
            f"https://referralapi.layeredge.io/api/light-node/node-status/{self.wallet.address}"
        )
        if response and response.get("data", {}).get("startTimestamp"):
            return True
        return False

    async def stop_node(self):
        if not await self.is_node_running():
            logger.info(f"{Fore.GREEN}Node is not running, no need to stop: {self.wallet.address}{Style.RESET_ALL}")
            return False
        
        for attempt in range(3):
            timestamp = int(time.time())
            message = encode_defunct(text=f"Node deactivation request for {self.wallet.address} at {timestamp}")
            sign = Account.sign_message(message, self.wallet.key).signature.hex()
            
            response = await self.make_request(
                "POST",
                f"https://referralapi.layeredge.io/api/light-node/node-action/{self.wallet.address}/stop",
                {'json': {'sign': sign, 'timestamp': timestamp}}
            )
            
            if response and response.get("message") == "node action executed successfully":
                logger.info(f"{Fore.GREEN}Node stopped successfully: {self.wallet.address}{Style.RESET_ALL}")
                return True
            logger.info(f"{Fore.RED}Failed to stop node, retrying: {self.wallet.address}{Style.RESET_ALL}")
            await asyncio.sleep(10)
        logger.error(f"{Fore.RED}Failed to stop node: {self.wallet.address}{Style.RESET_ALL}")
        return False

    async def check_node_points(self, retries=3, backoff_ms=2000):
        for attempt in range(retries):
            response = await self.make_request(
                "GET",
                f"https://referralapi.layeredge.io/api/referral/wallet-details/{self.wallet.address}"
            )
            
            if response:
                points = response.get("data", {}).get("nodePoints", 0)
                logger.info(f"{Fore.GREEN}Total Points for {self.wallet.address}: {points}{Style.RESET_ALL}")
                return points
            logger.info(f"{Fore.RED}Failed to retrieve node points, retrying: {self.wallet.address}{Style.RESET_ALL}")
            await asyncio.sleep(backoff_ms / 1000)
        logger.error(f"{Fore.RED}Failed to retrieve node points: {self.wallet.address}{Style.RESET_ALL}")
        return 0

    async def claim_daily(self, retries=3, backoff_ms=2000):
        if not await self.is_node_running():
            logger.info(f"{Fore.GREEN}Node is not running, no need to claim daily points: {self.wallet.address}{Style.RESET_ALL}")
            return False
        
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        timestamp = int(datetime.now(jakarta_tz).timestamp() * 1000)  # Current time in milliseconds
        message = encode_defunct(text=f"I am claiming my daily node point for {self.wallet.address} at {timestamp}")
        sign = Account.sign_message(message, self.wallet.key).signature.hex()
        
        payload = {
            "walletAddress": self.wallet.address,
            "timestamp": timestamp,
            "sign": sign
        }

        has_logged = False  # Flag to track logging

        for attempt in range(retries):
            try:
                response = await self.make_request(
                    "POST",
                    "https://referralapi.layeredge.io/api/light-node/claim-node-points",
                    {'json': payload}
                )

                if response and response.get("statusCode") == 200 and response.get("message") == "node points claimed successfully":
                    logger.info(f"{Fore.GREEN}Daily points claimed successfully for: {self.wallet.address}{Style.RESET_ALL}")
                    return True
                elif response and response.get("statusCode") == 405 and response.get("message") == "can not claim node points twice in 24 hours, come back after 24 hours!":
                    if not has_logged:  # Check if the message has already been logged
                        logger.error(f"{Fore.RED}Cannot claim node points twice in 24 hours for: {self.wallet.address}{Style.RESET_ALL}")
                        has_logged = True  # Set the flag to True
                    return False
            except Exception as e:
                logger.error(f"Error claiming daily points for {self.wallet.address}: {e}")
                await asyncio.sleep(backoff_ms / 1000)  # Wait before retrying

        return False

# Main Script
async def main():
    try:
        while True:
            wallets = await read_file("wallets.json")
            logger.info(f"Total wallets: {len(wallets)}")
            if not wallets:
                logger.warn("No wallets found. Waiting...")
                continue
            
            tasks = []  # Collect all tasks for all wallets
            total_points = 0  # Track the total points of all wallets
            for wallet_data in wallets:
                try:
                    address, private_key = wallet_data.split(":")
                    connection = LayerEdgeConnection(private_key)
                    logger.info(f"Processing wallet {address}")
                    
                    # Collect tasks for each wallet
                    tasks.append(asyncio.create_task(connection.connect_node()))
                    tasks.append(asyncio.create_task(connection.stop_node()))
                    tasks.append(asyncio.create_task(connection.check_node_points()))
                    tasks.append(asyncio.create_task(connection.claim_daily()))
                    
                    # Get the total points of this wallet
                    points = await connection.check_node_points()
                    total_points += points
                    
                except Exception as e:
                    logger.error(f"Error processing wallet: {wallet_data} - {e}")

            # Execute all tasks for all wallets concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

            # Log the total points of all wallets
            logger.info(f"Total points of all wallets: {total_points}")

            # Add a delay after processing all wallets
            sleep_time = random.randint(600, 1200)
            logger.info(f"All wallets processed. Sleeping for {sleep_time // 60:.1f} minutes...")
            await asyncio.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Terminated by user.")
    except Exception as e:
        logger.error(f"An error occurred in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
