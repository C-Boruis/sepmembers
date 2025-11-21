import streamlit as st
import pandas as pd
import os
import time

# -----------------------------------------------------------------------------
# 1. 설정 및 초기화
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울은평교회 성도 관리 시스템",
    page_icon="⛪",
    layout="wide"
)

# 데이터 파일 경로 설정
DATA_DIR = "data"
MEMBERS_FILE = "members.csv"
ACCOUNTS_FILE = "accounts.csv"
IMAGES_DIR = "2025년_Images"  # 사진이 저장된 폴더명 (CSV 내 경로와 일치해야 함)

# 폴더가 없으면 생성
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -----------------------------------------------------------------------------
# 2. 헬퍼 함수 (데이터 로드/저장)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60) # 캐시 기능으로 속도 향상
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        # 한글 깨짐 방지를 위해 utf-8-sig 또는 cp949 시도
        return pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        try:
            return pd.read_csv(file_path, encoding='cp949')
        except Exception as e:
            st.error(f"파일 로드 오류: {e}")
            return None

def save_data_to_csv(df):
    # CSV 문자열로 변환 (다운로드용)
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# -----------------------------------------------------------------------------
# 3. 데이터 전처리 (차량번호 추가 등)
# -----------------------------------------------------------------------------
def preprocess_members(df):
    # 필수 컬럼이 없으면 생성
    required_columns = [
        '교구', '구역', '사진', '이름', '생년', '구원일', '전화번호', 
        '자택전화 / 주소', '교제부서', '직분', '봉사부서', '가족', '차량번호'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = "" # 컬럼 추가
            
    # 결측치 처리
    df = df.fillna("")
    return df

# -----------------------------------------------------------------------------
# 4. 인증 (로그인) 함수
# -----------------------------------------------------------------------------
def login_section():
    st.markdown("## ⛪ 서울은평교회 성도 관리 시스템")
    
    # 계정 파일 로드 또는 생성
    if not os.path.exists(ACCOUNTS_FILE):
        # 초기 관리자 계정 생성
        init_accounts = pd.DataFrame({
            'id': ['admin'],
            'pw': ['1234'], # 실제 운영시 복잡한 비번 사용 권장
            'name': ['관리자'],
            'role': ['admin']
        })
        init_accounts.to_csv(ACCOUNTS_FILE, index=False, encoding='utf-8-sig')
        
    accounts = load_data(ACCOUNTS_FILE)

    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            user = accounts[(accounts['id'] == username) & (accounts['pw'] == password)]
            if not user.empty:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.iloc[0]['name']
                st.session_state['role'] = user.iloc[0]['role']
                st.success(f"{user.iloc[0]['name']}님 환영합니다!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 잘못되었습니다.")

# -----------------------------------------------------------------------------
# 5. 메인 기능 탭
# -----------------------------------------------------------------------------
def main_app():
    # 사이드바 (로그아웃)
    with st.sidebar:
        st.write(f"**{st.session_state['username']}** ({st.session_state['role']})님 접속 중")
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.divider()
        st.info("💡 데이터 수정 후 반드시 [변경사항 다운로드]를 하여 GitHub에 업로드해주세요.")

    # 데이터 로드
    if 'members_df' not in st.session_state:
        uploaded_file = st.sidebar.file_uploader("최신 명단 파일 업로드 (.csv)", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig') # 혹은 cp949
            st.session_state['members_df'] = preprocess_members(df)
        elif os.path.exists(MEMBERS_FILE):
            df = load_data(MEMBERS_FILE)
            st.session_state['members_df'] = preprocess_members(df)
        else:
            st.session_state['members_df'] = pd.DataFrame(columns=[
                '교구', '구역', '사진', '이름', '생년', '구원일', '전화번호', 
                '자택전화 / 주소', '교제부서', '직분', '봉사부서', '가족', '차량번호'
            ])

    df = st.session_state['members_df']

    # 탭 구성
    if st.session_state['role'] == 'admin':
        tab1, tab2, tab3 = st.tabs(["📖 성도 주소록", "🛠 성도 관리 (수정)", "⚙️ 계정 관리"])
    else:
        tab1 = st.tabs(["📖 성도 주소록"])[0]

    # --- TAB 1: 성도 주소록 (조회용) ---
    with tab1:
        st.header("성도 주소록")
        
        # 1. 필터 및 검색 (Filter)
        col1, col2, col3 = st.columns(3)
        with col1:
            # 교구 선택 (전체 포함)
            parish_list = ["전체"] + sorted(list(df['교구'].unique()))
            selected_parish = st.selectbox("교구 선택", parish_list)
        
        with col2:
            # 구역 선택 (교구에 따라 동적 변경)
            if selected_parish != "전체":
                district_options = sorted(df[df['교구'] == selected_parish]['구역'].unique())
            else:
                district_options = sorted(df['구역'].unique())
            
            district_list = ["전체"] + list(district_options)
            selected_district = st.selectbox("구역 선택", district_list)

        with col3:
            search_keyword = st.text_input("검색 (이름, 전화번호, 차량번호)")

        # 2. 데이터 필터링 로직
        filtered_df = df.copy()
        if selected_parish != "전체":
            filtered_df = filtered_df[filtered_df['교구'] == selected_parish]
        if selected_district != "전체":
            filtered_df = filtered_df[filtered_df['구역'] == selected_district]
        
        if search_keyword:
            # 이름, 전화번호, 차량번호 중 하나라도 포함되면 검색
            mask = (
                filtered_df['이름'].astype(str).str.contains(search_keyword) | 
                filtered_df['전화번호'].astype(str).str.contains(search_keyword) |
                filtered_df['차량번호'].astype(str).str.contains(search_keyword)
            )
            filtered_df = filtered_df[mask]

        st.markdown(f"**총 {len(filtered_df)}명 검색됨**")
        st.divider()

        # 3. 카드 형태 출력 (Card View)
        if filtered_df.empty:
            st.info("검색 결과가 없습니다.")
        else:
            # 2열로 카드 배치
            for i in range(0, len(filtered_df), 2):
                cols = st.columns(2)
                # 현재 줄의 데이터 가져오기
                batch = filtered_df.iloc[i:i+2]
                
                for idx, (index, person) in enumerate(batch.iterrows()):
                    with cols[idx]:
                        with st.container(border=True):
                            c1, c2 = st.columns([1, 2])
                            
                            # 사진 표시
                            with c1:
                                img_path = person['사진'] if pd.notna(person['사진']) else ""
                                # 로컬 경로 또는 웹 이미지 처리
                                if img_path and os.path.exists(img_path):
                                    st.image(img_path, use_column_width=True)
                                else:
                                    st.image("https://via.placeholder.com/150?text=No+Image", use_column_width=True)
                                
                                st.caption(f"{person['직분']}")

                            # 정보 표시
                            with c2:
                                st.subheader(f"{person['이름']} ({person['생년']})")
                                st.text(f"{person['교구']} / {person['구역']}")
                                st.text(f"📞 {person['전화번호']}")
                                
                                # 구글 지도 링크 생성
                                address = str(person['자택전화 / 주소'])
                                # 주소에서 전화번호 부분 제거하고 순수 주소만 추출하는 로직 필요할 수 있음
                                # 여기선 간단히 전체 텍스트로 검색
                                map_url = f"https://www.google.com/maps/search/?api=1&query={address}"
                                st.markdown(f"[📍 지도 보기]({map_url})")
                                
                                st.text(f"🎂 구원일: {person['구원일']}")
                                if person['차량번호']:
                                    st.markdown(f"🚗 **{person['차량번호']}**")
                                
                                with st.expander("상세 정보"):
                                    st.write(f"**가족:** {person['가족']}")
                                    st.write(f"**봉사:** {person['봉사부서']}")
                                    st.write(f"**주소:** {address}")

    # --- TAB 2: 성도 관리 (Admin Only) ---
    if st.session_state['role'] == 'admin':
        with tab2:
            st.header("🛠 성도 데이터 관리")
            st.warning("수정 후 반드시 하단의 [변경된 엑셀 다운로드]를 눌러 파일을 저장하세요.")

            # 데이터 에디터 (엑셀처럼 편집 가능)
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic", # 행 추가/삭제 가능
                use_container_width=True,
                key="editor"
            )

            # 상태 업데이트
            if not edited_df.equals(st.session_state['members_df']):
                st.session_state['members_df'] = edited_df
                st.success("변경사항이 임시 저장되었습니다. (아래 버튼으로 파일 다운로드 필요)")

            st.divider()
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                # CSV 다운로드 버튼
                csv_data = save_data_to_csv(edited_df)
                st.download_button(
                    label="💾 변경된 명단 다운로드 (CSV)",
                    data=csv_data,
                    file_name="members_updated.csv",
                    mime="text/csv"
                )
            with col_d2:
                st.info("다운로드 받은 파일을 GitHub의 'members.csv'에 덮어씌우면 영구 반영됩니다.")

    # --- TAB 3: 계정 관리 (Admin Only) ---
    if st.session_state['role'] == 'admin':
        with tab3:
            st.header("⚙️ 계정 관리")
            
            if os.path.exists(ACCOUNTS_FILE):
                acc_df = load_data(ACCOUNTS_FILE)
            else:
                acc_df = pd.DataFrame(columns=['id', 'pw', 'name', 'role'])

            # 계정 편집기
            edited_acc_df = st.data_editor(
                acc_df,
                num_rows="dynamic",
                use_container_width=True,
                key="acc_editor"
            )
            
            # 계정 저장 버튼
            acc_csv = save_data_to_csv(edited_acc_df)
            st.download_button(
                label="💾 계정 목록 다운로드 (CSV)",
                data=acc_csv,
                file_name="accounts_updated.csv",
                mime="text/csv"
            )

# -----------------------------------------------------------------------------
# 6. 실행 진입점
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        login_section()
    else:
        main_app()