# LINE Notify にメッセージ送信するテストプログラム(python版)

## 概要
LINE Notifyについてはこちら→ <https://notify-bot.line.me/ja/>   
socket通信、標準モジュールurllibを使用したテストプログラムを作成しました。  
それぞれasyncioで非同期化したものも作りました。  

動作確認はバージョン3.10で行いましたが、3.7くらいまでは大丈夫でしょう。  

Javascript版を作ったので、それのpython版も、というくだらない動機です。  


参考：[ ippei8jp / LINE_Notify_javascript](https://github.com/ippei8jp/LINE_Notify_javascript)  


## 事前準備
アクセストークンが必要なので、[このへん](https://qiita.com/iitenkida7/items/576a8226ba6584864d95)
を参考にアクセストークンを取得してください。  

取得したアクセストークンは``util/access_token.py``ファイルに以下のように格納してください。  
間違ってgithubにcommitしてしまわないように、別ファイルにして``.gitignore``に書いてあります。  

```
access_token    = '«取得したアクセストークン»'
```

## プログラム
| ファイル名          | 内容                                                 |
|-----------------------------------------|------------------------------------------------------|
|util/access_token.py                     | アクセストークン(上記に従って作成してください)       |
|util/my_util.py                          | その他共通ルーチン                                   |
|util/prompt.py                           | asyncio対応キー入力モジュール                        |
|tiny_line/tiny_line.py                   | socket通信版 LINE Notify送信用クラス定義             |
|tiny_line/test_tiny_line.py              | socket通信版 テストプログラム本体                    |
|tiny_line_async/test_tiny_line_async.py  | socket(asyncio対応)通信版 INE Notify送信用クラス定義 |
|tiny_line_async/tiny_line_async.py       | socket(asyncio対応)通信版 テストプログラム本体       |
|urllib/test_urllib.py                    | urllib(asyncio対応)版 テストプログラム本体           |
|urllib/test_urllib_asyncio.py            | urllib版 テストプログラム本体                        |

## 実行方法
特にオプション/パラメータはありません。テストプログラムをpython3で実行してください。  
(テスト用にちょこっとコマンドラインパラメータ使ってるけど、気にしないでちょ)  

それぞれのasyncio対応版で実行時に``-B``オプションをつけると、バックグラウンドタスクが動きます。  
バックグラウンドタスクはひたすら``.``を表示するので、
IO待ちの間メイン処理が中断されてバックグラウンドタスクに処理が移っていることが確認できます。  

## 感想
lowlevelなAPIを使用することで、実際にどのようなデータのやり取りが行われているか理解できると思います。  
まぁ、素直にrequestsやaiohttp使えばいいんですけど...  

asyncioを使うとIO処理待ち時間に別タスクを動かすことができるので、CPUリソースを有効に活用できます。  
センサ入力を短い周期で読み込んでいたり、なんらかの制御を短い周期で行っている場合、  
通信を行うことでデータ抜けやレスポンス悪化を防げる可能性があります。  


urllibのようなやや上位のAPIを使用した場合でも``loop.run_in_executor()``を使うと
わりと簡単に非同期化できるような気がします(``urllib/test_urllib_asyncio.py``参照)。  
(できないプログラムもあるようですが)  


送信回数に制限があるので(現状1時間に1000回だったかな?)、やりすぎにはご注意ください。  


