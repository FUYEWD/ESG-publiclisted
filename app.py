import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生警告訊息，這裡關閉
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv"

st.set_page_config(page_title="開放資料 CSV 檢視器", layout="wide")
st.title("📊 開放資料 CSV 檢視器")


@st.cache_data(ttl=3600, show_spinner="下載資料中...")
def load_data(url: str, verify_ssl: bool) -> tuple[pd.DataFrame, bytes]:
    """下載 CSV，回傳 (DataFrame, 原始 bytes)。"""
    response = requests.get(url, verify=verify_ssl, timeout=30)
    response.raise_for_status()
    content = response.content
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")  # 繁體中文
    return df, content


# ---------------- 側邊欄 ----------------
with st.sidebar:
    st.header("設定")
    url = st.text_input("CSV 連結", value=DEFAULT_URL)
    verify_ssl = st.checkbox("驗證 SSL 憑證 (verify)", value=False)
    drop_na = st.checkbox("移除含空值的列 (dropna)", value=True)
    if st.button("🔄 重新下載"):
        st.cache_data.clear()

# ---------------- 主畫面 ----------------
try:
    df, raw_bytes = load_data(url, verify_ssl)
except requests.RequestException as e:
    st.error(f"下載失敗：{e}")
    st.stop()
except Exception as e:
    st.error(f"讀取 CSV 失敗：{e}")
    st.stop()

if drop_na:
    df = df.dropna()

col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df):,}")
col2.metric("欄位數", len(df.columns))

keyword = st.text_input("🔍 關鍵字搜尋（搜尋所有欄位）")
if keyword:
    mask = df.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, na=False)
    ).any(axis=1)
    df = df[mask]
    st.caption(f"符合 {len(df):,} 筆")

st.dataframe(df, use_container_width=True)

st.download_button(
    "⬇️ 下載目前表格 (CSV)",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="data01.csv",
    mime="text/csv",
)
