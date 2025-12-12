
from web3 import Web3
import time
import re
from colorama import init, Fore, Style

init(autoreset=True)


RPC_URL = "https://atlantic.dplabs-internal.com"
EXPLORER = "https://atlantic.pharosscan.xyz/tx/0x"

print(f"{Fore.CYAN}{'='*95}")
print(f"{Fore.WHITE}     BITVERSE ATLANTIC – LP + SWAP BOT ")
print(f"{Fore.CYAN}{'='*95}")


def load_proxies():
    try:
        with open("proxy.txt") as f:
            return [l.strip() for l in f if l.strip() and ":" in l]
    except:
        return []

proxies = load_proxies()
use_proxy = input(f"{Fore.CYAN}Use proxy? (1=Yes / 2=No) → {Fore.WHITE}").strip() in ["1", "y", "Y", "yes"]

current_proxy = None

def get_web3():
    global current_proxy
    if not use_proxy:
        return Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 40}))

    if current_proxy:
        try:
            w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={
                "timeout": 30,
                "proxies": {"http": f"http://{current_proxy}", "https": f"http://{current_proxy}"}
            }))
            w3.eth.block_number
            return w3
        except: pass

    import random
    random.shuffle(proxies)
    for p in proxies:
        try:
            w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={
                "timeout": 30,
                "proxies": {"http": f"http://{p}", "https": f"http://{p}"}
            }))
            w3.eth.block_number
            current_proxy = p
            print(f"{Fore.GREEN}Proxy locked → {p.split('@')[-1]}")
            return w3
        except: continue

    print(f"{Fore.YELLOW}All proxies failed → using direct")
    current_proxy = None
    return Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 40}))


keys = []
with open("accounts.txt") as f:
    for line in f:
        k = line.strip()
        if not k: continue
        k = re.sub(r'[^0-9a-fA-Fx]', '', k.lower())
        if len(k) == 64: k = "0x" + k
        if len(k) == 66: keys.append(k)

lp_hashes = []
try:
    with open("lp_hash.txt") as f:
        for line in f:
            h = line.strip()
            if not h: continue
            h = re.sub(r'[^0-9a-fA-Fx]', '', h.lower())
            if len(h) == 64: h = "0x" + h
            if len(h) == 66: lp_hashes.append(h)
except: pass

swap_hashes = []
try:
    with open("swap_hash.txt") as f:
        for line in f:
            h = line.strip()
            if not h: continue
            h = re.sub(r'[^0-9a-fA-Fx]', '', h.lower())
            if len(h) == 64: h = "0x" + h
            if len(h) == 66: swap_hashes.append(h)
except: pass

if not keys:
    print(f"{Fore.RED}No private keys!")
    exit()


