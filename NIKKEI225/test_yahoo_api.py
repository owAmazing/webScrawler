import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://finance.yahoo.com/quote/%5EN225',
}
urls = [
    'https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EN225',
    'https://query1.finance.yahoo.com/v10/finance/quoteSummary/%5EN225?modules=summaryDetail,defaultKeyStatistics,financialData',
    'https://query1.finance.yahoo.com/v10/finance/quoteSummary/%5EN225?modules=defaultKeyStatistics',
]
for url in urls:
    r = requests.get(url, headers=headers, timeout=20)
    print('URL:', url)
    print('Status:', r.status_code)
    if r.status_code == 200:
        try:
            data = r.json()
            print('keys:', list(data.keys())[:10])
            print(json.dumps(data, indent=2)[:1200])
        except Exception as e:
            print('json err', e)
    else:
        print('text snippet:', r.text[:200])
    print('====')
