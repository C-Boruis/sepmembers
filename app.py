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
# 2. 데이터 로드 함수 (캐시 제거 - 즉시 반영을 위해)
# -----------------------------------------------------------------------------
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        # 무조건 문자열(String)로 읽기
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
# 4. 인증 (로그인) 함수 - [디버깅 강화]
# -----------------------------------------------------------------------------
def login_section():
    st.markdown("## ⛪ 서울은평교회 성도 관리 시스템")
    
    # 계정 파일이 없으면 강제 생성 (로그인 복구용)
    if not os.path.exists(ACCOUNTS_FILE):
        init_accounts = pd.DataFrame({
            'id': ['admin'],
            'pw': ['1234'],
            'name': ['관리자'],
            'role': ['admin']
        })
        init_accounts.to_csv(ACCOUNTS_FILE, index=False, encoding='utf-8-sig')
        st.warning("⚠️ 계정 파일이 없어 기본값(admin/1234)으로 새로 생성했습니다.")
        
    accounts = load_data(ACCOUNTS_FILE)

    # [데이터 정제] 공백 제거
    if accounts is not None:
        accounts['id'] = accounts['id'].astype(str).str.strip()
        accounts['pw'] = accounts['pw'].astype(str).str.strip()

    # 로그인 폼
    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            clean_username = str(username).strip()
            clean_password = str(password).strip()

            # 일치하는 사용자 찾기
            user = accounts[(accounts['id'] == clean_username) & (accounts['pw'] == clean_password)]
            
            if not user.empty:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.iloc[0]['name']
                st.session_state['role'] = user.iloc[0]['role']
                st.success("로그인 성공!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                
                # ----------------------------------------
                # [디버그 정보 출력] - 왜 안 되는지 보여줌
                # ----------------------------------------
                with st.expander("🚨 디버그 정보 보기 (클릭)", expanded=True):
                    st.write(f"👉 **입력한 값:** ID=[{clean_username}], PW=[{clean_password}]")
                    st.write("👇 **현재 저장된 계정 목록 (이 값과 똑같이 입력해야 합니다)**")
                    st.dataframe(accounts)

# -----------------------------------------------------------------------------
# 5. 메인 앱
# -----------------------------------------------------------------------------
def main_app():
    with st.sidebar:
        st.write(f"**{st.session_state['username']}**님 환영합니다.")
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
            st.session_state['members_df'] = preprocess_members(df)
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
            if os.path.exists(ACCOUNTS_FILE):
                acc_df = load_data(ACCOUNTS_FILE)
            else:
                acc_df = pd.DataFrame(columns=['id', 'pw', 'name', 'role'])
            edited_acc = st.data_editor(acc_df, num_rows="dynamic", use_container_width=True, key="acc")
            st.download_button("💾 계정 다운로드", save_data_to_csv(edited_acc), "accounts_updated.csv", "text/csv")

if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if not st.session_state['logged_in']: login_section()
    else: main_app()
