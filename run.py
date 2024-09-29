# -*- coding: utf-8 -*-
'''
@Author  : Hatanezumi
@Contact : Hatanezumi@chunshengserver.cn
'''
import sys
import requests
from src.AutoLogin import AutoLogin, LoginStatus

def net_test() -> bool: # 这个东西不稳定,看看就好
    try:
        print('正在进行联网测试')
        res = requests.get('http://baidu.com', timeout=3)
        if res.status_code != 200:
            return False
        return 'baidu' in res.text
    except:
        return False

logout = False # 是否演示自动下线

print('吉林移动校园网自动登录脚本')
if net_test():
    print('警告:您目前已连接到网络,会导致脚本失效,请手动下线终端!')
    sys.exit(0)

user = input('请输入用户名:')
al = AutoLogin(user, force_login=True)
res = al.auto_login()
if res == LoginStatus.LOGINPROBABLE:
    res = LoginStatus.LOGINSUCCESS if net_test() else LoginStatus.LOGINFAILED
print(res)
if res == LoginStatus.LOGINSUCCESS and logout:
    print('自动下线中')
    print(al.auto_logout())