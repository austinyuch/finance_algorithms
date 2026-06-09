import copy
import math
from pathlib import Path
import datetime

PATH_TMP_DIR = Path('temp_files')
# if PATH_TMP_DIR not exists, create one
if not PATH_TMP_DIR.exists():
    PATH_TMP_DIR.mkdir()

交易方法 = {
    "1":"等差",
    "2":"等比",
}

# 下單價格, 下單數量

def get單位價格差(flt_起始價格:float,
                flt最終價格:float,
                int_交易次數:int)->float:
    flt總價格差 = flt_起始價格 - flt最終價格
    flt_單位價格差 = abs(flt總價格差) / (int_交易次數 )
    return flt_單位價格差

def getLst買入價格(flt_起始價格:float,
                flt_單位價格差:float,
                int_交易次數:int)->list:
    # 計算買入價格
    lst_買入價格=[]
    for i in range(int_交易次數 +1 ):
        
        flt買入價格 = flt_起始價格 - (flt_單位價格差 * i)
        if flt買入價格==flt_起始價格:
            continue
        else:
            lst_買入價格.append(flt買入價格)

    return lst_買入價格

def get本階投入資金百分比(flt_一組金字塔的加總金額,flt_下單金額)->float:
    return (flt_下單金額/flt_一組金字塔的加總金額)*100

def get累計下跌百分比(flt_起始價格,flt_當前價格)->float:
    return ((flt_起始價格 - flt_當前價格)/flt_起始價格)*100

def etl_percentage(dic_金字塔下單資料:dict,
                flt_一組金字塔的加總金額:float,
                flt_起始價格:float,
                )->dict:
    
    dic_金字塔下單資料_ret = copy.deepcopy(dic_金字塔下單資料)

    flt_累計百分比 = 0
    flt_累計下跌百分比 = 0
    flt_最終價格=0
    flt_累計數量=0
    flt_累計投資金額=0

    # for key,value in dic_金字塔下單資料.items():  
    lst_results = []  
    for dic_階資料 in dic_金字塔下單資料['各階資料']:    
        dic_階資料_etl = copy.deepcopy(dic_階資料)
        flt_百分比 = 0                   
        flt_百分比 = get本階投入資金百分比(flt_一組金字塔的加總金額,dic_階資料_etl["當次投資金額"])
        dic_階資料_etl["投入百分比"] =  float("{:.2f}".format(flt_百分比))
        
        flt_累計百分比 += flt_百分比
        # float("{:.2f}".format(13.949999999999999))
        dic_階資料_etl["累計投入百分比"]= float("{:.2f}".format(flt_累計百分比))

        flt_累計投資金額 += dic_階資料_etl["當次投資金額"]
        dic_階資料_etl["累計投資金額"] = float("{:.2f}".format(flt_累計投資金額))

        # 計算累計下跌百分比 : ((起始價格 - 本階價格)/起始價格)*100
        flt_累計下跌百分比 = get累計下跌百分比(flt_起始價格,dic_階資料_etl['價格'])
        
        dic_階資料_etl["股價跌幅(%)"]= float("{:.2f}".format(flt_累計下跌百分比))
        
        flt_累計數量 += dic_階資料_etl["單位數"]
        flt_最終價格 = dic_階資料_etl['價格']

        lst_results.append(dic_階資料_etl)

    dic_金字塔下單資料_ret['各階資料'] = lst_results
     
    dic_金字塔下單資料_ret["起始價格"] = flt_起始價格     
    dic_金字塔下單資料_ret["最終價格"] = flt_最終價格
    dic_金字塔下單資料_ret["股價跌幅(%)"] = float("{:.2f}".format(flt_累計下跌百分比))
    
    dic_金字塔下單資料_ret["總投入金額"] = flt_一組金字塔的加總金額
    dic_金字塔下單資料_ret["累計數量"]= float("{:.2f}".format(flt_累計數量))
    
    flt_平均成本 = flt_一組金字塔的加總金額/ flt_累計數量  
    dic_金字塔下單資料_ret["平均成本"] = float("{:.2f}".format(flt_平均成本))
    
    
    return dic_金字塔下單資料_ret


def get本階下單資料(lst_買入價格:list, 
                flt_最小增加數量:float, 
                round單位數, 
                i:int, 
                flt_本階單位數:float):
    dic_本階下單資料={} 
    if round單位數:
        if flt_本階單位數 < flt_最小增加數量:
            flt_本階單位數 = flt_最小增加數量        
        flt_本階單位數 = round(flt_本階單位數,-int(math.log10(flt_最小增加數量)))

    flt_本階下單金額 = lst_買入價格[i] *  flt_本階單位數        
        
    dic_本階下單資料 = {
        "階": i+1,
        "價格":lst_買入價格[i],
        "單位數":flt_本階單位數,
        # "金額":flt_本階下單金額,
        "當次投資金額":flt_本階下單金額,
    }
    
    return dic_本階下單資料

