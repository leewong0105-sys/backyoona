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
    page_title="전국 고령화 팝팝 지도",
    page_icon="지도",
    layout="wide",
)

POPULATION_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/"
    "data/population_yearly.csv.gz"
)

GEOJSON_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/"
    "data/boundaries/sigungu_kr.geojson"
)

# 5단계 색상
COLORS = [
    "#FFF1B8",
    "#FFD6A5",
    "#FFB4A2",
    "#F28482",
    "#C85A7A",
]


# =========================================================
# 디자인
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background:
            radial-gradient(
                circle at 5% 5%,
                rgba(255, 236, 174, 0.45),
                transparent 18%
            ),
            radial-gradient(
                circle at 95% 5%,
                rgba(255, 207, 222, 0.45),
                transparent 20%
            ),
            radial-gradient(
                circle at 95% 90%,
                rgba(200, 239, 226, 0.40),
                transparent 20%
            ),
            #FFFDF9;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* -----------------------------------------------------
       제목
    ----------------------------------------------------- */

    .title {
        color: #46333B;
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: -2px;
        line-height: 1.15;
        margin-bottom: 4px;
    }

    .title-point {
        color: #E76582;
    }

    .subtitle {
        color: #927982;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 20px;
    }


    /* -----------------------------------------------------
       깜찍한 배지
    ----------------------------------------------------- */

    .badge {
        display: inline-block;
        background: #FFE1E9;
        color: #C65070;
        border: 1px solid #F4C9D5;
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 0.82rem;
        font-weight: 800;
        margin-bottom: 8px;
    }


    /* -----------------------------------------------------
       통통 튀는 장식
    ----------------------------------------------------- */

    .bounce {
        display: inline-block;
        animation: bounce 1.5s ease-in-out infinite;
    }

    .bounce:nth-child(2) {
        animation-delay: 0.2s;
    }

    .bounce:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes bounce {

        0%, 100% {
            transform: translateY(0) rotate(0deg);
        }

        50% {
            transform: translateY(-7px) rotate(7deg);
        }

    }


    /* -----------------------------------------------------
       기준 연도 카드
       ※ 이 카드 안에는 이모지를 넣지 않습니다.
    ----------------------------------------------------- */

    .year-card {
        background: #FFFFFF;
        border: 2px solid #F4DCE2;
        border-radius: 22px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow:
            0 8px 24px rgba(80, 50, 60, 0.07);
    }

    .year-label {
        color: #9A828A;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .year-value {
        color: #D85D78;
        font-size: 1.4rem;
        font-weight: 900;
    }


    /* -----------------------------------------------------
       섹션
    ----------------------------------------------------- */

    .section-title {
        color: #46333B;
        font-size: 1.45rem;
        font-weight: 900;
        margin-top: 24px;
        margin-bottom: 4px;
    }

    .section-description {
        color: #927C84;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }


    /* -----------------------------------------------------
       지도 안내
    ----------------------------------------------------- */

    .hover-guide {
        background: linear-gradient(
            100deg,
            #FFF1C9,
            #FFE5EE
        );

        border: 1px solid #F1D6DE;
        border-radius: 17px;

        padding: 11px 15px;
        margin-bottom: 10px;

        color: #735861;
        font-size: 0.9rem;
        font-weight: 700;
    }


    /* -----------------------------------------------------
       지도 카드
    ----------------------------------------------------- */

    [data-testid="stPlotlyChart"] {
        background: #FFFFFF;
        border: 1px solid #F0E0E4;
        border-radius: 25px;
        padding: 5px;
        box-shadow:
            0 12px 32px rgba(80, 50, 60, 0.09);
    }


    /* -----------------------------------------------------
       순위 카드
    ----------------------------------------------------- */

    .rank {
        border-radius: 18px;
        padding: 13px 16px;
        margin-bottom: 8px;
        font-weight: 900;
    }

    .rank-high {
        background: linear-gradient(
            100deg,
            #FFE0E8,
            #FFF0D4
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
        border: 1px solid #C8E9DF;
    }


    /* -----------------------------------------------------
       표
    ----------------------------------------------------- */

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
    }


    /* -----------------------------------------------------
       하단
    ----------------------------------------------------- */

    .footer {
        text-align: center;
        color: #A58F96;
        font-size: 0.8rem;
        margin-top: 25px;
        line-height: 1.8;
    }


    /* Streamlit 기본 메뉴 숨기기 */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 인구 데이터
# =========================================================

@st.cache_data
def load_population():
    """압축된 인구 CSV를 불러옵니다."""

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
            dtype={
                "코드": "string",
            },
        )

    # 코드는 숫자가 아니라 행정구역 식별자입니다.
    df["코드"] = (
        df["코드"]
        .astype("string")
        .str.strip()
        .str.zfill(8)
    )

    return df


