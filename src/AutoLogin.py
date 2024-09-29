# -*- coding: utf-8 -*-
'''
@Author  : Hatanezumi
@Contact : Hatanezumi@chunshengserver.cn
'''
import requests
from .Errors import *
from .Color import *
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

    LOGOUTFAILED = '登出失败'
    LOGOUTSUCCESS = '登出成功'

class AutoLogin:
    def __init__(self, user: str, password: str = '112233', print_info: bool = True, force_login: bool = False) -> None:
        self.user = user
        self.password = password
        self.print_info = print_info
        self.force_login = force_login
        self.data = {}
    def __print(self, text: str, text_color: Color = Color.DEFAULT, background_color: BackGroundColor = BackGroundColor.DEFAULT, style: Style = Style.DEFAULT) -> None:
        if self.print_info:
            color_print(text=text, text_color=text_color, background_color=background_color, style=style)
    def __get_page(self, link: str) -> requests.Response:
        res = requests.get(link, headers=HEADER)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res
    def __get_soup(self, link: str) -> BeautifulSoup:
        return BeautifulSoup(self.__get_page(link).text, 'html.parser')
    def __get_login_page_link(self) -> str:
        soup = self.__get_soup(BASEPAGE)
        frame = soup.find('frame')
        if not frame:
            raise HtmlDecodeException('未在页面中找到frame标签')
        link = frame.get('src')
        if not link:
            raise HtmlDecodeException('未在frame中找到链接')
        return link
    def __analyze_post(self, page: str, attrs: dict) -> tuple[str, dict[str, str]]:
        soup = BeautifulSoup(page, 'html.parser')
        verifyCodeTR = soup.find('tr', attrs={'id':'verifyCodeTR'})
        if verifyCodeTR:
            raise VerifyCodeDetectedException('检测到验证码')
        form = soup.find('form', attrs=attrs)
        if not form:
            raise HtmlDecodeException(f'未在页面中找到{attrs}')
        post_link = form.get('action')
        if not post_link:
            raise HtmlDecodeException('未在loginForm中找到链接')
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
        return self.__analyze_post(self.__get_page(login_link).text, {'id':'loginForm'})
    def __analyze_post_page(self, page: str) -> tuple[str, dict[str, str]]:
        return self.__analyze_post(page, {'name':'submitForm'})
    def __get_info(self, page: str) -> str:
        return page.split('$("#info").text("',1)[1].split('");',1)[0]
    def __post_login(self, post_link: str) -> tuple[LoginStatus, str|None]:
        self.data['userName'] = self.user
        self.data['userPwd'] = self.password
        if self.force_login:
            self.__print('您正在使用强制登录模式,可能会导致已上线的用户强制下线', Color.YELLOW, style=Style.BOLD)
            post_link = post_link.replace('portalLogin', 'portalForceLogin')
        res = requests.post(post_link, headers=HEADER, data=self.data)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        try:
            info = self.__get_info(res.text)
            self.__print(info, Color.YELLOW)
            if info == '系统正忙，请稍候重试':
                self.__print('可能已成功登录,请自行验证', Color.YELLOW)
                return (LoginStatus.LOGINPROBABLE, None)
        except:
            return (LoginStatus.LOGINSUCCESS, res.text)
        return (LoginStatus.LOGINFAILED, None)
    def __post_login_redirect(self, post_link: str) -> LoginStatus:
        res = requests.post(post_link, headers=HEADER, data=self.data)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        if '已登录' in res.text:
            try:
                self.data['logout_link'] = res.text.split('''$('#formLogout').attr("action", "''', 1)[1].split('&isCloseWindow=N");', 1)[0]
            except:
                pass
            finally:
                return LoginStatus.LOGINSUCCESS
        else:
            return LoginStatus.LOGINFAILED
    def auto_logout(self) -> LoginStatus:
        if 'logout_link' not in self.data.keys():
            raise NotLoginException('未找到logout的链接数据,可能您未登录')
        res = requests.post(self.data['logout_link'], headers=HEADER, data=self.data)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        info = self.__get_info(res.text)
        if info == '下线成功！':
            return LoginStatus.LOGOUTSUCCESS
        else:
            self.__print(info, Color.RED, style=Style.BOLD)
            return LoginStatus.LOGOUTFAILED
    def auto_login(self) -> LoginStatus:
        try:
            login_link = self.__get_login_page_link()
            self.__print(f'login_link获取成功:{login_link}', Color.GREEN)
            post_link, self.data = self.__analyze_login_page(login_link)
            self.__print(f'post_link及数据获取成功:{post_link}', Color.GREEN)
            login_type, page = self.__post_login(post_link)
            if login_type != LoginStatus.LOGINSUCCESS:
                return login_type
            self.__print('Post登录成功,查询结果', Color.GREEN)
            post_link, self.data = self.__analyze_post_page(page)
            self.__print(f'查询地址及数据获取成功:{post_link}', Color.GREEN)
            return self.__post_login_redirect(post_link)
        except AutoLoginException as err:
            self.__print(err, Color.RED)
            return LoginStatus.LOGINFAILED
        except:
            raise