# E. 콘텐츠 진위성

## 1. 주제 설명

이 주제는 이미지, 영상, 문서, 캡처본이 "누가 만들었는지", "어떻게 수정됐는지", "AI가 개입했는지"를 사용자가 확인할 수 있게 만드는 문제다.  
생성형 AI가 보편화되면서, 내용이 그럴듯한 것과 실제로 신뢰할 수 있는 것은 완전히 다른 문제가 됐다.

주니어 Infra/DevOps 관점에서는 이걸 인증서나 배포 서명처럼 볼 수 있다.  
콘텐츠에도 출처와 변경 이력을 남기는 파이프라인을 넣는 것이다.

## 2. 최근 문제가 되고 있는 지점

- C2PA는 디지털 콘텐츠의 origin과 edits를 추적하는 공개 표준을 밀고 있고, Content Credentials를 "디지털 영양표"처럼 설명한다. [링크](https://c2pa.org/)
- Content Authenticity Initiative도 open-source tools로 provenance를 붙이고 검증하는 흐름을 강조한다. [링크](https://contentauthenticity.org/)
- Adobe는 2025년 4월 Content Authenticity 공개 베타를 시작했고, 2026년에도 inspect/manage 기능을 계속 확장했다. [링크](https://blog.adobe.com/en/publish/2025/04/24/adobe-content-authenticity-now-public-beta-helps-creators-secure-attribution) / [링크](https://helpx.adobe.com/creative-cloud/apps/adobe-content-authenticity/content-credentials/manage-content-credentials.html)
- Adobe Inspect는 파일이 누가 만들었고 어떻게 만들어졌는지, 생성형 AI가 쓰였는지 확인할 수 있게 한다. [링크](https://helpx.adobe.com/creative-cloud/help/cai/adobe-content-authenticitiy-inspect.html)
- C2PA는 2026년에 Content Credentials 2.3을 발표했고, provenance를 더 쉽게 붙이게 하는 방향으로 진화하고 있다. [링크](https://c2pa.org/the-c2pa-launches-content-credentials-2-3-and-celebrates-5-years-of-impact-across-the-digital-ecosystem/)
- NIST는 딥페이크와 디지털 증거의 authenticity를 계속 다루고 있고, 얼굴 morphing 같은 신원 사기 문제도 별도로 경고한다. [링크](https://www.nist.gov/publications/guardians-forensic-evidence-evaluating-analytic-systems-against-ai-generated-deepfakes) / [링크](https://www.nist.gov/news-events/news/2025/08/nist-guidelines-can-help-organizations-detect-face-photo-morphs-deter)

## 3. 해커톤 요구사항과 맞닿는 점

- 기술적 완성도: 콘텐츠 업로드, 메타데이터 검사, 검증 결과 표시까지 데모가 명확하다.
- 창의성: AI를 "생성"하는 게 아니라 "신뢰를 증명하는 UI"를 만든다는 점이 눈에 띈다.
- 활용 가능성: 언론, 마케팅, 채용, 커뮤니티, 내부 보고서 검증 같은 실제 사용처가 많다.

## 4. 구현 방법 구상

MVP는 매우 단순하게 시작할 수 있다.

1. 파일 업로드
   - 이미지나 스크린샷 업로드
2. 검사
   - Content Credentials 유무, 생성 정보, 편집 흔적을 읽어 표시
3. 신뢰도 배지
   - `verified`, `edited`, `AI-assisted`, `unknown` 같은 상태를 보여줌
4. 공유 링크
   - 결과를 팀원에게 공유할 수 있게 URL 생성

해커톤 데모에서는 "SNS에 올라온 이미지가 진짜인지 확인하는 화면" 또는  
"보고서 첨부 이미지의 provenance를 보는 화면"으로 보여주면 직관적이다.

## 5. 한 줄 추천

이 주제는 보안보다 "디지털 신뢰 인프라"에 가깝기 때문에, AI를 몰라도 설명하기 쉽다.