# =========================================================
# 경계 데이터
# =========================================================

@st.cache_data
def load_geojson():
    """전국 시군구 경계를 불러옵니다."""

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
def calculate_rates(df):
    """최신 연도의 읍·면·동 데이터를 시군구별로 합산합니다."""

    # 가장 최신 연도
    latest_year = int(df["연도"].max())

    data = df[
        df["연도"] == latest_year
    ].copy()

    # 읍·면·동 코드의 앞 5자리가 시군구 코드
    data["시군구코드"] = (
        data["코드"].str[:5]
    )


    # -----------------------------------------------------
    # 전체 인구 열
    # -----------------------------------------------------

    total_cols = [
        f"계_{age}세"
        for age in range(100)
        if f"계_{age}세" in data.columns
    ]

    if "계_100세 이상" in data.columns:
        total_cols.append(
            "계_100세 이상"
        )


    # -----------------------------------------------------
    # 65세 이상 인구 열
    # -----------------------------------------------------

    elderly_cols = [
        f"계_{age}세"
        for age in range(65, 100)
        if f"계_{age}세" in data.columns
    ]

    if "계_100세 이상" in data.columns:
        elderly_cols.append(
            "계_100세 이상"
        )


    # 숫자로 변환
    for col in set(
        total_cols + elderly_cols
    ):

        data[col] = pd.to_numeric(
            data[col],
            errors="coerce",
        ).fillna(0)


    # 읍·면·동별 합계
    data["전체인구"] = data[
        total_cols
    ].sum(axis=1)

    data["고령인구"] = data[
        elderly_cols
    ].sum(axis=1)


    # 시군구별 합계
    result = (
        data
        .groupby(
            "시군구코드",
            as_index=False,
        )
        .agg(
            전체인구=(
                "전체인구",
                "sum",
            ),
            고령인구=(
                "고령인구",
                "sum",
            ),
        )
    )


    # 고령화율
    result["고령화율"] = np.where(
        result["전체인구"] > 0,
        (
            result["고령인구"]
            / result["전체인구"]
            * 100
        ),
        np.nan,
    )

    return latest_year, result


# =========================================================
# 지도에 고령화율 연결
# =========================================================

def attach_rates(
    geojson,
    rates,
):
    """시군구 5자리 코드로 고령화율을 연결합니다."""

    rate_map = (
        rates
        .set_index("시군구코드")
        ["고령화율"]
        .to_dict()
    )

    for feature in geojson["features"]:

        properties = feature["properties"]

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

        properties["코드"] = code

        properties["고령화율"] = (
            rate_map.get(
                code,
                np.nan,
            )
        )

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
# 지도 생성
# =========================================================

def create_map(geojson):

    # 시군구별 단계 계산
    for feature in geojson["features"]:

        rate = feature[
            "properties"
        ]["고령화율"]

        feature[
            "properties"
        ]["단계"] = classify_rate(
            rate
        )


    # -----------------------------------------------------
    # 5단계 색상
    # -----------------------------------------------------

    colorscale = [
        [0.00, COLORS[0]],
        [0.20, COLORS[0]],

        [0.20, COLORS[1]],
        [0.40, COLORS[1]],

        [0.40, COLORS[2]],
        [0.60, COLORS[2]],

        [0.60, COLORS[3]],
        [0.80, COLORS[3]],

        [0.80, COLORS[4]],
        [1.00, COLORS[4]],
    ]


    # -----------------------------------------------------
    # 지도 데이터
    # -----------------------------------------------------

    locations = [
        feature[
            "properties"
        ]["코드"]

        for feature
        in geojson["features"]
    ]

    stages = [
        feature[
            "properties"
        ]["단계"]

        for feature
        in geojson["features"]
    ]


    # hover 데이터
    customdata = [
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
    ]


    # -----------------------------------------------------
    # 지도
    # -----------------------------------------------------

    fig = go.Figure(
        go.Choroplethmap(

            geojson=geojson,

            locations=locations,

            z=stages,

            featureidkey="properties.코드",

            zmin=0,
            zmax=4,

            colorscale=colorscale,

            marker_line_color="white",
            marker_line_width=0.8,

            customdata=customdata,

            # 일부러 아주 단순하게 구성
            # 한글 + 이모지 + 복잡한 HTML을 섞지 않음
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "시도: %{customdata[1]}<br>"
                "고령화율: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),

            hoverlabel=dict(
                bgcolor="#FFF9FB",
                bordercolor="#E76582",
                font=dict(
                    size=14,
                    color="#46333B",
                ),
            ),

            colorbar=dict(

                title="고령화율",

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

                len=0.65,
            ),
        )
    )


    # -----------------------------------------------------
    # 지도 위치
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

        height=700,

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    return fig


