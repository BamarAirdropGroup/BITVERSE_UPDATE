# BITVERSE_UPDATE
BITVERSE SWAP AND LIQUIDITY ADD UPDATE BOT 



#PRE-REQUIREMENTS

 - 1 TX HASH (LP ADD) AND 1 TX HASH FOR EACH WALLET (PRIVATE KEY)



# Clone the repo

 git clone https://github.com/BamarAirdropGroup/BITVERSE_UPDATE.git && cd BITVERSE_UPDATE && pip install -r requirements.txt



# Add private key per line in accounts.txt 

 nano accounts.txt


# Add swap tx hash (per line)

 nano swap_hash.txt



# Add LP Add tx hash ( per line )

 nano lp_hash.txt



# Add proxy if you wish

 nano proxy.txt



# Running 


 python bot.py



# Important Note

 ထည့် သော private key နဲ့ tx hash တို့ သည် သက်ဆိုင် ရာ wallet အတိုင်း အစဥ် လိုက်ဖြစ်ရပါမယ်။ ဥပမာ wallet 5 ခု run ရင် accounts.txt ထဲ private key 5 ခု, swap_hash.txt ထဲ hash 5 ခု , lp_hash.txt ထဲ hash 5 ခု  အသီးသီး ရှိ ရပါမယ် ။ 
