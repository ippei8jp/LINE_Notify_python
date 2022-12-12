import sys
import ssl
import re
import asyncio

sys.path.append("../util")

# ../utilからインポートするもの
from my_util import RFC3986_encode

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class tiny_line_async :
    # コンストラクタ
    def __init__(self, access_token, host=None, loop=None, debug=False) :
        # パラメータチェック
        if type(access_token) is not str:
            raise ValueError('access key must be string')
        
        self.access_token   = access_token
        # デフォルトのLINEのホスト情報
        self.host           = host or { 'host': 'notify-api.line.me', 'port': 443, 'endpoint': '/api/notify'}
        # イベントループ
        self.loop           = loop or asyncio.get_running_loop()
        self.__DEBUG__      = debug
    
    # デバッグ出力
    def __debug_print(self, str) :
        if self.__DEBUG__ :
            print(str)
    
    # リクエストヘッダの作成
    def __makeRequestMessage(self, message) :
        # make request
        # request = f'POST {self.host["endpoint"]} HTTP/1.0\n'  # HTTP/1.0 を指定するとChunked Transferにならないので、レスポンスが1行で済む
                                                                # このとき、headerの「Connection: close」は削除
        request = f'POST {self.host["endpoint"]} HTTP/1.1\n'
        
        # make message body
        body = f'message={RFC3986_encode(message)}'
        
        # make message header
        header  = f'Host: {self.host["host"]}\n'                      
        header += f'User-Agent: nanchatte line Bot python v0.1\n'     
        header += f'Accept: */*\n'                                    
        header += f'Authorization: Bearer {self.access_token}\n'      
        header += f'Content-Type: application/x-www-form-urlencoded\n'
        header += f'Connection: close\n'                 # これがないとrecvがタイムアウトするまで戻ってこない
        header += f'Content-Length: {str(len(body))}\n'               
        
        # request message
        return request, header, body
    
    # データの送信 & レスポンスの受信
    async def __sendmessage(self, msg) :
        ctx = ssl.create_default_context()
        ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        reader = None
        writer = None
        try :
            reader, writer = await asyncio.open_connection(
                                        host=self.host['host'],  # host
                                        port=self.host['port'],  # port
                                        ssl=ctx
                                )
            
        except Exception as e:
            # print(f'exception: {e}')
            raise e
            
        self.__debug_print('socket opened!!')
        try :
            # データを送信
            self.__debug_print('request sending...')
            writer.write(msg.encode('utf-8'))
            
            # データ受信
            recv_data = b''
            total_received = 0
            while True:
                # データ断片受信
                chunk = await reader.read(4096)
                if len(chunk) == 0:
                    # 受信データがない
                    break       # 受信終了
                recv_data += chunk
                total_received = total_received + len(chunk)
                
            # データ受信完了
            writer.close()
            await writer.wait_closed()
            self.__debug_print('socket closed!!')
        except Exception as e:
            # print(f'exception: {e}')
            # エラーが発生したらクローズして上位へ例外通知
            if writer :
                writer.close()
                await writer.wait_closed()
                self.__debug_print('socket closed!!')
            raise e
        
        # 受信データのパース
        try :
            recv_data   = recv_data.decode('utf-8')                 # 文字列化
            recv_data   = recv_data.replace("\r\n", "\n")           # CRLFをLFに変換
            status_line = re.search(r'^.*\n',   recv_data).group()              # 最初の1行取り出し
            empty_line  = re.search(r'^\n',   recv_data, flags=re.MULTILINE)    # 空行位置
            header = recv_data[:empty_line.start()]                             # 空行の前 取り出し
            body = recv_data[empty_line.end():]                                 # 空行の後 取り出し
            
            status_chunk = status_line.split()                      # 空白で分割
            status_code  = int(status_chunk[1])                     # 2番目がステータスコード
        except Exception as e:
            self.__debug_print(f'exception: {e}')
            self.__debug_print('==== recv_data ===============')
            self.__debug_print(recv_data)
            self.__debug_print('==============================')
            raise ValueError('Receive Data parse error')
        
        return {"status": status_code, "header": header, "body": body}
        
            
    
    # ######## notify API ################################
    def notify(self, msg) : 
        # 送信データの作成
        request, header, body = self.__makeRequestMessage(msg)
        reqMessage = f'{request}{header}\n{body}\n'
        
        # デバッグ用送信データの表示
        self.__debug_print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        self.__debug_print(reqMessage)
        self.__debug_print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        
        # データを送信
        result = self.__sendmessage(reqMessage)
        
        return result
    
