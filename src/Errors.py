# -*- coding: utf-8 -*-
'''
@Author  : Hatanezumi
@Contact : Hatanezumi@chunshengserver.cn
'''

class AutoLoginException(Exception): pass
class StatusCodeException(AutoLoginException): pass
class HtmlDecodeException(AutoLoginException): pass
class VerifyCodeDetectedException(AutoLoginException): pass