import sys
import time
import asyncio
if sys.platform == 'win32' :
    import msvcrt
else :  # linux
    import termios
    import tty
    
class Prompt:
    # コンストラクタ
    def __init__(self, loop=None, char_mode=False):
        if sys.platform == 'win32' and  char_mode :
            # Windowsではcharacterモードをサポートしない
            raise RuntimeError('character mode is not supported')
        
        # 3.10以降は生成にはnew_event_loop()、取得にはget_running_loop()を使用
        # ここは新規作成ではないのでget_running_loop()で大丈夫(3.7以降なら)
        # self.loop = loop or asyncio.get_event_loop()
        self.loop = loop or asyncio.get_running_loop()
        
        # FIFOキューの作成
        self.q = asyncio.Queue()
        
        # その他変数初期化
        self.char_mode = char_mode
        
        if sys.platform == 'win32' :
            # ラインバッファ
            self.linebuff = ''
            
            # タスクの生成
            selk_get_key_task  = self.loop.create_task(self.got_input_task())
        else :  # linux
            # 標準入力のファイルディスクプリタを取得
            stdin_fd = sys.stdin.fileno()
            
            # 標準り入力のリーダを設定
            self.loop.add_reader(stdin_fd, self.got_input)
            
            self.old_termcap = None
            if self.char_mode :
                # 1文字入力時の設定 (バッファリングなし設定)
                
                # 標準入力の端末属性を取得しておく(最後に元に戻すため)
                self.old_termcap = termios.tcgetattr(stdin_fd)
                
                # 標準入力のモードを切り替える
                tty.setcbreak(stdin_fd)
        
        
    # 終了処理
    def terminate(self):
        if sys.platform == 'win32' :
            pass
        else :  # linux
            if self.old_termcap :
                # termcap書き換え済みなら元に戻す
                
                # 標準入力のファイルディスクプリタを取得
                stdin_fd = sys.stdin.fileno()
                
                # 標準入力の端末属性を元に戻す
                termios.tcsetattr(stdin_fd, termios.TCSANOW, self.old_termcap)
    
    # キー入力取得
    if sys.platform == 'win32' :        # windowsではタスクとして使用
        async def got_input_task(self):
            while True :
                if msvcrt.kbhit() :
                    # キー入力あり
                    c = str(msvcrt.getch(), encoding='utf-8')
                    if c == '\r' :
                        c = '\n'        # 改行コードをLFに変更
                    print(c, end='', flush=True)   # echo back
                    if self.char_mode :
                        await self.q.put(c)
                    else :
                        if c == '\x08' :
                            # BSで1文字戻る
                            self.linebuff = self.linebuff[:-1]
                        else :
                            self.linebuff = self.linebuff + c
                        if c == '\n' :
                            await self.q.put(self.linebuff)
                            self.linebuff = ''
                else :
                    # キー入力なし
                    await asyncio.sleep(0.3)    # ちょっと待つ
    
    else : # Linux
        def got_input(self):
            pass
            if self.char_mode :
                asyncio.ensure_future(self.q.put(sys.stdin.read(1)), loop=self.loop)        # 1文字入力
            else :
                asyncio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)     # 1行入力
    
    async def __call__(self, msg, end='', flush=True):
        print(msg, end=end, flush=flush)
        data = await self.q.get()
        if not self.char_mode :
            # 1行入力時は改行を削除
            data = data.rstrip('\n') 
        return data                       # 1文字入力
    
    async def alternative_input(self, strs) :
        for str in strs :
            if self.char_mode :
                for ch in str :
                    await self.q.put(ch)       # 代替入力
            else :
                await self.q.put(str)          # 代替入力


# テストルーチン
if __name__=="__main__" :
    # コマンドラインパラメータ
    from argparse import ArgumentParser, SUPPRESS, RawTextHelpFormatter
    parser = ArgumentParser(add_help=False, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-h', '--help', action='help', default=SUPPRESS, 
                            help='Show this help message and exit.'
                        )
    parser.add_argument('-c', '--char',     action='store_true', 
                            help='Set character mode.'
                        )
    parser.add_argument('-t', '--timeout',  action='store_true', 
                            help='Set Timeout mode.'
                        )
    args = parser.parse_args()

    # テスト用パラメータ
    char_mode    = args.char
    timeout_mode = args.timeout
    
    print("Character mode" if char_mode      else "Line mode")
    print("w/o Timeout"    if timeout_mode   else "with Timeout")
    
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
    
    # Promptのインスタンス
    prompt = Prompt(loop=loop, char_mode=char_mode)
    
    # ===============================================
    import atexit               # 終了時処理用
    
    # 終了時処理
    def all_done():     
        print("==== terminating... ====")
        # Promptで変更した標準入力の端末属性を元に戻す
        if 'prompt' in globals() and prompt :
            prompt.terminate()
        
        print("==== terminated ====")
    
    # 終了時処理を登録
    atexit.register(all_done)
    
    # ===============================================
    async def main(loop):
        print('**** START ****')
        
        if char_mode :
            if timeout_mode :
                # タイムアウト付きで入力待ちする
                while True:
                    try :
                        ch = await asyncio.wait_for(prompt(''), timeout=5.0)
                        if ch == 'q' :
                            return
                        print(f'INPUT:"{ch}"')
                    except asyncio.TimeoutError:        # キー入力のタイムアウト
                        # タイムアウトした
                        # # 通常は何もせずに続ければ良い
                        # pass
                        print('TIMEOUT')
            else :
                # タイムアウトなしで入力待ちする
                while True:
                    ch = await prompt('')
                    if ch == 'q' :
                        return
                    print(f'INPUT:"{ch}"')
        
        else :
            if timeout_mode :
                # タイムアウト付きで入力待ちする
                while True:
                    try :
                        line = await asyncio.wait_for(prompt('PROMPT:'), timeout=5.0)
                        if line == 'q' :
                            return
                        print(f'INPUT:{line}')
                    except asyncio.TimeoutError:        # キー入力のタイムアウト
                        # タイムアウトした
                        # # 通常は何もせずに続ければ良い
                        # pass
                        print('TIMEOUT')
            else :
                # タイムアウトなしで入力待ちする
                while True:
                    line = await prompt('PROMPT:')
                    if line == 'q' :
                        return
                    print(f'INPUT:{line}')
    
    loop.run_until_complete(main(loop))