#====等差金字塔====

def get一組等差金字塔下單資料(flt_起始價格:float,
                        int_交易次數:int, 
                        flt_下單數量等差參數:float, 
                        flt_起始單位數:float, 
                        lst_買入價格:list,
                        flt_最小增加數量:float,
                        flt_金字塔放大倍數:float=1.0,
                        round單位數:bool=False)->dict:
    flt_一組金字塔的加總金額 = 0
    dic_單位等差金字塔下單資料 ={}
    lst_results = []
    for i in range(int_交易次數  ):
        
        # 本階金額 = 本階買入價格 * 本階單位數  
        flt_本階單位數 = (flt_起始單位數 + (flt_下單數量等差參數 * i) ) * flt_金字塔放大倍數
       
        dic_本階下單資料 = get本階下單資料(lst_買入價格, 
                                    flt_最小增加數量, 
                                    round單位數, 
                                    i, 
                                    flt_本階單位數)

        # 階層數 = str(i + 1)
        # dic_單位等差金字塔下單資料[階層數] = dic_本階下單資料
        lst_results.append(dic_本階下單資料)
        flt_一組金字塔的加總金額 += dic_本階下單資料["當次投資金額"]
    
    # 處理各階層佔比    
    dic_單位等差金字塔下單資料['各階資料'] = lst_results
    dic_單位等差金字塔下單資料 = etl_percentage(dic_單位等差金字塔下單資料,
                                            flt_一組金字塔的加總金額,
                                            flt_起始價格)

    return dic_單位等差金字塔下單資料



def get買入等差金字塔(flt_總預算:float,
                    flt_起始價格:float, 
                    flt最終價格:float, 
                    int_交易次數:int, 
                    flt_最小增加數量:float, 
                    flt_下單數量等差參數:float, 
                    flt_起始單位數:float=1.0)->dict:    

    flt_單位價格差 = get單位價格差(flt_起始價格,flt最終價格,int_交易次數)
    
    lst_買入價格 = getLst買入價格(flt_起始價格,flt_單位價格差,int_交易次數)
    
    dic_單位等差金字塔下單資料 = get一組等差金字塔下單資料(flt_起始價格,
                                                int_交易次數, 
                                                flt_下單數量等差參數, 
                                                flt_起始單位數, 
                                                lst_買入價格,
                                                flt_最小增加數量)

    flt_金字塔放大倍數 = flt_總預算 / dic_單位等差金字塔下單資料["總投入金額"] 

    dic_等差金字塔下單資料 = get一組等差金字塔下單資料(flt_起始價格,
                                                int_交易次數, 
                                                flt_下單數量等差參數, 
                                                flt_起始單位數, 
                                                lst_買入價格,
                                                flt_最小增加數量,
                                                flt_金字塔放大倍數=flt_金字塔放大倍數,
                                                round單位數=True)

    
    return dic_等差金字塔下單資料

#====等比金字塔====


def get一組等比金字塔下單資料(flt_起始價格:float,
                        int_交易次數:int, 
                        flt_下單數量等比參數:float, 
                        flt_起始單位數:float, 
                        lst_買入價格:list,
                        flt_最小增加數量:float,
                        flt_金字塔放大倍數:float=1.0,
                        round單位數:bool=False)->dict:
    flt_一組金字塔的加總金額 = 0
    dic_單位等比金字塔下單資料 ={}
    lst_results = []
    for i in range(int_交易次數 ):
        
        # 本階金額 = 本階買入價格 * 本階單位數  
        flt_本階單位數 = (flt_起始單位數 * (flt_下單數量等比參數 ** i) ) * flt_金字塔放大倍數
        
        dic_本階下單資料 = get本階下單資料(lst_買入價格, flt_最小增加數量, round單位數, i, flt_本階單位數)

        # 階層數 = str(i + 1)  
        # dic_單位等比金字塔下單資料[階層數] = dic_本階下單資料 

        lst_results.append(dic_本階下單資料)            
        flt_一組金字塔的加總金額 += dic_本階下單資料["當次投資金額"]
    
    # 處理各階層佔比    
    dic_單位等比金字塔下單資料['各階資料'] = lst_results
    dic_單位等比金字塔下單資料= etl_percentage(dic_單位等比金字塔下單資料,
                                            flt_一組金字塔的加總金額,
                                            flt_起始價格)

    return dic_單位等比金字塔下單資料