def ultimate_replay(private_key, tx_hash, action_name, repeat_times):
    global current_proxy
    success = 0
    addr = Web3().eth.account.from_key(private_key).address
    short = f"{addr[:10]}...{addr[-8:]}"
    print(f"{Fore.MAGENTA}{action_name} → {short}")

    
    original_tx = None
    for _ in range(15):
        try:
            w3 = get_web3()
            original_tx = w3.eth.get_transaction(tx_hash)
            print(f"{Fore.GREEN}Fetched original calldata")
            break
        except Exception as e:
            print(f"{Fore.RED}Fetch failed – retrying...")
            time.sleep(6)
            current_proxy = None

    if not original_tx:
        print(f"{Fore.RED}Skipping – cannot fetch calldata")
        current_proxy = None
        return 0

    calldata = original_tx.input.hex()
    to_addr = original_tx['to']
    gas = original_tx['gas']
    value = original_tx['value']

    
    is_eip1559 = 'maxFeePerGas' in original_tx and original_tx['maxFeePerGas'] is not None
    access_list = original_tx.get('accessList', [])

    print(f"{Fore.CYAN}   Target : {to_addr}")
    print(f"{Fore.CYAN}   Length : {len(calldata)-2} chars")
    print(f"{Fore.CYAN}   Gas    : {gas}")
    print(f"{Fore.CYAN}   Type   : {'EIP-1559' if is_eip1559 else 'Legacy'}")

    for i in range(1, repeat_times + 1):
        print(f"{Fore.MAGENTA}   {action_name} #{i:02d}/{repeat_times}", end=" ")
        for _ in range(12):
            try:
                w3 = get_web3()
                nonce = w3.eth.get_transaction_count(addr, 'pending')

                if is_eip1559:
                    tx = {
                        "chainId": w3.eth.chain_id,
                        "nonce": nonce,
                        "to": to_addr,
                        "data": calldata,
                        "value": value,
                        "gas": gas,
                        "maxFeePerGas": original_tx['maxFeePerGas'],
                        "maxPriorityFeePerGas": original_tx['maxPriorityFeePerGas'],
                        "accessList": access_list,
                    }
                else:
                    tx = {
                        "chainId": w3.eth.chain_id,
                        "nonce": nonce,
                        "to": to_addr,
                        "data": calldata,
                        "value": value,
                        "gas": gas,
                        "gasPrice": original_tx['gasPrice'],
                    }

                signed = w3.eth.account.sign_transaction(tx, private_key)
                tx_sent = w3.eth.send_raw_transaction(signed.raw_transaction)

                link = EXPLORER + tx_sent.hex()
                print(f"{Fore.CYAN}→ {link}")

                receipt = w3.eth.wait_for_transaction_receipt(tx_sent, timeout=120)
                if receipt.status == 1:
                    print(f"{Fore.GREEN}SUCCESS")
                    success += 1
                    break
                else:
                    print(f"{Fore.RED}REVERT")
            except Exception as e:
                if any(x in str(e).lower() for x in ["nonce too low", "already known", "replacement"]):
                    time.sleep(3)
                    continue
                print(f"{Fore.RED}ERR", end=" ")
            time.sleep(3)
        time.sleep(4)

    print(f"{Fore.MAGENTA}   {action_name} Result: {success}/{repeat_times} successful")
    return success


print(f"{Fore.GREEN}Wallets     : {len(keys)}")
print(f"{Fore.CYAN}LP Hashes   : {len(lp_hashes)}")
print(f"{Fore.YELLOW}Swap Hashes : {len(swap_hashes)}")

while True:
    mode = input(f"{Fore.CYAN}Mode (1=LP / 2=Swap / 3=Both) → {Fore.WHITE}").strip()
    if mode in "123": break

if mode == "1":
    lp_times = int(input(f"{Fore.CYAN}LP Add times per wallet → {Fore.WHITE}") or "1")
    swap_times = 0
elif mode == "2":
    lp_times = 0
    swap_times = int(input(f"{Fore.CYAN}Swap times per wallet → {Fore.WHITE}") or "1")
else:
    lp_times = int(input(f"{Fore.CYAN}LP Add times per wallet → {Fore.WHITE}") or "1")
    swap_times = int(input(f"{Fore.CYAN}Swap times per wallet → {Fore.WHITE}") or "1")

total_success = 0

for idx, pk in enumerate(keys, 1):
    current_proxy = None
    addr = Web3().eth.account.from_key(pk).address
    print(f"\n{Fore.WHITE}[{idx}/{len(keys)}] {addr[:12]}...{addr[-10:]}")

    if mode in "13" and idx <= len(lp_hashes) and lp_times > 0:
        total_success += ultimate_replay(pk, lp_hashes[idx-1], "LP Add", lp_times)
        if mode == "3" and swap_times > 0:
            time.sleep(5)

    if mode in "23" and idx <= len(swap_hashes) and swap_times > 0:
        total_success += ultimate_replay(pk, swap_hashes[idx-1], "Swap", swap_times)

    if idx < len(keys):
        time.sleep(5)

print(f"\n{Fore.CYAN}{'='*95}")
print(f"{Fore.GREEN}ALL COMPLETED! Total successful: {total_success}")
print(f"{Fore.CYAN}{'='*95}")
