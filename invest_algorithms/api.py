from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import confs as cfg
import loggingsys
import algo_pyramid


log = loggingsys.generate_general_my_log(log_name=__name__,
                                        log_level=cfg.GLOBAL_LOG_LEVEL,
                                        interval="d")

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    # Explicit allowlist from API_CORS_ORIGINS; empty means no cross-origin access.
    # Credentials are disabled because the API is stateless (no cookies/auth),
    # which also avoids the invalid "*" + allow_credentials combination.
    allow_origins=cfg.lst_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
@app.get("/")
def read_api_root():    
    return cfg.dic_api

@app.get("/api/pyramidArithmetic")
def get_pyramid_arithmetic(
                    fltBudget:float,
                    fltPriceInit:float, 
                    fltPriceFinal:float, 
                    intTransactionTimes:int=10, 
                    fltIncrementAmountMinimum:float=1.0, 
                    fltOrderAmountArithmeticParam:float=2.0, 
                    fltOrderAmountInit:float=1.0,
                    toCsv:bool=True
                )->dict:    
    """
    等差金字塔 <br>
    :param fltBudget:(下單)總預算 <br>
    :param fltPriceInit:觸發股價(為規則開始計算的最高點, 並非開始買入的最高點股價),e.g. 0050股價 130 才開始觸發此條件<br>
    :param fltPriceFinal:終止股價(最後買入的最低點股價),e.g. 0050股價 80 <br>
    :param intTransactionTimes:預計交易次數(分成幾次下單),預設10次 <br>
    :param fltIncrementAmountMinimum:最小單位(股),預設1(e.g.0.01股, 1股, 5股, or 1000股) <br>
    :param fltOrderAmountArithmeticParam: 下單數量等差參數,預設2 <br>
      金字塔放大倍數 = 總預算 / 單位等差金字塔下單資料["總金額"] <br>
      本階單位數 = (起始單位數 + (下單數量等差參數 * i) ) * 金字塔放大倍數 e.g. 1 <br>
    :param fltOrderAmountInit=1.0: 第一張單起始單位數,預設1股 <br>
    :param toCsv: 是否輸出csv檔案, 預設 true 為 輸出csv (編碼為UTF-8;Excel預設開啟為Big5,請載入時自行調整) <br>
    :return: e.g.    	
    {
    "各階資料": [
            {
            "階": 1,
            "價格": 390,
            "單位數": 14,
            "金額": 5460,
            "百分比": 5.46,
            "累計百分比": 5.46,
            "累計下跌百分比": 2.5
            },
            {
            "階": 2,
            "價格": 380,
            "單位數": 34,
            "金額": 12920,
            "百分比": 12.91,
            "累計百分比": 18.37,
            "累計下跌百分比": 7.5
            },
            {
            "階": 3,
            "價格": 370,
            "單位數": 55,
            "金額": 20350,
            "百分比": 20.34,
            "累計百分比": 38.71,
            "累計下跌百分比": 15
            },
            {
            "階": 4,
            "價格": 360,
            "單位數": 76,
            "金額": 27360,
            "百分比": 27.35,
            "累計百分比": 66.06,
            "累計下跌百分比": 25
            },
            {
            "階": 5,
            "價格": 350,
            "單位數": 97,
            "金額": 33950,
            "百分比": 33.94,
            "累計百分比": 100,
            "累計下跌百分比": 37.5
            }
        ],
        "總投入金額": 100040,
        "起始價格": 400,
        "平均成本": 362.46,
        "累計數量": 276,
        "最終價格": 350,
        "累計下跌百分比": 37.5
    }
    """
    try:
        
        dic_ret = algo_pyramid.get買入等差金字塔(fltBudget,#flt_總預算
                                            fltPriceInit, #flt_起始價格
                                            fltPriceFinal, #flt最終價格
                                            intTransactionTimes, #int_交易次數
                                            fltIncrementAmountMinimum, #flt_最小增加數量
                                            fltOrderAmountArithmeticParam,  #flt_下單數量等差參數
                                            flt_起始單位數=fltOrderAmountInit)#flt_起始單位數
        if not toCsv:
            return dic_ret
        else:                        
            file_path,fname = algo_pyramid.金字塔資料轉csv(dic_ret)
            return FileResponse(path=file_path, filename=fname)
            

    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameters for pyramid calculation.",
        )

@app.get("/api/pyramidGeometric")
def get_pyramid_geometric(
                    fltBudget:float,
                    fltPriceInit:float, 
                    fltPriceFinal:float, 
                    intTransactionTimes:int=10, 
                    fltIncrementAmountMinimum:float=1.0, 
                    fltOrderAmountGeometicParam:float=2.0, 
                    fltOrderAmountInit:float=1.0,
                    toCsv:bool=True
                )->dict:    
    """
    等比金字塔 <br>
    :param fltBudget:(下單)總預算 <br>
    :param fltPriceInit:觸發股價(為規則開始計算的最高點, 並非開始買入的最高點股價),e.g. 0050股價 130 才開始觸發此條件<br>
    :param fltPriceFinal:終止價格(最後買入的最低點股價),e.g. 0050股價 80 <br>
    :param intTransactionTimes:預計交易次數(分成幾次下單),預設10次 <br>
    :param fltIncrementAmountMinimum:最小單位(股),預設1(e.g.0.01股, 1股, 5股, or 1000股) <br>
    :param fltOrderAmountGeometicParam:等比增量算式參數,預設2倍 <br>
      金字塔放大倍數 = 總預算 / 單位等差金字塔下單資料["總金額"] <br>
      本階單位數 = (起始單位數 * (下單數量等比參數^第i階次方) ) * 金字塔放大倍數 <br>
    :param fltOrderAmountInit:起始單位數,預設1股 <br>
    :param toCsv: 是否輸出csv檔案, 預設 true 為 輸出csv (編碼為UTF-8;Excel預設開啟為Big5,請載入時自行調整) <br>
    :return: e.g.
        "各階資料": [{
            "1": {
                "價格": 480,
                "單位數": 18,
                "金額": 8640,
                "百分比": 8.652112958141398
            },
            "2": {
                "價格": 460,
                "單位數": 27,
                "金額": 12420,
                "百分比": 12.43741237732826
            },
            "3": {
                "價格": 440,
                "單位數": 40,
                "金額": 17600,
                "百分比": 17.624674544362108
            },
            "4": {
                "價格": 420,
                "單位數": 60,
                "金額": 25200,
                "百分比": 25.235329461245744
            },
            "5": {
                "價格": 400,
                "單位數": 90,
                "金額": 36000,
                "百分比": 36.05047065892249
            },
        ],
          "總投入金額": 100040,
        "起始價格": 400,
        "平均成本": 362.46,
        "累計數量": 276,
        "最終價格": 350,
        "累計下跌百分比": 37.5
        }

    """
    try:
        dic_ret = algo_pyramid.get買入等比金字塔(fltBudget,
                                        fltPriceInit, 
                                        fltPriceFinal, 
                                        intTransactionTimes, 
                                        fltIncrementAmountMinimum, 
                                        fltOrderAmountGeometicParam, 
                                        flt_起始單位數=fltOrderAmountInit)
        if not toCsv:
            return dic_ret
        else:                        
            file_path,fname = algo_pyramid.金字塔資料轉csv(dic_ret)
            return FileResponse(path=file_path, filename=fname)
          

    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameters for pyramid calculation.",
        )
