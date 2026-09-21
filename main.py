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
    page_title="전국 인구통계 놀이터",
    page_icon="인구",
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


# =========================================================
# 색상
# =========================================================

PALETTE = [
    "#FFF1B8",
    "#FFD6A5",
    "#FFB4A2",
    "#F28482",
    "#C85A7A",
]


# =========================================================
# 깔끔하고 살짝 깜찍한 디자인
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 5% 5%,
                rgba(255, 236, 174, 0.42),
                transparent 18%
            ),
            radial-gradient(
                circle at 95% 5%,
                rgba(255, 207, 222, 0.42),
                transparent 20%
            ),
            radial-gradient(
                circle at 95% 90%,
                rgba(200, 239, 226, 0.35),
                transparent 20%
            ),
            #FFFDF9;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .title {
        color: #46333B;
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: -2px;
        line-height: 1.15;
        margin-bottom: 4px;
    }

    .pink {
        color: #E76582;
    }

    .yellow {
        color: #E8A33A;
    }

    .subtitle {
        color: #927982;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 22px;
    }

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

    .year-card {
        background: white;
        border: 2px solid #F4DCE2;
        border-radius: 22px;
        padding: 15px 20px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(80, 50, 60, 0.07);
    }

    .year-label {
        color: #9A828A;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .year-value {
        color: #D85D78;
        font-size: 1.4rem;
        font-weight: 900;
    }

    .section-title {
        color: #46333B;
        font-size: 1.45rem;
        font-weight: 900;
        margin-top: 18px;
        margin-bottom: 4px;
    }

    .section-description {
        color: #927C84;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }

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

    [data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid #F0E0E4;
        border-radius: 25px;
        padding: 5px;
        box-shadow: 0 12px 32px rgba(80, 50, 60, 0.09);
    }

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

    .metric-card {
        background: white;
        border: 1px solid #F0DDE2;
        border-radius: 20px;
        padding: 15px 18px;
        margin-bottom: 15px;
        box-shadow: 0 6px 18px rgba(80, 50, 60, 0.05);
    }

    .metric-name {
        color: #927C84;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .metric-value {
        color: #D85D78;
        font-size: 1.35rem;
        font-weight: 900;
    }

    .footer {
        text-align: center;
        color: #A58F96;
        font-size: 0.8rem;
        margin-top: 25px;
        line-height: 1.8;
    }

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
    }

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
# 데이터 불러오기
# =========================================================

@st.cache_data
def load_population():
    """압축된 전국 읍·면·동 인구 데이터를 불러옵니다."""

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

    # 코드는 계산용 숫자가 아니라 행정구역 식별자입니다.
    df["코드"] = (
        df["코드"]
        .astype("string")
        .str.strip()
        .str.zfill(8)
    )

    return df


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
# 나이별 열 준비
# =========================================================

def get_age_columns(df, start_age, end_age):
    """
    지정한 나이 범위의 '계_' 인구 열을 찾습니다.

    예:
    0~14세 -> 계_0세 ~ 계_14세
    """

    columns = []

    for age in range(
        start_age,
        end_age + 1,
    ):

        column = f"계_{age}세"

        if column in df.columns:
            columns.append(column)

    return columns


# =========================================================
# 시군구별 인구 지표 계산
# =========================================================

