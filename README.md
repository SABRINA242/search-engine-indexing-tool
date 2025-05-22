# 🔍 검색엔진 색인 자동화 도구

Google Search Console, Bing Webmaster Tools, 네이버 서치어드바이저에 자동으로 색인을 요청하는 웹 도구입니다.

## ✨ 주요 기능

- **다중 플랫폼 지원**: Google, Bing, 네이버 동시 색인 요청
- **설정 관리**: API 키와 사이트 설정을 안전하게 로컬 저장
- **배치 처리**: 여러 URL을 한 번에 색인 요청
- **실시간 모니터링**: 색인 요청 진행상황과 결과 실시간 확인
- **데이터 보안**: 모든 설정은 사용자 브라우저에만 저장 (서버 저장 안함)

## 🚀 사용법

### 1. 사이트 설정
- 사이트 URL과 사이트맵 URL 입력
- 설정 저장/불러오기 기능 활용

### 2. API 설정
- **Google Search Console**: OAuth 2.0 Client ID/Secret
- **Bing Webmaster Tools**: API Key
- **네이버 서치어드바이저**: Client ID/Secret

### 3. 색인 요청
- 색인할 URL 목록 입력 (한 줄에 하나씩)
- 원하는 플랫폼 선택
- 색인 요청 실행

## 🔧 API 설정 가이드

### Google Search Console API
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Search Console API 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. 승인된 리디렉션 URI 설정

### Bing Webmaster Tools API
1. [Bing Webmaster Tools](https://www.bing.com/webmasters/)에서 사이트 등록
2. API 키 발급 요청
3. 사이트 소유권 확인

### 네이버 서치어드바이저 API
1. [네이버 개발자센터](https://developers.naver.com/)에서 애플리케이션 등록
2. 서치어드바이저 API 사용 권한 신청
3. Client ID/Secret 발급

## 📱 호환성

- **브라우저**: Chrome, Firefox, Safari, Edge (최신 버전)
- **모바일**: 반응형 디자인으로 모바일 기기 지원
- **데이터 저장**: localStorage 사용 (브라우저 로컬 저장)

## 🔒 보안 및 개인정보

- 모든 API 키와 설정은 사용자 브라우저에만 저장됩니다
- 서버에 어떤 개인정보도 전송하지 않습니다
- 설정 파일을 JSON 형태로 내보내기/가져오기 가능

## 🎯 향후 계획

- [ ] 스케줄링 기능 (정기적 색인 요청)
- [ ] 이메일/슬랙 알림 기능
- [ ] 색인 상태 추적 및 분석
- [ ] 다양한 검색엔진 추가 지원

## 🤝 기여하기

이 프로젝트는 오픈소스입니다. 기여를 환영합니다!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 Issues를 통해 연락해주세요.

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!
