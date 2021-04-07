from flask import Flask, render_template, request
from value_estimator import parseStockTickers, StockInfo, DCFInfo, parse, dcf, Graham, graham, separateThousand, roundNumber
import html

app = Flask(__name__)

def getFormInput(request):
	ticker = request.form['stockTicker']
	if " - " in ticker:
		ticker = ticker.split(" ")[0]
	processed_ticker = html.escape(ticker.upper())
	print('ticker', processed_ticker)
	valuationTerm = request.form['valuationTerm']
	if valuationTerm:
		processed_term = int(valuationTerm)
	else:
		processed_term = 5
	print('term', processed_term)
	return {'ticker': processed_ticker, 'term': processed_term}

def getCurrency(financialInfo):
	if "millions" in financialInfo:
		factor = "millions "
	elif "billions" in financialInfo:
		factor = "billions "
	elif "thousands" in financialInfo:
		factor = "thousands"
	else:
		factor = None

	if factor:
		currency = financialInfo.split(factor)[1].split('.')[0]
	else:
		currency = ""

	return currency

@app.route("/", methods=['GET', 'POST'])
def homePage():
	globalErrorMessage = ""
	stockTickers = parseStockTickers()
	stockInfo = StockInfo()
	dcfInfo = DCFInfo()
	grahamInfo = Graham()
	if request.method == "POST":
		try:
			formInput = getFormInput(request)
			ticker = formInput['ticker']
			term = formInput['term']
			stockInfo = parse(ticker, term)
			dcfInfo = dcf(stockInfo)
			grahamInfo = graham(stockInfo)

			stockInfo.marketPrice = separateThousand(stockInfo.marketPrice)
			if (type(stockInfo.yahooFinanceInfo.marketCap) == int or type(stockInfo.yahooFinanceInfo.marketCap) == float) and stockInfo.yahooFinanceInfo.marketCap > 0: 
				stockInfo.yahooFinanceInfo.marketCap = separateThousand(roundNumber(stockInfo.yahooFinanceInfo.marketCap/1000000000, 0))
			dcfInfo.fairValue = separateThousand(dcfInfo.fairValue)
			grahamInfo.expectedValue = separateThousand(grahamInfo.expectedValue)
		except Exception as e:
			print(e)
			globalErrorMessage = "something went wrong"
			print(globalErrorMessage)
	ticker = stockInfo.ticker or ""
	financialInfo = stockInfo.financialInfo
	currency = getCurrency(financialInfo)
	errorMessage = stockInfo.errorMessage or dcfInfo.errorMessage or grahamInfo.errorMessage or globalErrorMessage
	return render_template("homepage.html", stockTickers= stockTickers, stockInfo = stockInfo, dcfInfo = dcfInfo, grahamInfo = grahamInfo, ticker = ticker, financialInfo = financialInfo, currency = currency, errorMessage = errorMessage)

if __name__ == "__main__":
	app.run()