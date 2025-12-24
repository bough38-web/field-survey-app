import streamlit as st
import pandas as pd
from io import StringIO
from storage import match_branch_owner, save_targets

st.title("📋 조사 대상 반영")

method = st.radio(
    "데이터 반영 방법 선택",
    ["파일 업로드", "엑셀에서 복사하여 붙여넣기"]
)

# =========================
# A. 파일 업로드
# =========================
if method == "파일 업로드":
    uploaded = st.file_uploader(
        "엑셀 또는 CSV 업로드",
        type=["xlsx", "csv"]
    )

    if uploaded:
        df = (
            pd.read_csv(uploaded)
            if uploaded.name.endswith(".csv")
            else pd.read_excel(uploaded)
        )

        df.columns = df.columns.str.strip()
        df["계약번호"] = df["계약번호"].astype(str)

        df = match_branch_owner(df)
        save_targets(df)

        st.success("파일 업로드 데이터가 반영되었습니다.")
        st.dataframe(df.head())

# =========================
# ⭐ B. 엑셀 붙여넣기
# =========================
else:
    st.info("엑셀에서 복사(Ctrl+C) 후 아래에 붙여넣기(Ctrl+V) 하세요.")

    pasted = st.text_area(
        "엑셀 데이터 붙여넣기",
        height=220,
        placeholder="관리지사\t계약번호\t상호\n중앙지사\t12345\tOO상사"
    )

    if pasted.strip():
        df = pd.read_csv(StringIO(pasted), sep="\t")
        df.columns = df.columns.str.strip()
        df["계약번호"] = df["계약번호"].astype(str)

        df = match_branch_owner(df)
        save_targets(df)

        st.success("붙여넣은 엑셀 데이터가 반영되었습니다.")
        st.dataframe(df.head())