@st.cache_data
def calculate_statistics(df):

    latest_year = int(
        df["연도"].max()
    )

    # 최신 연도 데이터만 사용
    latest = df[
        df["연도"] == latest_year
    ].copy()

    # 읍·면·동 코드 앞 5자리 = 시군구 코드
    latest["시군구코드"] = (
        latest["코드"].str[:5]
    )


    # -----------------------------------------------------
    # 전체 인구
    # -----------------------------------------------------

    total_columns = get_age_columns(
        latest,
        0,
        99,
    )

    if "계_100세 이상" in latest.columns:
        total_columns.append(
            "계_100세 이상"
        )


    # -----------------------------------------------------
    # 0~14세
    # -----------------------------------------------------

    child_columns = get_age_columns(
        latest,
        0,
        14,
    )


    # -----------------------------------------------------
    # 15~64세
    # -----------------------------------------------------

    working_columns = get_age_columns(
        latest,
        15,
        64,
    )


    # -----------------------------------------------------
    # 65세 이상
    # -----------------------------------------------------

    elderly_columns = get_age_columns(
        latest,
        65,
        99,
    )

    if "계_100세 이상" in latest.columns:
        elderly_columns.append(
            "계_100세 이상"
        )


    # -----------------------------------------------------
    # 숫자로 변환
    # -----------------------------------------------------

    all_columns = set(
        total_columns
        + child_columns
        + working_columns
        + elderly_columns
    )

    for column in all_columns:

        latest[column] = pd.to_numeric(
            latest[column],
            errors="coerce",
        ).fillna(0)


    # -----------------------------------------------------
    # 읍·면·동별 인구 합계
    # -----------------------------------------------------

    latest["전체인구"] = latest[
        total_columns
    ].sum(axis=1)

    latest["유소년인구"] = latest[
        child_columns
    ].sum(axis=1)

    latest["생산연령인구"] = latest[
        working_columns
    ].sum(axis=1)

    latest["고령인구"] = latest[
        elderly_columns
    ].sum(axis=1)


    # -----------------------------------------------------
    # 시군구별 합산
    # -----------------------------------------------------

    sigungu = (
        latest
        .groupby(
            "시군구코드",
            as_index=False,
        )
        .agg(
            전체인구=(
                "전체인구",
                "sum",
            ),
            유소년인구=(
                "유소년인구",
                "sum",
            ),
            생산연령인구=(
                "생산연령인구",
                "sum",
            ),
            고령인구=(
                "고령인구",
                "sum",
            ),
        )
    )


    # -----------------------------------------------------
    # 지표 계산
    # -----------------------------------------------------

    sigungu["고령화율"] = np.where(
        sigungu["전체인구"] > 0,
        sigungu["고령인구"]
        / sigungu["전체인구"]
        * 100,
        np.nan,
    )

    sigungu["유소년비율"] = np.where(
        sigungu["전체인구"] > 0,
        sigungu["유소년인구"]
        / sigungu["전체인구"]
        * 100,
        np.nan,
    )

    sigungu["생산연령비율"] = np.where(
        sigungu["전체인구"] > 0,
        sigungu["생산연령인구"]
        / sigungu["전체인구"]
        * 100,
        np.nan,
    )

    sigungu["노년부양비"] = np.where(
        sigungu["생산연령인구"] > 0,
        sigungu["고령인구"]
        / sigungu["생산연령인구"]
        * 100,
        np.nan,
    )


    return latest_year, sigungu


# =========================================================
# 전국 연도별 인구
# =========================================================

@st.cache_data
def calculate_national_trend(df):

    total_columns = get_age_columns(
        df,
        0,
        99,
    )

    if "계_100세 이상" in df.columns:
        total_columns.append(
            "계_100세 이상"
        )

    data = df[
        ["연도"] + total_columns
    ].copy()

    for column in total_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        ).fillna(0)

    data["전체인구"] = data[
        total_columns
    ].sum(axis=1)

    trend = (
        data
        .groupby(
            "연도",
            as_index=False,
        )["전체인구"]
        .sum()
    )

    return trend


# =========================================================
# 지도 경계에 지표 연결
# =========================================================