# =========================================================
# 화면 - 제목
# =========================================================

st.markdown(
    """
    <div class="badge">
        DATA로 보는 우리 동네 이야기
    </div>

    <div class="title">
        전국
        <span class="title-point"> 고령화</span>
        팝팝 지도
        <span class="bounce">✨</span>
        <span class="bounce">●</span>
        <span class="bounce">✦</span>
    </div>

    <div class="subtitle">
        마우스를 살짝 올리면 시군구별 고령화율을 확인할 수 있어요.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 준비
# =========================================================

try:

    with st.spinner(
        "데이터를 가져오는 중이에요..."
    ):

        population = load_population()

        latest_year, rates = (
            calculate_rates(
                population
            )
        )

        geojson = load_geojson()

        geojson = attach_rates(
            geojson,
            rates,
        )

except Exception as e:

    st.error(
        "데이터를 불러오지 못했습니다."
    )

    st.exception(e)

    st.stop()


# =========================================================
# 기준 연도
# =========================================================

# 중요:
# 이 부분은 HTML 안에 이모지를 넣지 않습니다.
# Streamlit 기본 렌더링을 사용해서 한글 깨짐 가능성을 낮춥니다.

st.markdown(
    """
    <div class="year-card">
        <div class="year-label">
            기준 연도
        </div>
        <div class="year-value">
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"**{latest_year}년 전국 시군구**"
)

st.markdown(
    """
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "최신 연도 데이터를 기준으로 표시합니다."
)


# =========================================================
# 지도 설명
# =========================================================

st.markdown(
    """
    <div class="section-title">
        고령화율 한눈에 보기
    </div>

    <div class="section-description">
        색이 진할수록 65세 이상 인구 비율이 높아요.
    </div>

    <div class="hover-guide">
        👆 시군구에 마우스를 올려보세요!
        톡 하고 고령화율이 나타납니다.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 지도 출력
# =========================================================

fig = create_map(
    geojson
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# 시군구 이름 데이터
# =========================================================

names = pd.DataFrame(
    [
        {
            "시군구코드": feature[
                "properties"
            ]["코드"],

            "시군구": feature[
                "properties"
            ].get(
                "시군구",
                "",
            ),

            "시도": feature[
                "properties"
            ].get(
                "시도",
                "",
            ),
        }

        for feature
        in geojson["features"]
    ]
)


table = rates.merge(
    names,
    on="시군구코드",
    how="left",
)


table["지역"] = (
    table["시도"]
    + " "
    + table["시군구"]
).str.strip()


table = table.dropna(
    subset=["고령화율"]
)


# =========================================================
# TOP 10
# =========================================================

high = (
    table
    .sort_values(
        "고령화율",
        ascending=False,
    )
    .head(10)
    [["지역", "고령화율"]]
    .reset_index(drop=True)
)


low = (
    table
    .sort_values(
        "고령화율",
        ascending=True,
    )
    .head(10)
    [["지역", "고령화율"]]
    .reset_index(drop=True)
)


high["고령화율"] = high[
    "고령화율"
].map(
    lambda x: f"{x:.1f}%"
)


low["고령화율"] = low[
    "고령화율"
].map(
    lambda x: f"{x:.1f}%"
)


high.index += 1
low.index += 1

high.index.name = "순위"
low.index.name = "순위"


# =========================================================
# 순위표
# =========================================================

st.markdown(
    """
    <div class="section-title">
        고령화율 TOP & BOTTOM
    </div>

    <div class="section-description">
        최신 연도 기준 시군구별 고령화율입니다.
    </div>
    """,
    unsafe_allow_html=True,
)


left, right = st.columns(
    2,
    gap="large",
)


with left:

    st.markdown(
        """
        <div class="rank rank-high">
            높은 곳 TOP 10
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        high,
        use_container_width=True,
        height=400,
    )


with right:

    st.markdown(
        """
        <div class="rank rank-low">
            낮은 곳 TOP 10
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        low,
        use_container_width=True,
        height=400,
    )


# =========================================================
# 하단 설명
# =========================================================

st.markdown(
    f"""
    <div class="footer">
        고령화율 = 65세 이상 인구 ÷ 전체 인구 × 100
        <br>
        {latest_year}년 읍·면·동 데이터를 시군구 코드 앞 5자리 기준으로 합산
        <br>
        지도 구간: 19% · 23% · 28% · 38%
    </div>
    """,
    unsafe_allow_html=True,
)
