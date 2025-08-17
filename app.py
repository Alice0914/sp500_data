import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 1rem 0;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# S&P 500 tickers
@st.cache_data
def get_sp500_tickers():
    """Function to fetch S&P 500 tickers"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        return table['Symbol'].tolist()
    except:
        # Fallback list if Wikipedia fails
        return [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH',
            'JNJ', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'ABBV', 'BAC', 'PFE',
            'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'WMT', 'DIS', 'ABT', 'MRK', 'VZ',
            'ADBE', 'NFLX', 'NKE', 'CRM', 'XOM', 'ACN', 'DHR', 'BMY', 'LIN', 'TXN',
            'ORCL', 'WFC', 'NEE', 'QCOM', 'PM', 'RTX', 'UPS', 'SBUX', 'T', 'LOW'
        ]

SP500_TICKERS = get_sp500_tickers()

def get_query_params():
    """Get current query parameters from URL"""
    try:
        ticker = st.query_params.get("ticker", "GOOGL")
        period = st.query_params.get("period", "1y")
    except Exception:
        ticker = "AAPL"
        period = "1y"
    
    return ticker, period

def update_ticker_in_url():
    """Update ticker in URL when selectbox changes"""
    try:
        selected_ticker = st.session_state.ticker_selectbox
        current_ticker, current_period = get_query_params()
        st.query_params.ticker = selected_ticker
        st.query_params.period = current_period
    except Exception:
        pass

def update_period_in_url():
    """Update period in URL when selectbox changes"""
    try:
        period_options = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
            "2 Years": "2y",
            "5 Years": "5y"
        }
        selected_period = period_options[st.session_state.period_selectbox]
        current_ticker, current_period = get_query_params()
        st.query_params.ticker = current_ticker
        st.query_params.period = selected_period
    except Exception:
        pass

@st.cache_data
def get_stock_data(ticker, period="1y"):
    """Function to fetch stock data"""
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period=period, interval="1d")
        return hist_data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

@st.cache_data
def get_financial_data(ticker):
    """Function to fetch financial data"""
    try:
        stock = yf.Ticker(ticker)
        
        # Safely get each financial statement
        def safe_get_data(func, default=pd.DataFrame()):
            try:
                data = func()
                return data if data is not None else default
            except:
                return default
        
        return {
            'financials': safe_get_data(lambda: stock.financials),
            'quarterly_financials': safe_get_data(lambda: stock.quarterly_financials),
            'income_stmt': safe_get_data(lambda: stock.income_stmt),
            'quarterly_income_stmt': safe_get_data(lambda: stock.quarterly_income_stmt),
            'balance_sheet': safe_get_data(lambda: stock.balance_sheet),
            'quarterly_balance_sheet': safe_get_data(lambda: stock.quarterly_balance_sheet),
            'cash_flow': safe_get_data(lambda: stock.cashflow),
            'quarterly_cash_flow': safe_get_data(lambda: stock.quarterly_cashflow),
            'actions': safe_get_data(lambda: stock.actions),
            'info': stock.info if hasattr(stock, 'info') else {}
        }
    except Exception as e:
        st.error(f"Error fetching financial data: {e}")
        return None

def plot_stock_price(hist_data, ticker):
    """Function to plot stock price chart"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{ticker} Stock Price', 'Trading Volume'),
        row_width=[0.2, 0.7]
    )
    
    # Stock price candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name="Stock Price"
        ),
        row=1, col=1
    )
    
    # Volume chart
    fig.add_trace(
        go.Bar(
            x=hist_data.index,
            y=hist_data['Volume'],
            name="Volume",
            marker_color='rgba(158,202,225,0.8)'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"{ticker} Stock Price and Volume",
        xaxis_rangeslider_visible=False,
        height=600
    )
    
    return fig

def plot_financial_metrics(financial_data, ticker):
    """Function to plot financial metrics"""
    if financial_data['income_stmt'].empty:
        return None
    
    # Revenue and net income trends
    income_stmt = financial_data['income_stmt']
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Annual Revenue Trend', 'Net Income Trend', 'Quarterly Revenue', 'Quarterly Net Income')
    )
    
    # Annual data
    if 'Total Revenue' in income_stmt.index:
        revenue = income_stmt.loc['Total Revenue']
        fig.add_trace(
            go.Bar(x=revenue.index, y=revenue.values, name="Annual Revenue"),
            row=1, col=1
        )
    
    if 'Net Income' in income_stmt.index:
        net_income = income_stmt.loc['Net Income']
        fig.add_trace(
            go.Bar(x=net_income.index, y=net_income.values, name="Annual Net Income"),
            row=1, col=2
        )
    
    # Quarterly data
    quarterly_income = financial_data['quarterly_income_stmt']
    if not quarterly_income.empty:
        if 'Total Revenue' in quarterly_income.index:
            q_revenue = quarterly_income.loc['Total Revenue']
            fig.add_trace(
                go.Bar(x=q_revenue.index, y=q_revenue.values, name="Quarterly Revenue"),
                row=2, col=1
            )
        
        if 'Net Income' in quarterly_income.index:
            q_net_income = quarterly_income.loc['Net Income']
            fig.add_trace(
                go.Bar(x=q_net_income.index, y=q_net_income.values, name="Quarterly Net Income"),
                row=2, col=2
            )
    
    fig.update_layout(height=600, title_text=f"{ticker} Financial Performance")
    return fig

