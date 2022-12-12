import sys
import re

import urllib.request

sys.path.append("../util")

# ../utilからインポートするもの
from my_util import RFC3986_encode, getTimeString
from access_token import access_token

# HOSTパラメータ
host    = { 
            'host': 'notify-api.line.me', 
            'port': 443, 
            'endpoint': '/api/notify'
        }

# ===============================================
# コマンドラインパラメータ
from argparse import ArgumentParser, SUPPRESS, RawTextHelpFormatter
parser = ArgumentParser(add_help=False, formatter_class=RawTextHelpFormatter)
parser.add_argument('-h', '--help', action='help', default=SUPPRESS, 
                        help='Show this help message and exit.'
                    )
parser.add_argument('-A', '--addr_error',     action='store_true', 
                        help='Test for address error.'
                    )
parser.add_argument('-P', '--path_error',     action='store_true', 
                        help='Test for path error.'
                    )
parser.add_argument('-T', '--token_error',     action='store_true', 
                        help='Test for access token error.'
                    )
args = parser.parse_args()

# ===============================================
# テスト用パラメータに変更
if args.addr_error :
    host["host"] = 'notify-api.line.me2'    # エラーになるホスト名
if args.path_error :
    host["endpoint"] = '/api/notify2'       # エラーになるpath
if args.token_error :
    access_token = 'ERROR_TOKEN'            # エラーになるアクセストークン

# URLを組み立て
url = f'https://{host["host"]}{host["endpoint"]}'

# ===============================================
def line_notify(message) :
    # make message body
    body = f'message={RFC3986_encode(message)}'
    
    headers = {
        'User-Agent'    : 'nanchatte line Bot python v0.1', 
        'Accept'        : '*/*',
        'Authorization' : f'Bearer {access_token}',
        'Content-Type'  : 'application/x-www-form-urlencoded',
    }
    try :
        req = urllib.request.Request(url, data=body.encode(), headers=headers)
        with urllib.request.urlopen(req) as res:
            response_headers = res.info()
            response_body    = res.read().decode('utf-8')
            status_code      = res.code
        
        return {"status": status_code, "header": response_headers, "body": response_body}

    except urllib.error.HTTPError as e :    # HTTP ステータスコードが 4xx または 5xx だったとき
                                            # URLError より前に書くこと
        print(f'ERROR    : {e.code}    {e.reason}')
        print(f'response : {e.read()}')                 # メッセージボディの表示
        print(f'==== HEADER ====')
        print(f'{e.headers.as_string()}')
        raise e
    except urllib.error.URLError as e :     #  HTTP 通信に失敗したとき
        print(f'ERROR : {e.reason}')
        raise e
    except Exception as e:
        raise e

# ===============================================
def main() :
    
    while True :
        # 送信するメッセージを入力
        line = input('MSG> ')
        if line == 'q' :
            # 終了する
            break
        
        # 送信メッセージ
        message = f'{line} ({getTimeString()})'
        print(f'{message})')
        
        # 送信
        try :
            result = line_notify(message)
        except Exception as e:
            # エラーが発生した
            print(f'main : exception: {e}')
            break
        
        # 結果表示
        print('==== HEADER ===============')
        print(result["header"])
        print('==== BODY ===============')
        print(result["body"])
        print('===================')
        
        # bodyから{～}を取り出し、最初の1個のみ使用
        response = re.findall(r'{.*}', result["body"])[0]
        
        print(f'status code : {result["status"]}')
        print(f'response    : {response}')
        print('*******************')
    # end of main

# mainルーチンを実行
main()
