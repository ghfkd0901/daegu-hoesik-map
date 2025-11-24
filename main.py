import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# -----------------------------------
# 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="대구 회식 장소 지도",
    layout="wide",
)

st.title("🍻 대구 회식 장소 지도")

st.write("""
이 지도는 대구광역시 공식 맛집 플랫폼인  
[**대구푸드**](https://www.daegufood.go.kr/kor/) API 데이터를 기반으로 제작되었습니다.  
좌석 수, 룸 수, 주차 가능 대수를 기준으로 회식 장소를 쉽게 찾을 수 있도록 만든 도구입니다.
""")

# -----------------------------------
# CSV 로드
# -----------------------------------
# 프로젝트 내 data 파일 상대경로
FILE_PATH = os.path.join("daegu_food_final.csv")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.dropna(subset=["lat", "lon"])
    return df

df = load_data(FILE_PATH)

# -----------------------------------
# 이모지 매핑
# -----------------------------------
emoji_map = {
    "한식": "🍚",
    "일식": "🍣",
    "중식": "🥟",
    "양식": "🍕",
    "디저트/베이커리": "🍰",
    "주점": "🍺",
    "고기": "🍖",
}

def get_emoji(category):
    return emoji_map.get(category, "🍽")

# -----------------------------------
# 지도 스타일 옵션
# -----------------------------------
tile_options = {
    "밝은 지도 (CartoDB Positron)": "CartoDB positron",
    "화이트 지도 (CartoDB Voyager)": "CartoDB Voyager",
    "모던 라이트 (Stamen Toner Lite)": "Stamen Toner Lite",
    "일반 지도 (OpenStreetMap)": "OpenStreetMap",
}

# -----------------------------------
# 필터 UI
# -----------------------------------
st.sidebar.header("필터")

# 지도 스타일 선택 추가
selected_tile = st.sidebar.selectbox("지도 스타일 선택", list(tile_options.keys()))

# 구 선택
gu_list = sorted(df["GU"].unique().tolist())
selected_gu = st.sidebar.multiselect("구 선택", gu_list, default=gu_list)
df_filtered = df[df["GU"].isin(selected_gu)]

# 음식 종류 선택
fd_list = sorted(df["FD_CS"].unique().tolist())
selected_fd = st.sidebar.multiselect("음식 종류", fd_list, default=fd_list)
df_filtered = df_filtered[df_filtered["FD_CS"].isin(selected_fd)]

# 최소 좌석 수 (슬라이더)
max_seat = int(df_filtered["SEAT_CNT_NUM"].max())
min_seat = st.sidebar.slider("최소 좌석 수", 0, max_seat, 0)
df_filtered = df_filtered[df_filtered["SEAT_CNT_NUM"] >= min_seat]

# 최소 룸 수 (슬라이더)
max_room = int(df_filtered["ROOM_CNT"].max())
min_room = st.sidebar.slider("최소 룸 수", 0, max_room, 0)
df_filtered = df_filtered[df_filtered["ROOM_CNT"] >= min_room]

# 룸만 보기
room_only = st.sidebar.checkbox("룸 있는 곳만 보기", value=False)
if room_only:
    df_filtered = df_filtered[df_filtered["ROOM_CNT"] >= 1]

# 최소 주차 대수 (슬라이더)
max_park = int(df_filtered["PKPL_NUM"].max())
min_park = st.sidebar.slider("최소 주차 가능 대수", 0, max_park, 0)
df_filtered = df_filtered[df_filtered["PKPL_NUM"] >= min_park]

# -----------------------------------
# 상단 정보 표시
# -----------------------------------
st.write(f"**전체 식당 수:** {len(df):,}개  │  **필터 후 식당 수:** {len(df_filtered):,}개")

# -----------------------------------
# 지도 생성
# -----------------------------------
center = [df_filtered["lat"].mean(), df_filtered["lon"].mean()]
tile_to_use = tile_options[selected_tile]

m = folium.Map(location=center, zoom_start=12, tiles=tile_to_use)

# -----------------------------------
# 마커 생성 (이모지 포함)
# -----------------------------------
for _, row in df_filtered.iterrows():
    emoji = get_emoji(row["FD_CS"])

    icon_html = f"""
    <div style="font-size:24px; text-align:center;">
        {emoji}
    </div>
    """

    icon = folium.DivIcon(
        html=icon_html,
        icon_size=(24, 24),
        icon_anchor=(12, 12)
    )

    popup_html = f"""
    <b>{row['BZ_NM']}</b><br>
    {row['GNG_CS']}<br>
    좌석수: {row['SEAT_CNT_NUM']}<br>
    룸: {row['ROOM_CNT']}개<br>
    주차 가능: {row['PKPL_NUM']}대<br><br>
    <a href="https://map.naver.com/p/search/{row['BZ_NM']}" target="_blank">네이버 지도</a><br>
    <a href="https://map.kakao.com/?q={row['BZ_NM']}" target="_blank">카카오 지도</a>
    """

    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=folium.Popup(popup_html, max_width=250),
        icon=icon
    ).add_to(m)

# -----------------------------------
# Streamlit에 지도 출력
# -----------------------------------
st_folium(m, width="100%", height=650)

# -----------------------------------
# 데이터 테이블 표시 (열 이름 한국어로 변경)
# -----------------------------------
st.subheader("식당 리스트")

df_kor = df_filtered.rename(columns={
    "GU": "구",
    "FD_CS": "음식종류",
    "BZ_NM": "가게명",
    "GNG_CS": "주소",
    "SEAT_CNT_NUM": "좌석수",
    "ROOM_CNT": "룸수",
    "PKPL_NUM": "주차대수",
    "TLNO": "전화번호",
    "MBZ_HR": "영업시간"
})

show_cols = ["구", "음식종류", "가게명", "주소", "좌석수", "룸수", "주차대수", "전화번호", "영업시간"]

st.dataframe(df_kor[show_cols].reset_index(drop=True), height=300)