def attach_metric(
    geojson,
    statistics,
    metric_column,
):

    metric_map = (
        statistics
        .set_index("시군구코드")
        [metric_column]
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

        properties["지도값"] = metric_map.get(
            code,
            np.nan,
        )

    return geojson


# =========================================================
# 단계 구간 계산
# =========================================================

def get_breaks(values, fixed_breaks=None):

    values = pd.Series(values).dropna()

    if fixed_breaks is not None:
        return fixed_breaks

    if values.empty:
        return [0, 25, 50, 75]

    # 실제 전국 분포의 20/40/60/80 분위값
    quantiles = np.nanpercentile(
        values,
        [20, 40, 60, 80],
    )

    return [
        float(x)
        for x in quantiles
    ]


def classify_value(
    value,
    breaks,
):

    if pd.isna(value):
        return None

    if value < breaks[0]:
        return 0

    if value < breaks[1]:
        return 1

    if value < breaks[2]:
        return 2

    if value < breaks[3]:
        return 3

    return 4


# =========================================================
# 범례 문자열
# =========================================================

def make_legend(
    breaks,
    unit="%",
):

    b1, b2, b3, b4 = breaks

    return [
        f"{b1:.1f}{unit} 미만",
        f"{b1:.1f}~{b2:.1f}{unit}",
        f"{b2:.1f}~{b3:.1f}{unit}",
        f"{b3:.1f}~{b4:.1f}{unit}",
        f"{b4:.1f}{unit} 이상",
    ]


# =========================================================
# 지도 만들기
# =========================================================

def create_map(
    geojson,
    breaks,
):

    for feature in geojson["features"]:

        value = feature[
            "properties"
        ].get(
            "지도값",
            np.nan,
        )

        feature[
            "properties"
        ]["단계"] = classify_value(
            value,
            breaks,
        )


    # -----------------------------------------------------
    # 계단식 색상
    # -----------------------------------------------------

    colorscale = [
        [0.00, PALETTE[0]],
        [0.20, PALETTE[0]],

        [0.20, PALETTE[1]],
        [0.40, PALETTE[1]],

        [0.40, PALETTE[2]],
        [0.60, PALETTE[2]],

        [0.60, PALETTE[3]],
        [0.80, PALETTE[3]],

        [0.80, PALETTE[4]],
        [1.00, PALETTE[4]],
    ]


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
                "지도값",
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

            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "시도: %{customdata[1]}<br>"
                "비율: %{customdata[2]:.1f}%"
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

                title="비율",

                tickmode="array",

                tickvals=[
                    0,
                    1,
                    2,
                    3,
                    4,
                ],

                ticktext=make_legend(
                    breaks
                ),

                len=0.65,
            ),
        )
    )


    fig.update_layout(

        map=dict(
            style="white-bg",

            center=dict(
                lat=36.2,
                lon=127.8,
            ),

            zoom=6.2,
        ),

        height=680,

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
# 순위표
# =========================================================

def make_rank_tables(
    statistics,
    names,
    metric_column,
):

    table = statistics.merge(
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
        subset=[metric_column]
    )


    high = (
        table
        .sort_values(
            metric_column,
            ascending=False,
        )
        .head(10)
        [["지역", metric_column]]
        .reset_index(drop=True)
    )

    low = (
        table
        .sort_values(
            metric_column,
            ascending=True,
        )
        .head(10)
        [["지역", metric_column]]
        .reset_index(drop=True)
    )


    high[metric_column] = high[
        metric_column
    ].map(
        lambda x: f"{x:.1f}%"
    )

    low[metric_column] = low[
        metric_column
    ].map(
        lambda x: f"{x:.1f}%"
    )


    high.index += 1
    low.index += 1

    high.index.name = "순위"
    low.index.name = "순위"

    return high, low


# =========================================================
# 지표 화면
# =========================================================

def render_metric_tab(
    geojson,
    statistics,
    names,
    title,
    description,
    metric_column,
    latest_year,
    fixed_breaks=None,
):

    st.markdown(
        f"""
        <div class="section-title">
            {title}
        </div>

        <div class="section-description">
            {description}
        </div>

        <div class="hover-guide">
            지도에 마우스를 올리면 시군구별 수치를 확인할 수 있어요.
        </div>
        """,
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # 지도용 경계값
    # -----------------------------------------------------

    breaks = get_breaks(
        statistics[metric_column],
        fixed_breaks=fixed_breaks,
    )


    # -----------------------------------------------------
    # 현재 전국 평균
    # -----------------------------------------------------

    weighted_value = None

    if metric_column == "고령화율":

        total = statistics["전체인구"].sum()
        elderly = statistics["고령인구"].sum()

        if total > 0:
            weighted_value = (
                elderly / total * 100
            )

    elif metric_column == "유소년비율":

        total = statistics["전체인구"].sum()
        children = statistics["유소년인구"].sum()

        if total > 0:
            weighted_value = (
                children / total * 100
            )

    elif metric_column == "생산연령비율":

        total = statistics["전체인구"].sum()
        working = statistics["생산연령인구"].sum()

        if total > 0:
            weighted_value = (
                working / total * 100
            )

    elif metric_column == "노년부양비":

        working = statistics["생산연령인구"].sum()
        elderly = statistics["고령인구"].sum()

        if working > 0:
            weighted_value = (
                elderly / working * 100
            )


    if weighted_value is not None:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-name">
                    {latest_year}년 전국 기준
                </div>

                <div class="metric-value">
                    {weighted_value:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    # -----------------------------------------------------
    # 지도
    # -----------------------------------------------------

    map_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": feature["type"],
                "geometry": feature["geometry"],
                "properties": dict(
                    feature["properties"]
                ),
            }
            for feature in geojson["features"]
        ],
    }

    map_geojson = attach_metric(
        map_geojson,
        statistics,
        metric_column,
    )

    fig = create_map(
        map_geojson,
        breaks,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


    # -----------------------------------------------------
    # 순위표
    # -----------------------------------------------------

    high, low = make_rank_tables(
        statistics,
        names,
        metric_column,
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


    st.caption(
        "지도 색상 구간: "
        + " / ".join(
            make_legend(breaks)
        )
    )


# =========================================================
# 앱 제목
# =========================================================

st.markdown(
    """
    <div class="badge">
        전국 인구통계 DATA PLAYGROUND
    </div>

    <div class="title">
        우리나라 인구,
        <span class="pink">팝팝</span>
        뜯어보기
        <span class="bounce">✦</span>
        <span class="bounce">●</span>
        <span class="bounce">✧</span>
    </div>

    <div class="subtitle">
        시군구별 인구구조를 지도와 숫자로 한눈에 살펴보세요.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 준비
# =========================================================

try:

    with st.spinner(
        "인구 데이터를 가져오는 중..."
    ):

        population = load_population()

        latest_year, statistics = (
            calculate_statistics(
                population
            )
        )

        national_trend = (
            calculate_national_trend(
                population
            )
        )

        geojson = load_geojson()

except Exception as e:

    st.error(
        "데이터를 불러오지 못했습니다."
    )

    st.exception(e)

    st.stop()


# =========================================================
# 지도 지역명 데이터
# =========================================================

names = pd.DataFrame(
    [
        {
            "시군구코드": feature[
                "properties"
            ].get(
                "코드",
                "",
            ),

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

names["시군구코드"] = (
    names["시군구코드"]
    .astype("string")
    .str.zfill(5)
)


# =========================================================
# 최신 연도 카드
# =========================================================

st.markdown(
    f"""
    <div class="year-card">
        <div class="year-label">
            기준 연도
        </div>

        <div class="year-value">
            {latest_year}년 전국 시군구
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "가장 최신 연도의 읍·면·동 인구를 시군구 단위로 합산했습니다."
)


# =========================================================
# 탭
# =========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "고령화율",
        "유소년인구",
        "생산연령인구",
        "노년부양비",
        "전국 인구 추이",
    ]
)


