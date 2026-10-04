import streamlit as st
import pandas as pd
import ccxt

# Sayfa Yapılandırması
st.set_page_config(page_title="ADEM YATIRIM AI", page_icon="📈", layout="wide")

# Başlık ve Marka
st.title("🤖 ADEM YATIRIM AI - Akıllı Kripto İstasyonu")
st.markdown("Piyasaları tarayan, yapay zeka tabanlı sinyaller üreten ve cüzdanınızı anlık takip eden akıllı asistanınız.")

# Sekmeler (Tabs) Oluşturma
tab1, tab2 = st.tabs(["📊 Piyasa Analizi ve Sinyaller", "💼 Cüzdan ve Portföy Takibi"])

# --- TAB 1: PİYASA ANALİZİ VE SİNYALLER ---
with tab1:
    st.sidebar.header("⚙️ Piyasa Ayarları")
    exchange_name = st.sidebar.selectbox("Borsa", ["binance"], key="ex_1")
    symbol = st.sidebar.selectbox("Parite", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"], key="sym_1")
    timeframe = st.sidebar.selectbox("Zaman Dilimi", ["1h", "4h", "1d"], key="tf_1")

    @st.cache_data(ttl=60)
    def fetch_advanced_data(ex_name, sym, tf):
        try:
            exchange = getattr(ccxt, ex_name)()
            ohlcv = exchange.fetch_ohlcv(sym, timeframe=tf, limit=120)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            return pd.DataFrame()

    df = fetch_advanced_data(exchange_name, symbol, timeframe)

    if not df.empty:
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        price_change = ((current_price - prev_price) / prev_price) * 100

        # Teknik İndikatörler
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (std * 2)

        r_val = df['RSI'].iloc[-1]
        b_upper = df['BB_Upper'].iloc[-1]
        b_lower = df['BB_Lower'].iloc[-1]

        # Üst Bilgi Kartları
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Anlık Fiyat", f"${current_price:,.2f}", f"{price_change:.2f}%")
        c2.metric("RSI (14)", f"{r_val:.2f}")
        c3.metric("Bollinger Üst", f"${b_upper:,.2f}")
        c4.metric("Bollinger Alt", f"${b_lower:,.2f}")

        # Karar Matrisi
        st.subheader("🎯 ADEM YATIRIM AI - Karar Matrisi")
        score = 0
        reasons = []

        if r_val < 35:
            score += 2
            reasons.append("RSI aşırı satım bölgesinde (Fiyat cazip).")
        elif r_val > 65:
            score -= 2
            reasons.append("RSI aşırı alım bölgesinde (Dikkatli olunmalı).")

        if current_price <= b_lower * 1.01:
            score += 2
            reasons.append("Fiyat alt Bollinger bandına temas etti (Destek).")
        elif current_price >= b_upper * 0.99:
            score -= 2
            reasons.append("Fiyat üst Bollinger bandına dayandı (Direnç).")

        if score >= 2:
            action = "GÜÇLÜ AL"
            color = "green"
            stop_loss = current_price * 0.97
            take_profit = current_price * 1.06
        elif score <= -2:
            action = "GÜÇLÜ SAT / KÂR AL"
            color = "red"
            stop_loss = 0
            take_profit = 0
        else:
            action = "BEKLE (PİYASA NÖTR)"
            color = "orange"
            stop_loss = current_price * 0.98
            take_profit = current_price * 1.03

        st.markdown(f"### Tavsiye Edilen Aksiyon: <span style='color:{color}'>{action}</span>", unsafe_allow_html=True)
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.info(f"**Önerilen Stop-Loss:** ${stop_loss:,.2f}")
        with col_r2:
            st.success(f"**Önerilen Take-Profit:** ${take_profit:,.2f}")

        with st.expander("🔍 Analiz Gerekçeleri"):
            for r in reasons:
                st.write(f"- {r}")

        st.subheader("📊 Fiyat ve Bollinger Bantları")
        st.line_chart(df.set_index('timestamp')[['close', 'BB_Upper', 'BB_Middle', 'BB_Lower']])
    else:
        st.warning("Veriler yüklenemedi.")

# --- TAB 2: CÜZDAN VE PORTFÖY TAKİBİ ---
with tab2:
    st.header("💼 ADEM YATIRIM AI - Canlı Portföy Yönetimi")
    st.markdown("Elindeki varlıkları aşağıya gir, anlık piyasa fiyatlarıyla toplam değerini ve kar/zarar durumunu takip et.")

    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        btc_amount = st.number_input("Bitcoin (BTC) Miktarın", min_value=0.0, value=0.1, step=0.01)
    with col_w2:
        eth_amount = st.number_input("Ethereum (ETH) Miktarın", min_value=0.0, value=1.0, step=0.1)
    with col_w3:
        usdt_amount = st.number_input("Nakit USDT Miktarın", min_value=0.0, value=500.0, step=50.0)

    # Anlık fiyatları Binance'den çekelim
    try:
        ex = ccxt.binance()
        btc_ticker = ex.fetch_ticker('BTC/USDT')['last']
        eth_ticker = ex.fetch_ticker('ETH/USDT')['last']
    except:
        btc_ticker = 65000.0  # Hata durumunda geçici yedek fiyat
        eth_ticker = 35000.0

    # Hesaplamalar
    btc_value = btc_amount * btc_ticker
    eth_value = eth_amount * eth_ticker
    total_portfolio_value = btc_value + eth_value + usdt_amount

    st.divider()
    
    p1, p2, p3 = st.columns(3)
    p1.metric("BTC Varlık Değeri", f"${btc_value:,.2f}", f"Birim: ${btc_ticker:,.2f}")
    p2.metric("ETH Varlık Değeri", f"${eth_value:,.2f}", f"Birim: ${eth_ticker:,.2f}")
    p3.metric("Toplam Portföy Değeri", f"${total_portfolio_value:,.2f}")

    st.success("💡 **İpucu:** Bu cüzdan sekmesi, girdiğin miktarları anlık borsa fiyatlarıyla otomatik çarparak toplam servetini saniyesinde hesaplar.")