def display_key_metrics(info):
    """Function to display key metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        market_cap = info.get('marketCap', 'N/A')
        if market_cap != 'N/A':
            market_cap = f"${market_cap:,.0f}"
        st.metric("Market Cap", market_cap)
        
        pe_ratio = info.get('trailingPE', 'N/A')
        if pe_ratio != 'N/A':
            pe_ratio = f"{pe_ratio:.2f}"
        st.metric("P/E Ratio", pe_ratio)
    
    with col2:
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
        if current_price != 'N/A':
            current_price = f"${current_price:.2f}"
        st.metric("Current Price", current_price)
        
        dividend_yield = info.get('dividendYield', 'N/A')
        if dividend_yield != 'N/A':
            dividend_yield = f"{dividend_yield*100:.2f}%"
        st.metric("Dividend Yield", dividend_yield)
    
    with col3:
        day_high = info.get('dayHigh', 'N/A')
        day_low = info.get('dayLow', 'N/A')
        if day_high != 'N/A' and day_low != 'N/A':
            day_range = f"${day_low:.2f} - ${day_high:.2f}"
        else:
            day_range = 'N/A'
        st.metric("Day Range", day_range)
        
        book_value = info.get('bookValue', 'N/A')
        if book_value != 'N/A':
            book_value = f"${book_value:.2f}"
        st.metric("Book Value", book_value)
    
    with col4:
        volume = info.get('volume', 'N/A')
        if volume != 'N/A':
            volume = f"{volume:,}"
        st.metric("Volume", volume)
        
        beta = info.get('beta', 'N/A')
        if beta != 'N/A':
            beta = f"{beta:.2f}"
        st.metric("Beta", beta)

def safe_display_dataframe(data, title, warning_msg):
    """Safely display dataframe with error handling"""
    try:
        if data is not None and not data.empty:
            if len(data.columns) > 0 and len(data.index) > 0:
                st.dataframe(data, use_container_width=True)
            else:
                st.warning(warning_msg)
        else:
            st.warning(warning_msg)
    except Exception as e:
        st.error(f"Error displaying {title}: {str(e)}")
        st.warning(f"Unable to display {title} data.")

def display_all_financial_data(financial_data):
    """Display all financial data in order"""
    
    # Annual Reports Section
    st.markdown('<div class="section-header">📅 Annual Reports</div>', unsafe_allow_html=True)
    
    # 1. Annual Financials
    st.subheader("📊 Annual Financial Statements")
    safe_display_dataframe(financial_data['financials'], "Annual Financials", "No annual financial data available.")
    st.markdown("---")
    
    # 2. Annual Income Statement
    st.subheader("💰 Annual Income Statement")
    safe_display_dataframe(financial_data['income_stmt'], "Annual Income Statement", "No Annual Income Statement data available.")
    st.markdown("---")
    
    # 3. Annual Balance Sheet
    st.subheader("⚖️ Annual Balance Sheet")
    safe_display_dataframe(financial_data['balance_sheet'], "Annual Balance Sheet", "No Annual Balance Sheet data available.")
    st.markdown("---")
    
    # 4. Annual Cash Flow
    st.subheader("💵 Annual Cash Flow")
    safe_display_dataframe(financial_data['cash_flow'], "Annual Cash Flow", "No Annual Cash Flow data available.")
    st.markdown("---")
    
    # Quarterly Reports Section
    st.markdown('<div class="section-header">📈 Quarterly Reports</div>', unsafe_allow_html=True)
    
    # 5. Quarterly Financials
    st.subheader("📈 Quarterly Financial Statements")
    safe_display_dataframe(financial_data['quarterly_financials'], "Quarterly Financials", "No quarterly financial data available.")
    st.markdown("---")
    
    # 6. Quarterly Income Statement
    st.subheader("💰 Quarterly Income Statement")
    safe_display_dataframe(financial_data['quarterly_income_stmt'], "Quarterly Income Statement", "No Quarterly Income Statement data available.")
    st.markdown("---")
    
    # 7. Quarterly Balance Sheet
    st.subheader("⚖️ Quarterly Balance Sheet")
    safe_display_dataframe(financial_data['quarterly_balance_sheet'], "Quarterly Balance Sheet", "No Quarterly Balance Sheet data available.")
    st.markdown("---")
    
    # 8. Quarterly Cash Flow
    st.subheader("💵 Quarterly Cash Flow")
    safe_display_dataframe(financial_data['quarterly_cash_flow'], "Quarterly Cash Flow", "No Quarterly Cash Flow data available.")

def main():
    # Get URL parameters
    url_ticker, url_period = get_query_params()
    
    # Validate parameters
    if url_ticker not in SP500_TICKERS:
        url_ticker = 'AAPL'
    
    # Header
    st.markdown('<h1 class="main-header">📈 Stock Analysis Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Comprehensive financial information and stock price analysis for S&P 500 companies.</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Settings")
        
        # Ticker selection with callback
        try:
            ticker_index = SP500_TICKERS.index(url_ticker)
        except ValueError:
            ticker_index = 0
            
        selected_ticker = st.selectbox(
            "Select S&P 500 Stock:",
            options=SP500_TICKERS,
            index=ticker_index,
            key="ticker_selectbox",
            on_change=update_ticker_in_url
        )
        
        # Period selection with callback
        period_options = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
            "2 Years": "2y",
            "5 Years": "5y"
        }
        
        # Find period index
        period_index = 3  # Default to "1 Year"
        for i, (name, value) in enumerate(period_options.items()):
            if value == url_period:
                period_index = i
                break
        
        selected_period_name = st.selectbox(
            "Analysis Period:",
            options=list(period_options.keys()),
            index=period_index,
            key="period_selectbox",
            on_change=update_period_in_url
        )
        selected_period = period_options[selected_period_name]
        
        # Analysis button
        analyze_button = st.button("🔍 Start Analysis", type="primary")
        
        # Display current URL info
        st.markdown("---")
        st.markdown("**Current Selection:**")
        st.write(f"Ticker: `{selected_ticker}`")
        st.write(f"Period: `{selected_period}`")
    
    # Always show data when a ticker is selected
    if selected_ticker:
        with st.spinner(f'Analyzing {selected_ticker} data...'):
            # Fetch stock data
            hist_data = get_stock_data(selected_ticker, selected_period)
            financial_data = get_financial_data(selected_ticker)
            
            if hist_data is not None and financial_data is not None:
                # Company information
                st.markdown('<div class="section-header">🏢 Company Information</div>', unsafe_allow_html=True)
                info = financial_data['info']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Company Name:** {info.get('longName', 'N/A')}")
                    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                    st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                    st.write(f"**Country:** {info.get('country', 'N/A')}")
                
                with col2:
                    st.write(f"**Employees:** {info.get('fullTimeEmployees', 'N/A'):,}" if info.get('fullTimeEmployees') else "**Employees:** N/A")
                    st.write(f"**Website:** {info.get('website', 'N/A')}")
                    st.write(f"**Founded:** {info.get('foundingYear', 'N/A')}")
                
                # Company description
                if 'longBusinessSummary' in info:
                    st.write("**Company Description:**")
                    st.write(info['longBusinessSummary'])
                    
                # Display key metrics
                st.markdown(f'<div class="section-header">📋 {selected_ticker} Key Metrics</div>', unsafe_allow_html=True)
                display_key_metrics(financial_data['info'])
                
                # Stock price chart
                st.markdown('<div class="section-header">📈 Stock Price Chart</div>', unsafe_allow_html=True)
                price_chart = plot_stock_price(hist_data, selected_ticker)
                st.plotly_chart(price_chart, use_container_width=True)
                
                # Financial performance chart
                st.markdown('<div class="section-header">💰 Financial Performance</div>', unsafe_allow_html=True)
                financial_chart = plot_financial_metrics(financial_data, selected_ticker)
                if financial_chart:
                    st.plotly_chart(financial_chart, use_container_width=True)
                
                # Display all financial data
                st.markdown('<div class="section-header">📊 Detailed Financial Data</div>', unsafe_allow_html=True)
                display_all_financial_data(financial_data)
                
                # Dividend and stock split information
                if not financial_data['actions'].empty:
                    st.markdown('<div class="section-header">💵 Dividends and Stock Splits</div>', unsafe_allow_html=True)
                    st.dataframe(financial_data['actions'], use_container_width=True)
            
            else:
                st.error("Unable to fetch data for the selected ticker. Please try selecting a different stock.")
    
    else:
        st.info("Please select an S&P 500 stock from the sidebar to begin analysis.")
    
    # Footer
    st.markdown("---")

if __name__ == "__main__":
    main()
