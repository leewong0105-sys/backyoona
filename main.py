# main.py
# 🗺️ 전국 시군구별 고령화율 팝팝 지도
#
# 주요 기능
# - 최신 연도의 시군구별 65세 이상 인구 비율
# - 코드 앞 5자리 기준 시군구 매칭
# - 5단계 단계구분도
# - 귀여운 hover 정보
# - TOP 10 / BOTTOM 10
# - 깜찍한 UI / 카드 / 배지 / 장식
# - 배경 지도 타일 없음


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
    page_title="고령화 팝팝 지도",
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


# =========================================================
# 색상
# =========================================================

COLORS = [
    "#FFF4C2",  # 1단계 - 크림
    "#FFD9A8",  # 2단계 - 복숭아
    "#FFB6A3",  # 3단계 - 살구
    "#F48686",  # 4단계 - 코랄
    "#C85A78",  # 5단계 - 딸기
]


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* -----------------------------------------------------
       전체 배경
    ----------------------------------------------------- */

    .stApp {
        background:
            radial-gradient(
                circle at 4% 4%,
                rgba(255, 229, 145, 0.45) 0,
                transparent 19%
            ),
            radial-gradient(
                circle at 96% 5%,
                rgba(255, 190, 211, 0.40) 0,
                transparent 20%
            ),
            radial-gradient(
                circle at 92% 90%,
                rgba(178, 235, 220, 0.35) 0,
                transparent 22%
            ),
            #FFFDF9;
    }


    /* -----------------------------------------------------
       기본 여백
    ----------------------------------------------------- */

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* -----------------------------------------------------
       메인 제목
    ----------------------------------------------------- */

    .title-wrap {
        position: relative;
        margin-bottom: 8px;
    }

    .main-title {
        color: #47323B;
        font-size: 3.15rem;
        font-weight: 950;
        letter-spacing: -3px;
        line-height: 1.1;
    }

    .main-title .pink {
        color: #E76582;
    }

    .main-title .yellow {
        color: #F2A93B;
    }

    .subtitle {
        color: #957B84;
        font-size: 1.02rem;
        font-weight: 650;
        margin-bottom: 20px;
    }


    /* -----------------------------------------------------
       제목 주변의 통통 튀는 장식
    ----------------------------------------------------- */

    .sparkle {
        display: inline-block;
        animation: bounce 1.6s infinite ease-in-out;
    }

    .sparkle:nth-child(2) {
        animation-delay: 0.25s;
    }

    .sparkle:nth-child(3) {
        animation-delay: 0.5s;
    }

    @keyframes bounce {
        0%, 100% {
            transform: translateY(0) rotate(0deg);
        }

        50% {
            transform: translateY(-7px) rotate(8deg);
        }
    }


    /* -----------------------------------------------------
       배지
    ----------------------------------------------------- */

    .cute-badge {
        display: inline-block;
        background: #FFE2EA;
        color: #C94E70;
        border: 1px solid #F5C7D4;
        border-radius: 999px;
        padding: 7px 16px;
        font-size: 0.82rem;
        font-weight: 850;
        box-shadow:
            0 5px 15px rgba(201, 78, 112, 0.12);
        margin-bottom: 10px;
    }


    /* -----------------------------------------------------
       기준연도 카드
    ----------------------------------------------------- */

    .year-card {
        position: relative;
        overflow: hidden;

        background: rgba(255,255,255,0.90);
        border: 2px solid #F5DCE2;
        border-radius: 25px;

        padding: 17px 22px;

        box-shadow:
            0 9px 28px rgba(95, 58, 71, 0.08);

        margin-bottom: 20px;
    }

    .year-card::after {
        content: "POP!";
        position: absolute;
        right: 22px;
        top: 13px;

        background: #FFF0A9;
        color: #9B6A20;

        font-size: 0.72rem;
        font-weight: 950;

        padding: 6px 9px;

        border-radius: 10px;

        transform: rotate(7deg);

        animation: tinyPop 1.8s infinite ease-in-out;
    }

    @keyframes tinyPop {
        0%, 100% {
            transform: rotate(7deg) scale(1);
        }

        50% {
            transform: rotate(-4deg) scale(1.08);
        }
    }

    .year-label {
        color: #9D828B;
        font-size: 0.78rem;
        font-weight: 750;
    }

    .year-value {
        color: #D95D78;
        font-size: 1.45rem;
        font-weight: 950;
    }


    /* -----------------------------------------------------
       섹션 제목
    ----------------------------------------------------- */

    .section-title {
        color: #47323B;
        font-size: 1.48rem;
        font-weight: 950;
        letter-spacing: -1px;
        margin-top: 25px;
        margin-bottom: 5px;
    }

    .section-description {
        color: #927B83;
        font-size: 0.91rem;
        font-weight: 600;
        margin-bottom: 13px;
    }


    /* -----------------------------------------------------
       지도 안내 카드
    ----------------------------------------------------- */

    .hover-guide {
        display: flex;
        align-items: center;
        gap: 12px;

        background: linear-gradient(
            100deg,
            #FFF2C9,
            #FFE7EF
        );

        border: 1px solid #F3D7DE;
        border-radius: 18px;

        padding: 12px 17px;
        margin-bottom: 10px;

        color: #715761;
        font-size: 0.9rem;
        font-weight: 750;

        box-shadow:
            0 5px 16px rgba(100, 62, 74, 0.06);
    }

    .hover-icon {
        font-size: 1.35rem;
        animation: hoverBounce 1.2s infinite;
    }

    @keyframes hoverBounce {
        0%, 100% {
            transform: translateY(0);
        }

        50% {
            transform: translateY(-5px);
        }
    }


    /* -----------------------------------------------------
       지도
    ----------------------------------------------------- */

    [data-testid="stPlotlyChart"] {
        background: rgba(255,255,255,0.96);
        border: 1px solid #F1E0E4;
        border-radius: 28px;

        padding: 8px;

        box-shadow:
            0 13px 35px rgba(82, 51, 61, 0.10);
    }


    /* -----------------------------------------------------
       TOP / BOTTOM 헤더
    ----------------------------------------------------- */

    .rank-header {
        border-radius: 20px;
        padding: 15px 18px;
        margin-bottom: 10px;

        font-weight: 950;
        font-size: 1.02rem;

        box-shadow:
            0 6px 18px rgba(85, 54, 64, 0.06);
    }

    .rank-high {
        background: linear-gradient(
            100deg,
            #FFE0E8,
            #FFF0D0
        );

        color: #B84E68;
        border: 1px solid #F4CDD6;
    }

    .rank-low {
        background: linear-gradient(
            100deg,
            #DDF7EF,
            #E9F5FF
        );

        color: #378875;
        border: 1px solid #C7E9DF;
    }


    /* -----------------------------------------------------
       표
    ----------------------------------------------------- */

    [data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;

        border: 1px solid #F0E2E5;

        box-shadow:
            0 7px 22px rgba(80, 50, 60, 0.07);
    }


    /* -----------------------------------------------------
       하단 설명
    ----------------------------------------------------- */

    .footer-note {
        text-align: center;

        color: #AA929A;

        font-size: 0.81rem;
        font-weight: 600;

        margin-top: 30px;
        padding: 20px;
    }


    /* -----------------------------------------------------
       Streamlit 기본 UI 숨기기
    ----------------------------------------------------- */

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
# 데이터 불러오기
# =========================================================