# =========================================================
# 1. 고령화율
# =========================================================

with tab1:

    render_metric_tab(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="고령화율",
        description=(
            "65세 이상 인구가 전체 인구에서 차지하는 비율입니다."
        ),
        metric_column="고령화율",
        latest_year=latest_year,

        # 사용자가 지정한 고정 구간
        fixed_breaks=[
            19,
            23,
            28,
            38,
        ],
    )


# =========================================================
# 2. 유소년인구
# =========================================================

with tab2:

    render_metric_tab(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="유소년인구 비율",
        description=(
            "0~14세 인구가 전체 인구에서 차지하는 비율입니다."
        ),
        metric_column="유소년비율",
        latest_year=latest_year,
    )


# =========================================================
# 3. 생산연령인구
# =========================================================

with tab3:

    render_metric_tab(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="생산연령인구 비율",
        description=(
            "15~64세 인구가 전체 인구에서 차지하는 비율입니다."
        ),
        metric_column="생산연령비율",
        latest_year=latest_year,
    )


# =========================================================
# 4. 노년부양비
# =========================================================

with tab4:

    render_metric_tab(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="노년부양비",
        description=(
            "생산연령인구 100명이 부양해야 하는 65세 이상 인구의 수입니다."
        ),
        metric_column="노년부양비",
        latest_year=latest_year,
    )


