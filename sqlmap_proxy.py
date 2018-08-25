# sqlmap -u http://www.baiyifangzhi.org/newshow.asp?id=140 --proxy=http://127.0.0.1:9999
import socket
from socket import error
import threading
import random
import time
import requests
import gevent
import re
from gevent import monkey;monkey.patch_all()

def reuse():#使用该函数更新 already列表数
    already = []
    res = requests.get('https://1aker.cn/open/proxies.html').text.strip('\r\n').split('<br>')
    for i in res:
        try:
            already.append(eval(i))
        except:
            pass
    if already == []:
        time.sleep(5)
        already = reuse()
    return already

class ProxyServerTest():
    def __init__(self):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)#本地socket服务
        self.ip_list = reuse()
        self.data = b''
        self.data_recv = b''
        self.success = False
    def change_iplist(self):
        while True:
            new = reuse()
            time.sleep(10)
        self.ip_list = new
        return
    def gettime(self):
        return '[' + time.asctime(time.localtime(time.time()))[11:19] + ']'

    def reuse(self):  # 使用该函数更新 already列表数据
        already = []
        res = requests.get('https://1aker.cn/open/proxies.html').text.strip('\r\n').split('<br>')
        for i in res:
            try:
                already.append(eval(i))
            except:
                pass
        return already
    def sqlmap_recv(self):
        try:#接收sqlmap数据
            data = self.sqlmap_client.recv(2048)
            if not data:
                exit()
            self.data += data
            print(self.gettime() + 'Receving from sqlmap:', self.data)
        except error as e:
            print(self.gettime() + ': 与sqlmap建立连接时发生错误', e)
            return False



    def socket_reverse(self):
        proxysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:# 进入代理连接发送循环,必须连接成功才算结束
            # 流量代理，目标代理服务器，将客户端接收数据转发给代理服务器
            if self.data_recv:
                return True
            ip_use = random.choice(self.ip_list) # 随机选择一个...不行再换
            print(self.gettime() + "Using proxy ip:" + str(ip_use))
            try:# 这是一个建立到代理服务器的错误判断
                proxysocket.settimeout(10)
                if self.data_recv:
                    return True
                proxysocket.connect((ip_use[0], int(ip_use[1])))  # 这里将会建立代理连接
            except Exception as e:
                print(self.gettime() + '建立到代理服务器发生错误', e)
                #self.ip_list = self.reuse()
                #proxysocket.close()
                break

            try:# 这是一个发送数据包到代理服务器的错误判断
                if self.data_recv:
                    return True
                proxysocket.send(self.data)
            except error as e:
                print(self.gettime() + "发送给代理服务器数据时出错 : " + str(e))
                #self.ip_list = self.reuse()
                #proxysocket.close()
                break

            try:# 这是一个接收代理服务器回传信息的错误判断
                if self.data_recv:
                    return True
                temps = b''
                while True:
                    temp = proxysocket.recv(1024)# 从代理服务器接收数据，然后转发回sqlmap
                    if not temp:
                        break
                    temps += temp
                #if re.findall(r'',temps) != []:
                self.data_recv = temps
            except socket.timeout as e:
                print(self.gettime() + "接收代理回传的数据时发生错误 : " + str(e))
                #self.ip_list = self.reuse()
                break
            finally:
                #proxysocket.close()
                pass

    def socket_get(self):
        while True:
            proxysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxysocket.settimeout(7)
            ip_use = random.choice(self.ip_list)  # 随机选择一个...不行再换
            try:
                proxysocket.connect((ip_use[0], int(ip_use[1])))  # 这里将会建立代理连接
                if self.success == True:
                    return
                #print(self.gettime() + 'Successful connect to：' + str(ip_use) + ' sending', self.data)
                proxysocket.send(self.data)
                break
            except:
                proxysocket.close()
                return
        temp = b''
        if self.success == True:
            return
        while True:
            try:
                data_recv = proxysocket.recv(1024)  # 从代理服务器接收数据，然后转发回sqlmap
                # if not data_recv:
                #     break
                if len(data_recv) == 0:
                    break
                temp += data_recv
                if self.success == True:
                    return
                if re.findall (r'HTTP/1\.1 200', temp.decode ()) != []:
                    self.data_recv = temp
                    print(self.gettime() + 'Proxy receving:', self.data_recv)
                    self.success = True
                    proxysocket.close()
                    break
            except Exception as e:
                proxysocket.close()
                return

    def recving_judge(self, filte):
        if re.findall(r'429 Too Many Requests', filte) == [] and re.findall (r'please try again later',filte) == [] and re.findall (r'Maximum number of open connections reached', filte) == [] and re.findall (r'403 Forbidden',                                                                              filte) == []:
            if re.findall(r'Error: The requested URL could not be checked', filte) == [] and re.findall(r'Proxy error: 503', filte) == [] and re.findall (r'500 Internal Server Error', filte) == []:
                if re.findall(r'kouyu\.youdao\.com', filte) == []:
                    return True
        return True
    def requests_get(self, url, headers, i):
        proxy = self.ip_list[i]
        proxies = {'http': 'http://%s:%s' % (proxy[0], proxy[1])}
        while True:
            try:
                if self.success == True:
                    return
                res = requests.get(url=url, headers=headers, proxies=proxies, timeout=1.8).content
                if len(res) < 275:# 短到大部分是无效包
                    return
                self.data_recv = res
                self.success = True
            except Exception as e:
                pass

    def handle2(self):
        request = self.data.decode()#requests方法
        if re.findall(r'GET',request) != []:
            headers = {}
            url = re.findall(r'GET (.*?) HTTP/1.1', str(request))[0]
            res = re.findall(r'\n(.*?)\n', str(request))
            for i in res:
                try:
                    temp = re.findall(r'(.*?): (.*)',str(i))[0]
                    headers[temp[0]] = temp[1].replace('\r','')
                except:
                    pass
        #print(self.gettime() + 'URL：', url)
        #print(self.gettime() + 'Headers：', headers)
        thread_list = []
        #print(self.gettime() + '我们将开启%d 个线程去各代理服务器为你获取数据' % len(self.ip_list))
        #print (self.gettime () + '本次目标', url, headers)
        for i in range(len(self.ip_list)):
            t = threading.Thread(target=self.requests_get, args=(url, headers, i))
            t.start()
            thread_list.append(t)
        for i in thread_list:
            i.join()
        print(self.gettime() + 'Proxy receving:', self.data_recv)


    def handle(self):
        print(self.gettime() + 'Receving from sqlmap:', self.data)
        # socket方法
        thread_list = []
        for i in range(100):
            t = threading.Thread(target=self.socket_get, args=())
            t.start()
            thread_list.append(t)
        for i in thread_list:
            i.join()

    def run(self):
        threading.Thread(target=self.change_iplist, args=()).start()# 5秒换新ip_list线程
        try:
            self.server.bind(('127.0.0.1', 9999)) # 本地服务IP和端口
            self.server.listen(10)#  最大连接数
        except error as e:
            print(self.gettime() + "监听端口出现问题 : "+str(e))
        print(self.gettime() + 'Waiting for connection...')
        while True:
            self.sqlmap_client, self.addr = self.server.accept()
            #print(self.gettime() + 'NEW accept sqlmap, host :%s and port:%s' % (str(self.addr[0]), str(self.addr[1])))  # sqlmap建立连接
            self.sqlmap_recv()
            self.handle2()
            while self.success == False:
                self.handle2()
            print(self.gettime() + 'Send to sqlmap:', self.data_recv)
            self.sqlmap_client.send(self.data_recv)
            self.data = b''
            self.data_recv = b''
            self.success = False
            self.sqlmap_client.close()

def main():
    try:
        ProxiesServer = ProxyServerTest()
        t = threading.Thread(target=ProxiesServer.run, name='LoopThread')
        t.start()
        t.join()
    except Exception as e:
        print("主函数发生了一个错误 : " + str(e))


if __name__ == '__main__':
    main()