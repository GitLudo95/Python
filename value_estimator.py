from lxml import html
import requests
import json
import argparse
from collections import OrderedDict
import re
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

class YahooFinanceInfo:
    def __init__(self, companyName="", trailingPE=0, marketCap=0, forwardPE=0, pegRatio=0, priceToSalesTrailing12Months=0, logoURL=""):
        self.companyName = companyName
        self.trailingPE = trailingPE
        self.marketCap = marketCap
        self.forwardPE = forwardPE
        self.pegRatio = pegRatio
        self.priceToSalesTrailing12Months = priceToSalesTrailing12Months
        self.logoURL = logoURL

class StockInfo:
    def __init__(self, ticker="", yahooFinanceInfo=YahooFinanceInfo(), freeCashFlow=0, financialInfo="", growthEstimate=0, years=0, eps=0, discountRate=0, perpetualRate=0, shares=0, marketPrice=0, errorMessage=""):
        self.ticker = ticker
        self.yahooFinanceInfo = yahooFinanceInfo
        self.freeCashFlow = freeCashFlow
        self.financialInfo = financialInfo
        self.growthEstimate = growthEstimate
        self.years = years
        self.eps = eps
        self.discountRate = discountRate
        self.perpetualRate = perpetualRate
        self.shares = shares
        self.marketPrice = marketPrice
        self.errorMessage = errorMessage

class DCFInfo:
    def __init__(self, forecastedCashflows="", presentValueOfCF=0, fairValue=0, errorMessage=""):
        self.forecastedCashflows = forecastedCashflows
        self.presentValueOfCF = presentValueOfCF
        self.fairValue = fairValue
        self.errorMessage = errorMessage

class Graham:
    def __init__(self, expectedValue=0, growthEstimatePricedIn=0, bondYield=0, errorMessage=""):
        self.expectedValue = expectedValue
        self.growthEstimatePricedIn = growthEstimatePricedIn
        self.bondYield = bondYield
        self.errorMessage = errorMessage

def separateThousand(num):
    if type(num) == int or type(num) == float: 
        return '{:,}'.format(num)
    else:
        return num

def roundNumber(num, decimals):
    if type(num) == int or type(num) == float: 
        return round(num, 2)
    else:
        try:
            return round(float(num), 2)
        except Exception:
            return num

def parseWACC(url):
    print("url", url)
    response = requests.get(url, verify=False)
    parser = html.fromstring(response.content)
    waccText = parser.cssselect('div[id="target_def_description"]')[0].text_content()
    wacc = re.findall('\d+\.\d+', waccText)[0]
    print(wacc)
    return float(wacc)

def parseFreeCashFlow(url):
    print("url", url)
    response = requests.get(url, verify=False)
    parser = html.fromstring(response.content)
    financialInfo = ""
    for div in parser.cssselect('.fint-info'):
        financialInfo = div.text_content()
    freeCashFlows = parser.xpath('//table[contains(@id,"fintable")]//tr[td/span/text()[contains(., "Free Cash Flow")]]')[0].xpath('.//td/text()')
    
    return float(freeCashFlows[0].replace(',', '')), financialInfo

def parseGrowthEstimate(url):
    print("url", url)
    response = requests.get(url, verify=False)
    parser = html.fromstring(response.content)
    growthEstimate = parser.xpath('//table//tbody//tr')

    for row in growthEstimate:
        label = row.xpath("td/span/text()")[0]
        if 'Next 5 years' in label:
            growthEstimate = float(row.xpath("td/text()")[0].replace('%', ''))
            break

    return growthEstimate

def parseShares(url):
    print("url", url)
    response = requests.get(url, verify=False)
    parser = html.fromstring(response.content)
    shares = parser.xpath('//div[@class="info"]//table//tbody//tr[td/text()[contains(., "Shares Out")]]')

    shares = shares[0].xpath('td/text()')[1]
    factor = 1000 if 'B' in shares else 1 
    return float(shares.replace('B', '').replace('M', '')) * factor