@st.cache_data
def load_population():

    response = requests.get(
        POPULATION_URL,
        timeout=60,
    )

    response.raise_for_status()

    with gzip.GzipFile(
        fileobj=io.BytesIO(response.content)
    ) as gz:

        df = pd.read_csv(
            gz,
            dtype={"코드": "string"},
        )

    # 코드는 숫자가 아니라 이름표이므로 문자열로 유지합니다.
    df["코드"] = (
        df["코드"]
        .astype("string")
        .str.strip()
        .str.zfill(8)
    )

    return df


@st.cache_data
def load_geojson():

    response = requests.get(
        GEOJSON_URL,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# 고령화율 계산
# =========================================================

@st.cache_data
def make_sigungu_data(df):

    # 가장 최신 연도
    latest_year = int(df["연도"].max())

    latest = df[
        df["연도"] == latest_year
    ].copy()

    # 읍·면·동 코드 앞 5자리 = 시군구 코드
    latest["시군구코드"] = (
        latest["코드"].str[:5]
    )


    # -----------------------------------------------------
    # 65세 이상 인구
    # -----------------------------------------------------

    elderly_columns = [
        f"계_{age}세"
        for age in range(65, 100)
        if f"계_{age}세" in latest.columns
    ]

    if "계_100세 이상" in latest.columns:
        elderly_columns.append(
            "계_100세 이상"
        )


    # -----------------------------------------------------
    # 전체 인구
    # -----------------------------------------------------

    total_columns = [
        f"계_{age}세"
        for age in range(0, 100)
        if f"계_{age}세" in latest.columns
    ]

    if "계_100세 이상" in latest.columns:
        total_columns.append(
            "계_100세 이상"
        )


    # 숫자로 변환
    for col in set(
        elderly_columns + total_columns
    ):

        latest[col] = pd.to_numeric(
            latest[col],
            errors="coerce",
        ).fillna(0)


    # 읍·면·동별 계산
    latest["고령인구"] = (
        latest[elderly_columns].sum(axis=1)
    )

    latest["전체인구"] = (
        latest[total_columns].sum(axis=1)
    )


    # -----------------------------------------------------
    # 시군구별 합계
    # -----------------------------------------------------

    sigungu = (
        latest
        .groupby(
            "시군구코드",
            as_index=False,
        )
        .agg(
            고령인구=("고령인구", "sum"),
            전체인구=("전체인구", "sum"),
        )
    )


    # 고령화율
    sigungu["고령화율"] = np.where(
        sigungu["전체인구"] > 0,

        sigungu["고령인구"]
        / sigungu["전체인구"]
        * 100,

        np.nan,
    )


    return latest_year, sigungu


# =========================================================
# GeoJSON에 고령화율 붙이기
# =========================================================

def add_geojson_properties(
    geojson,
    sigungu,
):

    value_map = (
        sigungu
        .set_index("시군구코드")
        ["고령화율"]
        .to_dict()
    )


    for feature in geojson["features"]:

        properties = feature.get(
            "properties",
            {},
        )


        code = (
            str(
                properties.get(
                    "코드",
                    "",
                )
            )
            .strip()
            .zfill(5)
        )


        properties["고령화율"] = (
            value_map.get(
                code,
                np.nan,
            )
        )


        feature["properties"] = properties


    return geojson


# =========================================================
# 5단계 분류
# =========================================================

def classify_rate(rate):

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

    # 각 시군구를 0~4 단계로 분류
    for feature in geojson["features"]:

        rate = feature[
            "properties"
        ].get(
            "고령화율",
            np.nan,
        )

        feature[
            "properties"
        ]["단계"] = classify_rate(rate)


    # -----------------------------------------------------
    # 5단계 색상
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 지도
    # -----------------------------------------------------

    fig = go.Figure(
        go.Choroplethmap(

            geojson=geojson,

            locations=[
                str(
                    feature[
                        "properties"
                    ].get(
                        "코드",
                        "",
                    )
                ).zfill(5)

                for feature
                in geojson["features"]
            ],

            z=[
                feature[
                    "properties"
                ].get(
                    "단계",
                    np.nan,
                )

                for feature
                in geojson["features"]
            ],

            featureidkey="properties.코드",

            zmin=0,
            zmax=4,

            colorscale=colorscale,


            # -------------------------------------------------
            # 경계선
            # -------------------------------------------------

            marker_line_color="#FFFFFF",
            marker_line_width=0.85,


            # -------------------------------------------------
            # hover에 전달할 정보
            # -------------------------------------------------

            customdata=[

                [

                    feature[
                        "properties"
                    ].get(
                        "시군구",
                        "",
                    ),

                    feature[
                        "properties"
                    ].get(
                        "시도",
                        "",
                    ),

                    feature[
                        "properties"
                    ].get(
                        "고령화율",
                        np.nan,
                    ),

                ]

                for feature
                in geojson["features"]
            ],


            # -------------------------------------------------
            # ✨ 핵심: 귀여운 hover
            # -------------------------------------------------

            hovertemplate=(

                "<span style='font-size:18px'>"
                "✨ <b>%{customdata[0]}</b>"
                "</span>"
                "<br>"

                "<span style='font-size:12px'>"
                "📍 %{customdata[1]}"
                "</span>"
                "<br><br>"

                "<span style='font-size:13px'>"
                "👵🏻 65세 이상"
                "</span>"
                "<br>"

                "<span style='font-size:24px; "
                "color:#E76582'>"
                "<b>%{customdata[2]:.1f}%</b>"
                "</span>"

                "<br>"

                "<span style='font-size:11px; "
                "color:#999'>"
                "톡! 하고 확인했어요 💕"
                "</span>"

                "<extra></extra>"
            ),


            # -------------------------------------------------
            # hover 박스 스타일
            # -------------------------------------------------

            hoverlabel=dict(

                bgcolor="#FFFDFB",

                bordercolor="#E76582",

                font=dict(
                    family="Arial, sans-serif",
                    size=13,
                    color="#503A42",
                ),

                align="left",
            ),


            # -------------------------------------------------
            # 범례
            # -------------------------------------------------

            colorbar=dict(

                title=dict(
                    text="💗 고령화율",
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

                bgcolor=(
                    "rgba(255,255,255,0.94)"
                ),

                bordercolor="#F0DDE2",
                borderwidth=1,
            ),
        )
    )


    # -----------------------------------------------------
    # 지도 설정
    # -----------------------------------------------------

    fig.update_layout(

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

        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),

        plot_bgcolor=(
            "rgba(0,0,0,0)"
        ),
    )


    return fig


# =========================================================
# 화면 시작
# =========================================================

st.markdown(
    """
    <div class="title-wrap">

        <div class="cute-badge">
            ✨ DATA로 보는 우리 동네 이야기
        </div>

        <div class="main-title">
            전국
            <span class="pink"> 고령화</span>
            <span class="yellow"> 팝팝</span>
            지도
            <span class="sparkle">✨</span>
            <span class="sparkle">🧓🏻</span>
            <span class="sparkle">💗</span>
        </div>

        <div class="subtitle">
            마우스를 살짝 올려보세요.
            지역이 톡! 하고 말을 걸어요 👀
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 로딩
# =========================================================

try:

    with st.spinner(
        "🧸 데이터를 데굴데굴 가져오는 중..."
    ):

        population_df = load_population()

        latest_year, sigungu_df = (
            make_sigungu_data(
                population_df
            )
        )

        geojson = load_geojson()

        geojson = add_geojson_properties(
            geojson,
            sigungu_df,
        )

except Exception as e:

    st.error(
        "앗! 데이터를 가져오다가 살짝 넘어졌어요 🥲"
    )

    st.exception(e)

    st.stop()


# =========================================================
# 기준 연도
# =========================================================

st.markdown(
    f"""
    <div class="year-card">

        <div class="year-label">
            📅 지도 기준 연도
        </div>

        <div class="year-value">
            {latest_year}년 전국 시군구
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 지도 제목
# =========================================================

st.markdown(
    """
    <div class="section-title">
        🗺️ 우리나라 고령화율을 한눈에!
    </div>

    <div class="section-description">
        색이 진할수록 65세 이상 인구 비율이 높아요.
    </div>

    <div class="hover-guide">
        <span class="hover-icon">👆🏻</span>

        <span>
            <b>마우스를 시군구 위에 살짝 올려보세요!</b>
            &nbsp; → &nbsp;
            지역 이름 + 시도 + 고령화율이 팝! 하고 나타나요 💥
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 지도
# =========================================================

fig = make_map(geojson)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# 지역 이름 연결
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
                properties.get(
                    "코드",
                    "",
                )
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
# TOP 10 / BOTTOM 10
# =========================================================

high_10 = (
    table_df
    .sort_values(
        "고령화율",
        ascending=False,
    )
    .head(10)
    .loc[
        :,
        ["지역", "고령화율"],
    ]
    .reset_index(drop=True)
)


low_10 = (
    table_df
    .sort_values(
        "고령화율",
        ascending=True,
    )
    .head(10)
    .loc[
        :,
        ["지역", "고령화율"],
    ]
    .reset_index(drop=True)
)


high_10["고령화율"] = (
    high_10["고령화율"]
    .map(
        lambda x: f"{x:.1f}%"
    )
)


low_10["고령화율"] = (
    low_10["고령화율"]
    .map(
        lambda x: f"{x:.1f}%"
    )
)


high_10.index = (
    high_10.index + 1
)

low_10.index = (
    low_10.index + 1
)

high_10.index.name = "순위"
low_10.index.name = "순위"


# =========================================================
# 순위 영역
# =========================================================

st.markdown(
    """
    <div class="section-title">
        🎀 고령화율 살펴보기
    </div>

    <div class="section-description">
        지도에서 본 내용을 표에서도 콕콕 확인할 수 있어요.
    </div>
    """,
    unsafe_allow_html=True,
)


col1, col2 = st.columns(
    2,
    gap="large",
)


# ---------------------------------------------------------
# 높은 곳
# ---------------------------------------------------------

with col1:

    st.markdown(
        """
        <div class="rank-header rank-high">
            🔥 고령화율 높은 곳 TOP 10
            <span style="float:right">
                👵🏻💗
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        high_10,
        use_container_width=True,
        height=400,
    )


# ---------------------------------------------------------
# 낮은 곳
# ---------------------------------------------------------

with col2:

    st.markdown(
        """
        <div class="rank-header rank-low">
            🌱 고령화율 낮은 곳 TOP 10
            <span style="float:right">
                🌱✨
            </span>
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
# 하단
# =========================================================

st.markdown(
    f"""
    <div class="footer-note">

        🧮
        고령화율 =
        <b>65세 이상 인구 ÷ 전체 인구 × 100</b>

        &nbsp;&nbsp;·&nbsp;&nbsp;

        📊 {latest_year}년 읍·면·동 데이터를
        시군구 코드 앞 5자리 기준으로 합산

        <br><br>

        🎨
        지도는
        <b>19% · 23% · 28% · 38%</b>
        기준의 5단계 색상으로 표시했어요.

        <br>

        <span style="color:#E76582">
            ✨ 마우스를 올리면 톡! ✨
        </span>

    </div>
    """,
    unsafe_allow_html=True,
)