def get買入等比金字塔(flt_總預算:float,
                    flt_起始價格:float, 
                    flt最終價格:float, 
                    int_交易次數:int, 
                    flt_最小增加數量:float, 
                    flt_下單數量等比參數:float, 
                    flt_起始單位數:float=1.0)->dict:    

    flt_單位價格差 = get單位價格差(flt_起始價格,flt最終價格,int_交易次數)
    
    lst_買入價格 = getLst買入價格(flt_起始價格,flt_單位價格差,int_交易次數)
    
    dic_單位等比金字塔下單資料 = get一組等比金字塔下單資料(flt_起始價格,
                                                int_交易次數, 
                                                flt_下單數量等比參數, 
                                                flt_起始單位數, 
                                                lst_買入價格,
                                                flt_最小增加數量)

    flt_金字塔放大倍數 = flt_總預算 / dic_單位等比金字塔下單資料["總投入金額"] 

    dic_等比金字塔下單資料 = get一組等比金字塔下單資料(flt_起始價格,
                                                int_交易次數, 
                                                flt_下單數量等比參數, 
                                                flt_起始單位數, 
                                                lst_買入價格,
                                                flt_最小增加數量,
                                                flt_金字塔放大倍數=flt_金字塔放大倍數,
                                                round單位數=True)

    
    return dic_等比金字塔下單資料

def getLocalTimestamp()->str:
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def 金字塔資料轉csv(dic_data):
    """
    "價格": 390,
    "單位數": 9,
    "金額": 3510,
    "百分比": 3.51,
    "累計百分比": 3.51,
    "累計下跌百分比": 2.5

    "總投入金額": 99990,
    "平均成本": 43183.33,
    "累計數量": 45,
    "起始價格": 400,
    "最終價格": 350,
    "累計下跌百分比": 37.5
    """
    import csv
    str_now = getLocalTimestamp()
    fname = '金字塔下單資料'+str_now+'.csv'
    path_file = PATH_TMP_DIR.joinpath(fname)
    # 將dic_ret 寫入 csv檔
    with open(path_file, 'w', newline='') as the_file:
        # writer = csv.writer(csvfile)
        # 寫入header summary
        # str_header = '階,買入價格,單位數,當次投資金額,投入百分比,累計投入百分比,累計投資金額,股價跌幅'
        str_header = '"Lv.","Unit Price($)","Share","Amount of Invest.($)","Invest.(%)","Accu. Invest.(%)","Accu. Invest. Total($)","Price Drop(%)"'
        the_file.write(str_header)
        the_file.write("\n")
        # the_file.write('\n'.join(tokens))
        lst_line_data = []
        for dic_階資料 in dic_data['各階資料']:
            # str_row = f"{dic_階資料['價格']},{dic_階資料['單位數']},{dic_階資料['金額']},{dic_階資料['百分比']},{dic_階資料['累計百分比']},{dic_階資料['累計下跌百分比']}"
            str_row = ",".join( [str(item) for item in dic_階資料.values()])
            lst_line_data.append(str_row)

        the_file.write("\n".join(lst_line_data))
        the_file.write("\n")
        the_file.write("\n")
        str_summary = f"""   
            ,,,,,Init. Price:,{dic_data["起始價格"]}       
            ,,,,,Final Price:,{dic_data["最終價格"]} 
            ,,,,,Price Drop(%):,{dic_data["股價跌幅(%)"]} 
            ,,,,,Investment Total:,{dic_data["總投入金額"]}
            ,,,,,Accumulated Amount:,{dic_data["累計數量"]}        
            ,,,,,Average Cost:,{dic_data["平均成本"]}              
            """
        the_file.write(str_summary)
        the_file.write("\n")

    return path_file,fname




if __name__ == "__main__":

    # dic_res = get買入等差金字塔(100000,
    #                 130, 
    #                 80,#flt最終價格:float, 
    #                 10,#int_交易次數:int, 
    #                 1,#flt_最小增加數量:float, 
    #                 2,#flt_下單數量等差參數:float, 
    #                 1#flt_起始單位數:float=1.0
    #                 )
    # print(dic_res)

    # lst_買入價格 = getLst買入價格(400,5,5)
    # flt_總預算 = float(100000) #float(input("請輸入總預算："))
    # flt_起始價格 = float(440) #float(input("請輸入起始金額："))
    # flt最終價格 = float(380) #float(input("請輸入最終金額："))
    # flt_最小增加數量 = float(1) #float(input("請輸入最小增加單位："))
    # flt_下單數量等差參數 = float(1) #float(input("請輸入下單數量等差參數：")) #前一階單位數 + 本接單位數 = 此階單位數  
    # flt_下單數量等比參數 = float(1.5) # float(input("請輸入下單數量等比參數：")) ＃前一階單位數*等比參數 = 此階單位數
    # int_交易次數 = int(6) # int(input("請輸入交易次數："))
    # dic_等差金字塔下單資料 = get買入等差金字塔(flt_總預算,flt_起始價格, flt最終價格, int_交易次數, flt_最小增加數量, flt_下單數量等差參數, flt_起始單位數=1)
    # dic_等比金字塔下單資料 = get買入等比金字塔(flt_總預算,flt_起始價格, flt最終價格, int_交易次數, flt_最小增加數量, flt_下單數量等比參數, flt_起始單位數=1)
    pass