def parseEpsAndMarketPrice(url):
    print("url", url)
    response = requests.get(url, verify=False)
    parser = html.fromstring(response.content)
    eps = parser.xpath('//table[contains(@id,"fintable")]//tr[td/span/text()[contains(., "EPS (Diluted)")]]')[0].xpath('.//td/text()')
    eps = float(eps[0].replace(",", ""))
    marketPrice = float(parser.xpath('//div[@id="sp"]/span[@id="cpr"]/text()')[0].replace('$', '').replace(',', ''))
    return {'eps': eps, 'marketPrice': marketPrice}

def parseLogger(marketPrice, eps, growthEstimate, years, discountRate, perpetualRate):
    print("Market price: {}".format(marketPrice))
    print("EPS: {}".format(eps))
    print("Growth estimate: {}".format(growthEstimate))
    print("Term: {} years".format(years))
    print("Discount Rate: {}%".format(discountRate))
    print("Perpetual Rate: {}%\n".format(perpetualRate))

def parseCurrentAAABondYield(url):
    print("url", url)
    response = requests.get(url, verify=False)
    parser = html.fromstring(response.content)
    bondYieldText = parser.cssselect('.key-stat-title')[0].text_content()
    bondYield = re.findall('\d+\.\d+', bondYieldText)[0]
    print(bondYield)
    return float(bondYield)

def parse(ticker, years=5, discountRate=10, perpetualRate=3):
    errorMessage = ""
    yahooFinanceInfo = YahooFinanceInfo()

    try:
        tickerInfo = yf.Ticker(ticker)
        yahooFinanceInfo.companyName = tickerInfo.info['longName']
        yahooFinanceInfo.trailingPE = roundNumber(tickerInfo.info['trailingPE'], 2)
        yahooFinanceInfo.marketCap = roundNumber(tickerInfo.info['marketCap'], 2)
        yahooFinanceInfo.forwardPE = roundNumber(tickerInfo.info['forwardPE'], 2)
        yahooFinanceInfo.pegRatio = roundNumber(tickerInfo.info['pegRatio'], 2)
        yahooFinanceInfo.priceToSalesTrailing12Months = roundNumber(tickerInfo.info['priceToSalesTrailing12Months'], 2)
        yahooFinanceInfo.logoURL = tickerInfo.info['logo_url']
    except Exception as e:
        print(e)
        errorMessage = "Could not retrieve all information from Yahoo Finance"
        print(errorMessage)

    url = "https://www.gurufocus.com/term/wacc/{}/WACC-Percentage/".format(ticker)
    
    try:
        wacc = parseWACC(url)
        if (type(wacc) == int or type(wacc) == float) and wacc > 1 and wacc < 30:
            discountRate = wacc
    except Exception as e:
        print(e)
    url = "https://stockanalysis.com/stocks/{}/financials/cash-flow-statement".format(ticker)
    
    try:
        cashflowInfo = parseFreeCashFlow(url)
        last_freeCashFlow = cashflowInfo[0]
        financialInfo = cashflowInfo[1]
    except Exception as e:
        print(e)
        errorMessage = "An unexpected error occured during retrieval of latest cashflows"
        print(errorMessage)
        return StockInfo(ticker, yahooFinanceInfo, 0, "", 0, years, 0, discountRate, perpetualRate, 0, 0, errorMessage)

    print("Latest Free Cash Flow: {}".format(last_freeCashFlow))

    url = "https://in.finance.yahoo.com/quote/{}/analysis?p={}".format(ticker, ticker)
    
    try:
        growthEstimate = parseGrowthEstimate(url)
    except Exception as e:
        print(e)
        errorMessage = "An unexpected error occured during retrieval of growth estimate"
        print(errorMessage)
        return StockInfo(ticker, yahooFinanceInfo, last_freeCashFlow, financialInfo, 0, years, 0, discountRate, perpetualRate, 0, 0, errorMessage)

    url = "https://stockanalysis.com/stocks/{}/".format(ticker)
    
    try:
        shares = parseShares(url)
    except Exception as e:
        print(e)
        errorMessage = "An unexpected error occured during retrieval of outstanding shares"
        print(errorMessage)
        return StockInfo(ticker, yahooFinanceInfo, last_freeCashFlow, financialInfo, growthEstimate, years, 0, discountRate, perpetualRate, 0, 0, errorMessage)

    url = "https://stockanalysis.com/stocks/{}/financials/".format(ticker)
    
    try:
        data = parseEpsAndMarketPrice(url)
        eps = data['eps']
        marketPrice = data['marketPrice']
    except Exception as e:
        print(e)
        errorMessage = "An unexpected error occured during retrieval of EPS and market price"
        print(errorMessage)
        return StockInfo(ticker, yahooFinanceInfo, last_freeCashFlow, financialInfo, growthEstimate, years, 0, discountRate, perpetualRate, shares, 0, errorMessage)

    try:
        parseLogger(marketPrice, eps, growthEstimate, years, discountRate, perpetualRate)
    except Exception as e:
        print(e)
        print("Logging failure")

    return StockInfo(ticker, yahooFinanceInfo, last_freeCashFlow, financialInfo, growthEstimate, years, eps, discountRate, perpetualRate, shares, marketPrice, errorMessage)

