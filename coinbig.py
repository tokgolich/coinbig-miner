# -*- coding: utf-8 -*-
import time
import hashlib
import requests
import copy

class CoinBig():
    def __init__(self):
        self.base_url = 'https://www.coinbig.com/api/publics/v1'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

    def auth(self, key, secret):
        self.apiKey = key
        self.secret = secret

    def sign(self, params):
        params["time"] = int(round(time.time() * 1000))
        params["apikey"] = self.apiKey
        _params = copy.copy(params)
        keys = sorted(_params.keys())
        string = ""
        for k in keys:
            string += '&' + str(k) + '=' + str(_params[k])
        string = string.lstrip('&')
        string += '&secret_key=' + self.secret
        _sign = hashlib.md5(bytes(string.encode('utf-8'))).hexdigest().upper()
        params['sign'] = _sign
        return params

    def public_request(self, method, api_url, **payload):
        """request public url"""
        r_url = self.base_url + api_url
        try:
            if method == 'POST':
                r = requests.request(method, r_url, json=payload, headers=self.headers)
            else:
                r = requests.request(method, r_url, params=payload, headers=self.headers)
            r.raise_for_status()
            if r.status_code == 200:
                return True, r.json()
            else:
                return False, {'error': 'E10000', 'data': r.status_code}
        except requests.exceptions.HTTPError as err:
            return False, {'error': 'E10001', 'data': r.text}
        except Exception as err:
            return False, {'error': 'E10002', 'data': err}

    def signed_request(self, method, api_url, data={}):
        url = self.base_url + api_url
        new_data = copy.copy(data)
        try:
            r = requests.request(method, url, data=self.sign(new_data), headers = self.headers)
            r.raise_for_status()
            if r.status_code == 200:
                return True, r.json()
            else:
                return False, {'error': 'E10000', 'data': r.status_code}
        except requests.exceptions.HTTPError as err:
            return False, {'error': 'E10001', 'data': r.text}
        except Exception as err:
            return False, {'error': 'E10002', 'data': err}

    # 获取各个币对的精度及其他信息
    def list_symbol_precision(self):
        return self.public_request('GET', '/listSymbolPrecision')

    # 获取行情 1次/1秒
    def get_ticker(self, symbol):
        return self.public_request('GET', '/ticker', symbol = symbol)

    # 获取用户资产(币种) 1次/1秒
    def get_userinfoBySymbol(self, symbol):
        params = {
            'shortName': symbol
        }
        return self.signed_request('POST', '/userinfoBySymbol', params)

    # 用户资产信息 	1次/1秒
    def get_userinfo(self):
        return self.signed_request('POST', '/userinfo')

    # 查询订单状况	 1次/1秒, 1未成交,2部分成交,3完全成交,4用户撤销,5部分撤回,6成交失败
    def get_order_info(self, order_id):
        params = {
            'order_id': order_id
        }
        return self.signed_request('POST', '/order_info', params)

    # 撤销订单 1次/1秒
    def cancel_order(self, order_id):
        params = {
            'order_id': order_id
        }
        return self.signed_request('POST', '/cancel_order', params)

    # 买卖类型: 限价单(buy/sell) 市价单(buy_market/sell_market) 1次/3秒
    def trade(self, symbol, trade_type, price, amount):
        params = {
            'type': trade_type,
            'price': price,
            'amount': amount,
            'symbol': symbol
        }
        return self.signed_request('POST', '/trade', params)

