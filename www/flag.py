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
pageSize: 30
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

# ck = "everywhere_tool_welcome=true; t=14311ec3aafd57dfeca9dc34db942c41; cna=KCpgFVcUJk8CAXFKK1gjY3ek; enc=CtFfr8LBwjjXreQlTADOdArmNTekIb0xzybQzWE%2FRjQspBO3b1UMgqwbmnmfLar6ilL6puchfnk8Glu39BFbJA%3D%3D; ali_ab=113.74.43.88.1557741049564.1; _bl_uid=hdjd5v2hnw8eX3mdC85hweyzvhqz; thw=cn; uc3=id2=&nk2=&lg2=; tracknick=; UM_distinctid=16bd4cb224a1b4-05dc9baf7a5373-e343166-1fa400-16bd4cb224bbdf; _m_h5_tk=f0a3a923c8a327a2aec68dbaf20ae75c_1563523082128; _m_h5_tk_enc=f540490628d54f52dac5fd4c6b11733f; cookie2=109c250314a382950d517b2e7fabe956; _tb_token_=3e77883d14f3e; x=2829884134; sn=%E4%BC%97%E6%B3%B0%E5%8A%9E%E5%85%AC%E4%B8%93%E8%90%A5%E5%BA%97%3A%E8%8F%9C%E9%B8%9F; unb=4102789044; skt=00aa87e7ca72b5d6; csg=0a5971ad; v=0; uc1=cookie14=UoTaG7jbMp%2B87Q%3D%3D&lng=zh_CN; l=cBQuNRCVvWHF_Q0wKOCwlurza77tkIRfguPzaNbMi_5Z-1T1JI_Ok4_JLe96cjWFTkTB4k6UXwetneVU8yDbTH_7iaxp3p1..; isg=BHh4kqHoUe5vZryGXvIb6y2ZSSbKSdxnLrb3dLLpvLNmzRm3WvDA-iarhYVYnZRD"

def parse_cookie(ck):
    cs = {}
    for c in ck.split('; '):
        cs[c.split('=')[0]] = c.split('=')[1]
    return cs

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3770.142 Safari/537.36',
    'referer': 'https://trade.taobao.com'
}
