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
    page_icon="👥",
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
    .stApp {
        background:
            radial-gradient(
                circle at 5% 5%,
                rgba(255, 236, 174, 0.35),
                transparent 18%
            ),
            radial-gradient(
                circle at 95% 5%,
                rgba(255, 207, 222, 0.35),
                transparent 20%
            ),
            #FFFDF9;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .cute-title {
        color: #46333B;
        font-size: 2.7rem;
        font-weight: 900;
        letter-spacing: -2px;
        line-height: 1.2;
    }

    .pink {
        color: #E76582;
    }

    .sub-text {
        color: #927982;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 20px;
    }

    .badge {
        display: inline-block;
        background: #FFE1E9;
        color: #C65070;
        border: 1px solid #F4C9D5;
        border-radius: 999px;
        padding: 5px 13px;
        font-size: 0.8rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .guide {
        background: linear-gradient(
            100deg,
            #FFF1C9,
            #FFE5EE
        );
        border: 1px solid #F1D6DE;
        border-radius: 16px;
        padding: 11px 15px;
        margin: 8px 0 12px 0;
        color: #735861;
        font-weight: 700;
    }

    .section-title {
        color: #46333B;
        font-size: 1.45rem;
        font-weight: 900;
        margin-top: 15px;
        margin-bottom: 3px;
    }

    .section-description {
        color: #927C84;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }

    [data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid #F0E0E4;
        border-radius: 22px;
        padding: 4px;
        box-shadow: 0 10px 28px rgba(80, 50, 60, 0.08);
    }

    .rank-high {
        background: #FFE4EA;
        color: #B84E68;
        border: 1px solid #F4CDD6;
        border-radius: 16px;
        padding: 12px 15px;
        margin-bottom: 8px;
        font-weight: 900;
    }

    .rank-low {
        background: #DDF7EF;
        color: #378875;
        border: 1px solid #C8E9DF;
        border-radius: 16px;
        padding: 12px 15px;
        margin-bottom: 8px;
        font-weight: 900;
    }

    .footer {
        text-align: center;
        color: #A58F96;
        font-size: 0.8rem;
        margin-top: 25px;
        line-height: 1.8;
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
    """전국 읍·면·동 인구 데이터를 불러옵니다."""

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

    # 코드는 숫자가 아니라 행정구역 식별자입니다.
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
# 나이별 열 찾기
# =========================================================

def age_columns(df, start_age, end_age):
    """지정한 나이 범위의 '계_' 열을 찾습니다."""

    columns = []

    for age in range(start_age, end_age + 1):
        column = f"계_{age}세"

        if column in df.columns:
            columns.append(column)

    return columns


# =========================================================
# 시군구별 통계 계산
# =========================================================

@st.cache_data
def calculate_statistics(df):

    latest_year = int(df["연도"].max())

    data = df[
        df["연도"] == latest_year
    ].copy()

    # 읍·면·동 코드 앞 5자리 = 시군구 코드
    data["시군구코드"] = data["코드"].str[:5]

    # 전체
    total_cols = age_columns(
        data,
        0,
        99,
    )

    if "계_100세 이상" in data.columns:
        total_cols.append("계_100세 이상")

    # 0~14세
    child_cols = age_columns(
        data,
        0,
        14,
    )

    # 15~64세
    working_cols = age_columns(
        data,
        15,
        64,
    )

    # 65세 이상
    elderly_cols = age_columns(
        data,
        65,
        99,
    )

    if "계_100세 이상" in data.columns:
        elderly_cols.append("계_100세 이상")

    # 숫자 변환
    all_cols = set(
        total_cols
        + child_cols
        + working_cols
        + elderly_cols
    )

    for column in all_cols:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        ).fillna(0)

    # 읍·면·동별 인구
    data["전체인구"] = data[
        total_cols
    ].sum(axis=1)

    data["유소년인구"] = data[
        child_cols
    ].sum(axis=1)

    data["생산연령인구"] = data[
        working_cols
    ].sum(axis=1)

    data["고령인구"] = data[
        elderly_cols
    ].sum(axis=1)

    # 시군구 합계
    result = (
        data
        .groupby(
            "시군구코드",
            as_index=False,
        )
        .agg(
            전체인구=("전체인구", "sum"),
            유소년인구=("유소년인구", "sum"),
            생산연령인구=("생산연령인구", "sum"),
            고령인구=("고령인구", "sum"),
        )
    )

    # 고령화율
    result["고령화율"] = np.where(
        result["전체인구"] > 0,
        result["고령인구"]
        / result["전체인구"]
        * 100,
        np.nan,
    )

    # 유소년 비율
    result["유소년비율"] = np.where(
        result["전체인구"] > 0,
        result["유소년인구"]
        / result["전체인구"]
        * 100,
        np.nan,
    )

    # 생산연령인구 비율
    result["생산연령비율"] = np.where(
        result["전체인구"] > 0,
        result["생산연령인구"]
        / result["전체인구"]
        * 100,
        np.nan,
    )

    # 노년부양비
    result["노년부양비"] = np.where(
        result["생산연령인구"] > 0,
        result["고령인구"]
        / result["생산연령인구"]
        * 100,
        np.nan,
    )

    return latest_year, result


# =========================================================
# 전국 인구 추이
# =========================================================

@st.cache_data
def calculate_national_trend(df):

    total_cols = age_columns(
        df,
        0,
        99,
    )

    if "계_100세 이상" in df.columns:
        total_cols.append("계_100세 이상")

    data = df[
        ["연도"] + total_cols
    ].copy()

    for column in total_cols:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        ).fillna(0)

    data["전체인구"] = data[
        total_cols
    ].sum(axis=1)

    return (
        data
        .groupby(
            "연도",
            as_index=False,
        )["전체인구"]
        .sum()
        .sort_values("연도")
    )


# =========================================================
# GeoJSON에 지표 연결
# =========================================================

def attach_metric(
    geojson,
    statistics,
    metric_column,
):

    value_map = (
        statistics
        .set_index("시군구코드")
        [metric_column]
        .to_dict()
    )

    for feature in geojson["features"]:

        props = feature["properties"]

        code = str(
            props.get("코드", "")
        ).strip().zfill(5)

        props["코드"] = code

        props["지도값"] = value_map.get(
            code,
            np.nan,
        )

    return geojson


# =========================================================
# 색상 구간
# =========================================================

def get_breaks(
    values,
    fixed_breaks=None,
):

    if fixed_breaks is not None:
        return fixed_breaks

    values = pd.Series(values).dropna()

    if values.empty:
        return [
            20,
            40,
            60,
            80,
        ]

    result = np.nanpercentile(
        values,
        [20, 40, 60, 80],
    )

    return [
        float(value)
        for value in result
    ]


def classify(
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


def legend_labels(breaks):

    b1, b2, b3, b4 = breaks

    return [
        f"{b1:.1f}% 미만",
        f"{b1:.1f}~{b2:.1f}%",
        f"{b2:.1f}~{b3:.1f}%",
        f"{b3:.1f}~{b4:.1f}%",
        f"{b4:.1f}% 이상",
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
        ]["단계"] = classify(
            value,
            breaks,
        )

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

    locations = [
        feature[
            "properties"
        ]["코드"]
        for feature in geojson["features"]
    ]

    stages = [
        feature[
            "properties"
        ]["단계"]
        for feature in geojson["features"]
    ]

    customdata = [
        [
            feature[
                "properties"
            ].get("시군구", ""),
            feature[
                "properties"
            ].get("시도", ""),
            feature[
                "properties"
            ].get("지도값", np.nan),
        ]
        for feature in geojson["features"]
    ]

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

            # hover는 단순 텍스트만 사용합니다.
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "시도: %{customdata[1]}<br>"
                "수치: %{customdata[2]:.1f}%"
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
                tickvals=[0, 1, 2, 3, 4],
                ticktext=legend_labels(breaks),
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
# 지표별 화면
# =========================================================

def render_metric(
    geojson,
    statistics,
    names,
    title,
    description,
    metric_column,
    fixed_breaks=None,
):

    st.markdown(
        f"### {title}"
    )

    st.write(description)

    st.info(
        "지도에 마우스를 올리면 시군구별 수치를 확인할 수 있어요."
    )

    # 지도 구간
    breaks = get_breaks(
        statistics[metric_column],
        fixed_breaks,
    )

    # 지도 데이터 복사
    map_geojson = {
        "type": "FeatureCollection",
        "features": [],
    }

    for feature in geojson["features"]:

        map_geojson["features"].append(
            {
                "type": feature["type"],
                "geometry": feature["geometry"],
                "properties": dict(
                    feature["properties"]
                ),
            }
        )

    map_geojson = attach_metric(
        map_geojson,
        statistics,
        metric_column,
    )

    # 지도
    fig = create_map(
        map_geojson,
        breaks,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # 순위
    high, low = make_rank_tables(
        statistics,
        names,
        metric_column,
    )

    left, right = st.columns(2)

    with left:

        st.markdown(
            '<div class="rank-high">높은 곳 TOP 10</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            high,
            use_container_width=True,
            height=400,
        )

    with right:

        st.markdown(
            '<div class="rank-low">낮은 곳 TOP 10</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            low,
            use_container_width=True,
            height=400,
        )

    st.caption(
        "지도 구간: "
        + " / ".join(
            legend_labels(breaks)
        )
    )


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="badge">전국 인구통계 DATA PLAYGROUND</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="cute-title">
        우리나라 인구,
        <span class="pink">팝팝</span>
        뜯어보기
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "시군구별 인구구조를 지도와 숫자로 한눈에 살펴보세요."
)

st.markdown("---")


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

except Exception as error:

    st.error(
        "데이터를 불러오지 못했습니다."
    )

    st.exception(error)

    st.stop()


# =========================================================
# 지역명
# =========================================================

names = pd.DataFrame(
    [
        {
            "시군구코드": str(
                feature["properties"].get(
                    "코드",
                    "",
                )
            ).zfill(5),

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


# =========================================================
# 중요: 기준 연도는 HTML을 사용하지 않음
# =========================================================

st.subheader("기준 연도")

st.metric(
    label="가장 최신 연도",
    value=f"{latest_year}년",
)

st.caption(
    "가장 최신 연도의 읍·면·동 인구를 사용합니다."
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

    render_metric(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="고령화율",
        description=(
            "65세 이상 인구가 전체 인구에서 차지하는 비율입니다."
        ),
        metric_column="고령화율",
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

    render_metric(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="유소년인구 비율",
        description=(
            "0~14세 인구가 전체 인구에서 차지하는 비율입니다."
        ),
        metric_column="유소년비율",
    )


# =========================================================
# 3. 생산연령인구
# =========================================================

with tab3:

    render_metric(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="생산연령인구 비율",
        description=(
            "15~64세 인구가 전체 인구에서 차지하는 비율입니다."
        ),
        metric_column="생산연령비율",
    )


# =========================================================
# 4. 노년부양비
# =========================================================

with tab4:

    render_metric(
        geojson=geojson,
        statistics=statistics,
        names=names,
        title="노년부양비",
        description=(
            "생산연령인구 100명에 해당하는 65세 이상 인구의 수입니다."
        ),
        metric_column="노년부양비",
    )


# =========================================================
# 5. 전국 인구 추이
# =========================================================

with tab5:

    st.subheader("전국 인구 추이")

    st.write(
        "2015년부터 가장 최신 연도까지 전국 인구 변화를 보여줍니다."
    )

    # ---------------------------------------------
    # 전국 기준값
    # ---------------------------------------------

    first_row = national_trend.iloc[0]
    latest_row = national_trend.iloc[-1]

    first_population = float(
        first_row["전체인구"]
    )

    latest_population = float(
        latest_row["전체인구"]
    )

    difference = (
        latest_population
        - first_population
    )

    if first_population != 0:
        difference_rate = (
            difference
            / first_population
            * 100
        )
    else:
        difference_rate = np.nan


    # ---------------------------------------------
    # 중요:
    # '전국 기준'을 HTML로 만들지 않습니다.
    # Streamlit 기본 metric을 사용합니다.
    # ---------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            label="최신 연도 전국 인구",
            value=f"{latest_population:,.0f}명",
        )

    with col2:

        st.metric(
            label=f"{int(first_row['연도'])}년 대비",
            value=f"{difference:+,.0f}명",
        )

    with col3:

        st.metric(
            label="전체 변화율",
            value=f"{difference_rate:+.1f}%",
        )


    # ---------------------------------------------
    # 그래프
    # ---------------------------------------------

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
                color="white",
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


    # ---------------------------------------------
    # 연도별 표
    # ---------------------------------------------

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
# 하단
# =========================================================

st.markdown("---")

st.caption(
    f"{latest_year}년 최신 읍·면·동 인구 데이터를 기준으로 계산했습니다."
)

st.caption(
    "시군구는 행정동 코드 앞 5자리를 이용해 지도와 연결했습니다."
)

st.caption(
    "고령화율 = 65세 이상 인구 ÷ 전체 인구 × 100"
)

st.caption(
    "노년부양비 = 65세 이상 인구 ÷ 15~64세 인구 × 100"
)
