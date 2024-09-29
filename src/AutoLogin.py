# -*- coding: utf-8 -*-
'''
@Author  : Hatanezumi
@Contact : Hatanezumi@chunshengserver.cn
'''
import requests
from . import Errors
from .Color import Color
from bs4 import BeautifulSoup, ResultSet, element

HEADER = {
    'sec-ch-ua':'"Chromium";v="94", "Microsoft Edge";v="94", ";Not A Brand";v="99"',
    'sec-ch-ua-mobile':'?0',
    'sec-ch-ua-platform':'"Windows"',
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.50'
}

BASEPAGE = 'http://1.1.1.1'

class LoginStatus:
    LOGINFAILED = '登录失败'
    LOGINSUCCESS = '登录成功'
    LOGINPROBABLE = '登录可能成功'

class AutoLogin:
    def __init__(self, user: str, password: str = '112233', print_info: bool = True) -> None:
        self.user = user
        self.password = password
        self.print_info = True
    def __print(self, text: str, color: Color = Color.DEFAULT) -> None:
        if self.print_info:
            print(f'\033[0;{color}m{text}\033[0m')
    def __get_page(self, link: str) -> requests.Response:
        res = requests.get(link, headers=HEADER)
        if res.status_code != 200:
            raise Errors.StatusCodeException(res.status_code)
        return res
    def __get_soup(self, link: str) -> BeautifulSoup:
        return BeautifulSoup(self.__get_page(link).text, 'html.parser')
    def __get_login_page_link(self) -> str:
        soup = self.__get_soup(BASEPAGE)
        frame = soup.find('frame')
        if not frame:
            raise Errors.HtmlDecodeException('未在页面中找到frame标签')
        link = frame.get('src')
        if not link:
            raise Errors.HtmlDecodeException('未在frame中找到链接')
        return link
    def __analyze_post(self, page: str, attrs: dict) -> tuple[str, dict[str, str]]:
        soup = BeautifulSoup(page, 'html.parser')
        verifyCodeTR = soup.find('tr', attrs={'id':'verifyCodeTR'})
        if verifyCodeTR:
            raise Errors.VerifyCodeDetectedException('检测到验证码')
        form = soup.find('form', attrs=attrs)
        if not form:
            raise Errors.HtmlDecodeException(f'未在页面中找到{attrs}')
        post_link = form.get('action')
        if not post_link:
            raise Errors.HtmlDecodeException('未在loginForm中找到链接')
        inputs: ResultSet[element.Tag] = soup.find_all('input')
        data = {}
        for tag in inputs:
            if tag.get('type') != 'hidden':
                continue
            name = tag.get('name')
            if not name:
                continue
            value = tag.get('value')
            if not value:
                value = ''
            data[name] = value
        return (post_link, data)
    def __analyze_login_page(self, login_link: str) -> tuple[str, dict[str, str]]:
        '''分析登录页面,返回post地址与参数'''
        return self.__analyze_post(self.__get_page(login_link).text, {'id':'loginForm'})
    def __analyze_post_page(self, page: str) -> tuple[str, dict[str, str]]:
        return self.__analyze_post(page, {'name':'submitForm'})
    def __post_login(self, post_link: str, data: dict[str, str]) -> tuple[LoginStatus, str|None]:
        data['userName'] = self.user
        data['userPwd'] = self.password
        res = requests.post(post_link, headers=HEADER, data=data)
        if res.status_code != 200:
            raise Errors.StatusCodeException(res.status_code)
        try:
            info = res.text.split('$("#info").text("',1)[1].split('");',1)[0]
            self.__print(info, Color.YELLOW)
            if info == '系统正忙，请稍候重试':
                self.__print('可能已成功登录,请自行验证', Color.YELLOW)
                return (LoginStatus.LOGINPROBABLE, None)
        except:
            return (LoginStatus.LOGINSUCCESS, res.text)
        return (LoginStatus.LOGINFAILED, None)
    def __post_login_redirect(self, post_link: str, data: dict[str, str]) -> LoginStatus:
        res = requests.post(post_link, headers=HEADER, data=data)
        if res.status_code != 200:
            raise Errors.StatusCodeException(res.status_code)
        return LoginStatus.LOGINSUCCESS if '已登录' in res.text else LoginStatus.LOGINFAILED
    def auto_login(self) -> LoginStatus:
        try:
            login_link = self.__get_login_page_link()
            self.__print(f'login_link获取成功:{login_link}', Color.GREEN)
            post_link, data = self.__analyze_login_page(login_link)
            self.__print(f'post_link及数据获取成功:{post_link}', Color.GREEN)
            login_type, page = self.__post_login(post_link, data)
            if login_type != LoginStatus.LOGINSUCCESS:
                return login_type
            self.__print('Post登录成功,查询结果', Color.GREEN)
            post_link, data = self.__analyze_post_page(page)
            self.__print(f'查询地址及数据获取成功:{post_link}', Color.GREEN)
            return self.__post_login_redirect(post_link, data)
        except Errors.AutoLoginException as err:
            self.__print(err, Color.RED)
            return LoginStatus.LOGINFAILED
        except:
            raise