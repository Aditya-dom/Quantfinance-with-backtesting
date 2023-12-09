# Import necessary libraries
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Define parameters
num_headlines = 3  # the number of article headlines displayed per ticker
tickers = ['AAPL', 'TSLA', 'AMZN']  # list of tickers to analyze

# Get data from finviz website
finviz_url = 'https://finviz.com/quote.ashx?t='
news_tables = {}

for ticker in tickers:
    url = finviz_url + ticker
    req = Request(url=url, headers={'user-agent': 'my-app/0.0.1'})
    resp = urlopen(req)
    html = BeautifulSoup(resp, features="lxml")
    news_table = html.find(id='news-table')
    news_tables[ticker] = news_table

# Display recent news headlines for each ticker
try:
    for ticker in tickers:
        df = news_tables[ticker]
        df_tr = df.findAll('tr')

        print ('\n')
        print ('Recent News Headlines for {}: '.format(ticker))

        for i, table_row in enumerate(df_tr):
            a_text = table_row.a.text
            td_text = table_row.td.text.strip()
            print(a_text, '(', td_text, ')')
            if i == num_headlines - 1:
                break
except KeyError:
    pass

# Extract and parse news data
parsed_news = []
for ticker, news_table in news_tables.items():
    for row in news_table.findAll('tr'):
        text = row.a.get_text()
        date_scrape = row.td.text.split()

        if len(date_scrape) == 1:
            time = date_scrape[0]
        else:
            date = date_scrape[0]
            time = date_scrape[1]

        ticker_name = ticker.split('_')[0]
        parsed_news.append([ticker_name, date, time, text])

# Perform sentiment analysis
analyzer = SentimentIntensityAnalyzer()

# Create dataframe of news headlines with sentiment scores
columns = ['Ticker', 'Date', 'Time', 'Headline']
news = pd.DataFrame(parsed_news, columns=columns)
scores = news['Headline'].apply(analyzer.polarity_scores).tolist()
scores_df = pd.DataFrame(scores)

# Join sentiment scores to news dataframe
news = news.join(scores_df, rsuffix='_right')

# Convert date to datetime object and remove Headline column
news['Date'] = pd.to_datetime(news.Date).dt.date
news = news.drop(columns=['Headline'])

# Group news by ticker and calculate mean sentiment for each
unique_tickers = news['Ticker'].unique().tolist()
news_dict = {name: news.loc[news['Ticker'] == name] for name in unique_tickers}
mean_sentiments = []
for ticker in tickers:
    dataframe = news_dict[ticker]
    dataframe = dataframe.set_index('Ticker')
    mean = round(dataframe['compound'].mean(), 2)
    mean_sentiments.append(mean)

# Create and display dataframe of tickers with mean sentiment scores
sentiments_df = pd.DataFrame(list(zip(tickers, mean_sentiments)), columns=['Ticker', 'Mean Sentiment'])
sentiments_df = sentiments_df.set_index('Ticker')
sentiments_df = sentiments_df.sort_values('Mean Sentiment', ascending=False)
print ('\n')
print (sentiments_df)