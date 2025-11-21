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
# 2. 데이터 로드 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        return pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
    except:
        try:
            return pd.read_csv(file_path, encoding='cp949', dtype=str)
        except:
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
# 4. 인증 (로그인) 함수 - [긴급 접속 코드 적용]
# -----------------------------------------------------------------------------
def login_section():
    st.markdown("## ⛪ 서울은평교회 성도 관리 시스템")
    
    # 로그인 폼
    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            clean_username = str(username).strip()
            clean_password = str(password).strip()

            # [핵심 수정] 파일 확인 전에 코드로 먼저 인증 (Master Key)
            # 파일이 깨져도 이 조건이 참이면 무조건 로그인 됩니다.
            is_master_admin = (clean_username == "admin" and clean_password == "1234")
            
            # 파일에서 확인 (일반 유저용)
            is_file_user = False
            user_role = "user"
            user_name = "성도님"

            if not is_master_admin:
                if os.path.exists(ACCOUNTS_FILE):
                    accounts = load_data(ACCOUNTS_FILE)
                    if accounts is not None:
                        # 공백 제거
                        accounts['id'] = accounts['id'].astype(str).str.strip()
                        accounts['pw'] = accounts['pw'].astype(str).str.strip()
                        
                        user = accounts[(accounts['id'] == clean_username) & (accounts['pw'] == clean_password)]
                        if not user.empty:
                            is_file_user = True
                            user_name = user.iloc[0]['name']
                            user_role = user.iloc[0]['role']

            # 로그인 성공 처리
            if is_master_admin or is_file_user:
                st.session_state['logged_in'] = True
                
                if is_master_admin:
                    st.session_state['username'] = "관리자(긴급)"
                    st.session_state['role'] = "admin"
                else:
                    st.session_state['username'] = user_name
                    st.session_state['role'] = user_role
                
                st.success(f"{st.session_state['username']}님 환영합니다!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

# -----------------------------------------------------------------------------
# 5. 메인 앱
# -----------------------------------------------------------------------------
def main_app():
    with st.sidebar:
        st.write(f"**{st.session_state['username']}**님")
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.divider()
        st.info("💡 데이터 수정 후 반드시 [다운로드] 하여 GitHub에 업로드하세요.")

    # 명단 로드
    if 'members_df' not in st.session_state:
        uploaded_file = st.sidebar.file_uploader("명단 파일 업로드 (.csv)", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig', dtype=str)
            st.session_state['members_df'] = preprocess_members(df)
        elif os.path.exists(MEMBERS_FILE):
            df = load_data(MEMBERS_FILE)
            if df is not None:
                st.session_state['members_df'] = preprocess_members(df)
            else:
                st.session_state['members_df'] = pd.DataFrame(columns=[
                '교구', '구역', '사진', '이름', '생년', '구원일', '전화번호', 
                '자택전화 / 주소', '교제부서', '직분', '봉사부서', '가족', '차량번호'
            ])
        else:
            st.session_state['members_df'] = pd.DataFrame(columns=[
                '교구', '구역', '사진', '이름', '생년', '구원일', '전화번호', 
                '자택전화 / 주소', '교제부서', '직분', '봉사부서', '가족', '차량번호'
            ])

    df = st.session_state['members_df']

    # 탭 분기
    if st.session_state['role'] == 'admin':
        tab1, tab2, tab3 = st.tabs(["📖 주소록", "🛠 명단 관리", "⚙️ 계정 관리"])
    else:
        tab1 = st.tabs(["📖 주소록"])[0]

    # TAB 1: 주소록
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            parish_list = ["전체"] + sorted(list(df['교구'].unique()))
            selected_parish = st.selectbox("교구", parish_list)
        with col2:
            if selected_parish != "전체":
                district_options = sorted(df[df['교구'] == selected_parish]['구역'].unique())
            else:
                district_options = sorted(df['구역'].unique())
            selected_district = st.selectbox("구역", ["전체"] + list(district_options))
        with col3:
            search_keyword = st.text_input("검색 (이름/전화/차량)")

        filtered_df = df.copy()
        if selected_parish != "전체": filtered_df = filtered_df[filtered_df['교구'] == selected_parish]
        if selected_district != "전체": filtered_df = filtered_df[filtered_df['구역'] == selected_district]
        if search_keyword:
            mask = (filtered_df['이름'].astype(str).str.contains(search_keyword) | 
                    filtered_df['전화번호'].astype(str).str.contains(search_keyword) |
                    filtered_df['차량번호'].astype(str).str.contains(search_keyword))
            filtered_df = filtered_df[mask]

        st.write(f"총 {len(filtered_df)}명")
        if filtered_df.empty:
            st.info("검색 결과 없음")
        else:
            for i in range(0, len(filtered_df), 2):
                cols = st.columns(2)
                batch = filtered_df.iloc[i:i+2]
                for idx, (_, p) in enumerate(batch.iterrows()):
                    with cols[idx]:
                        with st.container(border=True):
                            c1, c2 = st.columns([1, 2])
                            with c1:
                                img = p['사진'] if pd.notna(p['사진']) else ""
                                if img and os.path.exists(img): st.image(img)
                                else: st.image("https://via.placeholder.com/150")
                            with c2:
                                st.subheader(p['이름'])
                                st.text(f"{p['교구']}/{p['구역']} {p['직분']}")
                                st.text(f"📞 {p['전화번호']}")
                                st.markdown(f"[📍 지도](https://www.google.com/maps/search/?api=1&query={p['자택전화 / 주소']})")
                                if p['차량번호']: st.write(f"🚗 {p['차량번호']}")
                                with st.expander("상세"):
                                    st.write(f"가족: {p['가족']}")
                                    st.write(f"주소: {p['자택전화 / 주소']}")

    # TAB 2: 명단 관리 (Admin)
    if st.session_state['role'] == 'admin':
        with tab2:
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
            if not edited_df.equals(st.session_state['members_df']):
                st.session_state['members_df'] = edited_df
            st.download_button("💾 명단 다운로드", save_data_to_csv(edited_df), "members_updated.csv", "text/csv")

    # TAB 3: 계정 관리 (Admin)
    if st.session_state['role'] == 'admin':
        with tab3:
            st.info("여기서 계정을 정리하고 다운로드 받은 뒤, GitHub에 업로드하면 오류가 해결됩니다.")
            if os.path.exists(ACCOUNTS_FILE):
                acc_df = load_data(ACCOUNTS_FILE)
            else:
                acc_df = pd.DataFrame(columns=['id', 'pw', 'name', 'role'])
                # 강제 초기화 데이터
                if acc_df.empty:
                    acc_df = pd.DataFrame([
                        {'id': 'admin', 'pw': '1234', 'name': '관리자', 'role': 'admin'},
                        {'id': 'user1', 'pw': '1111', 'name': '성도님', 'role': 'user'}
                    ])
            
            edited_acc = st.data_editor(acc_df, num_rows="dynamic", use_container_width=True, key="acc")
            st.download_button("💾 계정 다운로드", save_data_to_csv(edited_acc), "accounts_updated.csv", "text/csv")

if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if not st.session_state['logged_in']: login_section()
    else: main_app()
