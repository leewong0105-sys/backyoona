# main.py
# 🧓🏻 전국 시군구별 고령화율을 귀엽고 통통 튀게 보여주는 Streamlit 앱

import gzip
import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="전국 고령화 톡톡 지도",
    page_icon="🧓🏻",
    layout="wide",
    initial_sidebar_state="collapsed",
)


POPULATION_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/"
    "data/population_yearly.csv.gz"
)

GEOJSON_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/"
    "data/boundaries/sigungu_kr.geojson"
)


# ---------------------------------------------------------
# 지도 색상
# ---------------------------------------------------------

COLORS = [
    "#FFF1B8",  # 아주 옅은 노랑
    "#FFD6A5",  # 복숭아
    "#FFB4A2",  # 살구
    "#F28482",  # 코랄
    "#C85C7A",  # 진한 핑크
]

BREAKS = [19, 23, 28, 38]


# =========================================================
# 귀여운 CSS
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background:
            radial-gradient(circle at 5% 5%, #FFF4C7 0, transparent 22%),
            radial-gradient(circle at 95% 10%, #FFDCE8 0, transparent 22%),
            radial-gradient(circle at 90% 90%, #DDF7F0 0, transparent 22%),
            #FFFDF9;
    }

    /* 기본 폰트 */
    html, body, [class*="css"] {
        font-family:
            "Pretendard",
            "Apple SD Gothic Neo",
            "Noto Sans KR",
            sans-serif;
    }

    /* 상단 여백 */
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* 메인 타이틀 */
    .main-title {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -2px;
        color: #47313B;
        line-height: 1.15;
        margin-bottom: 0.35rem;
    }

    .main-title .point {
        color: #E86A83;
    }

    .subtitle {
        color: #8D747D;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }

    /* 귀여운 배지 */
    .cute-badge {
        display: inline-block;
        background: #FFE2EA;
        color: #C94F70;
        border-radius: 999px;
        padding: 7px 15px;
        font-size: 0.82rem;
        font-weight: 800;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(201, 79, 112, 0.12);
    }

    /* 기준연도 카드 */
    .year-card {
        background: rgba(255,255,255,0.88);
        border: 2px solid #F7D8DF;
        border-radius: 22px;
        padding: 18px 22px;
        box-shadow: 0 8px 25px rgba(122, 77, 91, 0.08);
        margin-bottom: 18px;
    }

    .year-label {
        color: #9B7C85;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .year-value {
        color: #D85E79;
        font-size: 1.55rem;
        font-weight: 900;
    }

    /* 섹션 제목 */
    .section-title {
        color: #47313B;
        font-size: 1.45rem;
        font-weight: 900;
        letter-spacing: -0.7px;
        margin-top: 25px;
        margin-bottom: 8px;
    }

    .section-description {
        color: #927A82;
        font-size: 0.92rem;
        margin-bottom: 15px;
    }

    /* 순위 카드 */
    .rank-header {
        border-radius: 20px;
        padding: 15px 19px;
        margin-bottom: 10px;
        font-weight: 900;
        font-size: 1.05rem;
    }

    .rank-high {
        background: #FFE5EA;
        color: #B94D68;
        border: 1px solid #F6CBD5;
    }

    .rank-low {
        background: #DFF6EF;
        color: #368875;
        border: 1px solid #C5E9DE;
    }

    /* Streamlit dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 6px 22px rgba(80, 52, 61, 0.07);
        border: 1px solid #F0E3E6;
    }

    /* 정보 박스 */
    [data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid #F3D6DD;
    }

    /* Plotly 지도 카드처럼 보이게 */
    [data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 25px;
        padding: 8px;
        box-shadow: 0 10px 30px rgba(80, 52, 61, 0.09);
        border: 1px solid #F2E6E8;
    }

    /* 하단 설명 */
    .footer-note {
        text-align: center;
        color: #AA9299;
        font-size: 0.82rem;
        margin-top: 28px;
        padding: 15px;
    }

    /* Streamlit 기본 메뉴 */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 가져오기
# =========================================================

@st.cache_data
def load_population():
    """인구 CSV를 내려받아 읽습니다."""

    response = requests.get(POPULATION_URL, timeout=60)
    response.raise_for_status()

    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        df = pd.read_csv(
            gz,
            dtype={"코드": "string"},
        )

    # 코드는 숫자가 아니라 행정구역을 연결하기 위한 이름표입니다.
    df["코드"] = (
        df["코드"]
        .astype("string")
        .str.strip()
        .str.zfill(8)
    )

    return df


@st.cache_data
def load_geojson():
    """시군구 경계 GeoJSON을 내려받습니다."""

    response = requests.get(GEOJSON_URL, timeout=60)
    response.raise_for_status()

    return response.json()


# =========================================================
# 고령화율 계산
# =========================================================

@st.cache_data
def make_sigungu_data(df):
    """최신 연도의 읍·면·동 데이터를 시군구별로 합칩니다."""

    latest_year = int(df["연도"].max())

    latest = df[df["연도"] == latest_year].copy()

    # 읍·면·동 코드의 앞 5자리가 시군구 코드입니다.
    latest["시군구코드"] = latest["코드"].str[:5]

    # 65세 이상
    elderly_columns = [
        f"계_{age}세"
        for age in range(65, 100)
        if f"계_{age}세" in latest.columns
    ]

    if "계_100세 이상" in latest.columns:
        elderly_columns.append("계_100세 이상")

    # 전체 연령
    total_columns = [
        f"계_{age}세"
        for age in range(0, 100)
        if f"계_{age}세" in latest.columns
    ]

    if "계_100세 이상" in latest.columns:
        total_columns.append("계_100세 이상")

    # 숫자로 변환
    for col in set(elderly_columns + total_columns):
        latest[col] = pd.to_numeric(
            latest[col],
            errors="coerce",
        ).fillna(0)

    latest["고령인구"] = latest[elderly_columns].sum(axis=1)
    latest["전체인구"] = latest[total_columns].sum(axis=1)

    # 시군구별 합계
    sigungu = (
        latest
        .groupby("시군구코드", as_index=False)
        .agg(
            고령인구=("고령인구", "sum"),
            전체인구=("전체인구", "sum"),
        )
    )

    sigungu["고령화율"] = np.where(
        sigungu["전체인구"] > 0,
        sigungu["고령인구"] / sigungu["전체인구"] * 100,
        np.nan,
    )

    return latest_year, sigungu


# =========================================================
# GeoJSON에 고령화율 붙이기
# =========================================================

def add_geojson_properties(geojson, sigungu):
    """시군구 코드 기준으로 고령화율을 지도에 연결합니다."""

    value_map = (
        sigungu
        .set_index("시군구코드")["고령화율"]
        .to_dict()
    )

    for feature in geojson["features"]:

        properties = feature.get("properties", {})

        code = (
            str(properties.get("코드", ""))
            .strip()
            .zfill(5)
        )

        properties["고령화율"] = value_map.get(
            code,
            np.nan,
        )

        feature["properties"] = properties

    return geojson


# =========================================================
# 5단계 분류
# =========================================================

def classify_rate(rate):
    """고령화율을 5개 구간으로 나눕니다."""

    if pd.isna(rate):
        return None

    if rate < 19:
        return 0

    if rate < 23:
        return 1

    if rate < 28:
        return 2

    if rate < 38:
        return 3

    return 4


# =========================================================
# 지도 만들기
# =========================================================

def make_map(geojson):

    for feature in geojson["features"]:

        rate = feature["properties"].get(
            "고령화율",
            np.nan,
        )

        feature["properties"]["단계"] = classify_rate(rate)

    # 5단계가 확실하게 끊겨 보이도록 색상 구간을 지정합니다.
    colorscale = [
        [0.00, COLORS[0]],
        [0.1999, COLORS[0]],

        [0.20, COLORS[1]],
        [0.3999, COLORS[1]],

        [0.40, COLORS[2]],
        [0.5999, COLORS[2]],

        [0.60, COLORS[3]],
        [0.7999, COLORS[3]],

        [0.80, COLORS[4]],
        [1.00, COLORS[4]],
    ]

    fig = go.Figure(
        go.Choroplethmap(
            geojson=geojson,

            locations=[
                str(
                    feature["properties"].get("코드", "")
                ).zfill(5)
                for feature in geojson["features"]
            ],

            z=[
                feature["properties"].get(
                    "단계",
                    np.nan,
                )
                for feature in geojson["features"]
            ],

            featureidkey="properties.코드",

            zmin=0,
            zmax=4,

            colorscale=colorscale,

            marker_line_color="#FFFFFF",
            marker_line_width=0.8,

            customdata=[
                [
                    feature["properties"].get(
                        "시군구",
                        "",
                    ),

                    feature["properties"].get(
                        "시도",
                        "",
                    ),

                    feature["properties"].get(
                        "고령화율",
                        np.nan,
                    ),
                ]
                for feature in geojson["features"]
            ],

            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "📍 %{customdata[1]}<br>"
                "👵 65세 이상: "
                "<b>%{customdata[2]:.1f}%</b>"
                "<extra></extra>"
            ),

            colorbar=dict(
                title=dict(
                    text="고령화율",
                    font=dict(
                        size=13,
                        color="#59434B",
                    ),
                ),

                tickmode="array",

                tickvals=[
                    0,
                    1,
                    2,
                    3,
                    4,
                ],

                ticktext=[
                    "19% 미만",
                    "19~23%",
                    "23~28%",
                    "28~38%",
                    "38% 이상",
                ],

                tickfont=dict(
                    size=11,
                    color="#59434B",
                ),

                len=0.62,

                bgcolor="rgba(255,255,255,0.92)",

                bordercolor="#F0E1E5",
                borderwidth=1,
            ),
        )
    )

    fig.update_layout(

        # 배경 타일 없이 흰색 배경만 사용
        map=dict(
            style="white-bg",
            center=dict(
                lat=36.2,
                lon=127.8,
            ),
            zoom=6.2,
        ),

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),

        height=720,

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# =========================================================
# 앱 화면
# =========================================================

# 귀여운 상단 배지
st.markdown(
    '<div class="cute-badge">✨ DATA로 보는 우리 동네 이야기</div>',
    unsafe_allow_html=True,
)

# 제목
st.markdown(
    """
    <div class="main-title">
        전국 <span class="point">고령화 톡톡</span> 지도 🗺️
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        우리나라 시군구의 65세 이상 인구 비율을 한눈에 살펴봐요 👀
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 로딩
# =========================================================

try:

    with st.spinner("🧸 데이터를 꼼꼼하게 가져오는 중이에요..."):

        population_df = load_population()

        latest_year, sigungu_df = make_sigungu_data(
            population_df
        )

        geojson = load_geojson()

        geojson = add_geojson_properties(
            geojson,
            sigungu_df,
        )

except Exception as e:

    st.error(
        "앗! 데이터를 불러오는 중 문제가 생겼어요 🥲"
    )

    st.exception(e)

    st.stop()


# =========================================================
# 기준 연도 카드
# =========================================================

st.markdown(
    f"""
    <div class="year-card">
        <div class="year-label">📅 현재 지도 기준</div>
        <div class="year-value">{latest_year}년 전국 시군구</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 지도
# =========================================================

st.markdown(
    """
    <div class="section-title">
        🧓🏻 고령화율 지도
    </div>
    <div class="section-description">
        색이 진할수록 65세 이상 인구의 비율이 높아요.
        지도를 콕 눌러도 좋고, 마우스를 올려도 정보를 볼 수 있어요!
    </div>
    """,
    unsafe_allow_html=True,
)

fig = make_map(geojson)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# 시군구 이름 붙이기
# =========================================================

geo_properties = []

for feature in geojson["features"]:

    properties = feature.get(
        "properties",
        {},
    )

    geo_properties.append(
        {
            "시군구코드": str(
                properties.get("코드", "")
            ).zfill(5),

            "시군구": properties.get(
                "시군구",
                "",
            ),

            "시도": properties.get(
                "시도",
                "",
            ),
        }
    )

geo_name_df = pd.DataFrame(
    geo_properties
)


table_df = sigungu_df.merge(
    geo_name_df,
    on="시군구코드",
    how="left",
)

table_df = table_df.dropna(
    subset=["고령화율"]
).copy()


table_df["지역"] = (
    table_df["시도"].fillna("")
    + " "
    + table_df["시군구"].fillna("")
).str.strip()


# =========================================================
# TOP / BOTTOM 10
# =========================================================

high_10 = (
    table_df
    .sort_values(
        "고령화율",
        ascending=False,
    )
    .head(10)
    .loc[:, ["지역", "고령화율"]]
    .reset_index(drop=True)
)

low_10 = (
    table_df
    .sort_values(
        "고령화율",
        ascending=True,
    )
    .head(10)
    .loc[:, ["지역", "고령화율"]]
    .reset_index(drop=True)
)


high_10["고령화율"] = high_10[
    "고령화율"
].map(
    lambda x: f"{x:.1f}%"
)

low_10["고령화율"] = low_10[
    "고령화율"
].map(
    lambda x: f"{x:.1f}%"
)


high_10.index = high_10.index + 1
low_10.index = low_10.index + 1

high_10.index.name = "순위"
low_10.index.name = "순위"


# =========================================================
# 두 표를 나란히 표시
# =========================================================

st.markdown(
    """
    <div class="section-title">
        🔎 고령화율 TOP & BOTTOM
    </div>
    <div class="section-description">
        최신 연도 기준으로 고령화율이 높은 지역과 낮은 지역을 살펴봐요.
    </div>
    """,
    unsafe_allow_html=True,
)


col1, col2 = st.columns(
    2,
    gap="large",
)


with col1:

    st.markdown(
        """
        <div class="rank-header rank-high">
            🔥 고령화율 높은 곳 TOP 10
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        high_10,
        use_container_width=True,
        height=400,
    )


with col2:

    st.markdown(
        """
        <div class="rank-header rank-low">
            🌱 고령화율 낮은 곳 TOP 10
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        low_10,
        use_container_width=True,
        height=400,
    )


# =========================================================
# 하단 설명
# =========================================================

st.markdown(
    f"""
    <div class="footer-note">
        💡 고령화율 = 65세 이상 인구 ÷ 전체 인구 × 100
        &nbsp; · &nbsp;
        {latest_year}년 읍·면·동 데이터를 시군구 코드 기준으로 합산했어요.
        <br>
        🧡 지도 색상은 19% · 23% · 28% · 38%를 기준으로 5단계로 나눴어요.
    </div>
    """,
    unsafe_allow_html=True,
)
