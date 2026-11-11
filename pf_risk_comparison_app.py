import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="PF 위험 부담 비교 모형", page_icon="🏗️", layout="wide")

st.title("부동산 PF 자금 조달 및 손실 부담 비교")
st.caption("자기자본 비율과 분양수입 감소에 따라 시행사와 대주단의 손실 부담이 어떻게 달라지는지 살펴보는 단순 모형입니다.")

st.info(
    "모형의 가정: 총사업비는 자기자본과 대출로 조달하며, 사업 종료 시 분양수입으로 대출 원금을 먼저 상환하고 "
    "남는 금액을 자기자본에 배분한다고 가정합니다. 따라서 사업 손실은 자기자본이 먼저 흡수하고, "
    "자기자본을 초과하는 부족액은 대주단의 손실로 표시합니다. 실제 PF의 계약·담보·보증 구조를 모두 반영한 것은 아닙니다."
)

left, right = st.columns(2)
with left:
    total_cost = st.number_input("총사업비 (억 원)", min_value=100, max_value=100000, value=1000, step=100)
    expected_revenue = st.number_input("예상 분양수입 (억 원)", min_value=100, max_value=200000, value=1200, step=50)
with right:
    decline_pct = st.slider("분양수입 감소율 (%)", min_value=0, max_value=60, value=25, step=5)
    selected_ratio = st.slider("개별 사업의 자기자본 비율 (%)", min_value=5, max_value=40, value=10, step=5)

actual_revenue = expected_revenue * (1 - decline_pct / 100)
project_result = actual_revenue - total_cost

st.subheader("선택한 조건의 분석")
m1, m2, m3 = st.columns(3)
m1.metric("감소 후 분양수입", f"{actual_revenue:,.0f}억 원")
m2.metric("사업 손익", f"{project_result:+,.0f}억 원")
m3.metric("자기자본 비율", f"{selected_ratio}%")

def calculate(ratio):
    equity = total_cost * ratio / 100
    debt = total_cost - equity
    # 사업 수입에서 대출 원금을 먼저 상환하고 잔여액을 자기자본에 배분하는 단순 가정
    lender_recovery = min(actual_revenue, debt)
    lender_loss = max(debt - actual_revenue, 0)
    equity_recovery = max(actual_revenue - debt, 0)
    equity_loss = max(equity - equity_recovery, 0)
    return {
        "자기자본 비율": f"{ratio}%",
        "자기자본": equity,
        "외부 차입금": debt,
        "자기자본 회수액": equity_recovery,
        "자기자본 손실": equity_loss,
        "대주단 손실": lender_loss,
        "대주단 손실률": lender_loss / debt * 100 if debt else 0
    }

ratios = [5, 10, 20, 30, 40]
rows = [calculate(r) for r in ratios]
df = pd.DataFrame(rows)

selected = calculate(selected_ratio)
c1, c2, c3 = st.columns(3)
c1.metric("시행사 자기자본 손실", f"{selected['자기자본 손실']:,.0f}억 원")
c2.metric("대주단 원금 손실", f"{selected['대주단 손실']:,.0f}억 원")
c3.metric("대주단 손실률", f"{selected['대주단 손실률']:.1f}%")

st.subheader("자기자본 비율별 손실 부담 비교")
st.write("같은 사업비와 같은 분양수입 감소 상황에서 자기자본 비율만 바꾸어 비교합니다.")
display_df = df[["자기자본 비율", "자기자본", "외부 차입금", "자기자본 손실", "대주단 손실", "대주단 손실률"]].copy()
for col in ["자기자본", "외부 차입금", "자기자본 손실", "대주단 손실"]:
    display_df[col] = display_df[col].map(lambda x: f"{x:,.0f}억")
display_df["대주단 손실률"] = display_df["대주단 손실률"].map(lambda x: f"{x:.1f}%")
st.dataframe(display_df, use_container_width=True, hide_index=True)

chart_left, chart_right = st.columns(2)
with chart_left:
    st.markdown("**자기자본 비율에 따른 대주단 손실**")
    fig, ax = plt.subplots(figsize=(7, 4))
    lender_losses = [r["대주단 손실"] for r in rows]
    ax.bar([r["자기자본 비율"] for r in rows], lender_losses)
    ax.set_xlabel("자기자본 비율")
    ax.set_ylabel("대주단 손실 (억 원)")
    ax.set_title("Lender Loss by Equity Ratio")
    ax.grid(axis="y", alpha=0.25)
    st.pyplot(fig)
    plt.close(fig)

with chart_right:
    st.markdown("**선택한 비율의 자금 조달 구조**")
    fig, ax = plt.subplots(figsize=(7, 4))
    equity = total_cost * selected_ratio / 100
    debt = total_cost - equity
    ax.bar(["자금 조달"], [equity], label="자기자본")
    ax.bar(["자금 조달"], [debt], bottom=[equity], label="외부 차입금")
    ax.set_ylabel("금액 (억 원)")
    ax.set_title(f"Funding Structure ({selected_ratio}% Equity)")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    st.pyplot(fig)
    plt.close(fig)

st.subheader("해석할 때 주의할 점")
st.markdown(
    """
    - 자기자본 비율이 높아지면 같은 사업비에서 외부 차입금 규모가 줄어듭니다.
    - 이 모형에서는 자기자본을 먼저 손실 흡수 재원으로 가정하므로, 자기자본이 클수록 대주단에 손실이 전가되기 시작하는 지점이 늦어집니다.
    - 그러나 사업 자체의 손실액이 자동으로 줄어드는 것은 아닙니다. 손실을 누가 부담하는지가 달라지는 것입니다.
    - 실제 PF에서는 담보권, 보증, 책임준공 약정, 이자, 공사비 증가, 분양대금 유입 시점 및 계약 조건에 따라 결과가 달라질 수 있습니다.
    """
)

st.caption("교육·탐구용 가상 모형입니다. 실제 사업의 부도 확률이나 금융기관의 실제 손실을 예측하는 도구가 아닙니다.")
