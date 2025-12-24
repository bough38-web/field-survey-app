import streamlit as st
import pandas as pd
from io import StringIO
from storage import save_targets, normalize_owner_column

st.title("📋 조사 대상 업로드")

method = st.radio(
    "데이터 반영 방법",
    ["파일 업로드", "엑셀 복사 붙여넣기"]
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

if method == "파일 업로드":
    file = st.file_uploader("엑셀 또는 CSV", type=["xlsx", "csv"])
    if file:
        df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
        df = normalize_columns(df)
        df = normalize_owner_column(df)
        df["계약번호"] = df["계약번호"].astype(str)
        save_targets(df)
        st.success("업로드 완료")
        st.dataframe(df.head())

else:
    pasted = st.text_area("엑셀 붙여넣기", height=250)
    if pasted.strip():
        df = pd.read_csv(StringIO(pasted), sep="\t")
        df = normalize_columns(df)
        df = normalize_owner_column(df)
        df["계약번호"] = df["계약번호"].astype(str)
        save_targets(df)
        st.success("붙여넣기 완료")
        st.dataframe(df.head())
