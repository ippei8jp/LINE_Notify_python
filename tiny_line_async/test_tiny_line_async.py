import sys
import re
import asyncio

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
parser.add_argument('-B', '--back_task',     action='store_true', 
                        help='Enable background task.'
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
from tiny_line_async import tiny_line_async

# ===============================================
# イベントループ取得
if sys.platform == 'win32' :
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else :  # linux
    if sys.version_info.minor < 10 :    # 3.10未満はget_event_loop()
        loop = asyncio.get_event_loop()
    else :                              # 3.10以降は生成にはnew_event_loop()、
                                        # 取得にはget_running_loop()を使用
        loop = asyncio.new_event_loop()

# ======================================================================================================================================
# キー入力
from prompt import Prompt

# Promptのインスタンス
prompt = Prompt(loop=loop, char_mode=False)
# prompt = Prompt(loop=loop, char_mode=True)       # 1文字入力モード(たぶんLinuxしか使えない)

# タイムアウトせずにキー入力する場合
# ch = await prompt('PROMPT:')
# タイムアウト付きでキー入力する場合
# ch = await asyncio.wait_for(prompt('PROMPT:'), timeout=5.0)

# ======================================================================================================================================
# 終了時処理
# 例外やCTRL+Cで終了した時にも終了処理をしたいので
import atexit               # 終了時処理用

def all_done():     
    # Promptで変更した標準入力の端末属性を元に戻す
    if prompt :
        prompt.terminate()
    
    print("==== terminated ====")

# 終了時処理を登録
atexit.register(all_done)


# ======================================================================================================================================
# テスト用バックグラウンド処理関連
back_task=None

# テスト用バックグラウンドタスク
async def task_background():
    while True:
        print(".", end='')
        await asyncio.sleep(0)      # 実行権を明け渡す

# テスト用バックグラウンドタスクを開始
def back_task_start() :
    global back_task
    if args.back_task :
        back_task = asyncio.create_task(task_background())

# テスト用バックグラウンドタスクを停止
def back_task_stop() :
    global back_task
    if back_task :
        back_task.cancel()
        back_task = None

# ======================================================================================================================================
async def main(loop) :
    # LINEモジュール初期化
    tl = tiny_line_async(access_token, host=host, loop=loop, debug=True)
    
    while True : 
        # 送信するメッセージを入力
        line = await prompt('MSG> ')
        if line == 'q' :
            # 終了する
            break
        
        # 送信メッセージ
        message = f'{line} ({getTimeString()})'
        print(f'{message})')

        back_task_start()               # テスト用タスクの開始
        # 送信
        try :
            result = await tl.notify(message)
        except Exception as e:
            # エラーが発生した
            back_task_stop()            # テスト用タスクの停止
            print(f'main : exception: {e}')
            break
        
        back_task_stop()            # テスト用タスクの停止
        
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

# mainタスクを実行
loop.run_until_complete(main(loop))
