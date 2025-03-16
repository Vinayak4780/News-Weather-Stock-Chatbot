import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import re
import urllib.parse
from datetime import datetime
import pytz
def get_news(count=5):
    feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
    return [(entry.title, entry.link) for entry in feed.entries[:count]]

def get_news_insights(news_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(news_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    insights = " ".join([p.text for p in paragraphs[:3]])
    return insights if insights else "No insights available."

def get_nse_stock_price(stock_symbol):
    try:
        # Create a session to bypass NSE's security
        session = requests.Session()

        # First request to NSE homepage to get session cookies
        session.get("https://www.nseindia.com", headers={"User-Agent": "Mozilla/5.0"})

        # NSE India API URL
        nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={stock_symbol.upper()}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com"
        }

        # Fetch stock data with session
        response = session.get(nse_url, headers=headers, timeout=5)

        # Check if request is successful
        if response.status_code != 200:
            return f"❌ Error: Could not retrieve stock data for '{stock_symbol}'."

        data = response.json()
        if "priceInfo" not in data:
            return f"❌ Stock price not found for '{stock_symbol}'."

        # Extract stock price & change
        stock_price = data["priceInfo"]["lastPrice"]
        prev_close = data["priceInfo"]["previousClose"]
        price_change = stock_price - prev_close
        percent_change = (price_change / prev_close) * 100

        # Add sign (↑ or ↓) based on change
        change_sign = "↑" if price_change > 0 else "↓" if price_change < 0 else "→"

        return (f"📈 {stock_symbol.upper()} Stock Price: ₹{stock_price}\n"
                f"📉 1-Day Change: {change_sign} ₹{abs(price_change):.2f} ({change_sign} {abs(percent_change):.2f}%)")

    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"

def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=%C|🌡️ Temperature: %t|💧 Humidity: %h|💨 Wind: %w"
        response = requests.get(url)

        if response.status_code == 200 and response.text.strip():
            # Decode special characters (fixes %20, %25 issues)
            weather_data = urllib.parse.unquote(response.text.strip())

            # Extract parts of the weather report
            parts = weather_data.split("|")
            weather_condition = parts[0].strip()
            temperature = parts[1].replace("🌡️ Temperature:", "").strip()
            humidity = parts[2].replace("💧 Humidity:", "").strip()
            wind = parts[3].replace("💨 Wind:", "").strip()

            # Determine if it's day or night using the city's timezone
            try:
                city_timezone = pytz.timezone(f"Asia/Kolkata")  # Default to IST for Indian cities
                current_hour = datetime.now(city_timezone).hour
                if 6 <= current_hour < 18:
                    time_symbol = "🌞"  # Daytime
                else:
                    time_symbol = "🌙"  # Nighttime
            except Exception:
                time_symbol = "🌤️"  

            return (f"{time_symbol} {weather_condition}\n"
                    f"🌡️ **Temperature:** {temperature}\n"
                    f"💧 **Humidity:** {humidity}\n"
                    f"💨 **Wind:** {wind}")

        else:
            return "❌ Could not retrieve weather data. Please check the city name."

    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {e}"


def get_currency_rate(from_currency, to_currency):
    url = f"https://www.x-rates.com/calculator/?from={from_currency}&to={to_currency}&amount=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    rate = soup.find("span", class_="ccOutputTrail").previous_sibling
    return rate.strip() if rate else "Exchange rate not found."

st.title("🤖 AI Chatbot")
st.write("Ask me about news, stocks, weather, Wikipedia, currency exchange, or sports scores.")

user_input = st.text_input("Enter your query:")
news_count = st.number_input("How many news articles do you want to see?", min_value=1, max_value=50, value=5)
if "history" not in st.session_state:
    st.session_state.history = []

if user_input:
    response = ""
    if "news" in user_input:
        st.subheader("📰 Latest News")
        news_list = get_news(news_count)
        response = "\n".join([f"- {title}" for title, _ in news_list]) 
        for idx, (title, link) in enumerate(news_list):
            st.write(f"- {title}")
            if st.button(f"See Insights for {title}", key=f"insights_{idx}"):
                st.subheader("🔍 News Insights")
                st.write(get_news_insights(link))
    elif "stock" in user_input.lower():
        stock_name = user_input.split("stock of")[-1].strip()
        st.subheader(f"📈 {stock_name.upper()} Stock Price") 
        response = get_nse_stock_price(stock_name)
        st.write(get_nse_stock_price(stock_name))
    elif "weather" in user_input.lower():
        city = user_input.split("weather")[-1].strip().replace("in", "").replace("of", "").replace("for", "").strip()
        if city:
            st.subheader(f"🌤️ Weather Report for {city.capitalize()}")
            response = get_weather(city)  
            st.write(get_weather(city))
    else:
        response = "❌ I didn't understand that. Try asking about news, weather, Wikipedia, or currency."
    if response:
        st.session_state.history.append((user_input, response))

st.subheader("📝 Previous Responses")
for query, res in st.session_state.history:
    st.markdown(f"**You:** {query}")
    st.markdown("**Bot:**")
    st.write(res) 
