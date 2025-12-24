import streamlit as st
import pandas as pd
from io import StringIO
from storage import save_targets

st.title("📋 조사 대상 반영")

method = st.radio(
    "데이터 반영 방법 선택",
    ["파일 업로드", "엑셀에서 복사하여 붙여넣기"]
)

def normalize_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("_", "")
        .str.strip()
    )
    return df.rename(columns={
        "세부해지사유및불만내용": "세부내용"
    })

# =========================
# 파일 업로드
# =========================
if method == "파일 업로드":
    uploaded = st.file_uploader("엑셀 또는 CSV 업로드", type=["xlsx", "csv"])
    if uploaded:
        df = pd.read_excel(uploaded) if uploaded.name.endswith("xlsx") else pd.read_csv(uploaded)
        df = normalize_columns(df)
        df["계약번호"] = df["계약번호"].astype(str)
        save_targets(df)
        st.success("업로드 데이터가 반영되었습니다.")
        st.dataframe(df.head())

# =========================
# 엑셀 붙여넣기
# =========================
else:
    st.info("엑셀에서 복사(Ctrl+C) 후 아래에 붙여넣기(Ctrl+V)")
    pasted = st.text_area(
        "엑셀 데이터 붙여넣기",
        height=250,
        placeholder="관리지사\이름(담당자)t계약번호\t상호\t해지사유\t불만유형\t세부 해지사유 및 불만 내용"
    )

    if pasted.strip():
        df = pd.read_csv(StringIO(pasted), sep="\t")
        df = normalize_columns(df)
        df["계약번호"] = df["계약번호"].astype(str)
        save_targets(df)
        st.success("붙여넣은 데이터가 반영되었습니다.")
        st.dataframe(df.head())