def dcfLogger(forecastedCashflows, presentValueOfCF, fairValue):
    print("Forecasted cashflows: {}".format(forecastedCashflows))
    print("Present value of cashflows: {}".format(presentValueOfCF))
    print("Fair value: {}".format(fairValue))

def dcf(data):
    forecast = [data.freeCashFlow]

    try:
        for i in range(1, data.years):
            forecast.append(round(forecast[-1] + (data.growthEstimate / 100) * forecast[-1], 2))

        forecast.append(round(forecast[-1] * (1 + (data.perpetualRate / 100)) / (data.discountRate / 100 - data.perpetualRate / 100), 2)) #terminal value
        discount_factors = [1 / (1 + (data.discountRate / 100))**(i + 1) for i in range(len(forecast) - 1)]

        pvs = [round(f * d, 2) for f, d in zip(forecast[:-1], discount_factors)]
        pvs.append(round(discount_factors[-1] * forecast[-1], 2)) # discounted terminal value

        formattedForecast = map(separateThousand, forecast)
        formattedPvs = map(separateThousand, pvs)
    
        forecastedCashflows = ", ".join(map(str, formattedForecast)) + " (Terminal value)"
        presentValueOfCF = ", ".join(map(str, formattedPvs)) + " (Terminal value)"

        dcf = sum(pvs)
    except Exception as e:
        print(e)
        errorMessage = "An unexpected error occured in the DCF model calculations"
        print(errorMessage)
        return DCFInfo("", 0, 0, errorMessage)

    if dcf > 0:
        fairValue = round((dcf / data.shares), 2)
    else:
        fairValue = round((0), 2)

    dcfLogger(forecastedCashflows, presentValueOfCF, fairValue)

    return DCFInfo(forecastedCashflows, presentValueOfCF, fairValue, "")

def graham(data):
    url = "https://ycharts.com/indicators/moodys_seasoned_aaa_corporate_bond_yield"
    try:
        bondYield = parseCurrentAAABondYield(url)
        if (type(bondYield) != int and type(bondYield) != float) or bondYield < 1 or bondYield > 30:
            bondYield = 3.5 # 5 year average
    except Exception as e:
        print(e)
        bondYield = 3.5 # 5 year average
    if data.eps > 0:
        try:
            expectedValue = round((data.eps * (8.5 + 2 * data.growthEstimate) * 4.4 ) / bondYield, 2)
            growthEstimatePricedIn = round((data.marketPrice / data.eps - 8.5) / 2, 2)
        except Exception as e:
            print(e)
            errorMessage = "An unexpected error occured during graham style valuation"
            print(errorMessage)
            return Graham(0, 0, bondYield, errorMessage)

        print("Expected value based on growth rate: {}".format(expectedValue))
        print("Growth rate priced in for next 7-10 years: {}\n".format(growthEstimatePricedIn))
    else:
        notApplicableString = "N/A since EPS is negative"
        expectedValue = notApplicableString
        growthEstimatePricedIn = notApplicableString
        print(notApplicableString)
    return Graham(expectedValue, growthEstimatePricedIn, bondYield, "")

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('ticker', help='')
    args = argparser.parse_args()
    ticker = args.ticker
    print("Fetching data for %s...\n" % (ticker))
    data = parse(ticker)
    if data.errorMessage == "":
        print("=" * 80)
        print("DCF model (basic)")
        print("=" * 80 + "\n")
        dcf(data)
        print("=" * 80)
        print("Graham style valuation basic (Page 295, The Intelligent Investor)")
        print("=" * 80 + "\n")
        graham(data)