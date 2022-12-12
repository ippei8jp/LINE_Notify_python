import sys
import re

sys.path.append("../util")

# ../utilからインポートするもの
from my_util import getTimeString
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

# ===============================================
from tiny_line import tiny_line

# ===============================================
def main() :
    # LINEモジュール初期化
    tl = tiny_line(access_token, host=host, debug=True)
    
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
            result = tl.notify(message)
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