# =========================================================
# 5. 전국 인구 추이
# =========================================================

with tab5:

    st.markdown(
        """
        <div class="section-title">
            전국 인구 추이
        </div>

        <div class="section-description">
            2015년부터 가장 최신 연도까지 전국 인구가 어떻게 변했는지 살펴봅니다.
        </div>
        """,
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # 최신 인구
    # -----------------------------------------------------

    latest_population = national_trend.iloc[-1][
        "전체인구"
    ]

    first_population = national_trend.iloc[0][
        "전체인구"
    ]

    change = (
        latest_population
        - first_population
    )

    change_percent = (
        change
        / first_population
        * 100
        if first_population > 0
        else np.nan
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-name">
                    최신 연도 전국 인구
                </div>

                <div class="metric-value">
                    {latest_population:,.0f}명
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    with col2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-name">
                    {int(national_trend.iloc[0]["연도"])}년 대비 변화
                </div>

                <div class="metric-value">
                    {change:+,.0f}명
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    with col3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-name">
                    전체 변화율
                </div>

                <div class="metric-value">
                    {change_percent:+.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    # -----------------------------------------------------
    # 그래프
    # -----------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=national_trend["연도"],
            y=national_trend["전체인구"],
            mode="lines+markers",
            line=dict(
                color="#E76582",
                width=4,
            ),
            marker=dict(
                color="#FFFFFF",
                size=9,
                line=dict(
                    color="#E76582",
                    width=3,
                ),
            ),
            hovertemplate=(
                "%{x}년<br>"
                "전국 인구: %{y:,.0f}명"
                "<extra></extra>"
            ),
        )
    )


    fig.update_layout(
        height=520,

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",

        xaxis=dict(
            title="연도",
            dtick=1,
            showgrid=False,
        ),

        yaxis=dict(
            title="인구",
            tickformat=",",
            gridcolor="#F0E5E8",
        ),

        hoverlabel=dict(
            bgcolor="#FFF9FB",
            bordercolor="#E76582",
            font=dict(
                size=14,
                color="#46333B",
            ),
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )


    # -----------------------------------------------------
    # 연도별 표
    # -----------------------------------------------------

    trend_table = national_trend.copy()

    trend_table["연도"] = (
        trend_table["연도"]
        .astype(int)
        .astype(str)
        + "년"
    )

    trend_table["전체인구"] = (
        trend_table["전체인구"]
        .map(
            lambda x: f"{x:,.0f}명"
        )
    )

    trend_table = trend_table.rename(
        columns={
            "연도": "연도",
            "전체인구": "전국 인구",
        }
    )

    st.dataframe(
        trend_table,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 하단 설명
# =========================================================

st.markdown(
    f"""
    <div class="footer">
        {latest_year}년 최신 읍·면·동 인구 데이터를 기준으로 계산했습니다.
        <br>
        시군구는 읍·면·동 행정코드 앞 5자리를 이용해 연결했습니다.
        <br>
        고령화율 = 65세 이상 인구 ÷ 전체 인구 × 100
        &nbsp; · &nbsp;
        노년부양비 = 65세 이상 인구 ÷ 15~64세 인구 × 100
    </div>
    """,
    unsafe_allow_html=True,
)
