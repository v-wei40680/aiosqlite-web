url = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'

params_flag = """_tb_token_: 3e77883d14f3e
event_submit_do_query: 1
action: memo/UpdateSellMemoAction
user_type: 1
pageNum: 1
auctionTitle: 
dateBegin: 0
dateEnd: 0
commentStatus: 
buyerNick: 
auctionStatus: 
returnUrl: 
logisticsService: 
from_flag: 
biz_order_id: 547956929022248730
flag: 1
memo: 1"""

params_orders = """auctionType: 0
close: 0
pageNum: 1
pageSize: 100
queryMore: false
rxAuditFlag: 0
rxElectronicAllFlag: 0
rxElectronicAuditFlag: 0
rxHasSendFlag: 0
rxOldFlag: 0
rxSendFlag: 0
rxSuccessflag: 0
rxWaitSendflag: 0
tradeTag: 0
useCheckcode: false
useOrderInfo: false
errorCheckcode: false
action: itemlist/SoldQueryAction
prePageNo: 1"""


def get_params(params):
    ps = {}
    for p in params.splitlines():
        ps[p.split(': ')[0]] = p.split(': ')[1]
    return ps

def parse_cookie(ck):
    cs = {}
    for c in ck.split('; '):
        cs[c.split('=')[0]] = c.split('=')[1]
    return cs

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3770.142 Safari/537.36',
    'referer': 'https://trade.taobao.com'
}

cookie = "everywhere_tool_welcome=true; miniDialog=true; mt=ci%3D-1_0; _bl_uid=knje0vX4lRXymjr8tpemtww55Rns; ali_ab=113.74.43.105.1557732791874.8; enc=JRh3CHLmqooFzdItIeCFErIMEKS0Gsy9SpTMiMKWQFiKq9O%2Fvf22OggT2T2ZH8Ib4WMj6kp3fW5umG5NcyCwIA%3D%3D; thw=cn; t=19dd46e488263b6ab9575c77205aecf6; _m_h5_tk=ec824b3367bfbccafeeebe140f35d3c8_1567417135652; _m_h5_tk_enc=9708958f8ed60e657828a79dc7184ac0; cookie2=1ce9d309a2b20350e1dafd4809d04b37; _tb_token_=3333777065a3b; x=3079394145; unb=4094468737; sn=%E9%80%9A%E4%BC%97%E6%97%97%E8%88%B0%E5%BA%97%3A%E8%8F%9C%E9%B8%9F; csg=a538d859; skt=365805d868227b70; cna=xLXTFaXAT2sCAXFKKEON3jQl; v=0; uc1=cookie14=UoTaH0Azs39Vrg%3D%3D&lng=zh_CN; l=cBEBQubmqFISeePvKOfZlurza77t0IOb8sPzaNbMiICPO2165ZR1WZUXilTBCnGVLsO2R3yE78S3BWL39yznhW-CPSbkvKJC.; isg=BMrKpOiAo3TCSy_B_eNEL4Q-G7C_Zk4VY1uHNVQCYZ2oB2vBPEqtJLo1FzN-98at"

cs = parse_cookie(cookie)