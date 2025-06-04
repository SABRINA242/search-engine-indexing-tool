# --- 사이트 관리 함수 ---
def load_managed_sites():
    """저장된 사이트 목록 불러오기"""
    if not os.path.exists(SITES_FILE):
        return []
    
    try:
        with open(SITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        add_log(f"❌ 사이트 목록 불러오기 오류: {e}")
        return []

def save_managed_sites(sites):
    """사이트 목록 저장하기"""
    try:
        with open(SITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(sites, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        add_log(f"❌ 사이트 목록 저장 오류: {e}")
        return False
        import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import threading
import time
import requests
import xml.etree.ElementTree as ET
import json
import os
import base64
import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Google API 관련 라이브러리
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Selenium 라이브러리 추가
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Google API 관련 라이브러리
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Selenium 라이브러리 추가
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- URL 메타데이터 관리 파일 ---
URL_METADATA_FILE = 'url_metadata.json'  # URL 메타데이터 (최초 발견 시간, 우선순위 등)

# --- 색인 요청 관련 상수 ---
GOOGLE_BATCH_SIZE = 15  # 구글 색인 요청 배치 크기
BING_BATCH_SIZE = 15    # Bing 색인 요청 배치 크기
NAVER_BATCH_SIZE = 15   # 네이버 색인 요청 배치 크기
RETRY_DELAY = 7200      # 재시도 지연 시간 (초) - 2시간

# --- 응답 대기 시간 설정 ---
GOOGLE_TIMEOUT = 30     # 구글 응답 대기 시간 (초)
BING_TIMEOUT = 5        # Bing 응답 대기 시간 (초) - 실제 응답 시간에 맞게 조정
NAVER_TIMEOUT = 10      # 네이버 응답 대기 시간 (초) - 로딩 표시 대기용

# --- 일일 할당량 설정 ---
DAILY_QUOTA = {
    "Google": 15,  # 구글 일일 할당량 (공식 제한)
    "Bing": 10,    # 빙 일일 할당량 (실제 사용자 피드백 기반)
    "Naver": 20    # 네이버 일일 할당량 (명시적 제한은 없지만 자주 요청 시 제한 가능성)
}

# --- 상태 코드 ---
STATUS_PENDING = "pending"    # 요청 전송 전
STATUS_REQUESTED = "requested"  # 요청 전송됨, 응답 대기 중
STATUS_SUCCESS = "success"    # 요청 성공 (응답 수신)
STATUS_ERROR = "error"        # 요청 실패
STATUS_TIMEOUT = "timeout"    # 응답 대기 시간 초과
STATUS_UNKNOWN = "unknown"    # 상태 불명확
STATUS_QUOTA_EXCEEDED = "quota_exceeded"  # 할당량 초과

# --- 기본 설정값 ---
DEFAULT_CONFIG = {
    'google': {
        'service_account_file': '',
        'site_url': ''
    },
    'bing': {
        'api_key': ''
    },
    'naver': {
        'id': '',
        'password': '',
        'client_id': '',
        'client_secret': ''
    }
}

# --- 전역 변수 (설정값 저장) ---
SERVICE_ACCOUNT_FILE = ''
SITE_URL = ''
SCOPES = ['https://www.googleapis.com/auth/indexing']
BING_API_KEY = ''
NAVER_ID = ''
NAVER_PASSWORD = ''
NAVER_CLIENT_ID = ''
NAVER_CLIENT_SECRET = ''

# --- 일일 할당량 관리 함수 ---
def load_daily_quota():
    """일일 할당량 및 사용량 로드"""
    if not os.path.exists(QUOTA_FILE):
        # 파일이 없으면 초기 설정으로 생성
        quota_data = {
            "date": time.strftime("%Y-%m-%d"),
            "usage": {
                "Google": 0,
                "Bing": 0,
                "Naver": 0
            }
        }
        save_daily_quota(quota_data)
        return quota_data
    
    try:
        with open(QUOTA_FILE, 'r', encoding='utf-8') as f:
            quota_data = json.load(f)
            
        # 날짜가 오늘이 아니면 사용량 초기화
        today = time.strftime("%Y-%m-%d")
        if quota_data["date"] != today:
            quota_data["date"] = today
            quota_data["usage"] = {
                "Google": 0,
                "Bing": 0,
                "Naver": 0
            }
            save_daily_quota(quota_data)
            add_log(f"📅 새로운 날짜 감지: 일일 할당량이 초기화되었습니다.")
        
        return quota_data
    except Exception as e:
        add_log(f"❌ 일일 할당량 정보 로드 실패: {e}")
        return {
            "date": time.strftime("%Y-%m-%d"),
            "usage": {
                "Google": 0,
                "Bing": 0,
                "Naver": 0
            }
        }

def save_daily_quota(quota_data):
    """일일 할당량 정보 저장"""
    try:
        with open(QUOTA_FILE, 'w', encoding='utf-8') as f:
            json.dump(quota_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        add_log(f"❌ 일일 할당량 정보 저장 실패: {e}")
        return False

def increment_usage_count(platform):
    """플랫폼별 사용량 증가"""
    quota_data = load_daily_quota()
    if platform in quota_data["usage"]:
        quota_data["usage"][platform] += 1
        save_daily_quota(quota_data)
        return quota_data["usage"][platform]
    return 0

def get_remaining_quota(platform):
    """남은 할당량 반환"""
    quota_data = load_daily_quota()
    if platform in quota_data["usage"] and platform in DAILY_QUOTA:
        used = quota_data["usage"][platform]
        total = DAILY_QUOTA[platform]
        return max(0, total - used)
    return 0

def is_quota_exceeded(platform):
    """할당량 초과 여부 확인"""
    return get_remaining_quota(platform) <= 0

def reset_daily_quota():
    """일일 할당량 수동 초기화"""
    quota_data = {
        "date": time.strftime("%Y-%m-%d"),
        "usage": {
            "Google": 0,
            "Bing": 0,
            "Naver": 0
        }
    }
    save_daily_quota(quota_data)
    add_log(f"🔄 일일 할당량이 수동으로 초기화되었습니다.")
    return True
def load_url_status():
    """저장된 URL 상태 정보 로드"""
    if not os.path.exists(URL_STATUS_FILE):
        return {}
    
    try:
        with open(URL_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        add_log(f"❌ URL 상태 정보 로드 실패: {e}")
        return {}

def save_url_status(status_data):
    """URL 상태 정보 저장"""
    try:
        with open(URL_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        add_log(f"❌ URL 상태 정보 저장 실패: {e}")
        return False

def update_url_status(url, platform, status, last_attempt=None):
    """URL 상태 정보 업데이트"""
    if last_attempt is None:
        last_attempt = int(time.time())
    
    status_data = load_url_status()
    
    if url not in status_data:
        status_data[url] = {}
    
    status_data[url][platform] = {
        'status': status,
        'last_attempt': last_attempt
    }
    
    save_url_status(status_data)

def get_pending_urls(urls, platform, current_time=None):
    """처리해야 할 URL 목록 반환 (실패하거나 아직 시도하지 않은 URL)"""
    if current_time is None:
        current_time = int(time.time())
    
    status_data = load_url_status()
    pending_urls = []
    
    for url in urls:
        # URL 상태가 없거나 해당 플랫폼 정보가 없는 경우
        if url not in status_data or platform not in status_data[url]:
            pending_urls.append(url)
            continue
        
        url_info = status_data[url][platform]
        status = url_info['status']
        
        # 성공한 경우 제외
        if status == STATUS_SUCCESS:
            continue
        
        # 실패, 시간 초과, 또는 불명확한 상태인 경우
        if status in [STATUS_ERROR, STATUS_TIMEOUT, STATUS_UNKNOWN]:
            # 재시도 시간이 지났는지 확인
            if current_time - url_info['last_attempt'] >= RETRY_DELAY:
                pending_urls.append(url)
        else:
            # 요청 중이거나 대기 중인 상태는 다시 요청
            pending_urls.append(url)
    
    return pending_urls

def get_batch_urls(urls, platform, batch_size):
    """배치 처리할 URL 목록 반환"""
    pending_urls = get_pending_urls(urls, platform)
    return pending_urls[:batch_size]

def get_status_display(status):
    """상태 코드에 대한 표시 텍스트 반환"""
    status_map = {
        STATUS_PENDING: "⏳ 준비 중",
        STATUS_REQUESTED: "🔄 요청 중",
        STATUS_SUCCESS: "✅ 성공",
        STATUS_ERROR: "❌ 실패",
        STATUS_TIMEOUT: "⏱️ 시간 초과",
        STATUS_UNKNOWN: "❓ 불명확"
    }
    return status_map.get(status, status)

def open_site_manager():
    """사이트 관리 창 열기"""
    # 이미 열려있는 창이 있으면 포커스
    if hasattr(root, 'site_manager_window') and root.site_manager_window:
        root.site_manager_window.focus_force()
        return
    
    # 관리 창 생성
    root.site_manager_window = tk.Toplevel(root)
    root.site_manager_window.title("사이트 관리")
    root.site_manager_window.geometry("700x500")
    root.site_manager_window.configure(bg="#2C3E50")
    root.site_manager_window.transient(root)
    root.site_manager_window.grab_set()
    
    # 창 닫힐 때 처리
    def on_manager_close():
        root.site_manager_window = None
        manager_window.destroy()
    
    root.site_manager_window.protocol("WM_DELETE_WINDOW", on_manager_close)
    
    manager_window = root.site_manager_window
    
    # 프레임 생성
    sites_frame = tk.Frame(manager_window, bg="#34495E")
    sites_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    details_frame = tk.Frame(manager_window, bg="#34495E")
    details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 사이트 목록 타이틀
    tk.Label(sites_frame, text="등록된 사이트", fg="white", bg="#34495E",
             font=("Segoe UI", 12, "bold")).pack(pady=10)
    
    # 사이트 목록 표시
    sites_listbox = tk.Listbox(sites_frame, width=30, height=15, 
                              font=("Segoe UI", 10), bg="#2D3748", fg="white",
                              selectbackground="#667eea")
    sites_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 스크롤바 추가
    scrollbar = tk.Scrollbar(sites_listbox)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    sites_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=sites_listbox.yview)
    
    # 사이트 목록 불러오기
    managed_sites = load_managed_sites()
    for site in managed_sites:
        sites_listbox.insert(tk.END, site['name'])
    
    # 상세 정보 프레임
    tk.Label(details_frame, text="사이트 정보", fg="white", bg="#34495E",
             font=("Segoe UI", 12, "bold")).pack(pady=10)
    
    details_inner_frame = tk.Frame(details_frame, bg="#34495E", padx=10, pady=10)
    details_inner_frame.pack(fill=tk.BOTH, expand=True)
    
    tk.Label(details_inner_frame, text="사이트 이름:", fg="white", bg="#34495E").grid(row=0, column=0, sticky=tk.W, pady=5)
    site_name_entry = tk.Entry(details_inner_frame, width=40)
    site_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    tk.Label(details_inner_frame, text="사이트 URL:", fg="white", bg="#34495E").grid(row=1, column=0, sticky=tk.W, pady=5)
    site_url_entry = tk.Entry(details_inner_frame, width=40)
    site_url_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    tk.Label(details_inner_frame, text="사이트맵 URL:", fg="white", bg="#34495E").grid(row=2, column=0, sticky=tk.W, pady=5)
    sitemap_url_entry = tk.Entry(details_inner_frame, width=40)
    sitemap_url_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    
    # 버튼 함수
    def clear_fields():
        """입력 필드 초기화"""
        site_name_entry.delete(0, tk.END)
        site_url_entry.delete(0, tk.END)
        sitemap_url_entry.delete(0, tk.END)
        sites_listbox.selection_clear(0, tk.END)
    
    def load_site_details(event=None):
        """선택한 사이트 정보 로드"""
        selected_indices = sites_listbox.curselection()
        if not selected_indices:
            return
        
        index = selected_indices[0]
        if index < len(managed_sites):
            site = managed_sites[index]
            site_name_entry.delete(0, tk.END)
            site_url_entry.delete(0, tk.END)
            sitemap_url_entry.delete(0, tk.END)
            
            site_name_entry.insert(0, site['name'])
            site_url_entry.insert(0, site['url'])
            sitemap_url_entry.insert(0, site['sitemap'])
    
    def add_or_update_site():
        """사이트 추가 또는 업데이트"""
        name = site_name_entry.get().strip()
        url = site_url_entry.get().strip()
        sitemap = sitemap_url_entry.get().strip()
        
        if not name or not url or not sitemap:
            messagebox.showwarning("입력 오류", "모든 필드를 입력해주세요.")
            return
        
        # URL 형식 확인
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if not sitemap.startswith(('http://', 'https://')):
            sitemap = 'https://' + sitemap
        
        # 선택된 항목이 있는지 확인
        selected_indices = sites_listbox.curselection()
        
        if selected_indices:  # 업데이트
            index = selected_indices[0]
            managed_sites[index] = {
                'name': name,
                'url': url,
                'sitemap': sitemap
            }
            sites_listbox.delete(index)
            sites_listbox.insert(index, name)
            sites_listbox.selection_set(index)
            add_log(f"✅ 사이트 '{name}' 정보가 업데이트되었습니다.")
        else:  # 새로 추가
            # 동일한 이름 체크
            for site in managed_sites:
                if site['name'] == name:
                    messagebox.showwarning("중복 오류", f"'{name}' 이름의 사이트가 이미 존재합니다.")
                    return
            
            new_site = {
                'name': name,
                'url': url,
                'sitemap': sitemap
            }
            managed_sites.append(new_site)
            sites_listbox.insert(tk.END, name)
            add_log(f"✅ 새 사이트 '{name}'이(가) 추가되었습니다.")
        
        # 저장
        save_managed_sites(managed_sites)
        update_site_combobox()
        clear_fields()
    
    def delete_site():
        """선택한 사이트 삭제"""
        selected_indices = sites_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("선택 오류", "삭제할 사이트를 선택해주세요.")
            return
        
        index = selected_indices[0]
        site_name = managed_sites[index]['name']
        
        confirm = messagebox.askyesno("삭제 확인", f"'{site_name}' 사이트를 정말 삭제하시겠습니까?")
        if not confirm:
            return
        
        del managed_sites[index]
        sites_listbox.delete(index)
        save_managed_sites(managed_sites)
        update_site_combobox()
        clear_fields()
        add_log(f"✅ 사이트 '{site_name}'이(가) 삭제되었습니다.")
    
    def use_selected_site():
        """선택한 사이트 정보를 메인 창에 적용"""
        selected_indices = sites_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("선택 오류", "사용할 사이트를 선택해주세요.")
            return
        
        index = selected_indices[0]
        site = managed_sites[index]
        
        # 메인 창 콤보박스에 선택
        site_combobox.set(site['name'])
        sitemap_combobox.delete(0, tk.END)
        sitemap_combobox.insert(0, site['sitemap'])
        
        # 사이트 URL 설정에 반영
        global SITE_URL
        SITE_URL = site['url']
        save_config()
        
        on_manager_close()
        add_log(f"✅ 사이트 '{site['name']}'이(가) 선택되었습니다.")
    
    # 이벤트 연결
    sites_listbox.bind('<<ListboxSelect>>', load_site_details)
    
    # 버튼 프레임
    button_frame = tk.Frame(details_frame, bg="#34495E")
    button_frame.pack(pady=10, fill=tk.X)
    
    add_button = tk.Button(button_frame, text="추가/업데이트", command=add_or_update_site,
                         bg="#2ecc71", fg="white", width=12)
    add_button.pack(side=tk.LEFT, padx=5)
    
    clear_button = tk.Button(button_frame, text="입력 초기화", command=clear_fields,
                          bg="#3498db", fg="white", width=12)
    clear_button.pack(side=tk.LEFT, padx=5)
    
    delete_button = tk.Button(button_frame, text="삭제", command=delete_site,
                           bg="#e74c3c", fg="white", width=12)
    delete_button.pack(side=tk.LEFT, padx=5)
    
    # 선택 버튼
    select_button = tk.Button(manager_window, text="선택한 사이트 사용", command=use_selected_site,
                           bg="#667eea", fg="white", font=("Segoe UI", 10, "bold"),
                           height=2)
    select_button.pack(pady=10, fill=tk.X, padx=10)

def update_site_combobox():
    """사이트 콤보박스 업데이트"""
    sites = load_managed_sites()
    site_names = [site['name'] for site in sites]
    site_combobox['values'] = site_names
    if sites:
        site_combobox.current(0)

def on_site_selected(event=None):
    """사이트 선택 시 사이트맵 URL 업데이트"""
    selected_site = site_combobox.get()
    sites = load_managed_sites()
    
    for site in sites:
        if site['name'] == selected_site:
            sitemap_combobox.delete(0, tk.END)
            sitemap_combobox.insert(0, site['sitemap'])
            
            # 사이트 URL 업데이트
            global SITE_URL
            SITE_URL = site['url']
            save_config()
            break

# --- Google API 서비스 객체 생성 함수 ---
def get_indexing_service():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('indexing', 'v3', credentials=creds)
        return service
    except Exception as e:
        error_message = str(e)
        add_log(f"❌ Google Indexing API 서비스 객체 생성 실패: {error_message}")
        root.after(0, lambda msg=error_message: messagebox.showerror("API 오류", f"Google Indexing API 연결에 실패했습니다. JSON 키 파일과 권한을 확인해주세요:\n{msg}"))
        return None

# --- UI 요소 생성 ---
title_label = tk.Label(root, text="🔍 검색엔진 색인 자동화",
                       font=("Segoe UI", 20, "bold"), fg="white", bg="#2C3E50")
title_label.pack(pady=15)

desc_label = tk.Label(root, text="사이트를 선택하고 색인 요청을 보내세요.",
                      font=("Segoe UI", 10), fg="white", bg="#2C3E50")
desc_label.pack(pady=5)

# 사이트 선택 프레임
site_frame = tk.Frame(root, bg="#34495E", padx=10, pady=10)
site_frame.pack(pady=10, padx=20, fill=tk.X)

site_label = tk.Label(site_frame, text="사이트 선택",
                     font=("Segoe UI", 10, "bold"), fg="white", bg="#34495E")
site_label.pack(anchor=tk.W, pady=5)

# 사이트 선택 프레임
site_selection_frame = tk.Frame(site_frame, bg="#34495E")
site_selection_frame.pack(fill=tk.X, pady=5)

# 사이트 콤보박스
site_combobox = ttk.Combobox(site_selection_frame, width=50, font=("Segoe UI", 10))
site_combobox.pack(side=tk.LEFT, padx=(0, 5))

# 사이트 관리 버튼
manage_sites_button = tk.Button(site_selection_frame, text="사이트 관리", 
                              command=open_site_manager, bg="#3498db", fg="white")
manage_sites_button.pack(side=tk.RIGHT)

# 사이트 선택 이벤트 연결
site_combobox.bind("<<ComboboxSelected>>", on_site_selected)

# 사이트맵 프레임
sitemap_frame = tk.Frame(root, bg="#34495E", padx=10, pady=10)
sitemap_frame.pack(pady=10, padx=20, fill=tk.X)

sitemap_label = tk.Label(sitemap_frame, text="사이트맵 URL",
                         font=("Segoe UI", 10, "bold"), fg="white", bg="#34495E")
sitemap_label.pack(anchor=tk.W, pady=5)

# 콤보박스와 입력 필드를 담을 프레임
sitemap_input_frame = tk.Frame(sitemap_frame, bg="#34495E")
sitemap_input_frame.pack(fill=tk.X, pady=5)

# 콤보박스로 변경
sitemap_combobox = ttk.Combobox(sitemap_input_frame, width=70, font=("Courier New", 10))
sitemap_combobox.pack(side=tk.LEFT)
sitemap_combobox.insert(0, "https://www.sitemaps.org/sitemap.xml")  # 기본 예시 URL

platform_frame = tk.Frame(root, bg="#2C3E50")
platform_frame.pack(pady=10)

google_var = tk.BooleanVar()
bing_var = tk.BooleanVar()
naver_var = tk.BooleanVar()

google_check = tk.Checkbutton(platform_frame, text="Google Search Console", variable=google_var,
                              fg="white", bg="#2C3E50", selectcolor="#34495E")
bing_check = tk.Checkbutton(platform_frame, text="Bing Webmaster", variable=bing_var,
                            fg="white", bg="#2C3E50", selectcolor="#34495E")
naver_check = tk.Checkbutton(platform_frame, text="네이버 서치어드바이저", variable=naver_var,
                             fg="white", bg="#2C3E50", selectcolor="#34495E")

google_check.pack(side=tk.LEFT, padx=10)
bing_check.pack(side=tk.LEFT, padx=10)
naver_check.pack(side=tk.LEFT, padx=10)

# --- 기능 함수 ---
def add_log(message):
    timestamp = time.strftime("[%H:%M:%S]", time.localtime())
    log_area.insert(tk.END, f"{timestamp} {message}\n")
    log_area.see(tk.END)

def parse_sitemap(sitemap_url_str):
    urls = []
    try:
        add_log(f"🔗 사이트맵 {sitemap_url_str} 다운로드 중...")
        response = requests.get(sitemap_url_str, timeout=10)
        response.raise_for_status()

        root_element = ET.fromstring(response.content)
        # 네임스페이스를 동적으로 가져오거나, 일반적인 경우를 처리하도록 개선
        namespace = ''
        if '}' in root_element.tag:
            namespace = root_element.tag.split('}')[0] + '}' # {http://www.sitemaps.org/schemas/sitemap/0.9}

        # urlset / sitemap 태그 찾기
        if root_element.findall(f'{namespace}url'): # sitemap인 경우
            for url_element in root_element.findall(f'{namespace}url'):
                loc_element = url_element.find(f'{namespace}loc')
                if loc_element is not None:
                    url = loc_element.text
                    urls.append(url)
                    
                    # 최종 수정 시간 확인 (있는 경우)
                    lastmod_element = url_element.find(f'{namespace}lastmod')
                    if lastmod_element is not None and lastmod_element.text:
                        try:
                            # ISO 8601 형식 날짜를 타임스탬프로 변환 (예: 2023-01-01T12:00:00+00:00)
                            lastmod_str = lastmod_element.text
                            if 'T' in lastmod_str:  # 날짜+시간 형식
                                dt = datetime.datetime.fromisoformat(lastmod_str.replace('Z', '+00:00'))
                            else:  # 날짜만 있는 형식
                                dt = datetime.datetime.fromisoformat(f"{lastmod_str}T00:00:00+00:00")
                            
                            # 타임스탬프로 변환
                            timestamp = int(dt.timestamp())
                            
                            # URL 메타데이터 업데이트
                            update_url_metadata(url, discovered_time=timestamp)
                        except Exception as e:
                            # 날짜 변환 실패 시 현재 시간 사용
                            update_url_metadata(url)
                    else:
                        # lastmod가 없는 경우 그냥 등록
                        update_url_metadata(url)
                    
        elif root_element.findall(f'{namespace}sitemap'): # sitemap index인 경우
             add_log("💡 사이트맵 인덱스 파일을 감지했습니다. 하위 사이트맵을 탐색합니다.")
             for sitemap_elem in root_element.findall(f'{namespace}sitemap'):
                loc_elem = sitemap_elem.find(f'{namespace}loc')
                if loc_elem is not None:
                    # 재귀 호출로 하위 사이트맵 파싱 (중복 제거 위해 set 사용 후 list 변환)
                    urls.extend(list(set(parse_sitemap(loc_elem.text))))

        if not urls:
            add_log(f"ℹ️ 사이트맵에서 URL을 찾지 못했거나, 지원하지 않는 형식일 수 있습니다. (루트 태그: {root_element.tag})")
        else:
             add_log(f"✅ 사이트맵에서 총 {len(urls)}개 URL을 성공적으로 추출했습니다.")

    except requests.exceptions.RequestException as e:
        add_log(f"❌ 사이트맵 다운로드 오류: {e}")
        root.after(0, lambda err=e: messagebox.showerror("오류", f"사이트맵을 다운로드할 수 없습니다: {err}"))
    except ET.ParseError as e:
        add_log(f"❌ 사이트맵 XML 파싱 오류: {e}")
        root.after(0, lambda err=e: messagebox.showerror("오류", f"사이트맵 XML 형식이 올바르지 않습니다: {err}"))
    except Exception as e:
        add_log(f"❌ 알 수 없는 사이트맵 처리 오류: {e}")
        root.after(0, lambda err=e: messagebox.showerror("오류", f"사이트맵 처리 중 오류 발생: {err}"))
    
    # URL 목록을 최신순으로 정렬 (메타데이터 기반)
    urls = sorted(list(set(urls)), key=lambda url: -get_url_discovery_time(url))
    
    return urls

# --- 실제 Indexing API 호출 함수들 ---
def call_google_indexing_api(indexing_service, url):
    try:
        # 할당량 확인
        if is_quota_exceeded("Google"):
            add_log(f"⚠️ Google: 일일 할당량({DAILY_QUOTA['Google']}개)을 모두 사용했습니다.")
            update_url_status(url, "Google", STATUS_QUOTA_EXCEEDED)
            return STATUS_QUOTA_EXCEEDED
        
        # 상태 업데이트: 요청 전송 전
        add_log(f"🔄 Google: {url} 색인 요청 준비 중...")
        update_url_status(url, "Google", STATUS_PENDING)
        
        # 요청 본문 준비
        request_body = {
            "url": url,
            "type": "URL_UPDATED"
        }
        
        # 상태 업데이트: 요청 전송 시작
        add_log(f"📤 Google: {url} 색인 요청 전송 중...")
        update_url_status(url, "Google", STATUS_REQUESTED)
        
        # 비동기 방식으로 요청 전송 및 응답 대기
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        def execute_request():
            return indexing_service.urlNotifications().publish(body=request_body).execute()
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(execute_request)
            try:
                response = future.result(timeout=GOOGLE_TIMEOUT)
                
                # 응답 처리
                if response and response.get('urlNotificationMetadata'):
                    metadata = response.get('urlNotificationMetadata')
                    # 요청 날짜/시간 정보 확인
                    url_details = metadata.get('url', '')
                    latency = metadata.get('latencyMillis', '')
                    
                    # 할당량 증가
                    usage_count = increment_usage_count("Google")
                    remaining = DAILY_QUOTA["Google"] - usage_count
                    
                    add_log(f"✅ Google: {url} 색인 요청 성공! (응답 시간: {latency}ms, 오늘 {usage_count}/{DAILY_QUOTA['Google']}개 사용)")
                    update_url_status(url, "Google", STATUS_SUCCESS)
                    return STATUS_SUCCESS
                else:
                    add_log(f"⚠️ Google: {url} 색인 요청 응답 불분명. 응답: {response}")
                    update_url_status(url, "Google", STATUS_UNKNOWN)
                    return STATUS_UNKNOWN
            
            except TimeoutError:
                add_log(f"⏱️ Google: {url} 색인 요청 응답 대기 시간 초과 ({GOOGLE_TIMEOUT}초)")
                update_url_status(url, "Google", STATUS_TIMEOUT)
                return STATUS_TIMEOUT
    
    except HttpError as error:
        error_content = "내용 확인 불가"
        try:
            error_content = error.content.decode('utf-8')
        except:
            pass # 디코딩 실패 시 기본 메시지 사용
        
        # 할당량 초과 메시지 확인
        if "Quota exceeded" in error_content or "resource exhausted" in error_content:
            add_log(f"❌ Google: {url} 색인 요청 실패 - 할당량 초과")
            update_url_status(url, "Google", STATUS_QUOTA_EXCEEDED)
            
            # 할당량 상태 업데이트 (모두 사용한 것으로 표시)
            quota_data = load_daily_quota()
            quota_data["usage"]["Google"] = DAILY_QUOTA["Google"]
            save_daily_quota(quota_data)
            
            # 할당량 초과 메시지 표시 및 프로그램 중단 요청
            root.after(0, lambda: messagebox.showerror(
                "할당량 초과", 
                "Google Indexing API 일일 할당량을 초과했습니다.\n"
                "더 이상의 색인 요청은 내일까지 불가능합니다.\n\n"
                "프로그램을 종료합니다."
            ))
            return STATUS_QUOTA_EXCEEDED
        else:
            add_log(f"❌ Google: {url} 색인 요청 실패 (HTTP 오류): {error_content}")
            update_url_status(url, "Google", STATUS_ERROR)
            return STATUS_ERROR
    
    except Exception as e:
        add_log(f"❌ Google: {url} 색인 요청 실패 (일반 오류): {e}")
        update_url_status(url, "Google", STATUS_ERROR)
        return STATUS_ERROR

def call_bing_indexing_api(url, bing_api_key):
    try:
        # 할당량 확인
        if is_quota_exceeded("Bing"):
            add_log(f"⚠️ Bing: 일일 할당량({DAILY_QUOTA['Bing']}개)을 모두 사용했습니다.")
            update_url_status(url, "Bing", STATUS_QUOTA_EXCEEDED)
            return STATUS_QUOTA_EXCEEDED
        
        # 유효성 검사
        if not bing_api_key or bing_api_key == 'YOUR_BING_API_KEY' or len(bing_api_key) < 10:
            add_log("❌ Bing API 키가 유효하지 않거나 설정되지 않았습니다. 요청을 건너뜝니다.")
            update_url_status(url, "Bing", STATUS_ERROR)
            return STATUS_ERROR
        
        # 상태 업데이트: 요청 전송 전
        add_log(f"🔄 Bing: {url} 색인 요청 준비 중...")
        update_url_status(url, "Bing", STATUS_PENDING)
        
        # 요청 준비
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        payload = {
            "siteUrl": SITE_URL,
            "urlList": [url]
        }
        
        api_url = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrl?apikey={bing_api_key}"
        if "SubmitUrlBatch" not in api_url:
            payload = {'siteUrl': SITE_URL, 'url': url}
        
        # 상태 업데이트: 요청 전송 시작
        add_log(f"📤 Bing: {url} 색인 요청 전송 중...")
        update_url_status(url, "Bing", STATUS_REQUESTED)
        
        # 비동기 방식으로 요청 전송 및 응답 대기
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        def execute_request():
            return requests.post(api_url, headers=headers, data=json.dumps(payload))
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(execute_request)
            try:
                response = future.result(timeout=BING_TIMEOUT)
                response.raise_for_status()
                
                # 응답 처리
                try:
                    response_json = response.json()
                    response_details = str(response_json)
                except:
                    response_details = f"HTTP {response.status_code}"
                
                # 할당량 증가
                usage_count = increment_usage_count("Bing")
                remaining = DAILY_QUOTA["Bing"] - usage_count
                
                add_log(f"✅ Bing: {url} 색인 요청 성공! (응답: {response_details}, 오늘 {usage_count}/{DAILY_QUOTA['Bing']}개 사용)")
                update_url_status(url, "Bing", STATUS_SUCCESS)
                return STATUS_SUCCESS
            
            except TimeoutError:
                add_log(f"⏱️ Bing: {url} 색인 요청 응답 대기 시간 초과 ({BING_TIMEOUT}초)")
                update_url_status(url, "Bing", STATUS_TIMEOUT)
                return STATUS_TIMEOUT

    except requests.exceptions.HTTPError as e:
        error_content = e.response.text
        
        # 할당량 초과 확인 (Bing은 다른 방식으로 표시할 수 있음)
        if e.response.status_code == 429 or "quota" in error_content.lower() or "limit" in error_content.lower():
            add_log(f"❌ Bing: {url} 색인 요청 실패 - 할당량 초과 가능성")
            update_url_status(url, "Bing", STATUS_QUOTA_EXCEEDED)
            
            # 할당량 상태 업데이트
            quota_data = load_daily_quota()
            quota_data["usage"]["Bing"] = DAILY_QUOTA["Bing"]
            save_daily_quota(quota_data)
            
            # 사용자에게 알림
            root.after(0, lambda: messagebox.showwarning(
                "Bing 할당량 초과", 
                "Bing API 일일 할당량을 초과했을 수 있습니다.\n"
                "더 이상의 Bing 색인 요청은 내일까지 불가능합니다."
            ))
            return STATUS_QUOTA_EXCEEDED
        else:
            add_log(f"❌ Bing: {url} 색인 요청 HTTP 오류 ({e.response.status_code}): {error_content}")
            update_url_status(url, "Bing", STATUS_ERROR)
            return STATUS_ERROR
    
    except requests.exceptions.RequestException as e:
        add_log(f"❌ Bing: {url} 색인 요청 네트워크 오류: {e}")
        update_url_status(url, "Bing", STATUS_ERROR)
        return STATUS_ERROR
    
    except Exception as e:
        add_log(f"❌ Bing: {url} 색인 요청 일반 오류: {e}")
        update_url_status(url, "Bing", STATUS_ERROR)
        return STATUS_ERROR

# 네이버 서치어드바이저 자동화 함수 (Selenium 사용)
def call_naver_search_advisor(url):
    try:
        # 할당량 확인
        if is_quota_exceeded("Naver"):
            add_log(f"⚠️ Naver: 일일 할당량({DAILY_QUOTA['Naver']}개)을 모두 사용했습니다.")
            update_url_status(url, "Naver", STATUS_QUOTA_EXCEEDED)
            return STATUS_QUOTA_EXCEEDED
        
        # 상태 업데이트: 요청 전송 전
        add_log(f"🔄 Naver: {url} 서치어드바이저 자동화 준비 중...")
        update_url_status(url, "Naver", STATUS_PENDING)
        
        # 브라우저 설정
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 백그라운드 실행 시 활성화
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 웹드라이버 설정
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        try:
            # 상태 업데이트: 브라우저 실행 및 자동화 시작
            add_log(f"🌐 Naver: {url} 브라우저 자동화 시작...")
            update_url_status(url, "Naver", STATUS_REQUESTED)
            
            # 네이버 로그인 페이지 접속
            driver.get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)  # 페이지 로딩 대기
            
            add_log(f"🔑 Naver: 로그인 중...")
            
            # 아이디 입력
            id_field = driver.find_element(By.ID, "id")
            id_field.send_keys(NAVER_ID)
            
            # 비밀번호 입력
            pw_field = driver.find_element(By.ID, "pw")
            pw_field.send_keys(NAVER_PASSWORD)
            
            # 로그인 버튼 클릭
            login_button = driver.find_element(By.ID, "log.login")
            login_button.click()
            
            # 로그인 완료 대기
            try:
                WebDriverWait(driver, 10).until(
                    EC.url_changes("https://nid.naver.com/nidlogin.login")
                )
                add_log(f"✅ Naver: 로그인 성공!")
            except:
                add_log(f"⚠️ Naver: 로그인 상태 확인 불가, 계속 진행합니다...")
            
            # 서치어드바이저 페이지로 이동
            add_log(f"🔄 Naver: 서치어드바이저 페이지로 이동 중...")
            driver.get("https://searchadvisor.naver.com/console/board")
            time.sleep(3)  # 페이지 로딩 대기
            
            # 웹 페이지 수집 요청 페이지로 이동
            add_log(f"🔄 Naver: 웹 페이지 수집 요청 페이지로 이동 중...")
            driver.get("https://searchadvisor.naver.com/console/request")
            time.sleep(2)
            
            # URL 입력 필드 찾기 및 입력
            add_log(f"📝 Naver: URL 입력 중...")
            
            try:
                url_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='URL을 입력하세요']")
                url_field.clear()
                url_field.send_keys(url)
                
                # 수집 요청 버튼 클릭
                add_log(f"📤 Naver: 수집 요청 제출 중...")
                submit_button = driver.find_element(By.XPATH, "//button[contains(text(), '수집 요청')]")
                submit_button.click()
                
                # 로딩 표시 감지 및 대기
                add_log(f"⏳ Naver: 로딩 중... (약 5초 소요)")
                
                # 로딩 인디케이터 감지 시도
                loading_detected = False
                try:
                    # 로딩 인디케이터 찾기 (CSS 선택자는 실제 네이버 페이지에 맞게 조정 필요)
                    loading_element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.loading, span.loading, .spinner, .loader"))
                    )
                    loading_detected = True
                    add_log(f"⏳ Naver: 로딩 표시 감지됨, 완료 대기 중...")
                except:
                    add_log(f"ℹ️ Naver: 로딩 표시가 감지되지 않았습니다. 완료 여부를 확인합니다...")
                
                # 로딩이 감지되었다면, 로딩 표시가 사라질 때까지 대기
                if loading_detected:
                    try:
                        WebDriverWait(driver, NAVER_TIMEOUT).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.loading, span.loading, .spinner, .loader"))
                        )
                        
                        # 할당량 증가
                        usage_count = increment_usage_count("Naver")
                        remaining = DAILY_QUOTA["Naver"] - usage_count
                        
                        add_log(f"✅ Naver: 로딩 완료, 요청이 성공적으로 처리되었습니다! (오늘 {usage_count}/{DAILY_QUOTA['Naver']}개 사용)")
                        update_url_status(url, "Naver", STATUS_SUCCESS)
                        
                        # 네이버 요청 간 추가 지연 (제한 방지)
                        add_log(f"⏱️ Naver: 다음 요청을 위해 추가 대기 중... (네이버 제한 방지)")
                        time.sleep(5)  # 네이버 요청 간 추가 5초 대기
                        
                        return STATUS_SUCCESS
                    except:
                        add_log(f"⚠️ Naver: 로딩 완료 감지 실패, 하지만 요청은 전송되었습니다.")
                        update_url_status(url, "Naver", STATUS_UNKNOWN)
                        return STATUS_UNKNOWN
                else:
                    # 로딩이 감지되지 않았다면 5초 대기 후 성공으로 간주
                    time.sleep(5)
                    
                    # 할당량 증가
                    usage_count = increment_usage_count("Naver")
                    remaining = DAILY_QUOTA["Naver"] - usage_count
                    
                    add_log(f"✅ Naver: {url} 수집 요청 전송 완료 (오늘 {usage_count}/{DAILY_QUOTA['Naver']}개 사용)")
                    update_url_status(url, "Naver", STATUS_SUCCESS)
                    
                    # 네이버 요청 간 추가 지연 (제한 방지)
                    add_log(f"⏱️ Naver: 다음 요청을 위해 추가 대기 중... (네이버 제한 방지)")
                    time.sleep(5)  # 네이버 요청 간 추가 5초 대기
                    
                    return STATUS_SUCCESS
                
            except Exception as e:
                # 할당량 초과 감지 시도 (메시지 또는 요소 기반)
                try:
                    quota_exceeded_element = driver.find_element(By.XPATH, "//div[contains(text(), '할당량') or contains(text(), '제한') or contains(text(), '초과')]")
                    if quota_exceeded_element:
                        add_log(f"❌ Naver: {url} 색인 요청 실패 - 할당량 초과")
                        update_url_status(url, "Naver", STATUS_QUOTA_EXCEEDED)
                        
                        # 할당량 상태 업데이트
                        quota_data = load_daily_quota()
                        quota_data["usage"]["Naver"] = DAILY_QUOTA["Naver"]
                        save_daily_quota(quota_data)
                        
                        # 사용자에게 알림
                        root.after(0, lambda: messagebox.showwarning(
                            "네이버 할당량 초과", 
                            "네이버 서치어드바이저 일일 할당량을 초과했습니다.\n"
                            "더 이상의 네이버 색인 요청은 내일까지 불가능합니다."
                        ))
                        return STATUS_QUOTA_EXCEEDED
                except:
                    pass
                
                add_log(f"❌ Naver: {url} 요소 찾기 또는 입력 실패: {e}")
                update_url_status(url, "Naver", STATUS_ERROR)
                return STATUS_ERROR
            
        finally:
            # 브라우저 종료
            driver.quit()
            
    except Exception as e:
        add_log(f"❌ Naver: {url} 서치어드바이저 자동화 실패: {e}")
        update_url_status(url, "Naver", STATUS_ERROR)
        return STATUS_ERROR

# 기존 네이버 API 함수는 주석 처리하고 웹 자동화 함수를 사용
def call_naver_indexing_api(url, client_id, client_secret):
    # 웹 자동화 함수 호출
    return call_naver_search_advisor(url)

# --- 메인 색인 프로세스 함수 ---
def start_indexing_process():
    sitemap_url_str = sitemap_combobox.get().strip()

    google_enabled = google_var.get()
    bing_enabled = bing_var.get()
    naver_enabled = naver_var.get()

    if not sitemap_url_str:
        messagebox.showwarning("경고", "사이트맵 URL을 입력하세요.")
        return
    
    if not (google_enabled or bing_enabled or naver_enabled):
        messagebox.showwarning("경고", "최소 하나의 플랫폼을 선택하세요.")
        return

    # 사이트맵 히스토리에 추가
    save_sitemap_history(sitemap_url_str)
    update_sitemap_combobox()

    add_log("🚀 색인 요청 프로세스를 시작합니다...")
    
    # 버튼 비활성화 (중복 실행 방지)
    request_button.config(state=tk.DISABLED)
    
    threading.Thread(target=indexing_task_thread, 
                     args=(sitemap_url_str, google_enabled, bing_enabled, naver_enabled),
                     daemon=True).start() # daemon=True 추가 (메인 창 종료 시 스레드도 종료)

def indexing_task_thread(sitemap_url_str, google_enabled, bing_enabled, naver_enabled):
    urls = parse_sitemap(sitemap_url_str)
    if not urls:
        root.after(0, add_log, "❌ 사이트맵에서 유효한 URL을 찾지 못했습니다. 작업을 중단합니다.")
        root.after(0, lambda: request_button.config(state=tk.NORMAL)) # 버튼 다시 활성화
        return

    total_processed_urls = 0 # 실제로 처리 시도한 URL 수
    successful_requests_map = {"Google": 0, "Bing": 0, "Naver": 0, "Total":0}
    
    platforms_to_index = []
    if google_enabled: platforms_to_index.append("Google")
    if bing_enabled: platforms_to_index.append("Bing")
    if naver_enabled: platforms_to_index.append("Naver")

    # URL 상태 관리를 위한 변수
    status_data = load_url_status()
    current_time = int(time.time())
    
    # 시간대에 따른 처리 전략 결정
    current_hour = datetime.datetime.now().hour
    prioritize_recent = True  # 기본적으로 최신 URL 우선
    prioritize_failed = False  # 기본적으로 실패한 URL은 나중에 처리
    
    # 시간대에 따라 전략 변경
    if current_hour >= 16:  # 오후 4시 이후
        add_log("🕙 오후 시간대입니다. 누락/실패한 URL을 우선 처리합니다.")
        prioritize_failed = True  # 실패한 URL 우선
    else:
        add_log("🕙 오전/오후 시간대입니다. 최신 URL을 우선 처리합니다.")
    
    # 각 플랫폼별 처리할 URL 개수 계산
    platform_pending_urls = {}
    for platform in platforms_to_index:
        platform_pending_urls[platform] = get_pending_urls(
            urls, platform, current_time, 
            prioritize_recent=prioritize_recent, 
            prioritize_failed=prioritize_failed
        )
    
    total_api_calls = sum(len(platform_pending_urls[platform]) for platform in platforms_to_index)
    
    root.after(0, add_log, f"📝 총 {len(urls)}개 URL 중 처리 대기 중인 URL 수:")
    for platform in platforms_to_index:
        pending_count = len(platform_pending_urls[platform])
        remaining_quota = get_remaining_quota(platform)
        root.after(0, add_log, f"- {platform}: {pending_count}개 (남은 할당량: {remaining_quota}개)")
    root.after(0, add_log, f"🔄 총 예상 API 호출 수: {total_api_calls}")
    
    processed_api_calls = 0
    
    google_indexing_service = None
    if google_enabled:
        google_indexing_service = get_indexing_service()
        if not google_indexing_service:
            root.after(0, add_log, "❌ Google API 서비스 객체 생성 실패. Google 요청을 건너뜝니다.")
            if "Google" in platforms_to_index:
                 total_api_calls -= len(platform_pending_urls["Google"])
                 platforms_to_index.remove("Google") # 구글 플랫폼 제외
            google_enabled = False 

    # 각 플랫폼별 색인 처리
    exit_processing = False  # 할당량 초과 시 프로세스 종료 플래그
    
    for platform in platforms_to_index:
        if exit_processing:
            break
        
        pending_urls = platform_pending_urls[platform]
        batch_size = GOOGLE_BATCH_SIZE if platform == "Google" else BING_BATCH_SIZE if platform == "Bing" else NAVER_BATCH_SIZE
        
        if not pending_urls:
            root.after(0, add_log, f"ℹ️ {platform}: 처리할 URL이 없습니다.")
            continue
        
        # 할당량 확인
        remaining_quota = get_remaining_quota(platform)
        if remaining_quota <= 0:
            root.after(0, add_log, f"⚠️ {platform}: 일일 할당량({DAILY_QUOTA[platform]}개)을 모두 사용했습니다. 다음 플랫폼으로 넘어갑니다.")
            continue
        
        # 처리할 URL 개수를 할당량에 맞게 조정
        if len(pending_urls) > remaining_quota:
            root.after(0, add_log, f"ℹ️ {platform}: 할당량이 충분하지 않아 {len(pending_urls)}개 중 {remaining_quota}개만 처리합니다.")
            pending_urls = pending_urls[:remaining_quota]
        
        # 한 번에 최대 10개씩 처리 (최신 URL 우선)
        max_per_run = min(10, len(pending_urls))
        if max_per_run < len(pending_urls):
            root.after(0, add_log, f"ℹ️ {platform}: 효율적인 처리를 위해 한 번에 10개씩 처리합니다 (최신 순). 나머지는 다음 실행 시 처리됩니다.")
            pending_urls = pending_urls[:max_per_run]
        
        # 배치 단위로 처리
        batch_count = (len(pending_urls) + batch_size - 1) // batch_size
        root.after(0, add_log, f"📦 {platform}: {batch_count}개 배치로 나누어 처리합니다.")
        
        for batch_idx in range(batch_count):
            if exit_processing:
                break
                
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(pending_urls))
            batch_urls = pending_urls[start_idx:end_idx]
            
            root.after(0, add_log, f"🔄 {platform}: 배치 {batch_idx + 1}/{batch_count} 처리 중... ({len(batch_urls)}개 URL)")
            
            for url in batch_urls:
                result = STATUS_PENDING
                
                if platform == "Google" and google_enabled:
                    if google_indexing_service:
                        result = call_google_indexing_api(google_indexing_service, url)
                    else:
                        result = STATUS_ERROR
                elif platform == "Bing" and bing_enabled:
                    result = call_bing_indexing_api(url, BING_API_KEY)
                elif platform == "Naver" and naver_enabled:
                    result = call_naver_indexing_api(url, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
                
                processed_api_calls += 1
                if result == STATUS_SUCCESS:
                    successful_requests_map[platform] = successful_requests_map.get(platform, 0) + 1
                    successful_requests_map["Total"] = successful_requests_map.get("Total", 0) + 1
                
                # 할당량 초과 감지 시 플랫폼 처리 중단
                if result == STATUS_QUOTA_EXCEEDED:
                    if platform == "Google":  # 구글 할당량 초과 시 전체 프로세스 종료
                        exit_processing = True
                        root.after(0, add_log, f"⚠️ {platform} 할당량 초과로 전체 처리를 중단합니다.")
                        break
                    else:  # 다른 플랫폼은 해당 플랫폼만 중단
                        root.after(0, add_log, f"⚠️ {platform} 할당량 초과로 해당 플랫폼 처리를 중단합니다.")
                        break
                
                root.after(0, update_progress_bar, processed_api_calls, total_api_calls)
                
                # 배치 내 각 요청 사이에 약간의 지연
                if processed_api_calls < total_api_calls and not exit_processing:
                    time.sleep(0.5)
            
            # 배치 간 지연 (할당량 제한 방지)
            if batch_idx < batch_count - 1 and not exit_processing:
                delay_message = f"⏱️ {platform}: 다음 배치 처리 전 10초 대기 중..."
                root.after(0, add_log, delay_message)
                time.sleep(10)  # 배치 간 10초 대기
        
        # 플랫폼 간 지연
        if platform != platforms_to_index[-1] and not exit_processing:
            platform_delay_message = f"⏱️ 다음 플랫폼으로 넘어가기 전 5초 대기 중..."
            root.after(0, add_log, platform_delay_message)
            time.sleep(5)  # 플랫폼 간 5초 대기

    # 작업 완료 후 요약 정보 출력
    if exit_processing:
        summary_message = "⚠️ 할당량 초과로 색인 요청 프로세스가 중단되었습니다.\n"
    else:
        summary_message = "🎉 모든 색인 요청 프로세스가 완료되었습니다!\n"
        
    summary_message += f"처리 완료된 URL 수: {processed_api_calls}\n"
    
    # 상태별 결과 카운트
    status_counts = {
        STATUS_SUCCESS: 0,
        STATUS_ERROR: 0,
        STATUS_TIMEOUT: 0,
        STATUS_UNKNOWN: 0,
        STATUS_REQUESTED: 0,
        STATUS_QUOTA_EXCEEDED: 0
    }
    
    # 상태 데이터 갱신 및 카운트
    status_data = load_url_status()
    for url in urls:
        for platform in platforms_to_index:
            if url in status_data and platform in status_data[url]:
                status = status_data[url][platform]['status']
                if status in status_counts:
                    status_counts[status] += 1
    
    # 상태별 결과 출력
    summary_message += f"\n요청 결과 상세:\n"
    summary_message += f"✅ 성공: {status_counts[STATUS_SUCCESS]}개\n"
    summary_message += f"❌ 실패: {status_counts[STATUS_ERROR]}개\n"
    summary_message += f"⏱️ 시간 초과: {status_counts[STATUS_TIMEOUT]}개\n"
    summary_message += f"❓ 응답 불분명: {status_counts[STATUS_UNKNOWN]}개\n"
    summary_message += f"🔄 요청 중: {status_counts[STATUS_REQUESTED]}개\n"
    if status_counts[STATUS_QUOTA_EXCEEDED] > 0:
        summary_message += f"⚠️ 할당량 초과: {status_counts[STATUS_QUOTA_EXCEEDED]}개\n"
    
    # 플랫폼별 결과 출력
    summary_message += f"\n플랫폼별 성공 건수:\n"
    summary_message += f"Google: {successful_requests_map['Google']}개\n"
    summary_message += f"Bing: {successful_requests_map['Bing']}개\n"
    summary_message += f"Naver: {successful_requests_map['Naver'] if naver_enabled else 0}개\n"
    
    # 할당량 정보 출력
    quota_data = load_daily_quota()
    summary_message += f"\n플랫폼별 할당량 사용 현황:\n"
    for platform in platforms_to_index:
        used = quota_data["usage"].get(platform, 0)
        total = DAILY_QUOTA.get(platform, 0)
        remaining = max(0, total - used)
        summary_message += f"{platform}: {used}/{total}개 사용 (남은 할당량: {remaining}개)\n"

    # 실패한 URL이 있는지 확인
    failed_count = status_counts[STATUS_ERROR] + status_counts[STATUS_TIMEOUT]
    if failed_count > 0:
        summary_message += f"\n실패한 URL은 다음 색인 요청 시 자동으로 재시도됩니다.\n"
        summary_message += "재시도는 마지막 시도 후 약 2시간 뒤에 가능합니다."
    
    # 처리 전략 안내
    if prioritize_failed:
        summary_message += f"\n🕙 현재 시간대는 오후 시간으로, 누락/실패한 URL을 우선 처리했습니다."
    else:
        summary_message += f"\n🕙 현재 시간대는 오전/오후 시간으로, 최신 URL을 우선 처리했습니다."

    root.after(0, add_log, summary_message)
    root.after(0, lambda: progress_fill.config(width=0)) # 진행률 바 초기화
    root.after(0, lambda: request_button.config(state=tk.NORMAL)) # 버튼 다시 활성화

    # 결과 메시지 표시
    result_message = (
        f"색인 요청 처리 완료\n\n"
        f"총 처리: {processed_api_calls}개 URL\n"
        f"✅ 성공: {status_counts[STATUS_SUCCESS]}개\n"
        f"❌ 실패: {status_counts[STATUS_ERROR]}개\n"
        f"⏱️ 시간 초과: {status_counts[STATUS_TIMEOUT]}개\n"
        f"❓ 응답 불분명: {status_counts[STATUS_UNKNOWN]}개\n"
    )
    
    if exit_processing:
        result_message += f"\n⚠️ 할당량 초과로 처리가 중단되었습니다."
    
    result_message += f"\n\n남은 할당량:"
    for platform in platforms_to_index:
        remaining = get_remaining_quota(platform)
        result_message += f"\n{platform}: {remaining}개"
    
    if prioritize_failed:
        result_message += f"\n\n🕙 오후 시간대: 누락/실패한 URL 우선 처리됨"
    else:
        result_message += f"\n\n🕙 오전/오후 시간대: 최신 URL 우선 처리됨"
    
    result_message += f"\n\nURL 상태는 '📊 URL 상태' 버튼에서 확인할 수 있습니다."
    
    root.after(0, lambda: messagebox.showinfo("색인 요청 완료", result_message))
    
    # 구글 할당량이 모두 소진되었으면 프로그램 종료 여부 확인
    if exit_processing:
        def confirm_exit():
            if messagebox.askyesno(
                "프로그램 종료", 
                "Google 할당량이 모두 소진되었습니다.\n"
                "2시간 후에 다시 시도할 수 있습니다.\n\n"
                "프로그램을 종료하시겠습니까?"
            ):
                root.destroy()
        
        root.after(1000, confirm_exit)

def update_progress_bar(completed, total):
    if total > 0:
        percentage = (completed / total) * 100
        # 진행률 바 최대 너비는 760으로 고정되어 있음
        bar_width = int(percentage / 100 * (progress_frame.winfo_width() or 760)) # 초기에는 너비가 0일 수 있음
        progress_fill.config(width=bar_width)
    else: # total이 0이면 진행률 바도 0
        progress_fill.config(width=0)

# --- 버튼들 ---
button_frame = tk.Frame(root, bg="#2C3E50")
button_frame.pack(pady=10)

request_button = tk.Button(button_frame, text="🚀 색인 요청 시작", command=start_indexing_process,
                           bg="#667eea", fg="white", font=("Segoe UI", 10, "bold"), relief="raised", bd=2)
request_button.pack(side=tk.LEFT, padx=10, pady=5)

settings_main_button = tk.Button(button_frame, text="⚙️ API 설정", command=open_settings_window,
                            bg="#455A64", fg="white", font=("Segoe UI", 10), relief="raised", bd=2)
settings_main_button.pack(side=tk.LEFT, padx=5, pady=5)

status_button = tk.Button(button_frame, text="📊 URL 상태", command=open_url_status_window,
                       bg="#3498db", fg="white", font=("Segoe UI", 10), relief="raised", bd=2)
status_button.pack(side=tk.LEFT, padx=5, pady=5)

quota_button = tk.Button(button_frame, text="📈 할당량 관리", command=open_quota_manager,
                      bg="#f39c12", fg="white", font=("Segoe UI", 10), relief="raised", bd=2)
quota_button.pack(side=tk.LEFT, padx=5, pady=5)

# --- 진행률 바 ---
progress_container = tk.Frame(root, bg="#2C3E50") # 배경색 일치
progress_container.pack(pady=10, padx=20, fill=tk.X)

progress_frame = tk.Frame(progress_container, bg="#E0E0E0", height=10, relief="flat", bd=0)
progress_frame.pack(fill=tk.X) # 너비를 채우도록 함

progress_fill = tk.Frame(progress_frame, bg="#667eea", width=0, height=10)
progress_fill.pack(side=tk.LEFT) # fill=tk.Y 불필요, 어차피 height 고정

# --- 로그 영역 ---
log_label = tk.Label(root, text="로그", font=("Segoe UI", 10, "bold"), fg="white", bg="#2C3E50")
log_label.pack(anchor=tk.W, padx=20, pady=(10,0)) # pady 상단에만 적용

log_area = scrolledtext.ScrolledText(root, width=90, height=15,
                                     font=("Courier New", 9), bg="#2D3748", fg="#E2E8F0",
                                     bd=2, relief="groove", wrap=tk.WORD) # wrap=tk.WORD 추가 (가로 스크롤 방지)
log_area.pack(pady=(0,10), padx=20, fill=tk.BOTH, expand=True) # pady 하단에만 적용

# 초기 로그 메시지
add_log("SEO 색인 도구가 시작되었습니다.")
add_log("사이트맵 URL을 입력하고 '색인 요청 시작' 버튼을 클릭하세요.")
add_log("주의: API 키, 사이트 URL 등은 코드 상단에서 실제 값으로 설정해야 합니다.")

# Tkinter 이벤트 루프 시작
root.mainloop()