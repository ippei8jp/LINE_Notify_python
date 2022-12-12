import datetime

def getTimeString() :
    return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ---- percent encoding
# RFC3986 非予約文字コードのリスト
# (「0～9」、「A～Z」、「a～z」、「-」、「.」、「_」、「~」 )
# 参考：https://www.asahi-net.or.jp/~ax2s-kmtn/ref/uric.html
RFC3986_UnreservedCodes = [x for x in [ *range(ord('0'), ord('9') + 1), 
                                        *range(ord('A'), ord('Z') + 1), 
                                        *range(ord('a'), ord('z') + 1), 
                                        ord('-'), ord('.'), ord('_'), ord('~')]]

# RFC3986エンコード
def RFC3986_encode(s):
    ret = ''                # 変換結果初期化
    s = s.encode('utf-8')   # utf8として文字コード化
    for c in s :
        if c in RFC3986_UnreservedCodes :
            # 非予約文字コードならそのまま文字化
            ret += chr(c)
        else :
            # 予約文字なら%XXに変換
            ret += f'%{c:02X}'
    return ret

