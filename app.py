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
IMAGES_DIR = "2025년_Images" 

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -----------------------------------------------------------------------------
# 2. 헬퍼 함수 (데이터 로드/저장)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        # 모든 데이터를 문자열(String)로 읽어오도록 강제 (오류 방지 핵심)
        return pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
    except:
        try:
            return pd.read_csv(file_path, encoding='cp949', dtype=str)
        except Exception as e:
            st.error(f"파일 로드 오류: {e}")
            return None

def save_data_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# -----------------------------------------------------------------------------
# 3. 데이터 전처리
# -----------------------------------------------------------------------------
def preprocess_members(df):
    required_columns = [
        '교구', '구역', '사진', '이름', '생년', '구원일', '전화번호', 
        '자택전화 / 주소', '교제부서', '직분', '봉사부서', '가족', '차량번호'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
            
    df = df.fillna("")
    return df

# -----------------------------------------------------------------------------
# 4. 인증 (로그인) 함수 - [수정됨]
# -----------------------------------------------------------------------------
def login_section():
    st.markdown("## ⛪ 서울은평교회 성도 관리 시스템")
    
    # 계정 파일 로드 또는 생성
    if not os.path.exists(ACCOUNTS_FILE):
        init_accounts = pd.DataFrame({
            'id': ['admin'],
            'pw': ['1234'],
            'name': ['관리자'],
            'role': ['admin']
        })
        init_accounts.to_csv(ACCOUNTS_FILE, index=False, encoding='utf-8-sig')
        
    accounts = load_data(ACCOUNTS_FILE)

    # [중요] 강제 형변환 (숫자로 적혀있어도 문자로 변환) & 공백 제거
    if accounts is not None:
        accounts['id'] = accounts['id'].astype(str).str.strip()
        accounts['pw'] = accounts['pw'].astype(str).str.strip()

    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            # 입력값도 앞뒤 공백 제거
            clean_username = str(username).strip()
            clean_password = str(password).strip()

            user = accounts[(accounts['id'] == clean_username) & (accounts['pw'] == clean_password)]
            
            if not user.empty:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.iloc[0]['name']
                st.session_state['role'] = user.iloc[0]['role']
                st.success(f"{user.iloc[0]['name']}님 환영합니다!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 잘못되었습니다.")
                # 디버깅용 (배포 후 문제 해결되면 주석 처리하거나 삭제하세요)
                # st.write("--- 디버깅 정보 (보안 주의) ---")
                # st.write(f"입력한 ID: {clean_username}, 입력한 PW: {clean_password}")
                # st.write("저장된 계정 목록:")
                # st.dataframe(accounts)

# -----------------------------------------------------------------------------
# 5. 메인 기능 탭
# -----------------------------------------------------------------------------
def main_app():
    with st.sidebar:
        st.write(f"**{st.session_state['username']}** ({st.session_state['role']})님 접속 중")
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.divider()
        st.info("💡 데이터 수정 후 반드시 [변경사항 다운로드]를 하여 GitHub에 업로드해주세요.")

    if 'members_df' not in st.session_state:
        uploaded_file = st.sidebar.file_uploader("최신 명단 파일 업로드 (.csv)", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig', dtype=str)
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

    if st.session_state['role'] == 'admin':
        tab1, tab2, tab3 = st.tabs(["📖 성도 주소록", "🛠 성도 관리 (수정)", "⚙️ 계정 관리"])
    else:
        tab1 = st.tabs(["📖 성도 주소록"])[0]

    # --- TAB 1: 성도 주소록 ---
    with tab1:
        st.header("성도 주소록")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            parish_list = ["전체"] + sorted(list(df['교구'].unique()))
            selected_parish = st.selectbox("교구 선택", parish_list)
        
        with col2:
            if selected_parish != "전체":
                district_options = sorted(df[df['교구'] == selected_parish]['구역'].unique())
            else:
                district_options = sorted(df['구역'].unique())
            district_list = ["전체"] + list(district_options)
            selected_district = st.selectbox("구역 선택", district_list)

        with col3:
            search_keyword = st.text_input("검색 (이름, 전화번호, 차량번호)")

        filtered_df = df.copy()
        if selected_parish != "전체":
            filtered_df = filtered_df[filtered_df['교구'] == selected_parish]
        if selected_district != "전체":
            filtered_df = filtered_df[filtered_df['구역'] == selected_district]
        
        if search_keyword:
            mask = (
                filtered_df['이름'].astype(str).str.contains(search_keyword) | 
                filtered_df['전화번호'].astype(str).str.contains(search_keyword) |
                filtered_df['차량번호'].astype(str).str.contains(search_keyword)
            )
            filtered_df = filtered_df[mask]

        st.markdown(f"**총 {len(filtered_df)}명 검색됨**")
        st.divider()

        if filtered_df.empty:
            st.info("검색 결과가 없습니다.")
        else:
            for i in range(0, len(filtered_df), 2):
                cols = st.columns(2)
                batch = filtered_df.iloc[i:i+2]
                
                for idx, (index, person) in enumerate(batch.iterrows()):
                    with cols[idx]:
                        with st.container(border=True):
                            c1, c2 = st.columns([1, 2])
                            with c1:
                                img_path = person['사진'] if pd.notna(person['사진']) else ""
                                if img_path and os.path.exists(img_path):
                                    st.image(img_path, use_column_width=True)
                                else:
                                    st.image("https://via.placeholder.com/150?text=No+Image", use_column_width=True)
                                st.caption(f"{person['직분']}")
                            with c2:
                                st.subheader(f"{person['이름']} ({person['생년']})")
                                st.text(f"{person['교구']} / {person['구역']}")
                                st.text(f"📞 {person['전화번호']}")
                                address = str(person['자택전화 / 주소'])
                                map_url = f"https://www.google.com/maps/search/?api=1&query={address}"
                                st.markdown(f"[📍 지도 보기]({map_url})")
                                st.text(f"🎂 구원일: {person['구원일']}")
                                if person['차량번호']:
                                    st.markdown(f"🚗 **{person['차량번호']}**")
                                with st.expander("상세 정보"):
                                    st.write(f"**가족:** {person['가족']}")
                                    st.write(f"**봉사:** {person['봉사부서']}")
                                    st.write(f"**주소:** {address}")

    # --- TAB 2: 성도 관리 ---
    if st.session_state['role'] == 'admin':
        with tab2:
            st.header("🛠 성도 데이터 관리")
            st.warning("수정 후 반드시 하단의 [변경된 엑셀 다운로드]를 눌러 파일을 저장하세요.")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
            
            if not edited_df.equals(st.session_state['members_df']):
                st.session_state['members_df'] = edited_df
                st.success("변경사항 임시 저장됨 (파일 다운로드 필요)")

            st.divider()
            st.download_button(
                label="💾 변경된 명단 다운로드 (CSV)",
                data=save_data_to_csv(edited_df),
                file_name="members_updated.csv",
                mime="text/csv"
            )

    # --- TAB 3: 계정 관리 ---
    if st.session_state['role'] == 'admin':
        with tab3:
            st.header("⚙️ 계정 관리")
            if os.path.exists(ACCOUNTS_FILE):
                acc_df = load_data(ACCOUNTS_FILE)
            else:
                acc_df = pd.DataFrame(columns=['id', 'pw', 'name', 'role'])
            
            edited_acc_df = st.data_editor(acc_df, num_rows="dynamic", use_container_width=True, key="acc_editor")
            st.download_button(
                label="💾 계정 목록 다운로드 (CSV)",
                data=save_data_to_csv(edited_acc_df),
                file_name="accounts_updated.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        login_section()
    else:
        main_app()
