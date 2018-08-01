#coding:utf-8

key = ""
secret = ""

#精度和最小挂单量
btc = {'name': 'btc_usdt', 'coin': 'btc', 'price_precision': 4, 'amount_precision': 4, 'min_amount': 0.03}
eth = {'name': 'eth_usdt', 'coin': 'eth', 'price_precision': 4, 'amount_precision': 4, 'min_amount': 0.03}

symbol = eth         #交易对

amount  = 0.04        # 每次购买数量
min_amount  = 0.035        # 每次购买最小数量
max_amount = 0.045          # 每次购买最大数量

order_sleep = 10    #订单处理等待时间s

trading_strategy = 2


