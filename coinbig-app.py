# !-*-coding:utf-8 -*-
# @TIME    : 2018/7/13/0011 15:32
# @Author  : Lich

import math, random
import time, os, sys
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread

from coinbig import CoinBig
import config
import traceback

class coinbig_app():

    def __init__(self):

        self.cb = CoinBig()
        self.cb.auth(config.key, config.secret)

        self._init_log()

    # 日志初始化
    def _init_log(self):
        self._log = logging.getLogger(__name__)
        self._log.setLevel(level=logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(filename)s %(funcName)s %(lineno)s "
                                      "%(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")  # 格式

        '''
        保存文档
        '''

        my_handler = RotatingFileHandler("app.log", mode='a', maxBytes=5 * 1024 * 1024,
                                         backupCount=2, encoding=None, delay=0)
        my_handler.setFormatter(formatter)
        my_handler.setLevel(logging.INFO)
        self._log.addHandler(my_handler)

    # 精度控制，直接抹除多余位数，非四舍五入
    def digits(self, num, digit):
        site = pow(10, digit)
        tmp = num * site
        tmp = math.floor(tmp) / site
        return tmp

    # 获取当前价格, 平价买卖
    def get_ticket1(self):
        while True:
            try:
                success, data = self.cb.get_ticker(config.symbol["name"])
                if success:
                    code = data["code"]
                    if code == 0:
                        ticker = data["data"]["ticker"]
                        #buy = float(ticker["buy"])
                        #sell = float(ticker["sell"])
                        #price = (buy + sell)/2.0
                        price = float(ticker["last"])
                        return self.digits(price, config.symbol['price_precision'])
                    else:
                        self._log.error('获取当前价格错误, code: {0}'.format(code))
            except Exception, e:
                self._log.error('获取当前价格错误')
            time.sleep(1)

    # 创建订单
    def creat_order(self, symbol, trade_type, price, amount):
        while True:
            try:
                success, data = self.cb.trade(symbol, trade_type, price, amount)
                if success:
                    code = data["code"]
                    if code == 0:
                        order_id = data["data"]["order_id"]
                        self._log.info('创建订单 {0} [{1},{2},{3}]'.format(order_id, trade_type, price, amount))
                        return order_id
                    elif code == -2:
                        self._log.error('余额不足, code: {0}, {1} {2} {3}'.format(code, trade_type, price, amount))
                        self._log.error("%s" % data["msg"].encode("utf-8"))
                        return -2
                    else:
                        self._log.error('创建订单失败, code: {0}, {1} {2} {3}'.format(code, trade_type, price, amount))
                        self._log.error("%s"%data["msg"].encode("utf-8"))
                        return code
            except Exception, e:
                self._log.error('创建订单失败')
            time.sleep(3)

    # 撤销订单
    def cancel_order(self, order_id):
        while True:
            try:
                success, data = self.cb.cancel_order(order_id)
                if success:
                    code = data["code"]
                    if code == 0:
                        self._log.info('撤销订单 {0}'.format(order_id))
                        break
                    else:
                        self._log.error('撤单失败, code: {0}'.format(code))
                        self._log.error("%s" % data["msg"].encode("utf-8"))
            except Exception, e:
                self._log.error('撤单失败 {0}'.format(order_id))
            time.sleep(1)

    # 循环判断订单完成
    def order_state(self, order_id):
        count = 0
        while True:
            try:
                success, data = self.cb.get_order_info(order_id)
                if success:
                    code = data["code"]
                    if code == 0:
                        status = data["data"]["orderinfo"]["status"]
                        if status == 3:
                            return 0
                        elif status == 2 or status == 1:
                            if count >= 15:
                                self.cancel_order(order_id)
                                left_amount = data["data"]["orderinfo"]["leftCount"]
                                return left_amount
                        else:
                            self._log.error('订单其它状态 {0}, status: {1}'.format(order_id, status))
                    else:
                        self._log.error('查询订单状态失败 {0}, code: {1}'.format(order_id, code))
                        self._log.error("%s" % data["msg"].encode("utf-8"))
            except Exception, e:
                self._log.error('查询订单状态失败 {0}'.format(order_id))

            count = count + 1
            time.sleep(1)

    def testbuy(self):
        left_amount = random.uniform(config.min_amount, config.max_amount)
        while left_amount >= config.symbol["min_amount"]:
            left_amount = self.digits(left_amount, config.symbol['amount_precision'])
            price = self.get_ticket1()
            order_id = self.creat_order(config.symbol["name"], "buy", price, left_amount)
            if order_id < 0:
                break
            left_amount = self.order_state(order_id)

    def testsell(self):
        left_amount = random.uniform(config.min_amount, config.max_amount)
        while left_amount >= config.symbol["min_amount"]:
            left_amount = self.digits(left_amount, config.symbol['amount_precision'])
            price = self.get_ticket1()
            order_id = self.creat_order(config.symbol["name"], "sell", price, left_amount)
            if order_id < 0:
                break
            left_amount = self.order_state(order_id)

    # 刷单流程
    def process(self):
        self.testbuy()
        time.sleep(3)
        self.testsell()
        time.sleep(3)

    # 循环
    def loop(self):
        while True:
            try:
                self.process()
            except Exception, e:
                self._log.error('未知错误')
                self._log.error('%s'%traceback.format_exc())

#fork后台运行进程
def createDaemon():
    # fork进程
    try:
        if os.fork() > 0:
            os._exit(0)
    except OSError, error:
        print 'fork #1 failed: %d (%s)' % (error.errno, error.strerror)
        os._exit(1)

    #os.chdir('/')
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            #print 'Daemon PID %d' % pid
            with open("coinbig-app.pid", 'w') as f:
                f.write("{0}\n".format(pid))
            os._exit(0)
    except OSError, error:
        print 'fork #2 failed: %d (%s)' % (error.errno, error.strerror)
        os._exit(0)

    # 重定向标准IO
    sys.stdout.flush()
    sys.stderr.flush()
    si = file("/dev/null", 'r')
    so = file("/dev/null", 'a+')
    se = file("/dev/null", 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # 在子进程中执行代码
    run = coinbig_app()
    thread = Thread(target=run.loop)
    thread.start()
    thread.join()

if __name__ == '__main__':

    print('Start coinbig-miner-app!')

    # 执行函数createDaemon
    createDaemon()

    print('Done')


