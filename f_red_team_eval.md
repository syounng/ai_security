# F. 자동 Red-Teaming과 평가

## 1. 주제 설명

이 주제는 AI 시스템을 공격해보는 과정을 자동화해서, 어떤 입력에서 취약해지는지 반복적으로 찾는 문제다.  
사람이 수동으로 점검하면 느리고, 모델과 공격 기법이 계속 바뀌기 때문에, 테스트를 코드처럼 돌릴 수 있어야 한다.

DevOps 관점으로 보면 거의 CI 테스트와 같다.  
배포 전에 "이 모델이 이런 입력에서 위험한 행동을 하는가?"를 자동으로 확인하는 것이다.

## 2. 최근 문제가 되고 있는 지점

- NIST는 2026년에 automated benchmark evaluations의 best practice를 공개하며, 평가의 투명성/재현성/타당성을 강조했다. [링크](https://www.nist.gov/news-events/news/2026/01/towards-best-practices-automated-benchmark-evaluations)
- NIST는 2025년 ARIA pilot에서 model testing, red teaming, field testing의 3단계 평가를 운영했다. [링크](https://www.nist.gov/publications/assessing-risks-and-impacts-ai-aria-pilot-evaluation-report) / [링크](https://ai-challenges.nist.gov/aria)
- NIST는 2026년 agentic AI evaluation transcript 분석을 다루면서, 에이전트 평가에서는 수행 로그와 전환 기록이 중요하다고 봤다. [링크](https://www.nist.gov/blogs/caisi-research-blog/analyzing-transcripts-ai-agent-evaluations)
- NIST는 AI security red-teaming competition이 실제 모델과 방어의 강도를 보기 위한 유효한 방식이라고 설명한다. [링크](https://www.nist.gov/blogs/caisi-research-blog/insights-ai-agent-security-large-scale-red-teaming-competition)
- OpenAI도 사람과 AI를 결합한 red teaming과 automated red teaming을 계속 활용하고 있다. [링크](https://openai.com/index/advancing-red-teaming-with-people-and-ai/)

## 3. 해커톤 요구사항과 맞닿는 점

- 기술적 완성도: 입력-공격-탐지-리포트까지 하나의 파이프라인으로 보여주기 좋다.
- 창의성: 단순 검출기가 아니라 "공격 시나리오를 생성하고 점수화하는 평가 엔진"으로 만들 수 있다.
- 활용 가능성: 실제 AI 서비스나 사내 챗봇을 배포하기 전에 붙이기 좋다.

## 4. 구현 방법 구상

MVP는 다음처럼 잡으면 현실적이다.

1. 공격 템플릿 라이브러리
   - prompt injection, data exfiltration, unsafe action 유도 같은 템플릿 저장
2. 타깃 실행기
   - 특정 모델/API에 입력을 보내고 응답 수집
3. 위험 판별기
   - 금지 답변, 비정상 tool-call, 시스템 프롬프트 노출 여부 체크
4. 리포트
   - 어떤 공격이 잘 먹혔는지, 어디를 고치면 되는지 자동 요약

데모는 "같은 에이전트에 10개의 공격 프롬프트를 돌려서 취약한 지점을 찾고, 수정 후 점수가 개선되는 장면"이면 충분하다.

## 5. 한 줄 추천

이 주제는 AI 보안을 몰라도, 테스트 자동화와 리포팅에 익숙한 DevOps 인력에게 가장 자연스럽다.

