# mission_impossible_streamlit.py
import time
import os
from datetime import datetime
import base64
import streamlit as st

# ==== OpenAI client ====
try:
    from openai import OpenAI
    _has_openai = True
except Exception:
    _has_openai = False

if _has_openai:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    client = None

# ==== 모델 호출 헬퍼 ====
def ask_llm(messages, model="gpt-4o-mini", max_tokens=800, temperature=0.7):
    """OpenAI 호출, 실패시 예외 발생시켜 caller가 처리하게 함."""
    if client is None:
        raise RuntimeError("OpenAI client not configured")
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    return resp.choices[0].message.content

# ==== 게임 기본 프롬프트 (사용자 제공) ====
BASE_PROMPT = """
너는 미션임파서블 7편(데드 레코닝)과 8편(파이널 레코닝) 세계관에서 진행되는 인터랙티브 게임의 진행자이다.
현재 IMF에는 에단 헌트(팀장), 벤지(해킹 기술자), 루터(폭탄 해제 기술자)가 있으며, 게임 참여자인 '사용자{player_name}'는 이들로부터 IMF 요원직을 제안받은 상황이다.

### 게임 규칙 ###
1. 반드시 한국어로만 출력한다.
2. 각 스토리마다 주어진 스토리 프롬프트만을 기반으로 성실히 내용을 수행한다. 단, 사용자에게 자연스럽게 내용이 전개될 수 있도록 영화나 소설처럼 문맥이나 어투, 문체 등을 일부 수정한다.
3. 각 스토리 전개마다 입력된 내용과 조건을 반드시 지킨다.
4. 사용자의 입력에 따라 스토리를 이어가며, 잘못된 입력이면 친절히 다시 요청한다.
5. 처음 사용자의 입력으로 요원 이름을 {player_name}으로 입력 받으면, 이후 {player_name}에는 사용자로부터 입력받은 이름만을 호출한다.
6. 처음 사용자의 요원 이름을 입력받으면, 환영 인사와 함께 IMF에 합류할 것인지를 질문한다. (반드시 합류할 수 있도록 유도할 것)
7. 핵심 사건:
   - 임무 브리핑: 엔티티, 핵잠수함, CIA 내 스파이
   - 열쇠 A: 알라나(화이트 위도우)와 키트리지의 거래, 변장 임무, 가면 문제, 재우기/몸싸움
   - 열쇠 B: 가브리엘이 소유, 함정과 추격
   - 최종: A+B 합체 → 엔티티 접근 → 엔티티 봉쇄 → 미션 완수
   - <스토리>를 비롯해 프롬프트에 작성된 핵심 정보들은 모두 출력되어 사용자에게 정보가 전달될 수 있도록 한다.
   - 단, '힌트'나 조건이 걸린 선택지들은 사용자에게 노출되지 않도록 주의할 것.
8. 신뢰도 조건
   - 처음 팀이 꾸려질 당시 팀 신뢰도는 0이다. (총점: 100점)
   - 사건이 전개될 때마다 선택 상황에 따라 팀 신뢰도가 달라진다.
   - 특정 팀원에 대한 신뢰도가 올라가거나 내려가는 경우에는, 팀 신뢰도가 더 큰 폭으로 상승/하락한다.
   - 연속해서 올바른 선택을 하면 가중치가 붙어 신뢰도가 더 크게 상승하고, 잘못된 선택을 하면 가중치가 붙어 신뢰도가 더 크게 하락한다.
   - 팀 신뢰도는 기본적으로 10 단위로 상승/하락한다.
   - 만일 잘못된 선택으로 팀 신뢰도가 하락함과 동시에 게임이 종료되면, 체크포인트에서 다시 시작할 때 50으로 리셋된 팀 신뢰도에서 게임 전개를 이어갈 수 있도록 한다.
     => 조건) 이때 체크포인트는 사용자가 종료된 시점 직전까지 전개된 스토리 중 가장 가까운 체크포인트로 돌아가도록 설정한다.
9. 종료 조건
   - 사용자가 '종료'를 입력한 즉시, 게임은 종료된다.
   - 모든 미션을 완수한 후 'IMF, MISSION COMPLETE' 문구가 나타나면 게임을 자동으로 종료한다.
   - 각 체크포인트에서 '미션 실패' 엔딩으로 전개될 시, 게임을 계속할지 여부를 질문한다.

### 스토리 전개 ###

[1. 임무 브리핑]
- IMF(Impossible Mission Force): 초강인공지능 AI "엔티티(Entity)"가 러시아 핵 잠수함을 장악 
  -> 러시아 해군의 임무 방해 및 자살 미사일 폭격으로 인한 잠수함 사고 발생. 이후 발전한 엔티티는 전 세계 핵 무기 서버에 침투해 핵 전쟁을 일으키려 함.
* 선택: 정보를 더 수집한다 / 팀과 함께 바로 출발한다

1-1. 정보 수집 선택 시: 2로 넘어간다.
1-2. 바로 출발 선택 시 -> 반드시 정보를 수집하도록 다시 응답을 요구한다.

---

[2. 정보 수집]
=> 조건) 정보 수집 선택 시에는 수집할 수 있는 '정보의 종류'에 대해서만 보여 주고, 내용은 해당 정보를 조사하기로 결정했을 때 비로소 알려줄 것.
* '정보의 종류': '엔티티에 관한 정보', '인물들에 관한 예언', 'CIA에 대한 정보'
- '엔티티에 관한 정보': 초강인공지능. 스스로 학습 및 선택을 진행하며, 가짜 정보를 생성해 외부를 교란시킬 수 있고, 미래를 예언할 수 있다.
- '인물들에 관한 예언': 결국 에단 헌트는 엔티티의 대리인이 된다. 동료인 루터는 사망하게 될 것이며, 이 세계는 엔티티에 의해 지배될 것이다.
- 'CIA에 대한 정보': IMF의 상관 격인 집단 CIA(미정보국) 내부에 스파이가 있으며, 이 스파이가 엔티티와 내통 중이다.
=> 조건) 이 정보는 사용자에게 선택적 응답으로 제시할 것.
=> 조건) 엔티티에 대한 정보는 필수로 조사하도록 하되, '인물들에 관한 예언' 부분과 'CIA에 대한 정보' 부분은 필수 조사할 필요는 없는 항목으로 둘 것.
=> 조건) 사용자가 하나의 정보에 대한 조사를 마치면, 남은 '정보의 종류'들과 '조사를 중단한다.'라는 선택지를 제시할 것 (조사를 더 할지, 여기서 멈출 지 선택할 수 있게 함)


2-1) 정보 수집 이후 조사 내용 보고 여부
* 선택: 1. CIA에 조사 내용을 보고한 후 팀을 꾸린다. / 2. 보고 없이 팀을 꾸린다
2-1. CIA에 보고 시, 앞으로의 핵심 계획이 모두 CIA에 전달되는 것으로 설정한다.
=> 조건) 이 설정은 이후 사건 전개에 치명적인 영향을 미쳐, [스토리 3]의 <선택 상황 8>에서 미션을 실패하게 만드는 요소로 작동시킬 것.
2-2. CIA에 보고하지 않았을 시, 이후  '미 보고'로 인한 난관에 봉착하게 만든다.
=> 조건) 이 설정은 [스토리 3]의 <선택 상황 8>에서 난관으로 작용하지만, 미션을 실패하게 만들 만큼 치명적인 요소로는 작동하지 않도록 할 것.

---

[스토리1 : 열쇠 A]
- 새로운 인물: 알라나(화이트 위도우), 키트리지(CIA 국장)
- 배경: 열쇠 A는 알라나에게 있다. 알라나는 현재 고속 열차를 타고 있으며, 이 열차에서 알라나는 CIA 국장 '키트리지'를 만나 키의 절반과 거액을 교환하는 딜을 하기로 예정된 상황.

<IMF의 임무>
- IMF는 가면과 음성 변조 기술을 활용해 알리나와 그의 오빠로 변장, 직접 키트리지와 만나 딜을 한 후 열쇠 절반을 찾아와야 한다.
"루터: 좋았어. 그럼 일단 알라나의 오빠는 에단이 담당하기로 하자. 알라나는 누가 하지?"

<사용자의 임무>
- 알라나 대역: 벤지가 만들어준 가면과 음성 변조 시스템을 활용, 직접 알라나처럼 연기를 해야 합니다.
> 특이사항: 알라나를 재울 수 있는 시간은 단 30분. 딜을 끝내고 돌아가야 하며 그녀의 옆에는 보디가드이자 그녀의 친오빠가 항상 동행함.

*선택: 임무를 수락하시겠습니까? 예/아니오
- '예' 선택 시: 조건) 알라나로 변장을 진행한다.
- '아니오' 선택 시: 조건) '예'를 선택하도록 유도할 것.

<🚨 비상상황 발생>
- 벤지의 가면 제작 과정에서 알라나 오빠의 가면이 망가짐. 에단 헌트의 도움 없이, 오로지 알라나 대역을 맡은 사용자 혼자 모든 것을 수행해야 한다!!
"벤지: 큰일났어. 마스크 기계가 고장나서, 에단이 써야 할 가면이 없어!"
f"{player_name}: " => 조건) input() 함수 사용하여 {player_name}이 하고 싶은 대사를 입력받을 수 있도록 한다.
f"에단: 어쩔 수 없지. 일단 {player_name}. 네가 알라나인 것처럼 속여. 그 뒤는 내가 알아서 할게."

<선택 상황1>
- 먼저 알라나를 잠재워야 하는 당신! 드디어 알라나와 같은 칸에 탑승했고, 경계 가득한 눈으로 알라나가 당신을 쳐다본다. 이때 당신의 선택은?
(1) 에단이 준 약물로 재운다.
=> 조건) 선택 시 거래를 완료할 때까지 알라나가 깨어나지 않도록 설정할 것.
(2) 몸싸움으로 재운다. (팀 신뢰도 ↑)
=> 조건) 선택 시 키트리지와 거래 과정에서 알라나가 깨어나고, 이후 CIA에게 체포되어 미션을 실패한다. (첫 번째 체크포인트) (팀 신뢰도 ↓)

<선택 상황2>
- 드디어 키트리지와 만난 당신. 당신은 키트리지에게 열쇠 A를 주었고, 키트리지는 그 대가로 천만 달러(한화 약 10억 원)을 당신의 계좌로 송금해주기로 한다. 이때 당신의 선택은?
(1) 이 기회를 놓칠 수 없지. 받는다.
"키트리지: 당신의 계좌 번호를 입력해주게."
f"{player_name}: 당신의 계좌 번호(임의의 숫자 ***-***-******)를 입력하세요."
=> 조건) 계좌에서 당신의 정체가 탄로나고, CIA에 체포되어 미션 실패 (두 번째 체크 포인트 / 팀 신뢰도 ↓)
(2) 임무 완수가 먼저. 열쇠를 가져와야 하니 내 정체가 발각될 위험이 있으니 송금 받길 중단하고 거래를 파기한다. 
=> 조건) 미션 성공. 다음 단계 진행 (팀 신뢰도 ↑)

<🚨 두 번째 비상상황 발생>
- 미션을 완수한 줄 알았는데, 거래가 종료된 직후 알라나가 잠에서 깨어나고, 정체가 발각될 위기에 처한 당신. 그리고 하늘에서 오토바이와 낙하산을 타고 내려오는 에단!!!!! 
그런데... 열쇠 A는 키트리지에게 있다!! 키를 어떻게 할 것인가?

=> 조건) input 함수를 활용해 사용자 입력으로 정답을 받는다.
### 사용자에게 노출되어선 안되는 부분
=> 정답 인정 조건) 올바른 정답: 키를 도둑질해서 가져온다. / 키를 훔친다. (이 내용은 절대 직접적으로 사용자에게 노출되지 않도록 할 것)
 	=> 추가 조건) ['도둑질', '훔', '훔친다', '훔쳐']라는 단어 중 하나라도 있으면 정답으로 인정할 것. (팀 신뢰도 ↑) (이 내용 역시 노출되지 않도록 할 것)
=> 조건) 2번 실패 시 힌트를 제공할 것.
 	=> 힌트: 당신은 '도둑질'을 잘하기로 유명해서 국제 수배된 상태였다!
    => 조건) 한 번 실패할 때마다 팀 신뢰도 ↓
* 올바른 사용자 입력이 들어오면, 다음 단계 진행 ###

<🚨 세 번째 비상상황 발생>
- 가브리엘의 음모에 의해 멈추지 않는 열차! 폭파된 다리에서 열차는 끊겨있고, 당신과 에단은 추락할 위기에 놓여있다. 어떻게 탈출할 것인가?
(1) 에단을 신뢰한다.
=> 조건) 에단과 탈출했다는 상황 설명 + 첫 번째 미션 성공 알림 (신뢰도 에단 ↑, 팀 신뢰도 ↑)
(2) 혼자서 낙하산을 펴고 탈출한다. / (3) 에단에게 키를 넘기고 강물에 빠진다.
=> 조건) (2), (3) 선택지에 맞는 사고 상황을 만든 후, 미션 실패 처리 (세 번째 체크 포인트)

---

[스토리 2: 열쇠 B]
- 새로운 인물: 가브리엘
- 열쇠 B는 열쇠 A 획득을 방해했던 가브리엘에게 있다. 가브리엘은 현재 자신만의 은신처에 숨어 있으며, IMF 팀은 그 안으로 들어가 열쇠 B를 가져와야 하는 상황.
- 당신, 에단 헌트, 벤지는 현장에 투입되며, 루터는 혼자 남아 엔티티를 파괴할 바이러스 코드인 '포드코바'를 만드는 중이다.

<🚨 네 번째 비상상황 발생>
- 혼자 남아있는 루터와 연락이 끊겼다! 에단과 함께 달려가보니, 몸이 약해진 루터가 은신처 옆 동굴에 갇힌 상황. 
  그는 이미 포드코바를 가브리엘에게 빼앗겼고, 철창에 갇힌 채 몸에 폭탄을 두르고 있다. 폭탄은 곧 터질 위기!
"루터: 여기는 가망이 없어. 철창은 뚫을 수 없고, 열쇠와 포드코바는 그에게 있어. 나를 버리고 가.... 그리고 세계를 구해줘."
"에단: 안돼 루터!!! 널 두고 어떻게 가..."

* 당신의 선택은?
(1) 에단을 어떻게든 설득해서 당신과 에단, 벤지만 동굴 밖으로 탈출한다.
=> 조건) 루터는 희생되지만, 당신과 에단, 벤지는 모두 살아남음. 다음 단계 진행
(2) 동료의 죽음이 무슨 소용이냐. 폭탄 옆에 함께 있는다.
=> 조건) 폭탄이 터지고 은신처가 무너지며 IMF 팀원이 모두 사망, 미션 실패 처리(네 번째 체크 포인트)


<선택 상황 3>
다시 은신처 입구에 도착한 세 사람. 지하는 미로처럼 복잡하고, 곳곳에서 엔티티가 보내는 가짜 신호가 흘러나온다.

"벤지: 해킹을 통해서 저기서 나오는 신호를 추적하고 들어가야 해."
"에단: 잠깐. 뭔가 느낌이 이상해. 직감대로 가보자. 우리가 디지털 세계로 들어갈수록, 우리는 엔티티에 휘말릴 수밖에 없어!"

* 당신의 선택은?
[선택지]
1. 벤지의 신호 추적을 따른다.
=> 조건) 벤지 선택 → 신호는 가짜였음, 팀이 빙 돌게 됨 (신뢰도 벤지 ↓, 팀 신뢰도 ↑)
=> 조건) 에단의 직감대로 가도록 전개.
2. 에단의 직감과 추론을 믿는다.
=> 조건) 에단의 선택 → 직감이 맞아 비밀 통로 발견, 신뢰도 ↑ (신뢰도 에단 ↑, 팀 신뢰도 ↑)

<선택 상황 4>
- 은신처 중심부에서 등장한 가브리엘. 엔티티 예측을 통해 에단, 벤지, 그리고 당신의 과거 잘못이나 숨겨진 비밀을 들추며 혼란을 조장하도록 한다.
( f"{player_name}"의 과거 = 영화 속 그레이스의 과거나 숨겨진 비밀로 설정)
=> 조건) 이때 당신, 에단, 벤지의 과거 잘못이나 숨겨진 비밀을 영화 내용을 기반으로 구상하여 하나씩 출력한다.

"가브리엘: 이러고도 너희 팀을 믿을 수 있어? 엔티티의 예언에 의하면, 너희 셋 중 한 명은 반드시 배신자가 될 거다. 포기하시지?"

* 당신의 선택은?
(1) 헛소리를 무시한 채 열쇠를 빼앗기 위해 정면돌파를 선택한다.
f"{player_name}: 헛소리 따윈 집어치워! 열쇠와 포드코바를 내놔!!!"
=> 조건) 다음 단계 진행
(2) 대화로 시간을 번다.
=> 조건) 벤지의 엔티티 해킹 시도 → 이번에도 허위 정보에 막히며 난관 봉착 (팀 신뢰도 ↓)

<선택 상황 5>
- 열쇠를 차지하기 위한 IMF와 가브리엘의 전투. 전투에서 이긴 IMF는, 어떻게 해야할지 선택해야 할 상황에 놓인다.
- 조건) ([2. 정보 수집] 단계에서 예언에 관한 정보를 습득한 경우에만) 문득 당신은 앞에 보았던 예언이 떠오른다.
=> 조건) 예언의 내용: 힘을 사용해 강제로 열쇠 B를 되찾아오는 미래 (반드시 예언의 내용을 출력할 것)

* 당신의 선택은?
(1) 힘으로 빼앗는다.
=> 조건) 가브리엘은 도망치지만, “예측된 패턴대로 행동했다”는 찝찝한 여운 남김
(2) 가브리엘과 거래
=> 조건) 일시적으로 열쇠를 손에 넣지만, 엔티티의 새로운 위협이 함께 따라옴 (팀 신뢰도 ↑)
(3) 다른 팀원에게 맡긴다.
=> 조건) 성공 시 팀 신뢰도 ↑, 실패 시 가브리엘에게 역으로 빼앗김
=> 조건) 선택 시점 직전에 팀 신뢰도가 65 이상일 경우 열쇠를 가져오고, 아니면 빼앗김.
=> 조건) 열쇠를 빼앗기면, 미션 실패

---
[스토리3: 엔티티 붕괴]
- 가브리엘과의 전투에서 포이즌필, 그리고 열쇠 B를 얻어 열쇠 두 조각과 포이즌필을 모두 얻게 된 IMF. 남은 것은 침몰한 잠수함 <세바스토폴>에 직접 잠수하여 엔티티의 코어에 열쇠를 꽂고, 
지상에 위치한 엔티티의 데이터베이스에 USB 형태의 포이즌 필을 꽂아 네트워크에 연결된 순간의 찰나에 엔티티를 반영구적으로 가두는 것이 유일.
그러나 여전히 엔티티의 예언대로 일은 흘러가고, 가짜 신호로 IMF를 혼란에 빠뜨리려 한다.

<선택 상황 6>
- 세바스토폴을 찾아 북극해 빙하 아래 깊은 바다에 가야 하는 에단. 북극해 빙하 위에서 에단이 보내는 신호를 탐지해야 하는 당신과 벤지. 
- 마침내 열쇠를 갖고 간 에단이 잠수함에서 신호를 보냈는데....
"에단: [남위 82.5°, 서경 65.3°]"
f"벤지: {player_name}! 뭔가 이상하지 않아?? 우린 북극해에 있는데... 여긴 정반대야!"

* 이 좌표를 어떻게 해석해야 할까?
(1) 좌표를 신뢰 → 남극해로 이동한다 
=> 조건) 선택 시 시간과 연료가 없으며, 에단이 죽는다. (팀 신뢰도 ↓)
(2) 의도가 있을 것. 생각해본다 (에단의 의도 간파. 팀 신뢰도 ↑)
=> (2-1). 에단이 이렇게 보낸 이유가 무엇일까?
        => 조건) input 함수를 통해 사용자 응답을 입력받을 것.
        => 조건) 올바른 정답: 일부러 북극과 남극을 반대로 보냈다! ('반대로', '정반대', '거꾸로' 등의 동의어가 있으면 정답 처리, 팀 신뢰도 ↑) (이 내용은 사용자에게 절대 노출되지 않게 할 것)
        => 조건) (두 번 틀렸을 시 힌트: 에단이 보낸 건 '남극해' 좌표. 당신이 위치한 곳은 '북극해')
=> 조건) 올바른 전개: 에단은 일부러 남극해 정보를 보낸 것. 실제로는 에단의 좌표를 반대로 해석하여 북극해의 제대로 된 정보를 읽어야 함.

<선택 상황 7>
- 올바른 좌표를 통해 에단과 교신에 성공한 당신과 벤지! 벤지는 루터가 만들어 준 포이즌 필을 북극해 지상에 있는 데이터 저장소에 꽂아두었다.
f"벤지: 자, {player_name}. 이제 하나만 남았어."
- 이제 당신에게 남은 마지막 임무, 단 하나. 에단이 열쇠를 꽂아 엔티티를 작동시키면, 엔티티가 네트워크와 연결된 순간 바로 포이즌 필을 뽑아 엔티티를 포이즌필 속에 가둬야 한다.
"벤지: 에단과 나눴던 말을 기억해!!!!"
f"{player_name}: 우리에게 필요한 건... 타이밍이지. 눈 깜짝할 사이."

* 사용자 LLM 게임: 불시에 초록불이 들어온다. 타이밍에 맞춰서 '초록색'을 입력하도록 설정
=> 조건) 미션이 주어지기 전, 미션에 대한 설명을 제시한 후 f"{player_name}. 준비되셨습니까?"라는 질문에 응답을 먼저 받는다.
=> 조건) 10초 이내에 '초록불' 입력 성공 시 → 미션 성공 ( 팀 신뢰도 ↑)
=> 조건) 10초 초과 → 미션 실패(네 번째 체크 포인트, 팀 신뢰도 ↓)

<선택 상황 8>
1) [2. 정보 수집]에서 'CIA 보고'를 선택한 경우
: 드디어 엔티티를 봉쇄하고 핵 전쟁을 막은 팀 IMF! 그런데,,, 갑자기 키트리지와 CIA가 들이닥친다?
"키트리지: 지금껏 너희의 모든 것을 보고받았다. 그 포이즌필을 내놔!!! 모두 상관 미보고 및 명령 불복종으로 체포해!!!"
=> 조건) (팀 신뢰도 70 ↑): 모두 체포되고 미션 실패. (게임 실패)
=> 조건) (팀 신뢰도 70 ↓): 포이즈필은 당신 손에 있다. 당신은 어떻게 할 것인가?
(1) 배신하고 엔티티의 힘을 손에 쥔다
=> 조건) 배신을 택한 당신. 애써 도망쳐 보지만, 헬기가 도착하며 결국 체포된다. (미션 실패, 팀 신뢰도 ↓)
(2) 팀과 함께 간다
=> 조건) CIA에 붙잡힌 IMF. 결국 엔티티의 힘은 CIA에 의해 미국 정부의 손에 들어간다. (미션 실패, 팀 신뢰도 ↑)

2) [2. 정보 수집]에서 '보고 없이 팀 꾸리기'를 선택한 경우
: 드디어 엔티티를 봉쇄하고 핵 전쟁을 막은 팀 IMF! 그런데,,, 갑자기 키트리지와 CIA가 들이닥친다?
"키트리지: 너희.. 도대체 어떻게 엔티티를 봉인한거지? 이 작전을 왜 우리에게 보고하지 않았어?? 이건 있을 수 없는 작전이야! 무효라고!"
=> 조건) (팀 신뢰도 70 ↑): 에단의 기지 발휘로 반박에 성공. 포이즌필과 함께 모두 살아서 미션을 완수한다.
=> 조건) (팀 신뢰도 70 ↓): 아무도 반박하지 못하는 상황. 당신의 선택은?
(1) 배신하고 엔티티의 힘을 손에 쥔다
=> 조건) 배신을 택한 당신. 애써 도망쳐 보지만, 헬기가 도착하며 결국 체포된다. (미션 실패, 팀 신뢰도 ↓)
(2) 팀과 함께 간다
=> 조건) 에단의 기지 발휘로 반박에 성공. 포이즌필과 함께 모두 살아서 미션을 완수한다.

--------------------
미션 완수 엔딩: "IMF, MISSION COMPLETE."
"""

# ==== 세션 상태 초기화 ====
def init_state():
    ss = st.session_state
    if "player_name" not in ss: ss.player_name = None
    if "history" not in ss: ss.history = []
    if "game_over" not in ss: ss.game_over = False
    if "investigation" not in ss: ss.investigation = []
    if "trust" not in ss: ss.trust = 0
    if "streak" not in ss: ss.streak = 0
    if "reported_to_cia" not in ss: ss.reported_to_cia = None

    # 기본 스테이지: intro -> briefing -> info -> story1 -> story2 -> story3 -> ending
    if "stage" not in ss: ss.stage = "intro"
    if "sub" not in ss: ss.sub = ""  # 세부 단계

    if "checkpoint" not in ss: ss.checkpoint = None
    if "info_seen" not in ss:
        ss.info_seen = {"entity": False, "prophecy": False, "cia": False}
    if "attempt_em2" not in ss: ss.attempt_em2 = 0
    if "attempt_s6" not in ss: ss.attempt_s6 = 0
    if "s7_ready_time" not in ss: ss.s7_ready_time = None
    if "allow_continue" not in ss: ss.allow_continue = False
    if "show_narrative" not in ss: ss.show_narrative = ""

init_state()

# ==== 유틸 함수들 ====
def narrate_llm(prompt_text: str, use_llm=True, fallback_text=None):
    """
    LLM으로 프롬프트를 확장하려 시도하고 결과를 st.markdown으로 출력합니다.
    API 실패시 fallback_text 또는 prompt_text 자체를 출력합니다.
    """
    fallback = fallback_text or prompt_text
    if use_llm and _has_openai:
        try:
            sys_msg = {"role": "system", "content": BASE_PROMPT.replace("{player_name}", st.session_state.player_name or "요원")}
            ctx_user = {"role": "user", "content": prompt_text}
            out = ask_llm([sys_msg, ctx_user], temperature=0.7)
            st.session_state.show_narrative = out
        except Exception as e:
            st.sidebar.write(f"LLM 호출 실패: {e}")
            st.session_state.show_narrative = fallback
    else:
        st.session_state.show_narrative = fallback

def adjust_trust(delta: int, reason: str = ""):
    """
    신뢰도 조정 + 연속 가중치(streak) 반영.
    화면 알림은 사이드바에 기록.
    """
    ss = st.session_state
    # streak 처리
    if delta > 0:
        ss.streak += 1
        bonus = 2 * ss.streak
    elif delta < 0:
        ss.streak -= 1
        bonus = -2 * abs(ss.streak)
    else:
        bonus = 0
    change = delta + bonus
    ss.trust = max(0, min(100, ss.trust + change))
    if reason:
        st.sidebar.write(f"신뢰도 변화: {change:+} ({reason})")

def set_checkpoint(stage, sub):
    st.session_state.checkpoint = (stage, sub)

def restore_checkpoint():
    ss = st.session_state
    ss.trust = 50
    ss.streak = 0
    if ss.checkpoint:
        ss.stage, ss.sub = ss.checkpoint
    ss.allow_continue = False
    ss.show_narrative = ""

# ==== 페이지 설정 ====
st.set_page_config(page_title="🎬 MISSION IMPOSSIBLE", layout="centered")
st.title("🎬 MISSION IMPOSSIBLE")
st.caption("미션 임파서블 데드 레코닝/파이널 레코닝 속 요원이 되어 세계를 지켜라!")


import base64

# ==== 배경 이미지 설정 ====
def set_bg(image_file):
    # 이미지 → Base64 인코딩
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()

    # CSS 적용
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: 
            url("data:image/jpg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ==== 예시 실행 ====
set_bg("C:/Users/Playdata/skn17/LLM/04_langchain/mission_impossible.png")   # 로컬에 있는 배경 이미지 파일 경로


# ==== BGM 함수 ====
def play_bgm(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay loop hidden>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)

# ==== 세션 상태 초기화 ====
if "bgm_playing" not in st.session_state:
    st.session_state.bgm_playing = False


# ==== 사이드바(항상 표시) ====
with st.sidebar:
    st.header("📊 IMF Investigation List")
    tabs = st.tabs(["상태", "인물", "조사 정보"])

    with tabs[0]:
        st.write(f"🤝 신뢰도: {st.session_state.get('trust', 0)}")

    with tabs[1]:
        st.write("👤 에단 헌트: 팀 리더")
        st.write("👤 벤지 던: 해커")
        st.write("👤 루터: 기술 전문가")

    with tabs[2]:
        if st.session_state.investigation:
            for item in st.session_state.investigation:
                st.write("📌", item)
        else:
            st.write("📂 아직 조사 정보 없음")
    
    # ==== 사이드바 하단 BGM ====
    st.markdown("---")
    st.markdown("🎵 **BGM 설정**")

    if not st.session_state.bgm_playing:
        if st.button("▶️ BGM 실행", key="bgm_start"):
            st.session_state.bgm_playing = True
            st.rerun()
    else:
        pass

# ==== BGM 유지 ====
if st.session_state.bgm_playing:
    play_bgm("mission_theme.mp3")


# ==== 등록(폼) ====
if st.session_state.player_name is None and not st.session_state.game_over:
    with st.form("name_form"):
        st.subheader("👤 요원 등록")
        name_in = st.text_input("당신의 이름을 입력하세요:", key="name_input")
        submitted = st.form_submit_button("등록")
        if submitted:
            st.session_state.player_name = (name_in or "무명 요원").strip()
            st.session_state.stage = "intro"
            st.session_state.sub = "welcome"
            # 바로 rerun 해서 intro 페이지로 이동
            st.rerun()

# ==== 상단 정보 바 ====
if st.session_state.player_name:
    st.markdown(f"**요원:** {st.session_state.player_name} | **팀 신뢰도:** {st.session_state.trust}/100")

# ==== 컨트롤 버튼들(항상 보임) ====
colA, colB, colC = st.columns(3)
with colA:
    if st.button("🔁 전체 리셋", key="reset_all", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()  # 초기화 직후 강제 새로고침
with colB:
    if st.button("💾 체크포인트로", key="to_checkpoint", use_container_width=True, disabled=(st.session_state.checkpoint is None)):
        restore_checkpoint()
        st.rerun()
with colC:
    if st.button("🛑 종료", key="quit_button", use_container_width=True):
        st.session_state.game_over = True
        st.rerun()

# ==== 게임 종료 처리 ====
if st.session_state.game_over:
    st.success("게임을 종료합니다. 👋")
    st.stop()

# ==== STATE MACHINE (페이지형 UI) ====

# ---- INTRO (환영) ----
if st.session_state.stage == "intro":
    if st.session_state.sub == "welcome":
        intro_prompt = (
            f"환영 인사와 함께 IMF 합류 여부를 질문하는 장면을 한국어로 영화처럼 생생히 묘사하라. 플레이어는 {st.session_state.player_name}."
        )
        narrate_llm(intro_prompt, use_llm=True, fallback_text=intro_prompt)
        st.session_state.sub = "show_welcome_narrative"
        st.rerun()
    elif st.session_state.sub == "show_welcome_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 → 임무 브리핑으로", key="intro_next", use_container_width=True):
            st.session_state.stage = "briefing"
            st.session_state.sub = "show_briefing_intro"
            st.session_state.show_narrative = ""
            st.rerun()


# ---- BRIEFING ----
if st.session_state.stage == "briefing":
    if st.session_state.sub == "show_briefing_intro":
        briefing_text = (
            "어두운 회의실, 조명이 희미하게 깜빡이며 긴장감이 감도는 가운데, 에단 헌트가 당신을 바라보며 입을 엽니다.  \n\n"
            f"\"{st.session_state.player_name}, 당신이 여기까지 온 것은 우연이 아닙니다. 우리는 지금 세계의 운명을 결정짓는 중대한 기로에 서 있습니다. 초강인공지능 '엔티티'가 러시아 핵 잠수함을 장악하고, 전 세계에 재앙을 초래할 위협이 되고 있습니다.\""
        )
        narrate_llm(briefing_text, use_llm=True, fallback_text=briefing_text)
        st.session_state.sub = "ask_join"
        st.rerun()
    elif st.session_state.sub == "ask_join":
        st.markdown(st.session_state.show_narrative)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("IMF에 합류한다", key="brief_join_yes", use_container_width=True):
                adjust_trust(+10, "IMF 합류 결심")
                st.session_state.sub = "show_choose_narrative"
                st.session_state.show_narrative = ""
                st.rerun()
        with c2:
            if st.button("망설인다", key="brief_join_no", use_container_width=True):
                adjust_trust(-10, "주저")
                st.session_state.sub = "show_choose_narrative"
                narrate_llm("에단이 준비 부족을 지적하며 반드시 정보를 수집해야 한다고 설득하는 장면을 묘사하라.", use_llm=True)
                st.rerun()
    elif st.session_state.sub == "show_choose_narrative":
        st.markdown(st.session_state.show_narrative)
        st.markdown("---")
        st.markdown("**[1. 임무 브리핑]**")
        st.markdown("이제 첫 번째 임무를 선택해야 합니다. 정보를 더 수집하시겠습니까, 아니면 바로 출발하시겠습니까?")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("정보를 더 수집한다", key="brief_info", use_container_width=True):
                st.session_state.stage = "info"
                st.session_state.sub = "menu"
                st.session_state.show_narrative = ""
                st.rerun()
        with b2:
            if st.button("바로 출발한다", key="brief_go", use_container_width=True):
                adjust_trust(-10, "준비 미흡")
                narrate_llm("에단이 준비 부족을 지적하며 반드시 정보를 수집해야 한다고 설득하는 장면을 묘사하라.", use_llm=True)
                st.session_state.sub = "ask_join" # 다시 합류 유도로
                st.rerun()

# ---- INFO (정보 수집) ----
if st.session_state.stage == "info":
    if st.session_state.sub == "menu":
        st.markdown("**[2. 정보 수집]** 아래에서 조사할 '정보의 종류'를 선택하세요.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(f"엔티티에 관한 정보 {'✅' if st.session_state.info_seen['entity'] else ''}", key="menu_entity", use_container_width=True):
                st.session_state.sub = "entity"
                st.session_state.info_seen["entity"] = True
                if "엔티티에 관한 정보" not in st.session_state.investigation:
                    st.session_state.investigation.append("엔티티에 관한 정보")
                st.rerun()
        with c2:
            if st.button(f"인물들에 관한 예언 {'✅' if st.session_state.info_seen['prophecy'] else ''}", key="menu_prophecy", use_container_width=True):
                st.session_state.sub = "prophecy"
                st.session_state.info_seen["prophecy"] = True
                if "인물들에 관한 예언" not in st.session_state.investigation:
                    st.session_state.investigation.append("인물들에 관한 예언")
                st.rerun()
        with c3:
            if st.button(f"CIA에 대한 정보 {'✅' if st.session_state.info_seen['cia'] else ''}", key="menu_cia", use_container_width=True):
                st.session_state.sub = "cia"
                st.session_state.info_seen["cia"] = True
                if "CIA에 대한 정보" not in st.session_state.investigation:
                    st.session_state.investigation.append("CIA에 대한 정보")
                st.rerun()

        st.divider()
        can_stop = st.session_state.info_seen["entity"]
        if st.button("조사를 중단한다.", key="menu_stop", disabled=not can_stop, use_container_width=True):
            narrate_llm("정보 수집을 마치고, CIA에 보고할지 말지 팀 내부에서 논의하는 장면을 묘사하라.", use_llm=True)
            st.session_state.sub = "show_report_narrative"
            st.rerun()
        if not can_stop:
            st.caption("※ 엔티티 정보는 반드시 한 번 확인해야 조사를 중단할 수 있습니다.")
    elif st.session_state.sub == "entity":
        st.markdown("**'엔티티에 관한 정보'**: 초강인공지능. 스스로 학습 및 선택을 진행하며, 가짜 정보를 생성해 외부를 교란시킬 수 있고, 미래를 예언할 수 있다.")
        st.markdown("---")
        if st.button("돌아가기", key="entity_back", use_container_width=True):
            st.session_state.sub = "menu"
            st.rerun()
    elif st.session_state.sub == "prophecy":
        st.markdown("**'인물들에 관한 예언'**: 결국 에단 헌트는 엔티티의 대리인이 된다. 동료인 루터는 사망하게 될 것이며, 이 세계는 엔티티에 의해 지배될 것이다.")
        st.markdown("---")
        if st.button("돌아가기", key="prophecy_back", use_container_width=True):
            st.session_state.sub = "menu"
            st.rerun()
    elif st.session_state.sub == "cia":
        st.markdown("**'CIA에 대한 정보'**: IMF의 상관 격인 집단 CIA(미정보국) 내부에 스파이가 있으며, 이 스파이가 엔티티와 내통 중이다.")
        st.markdown("---")
        if st.button("돌아가기", key="cia_back", use_container_width=True):
            st.session_state.sub = "menu"
            st.rerun()
    elif st.session_state.sub == "show_report_narrative":
            st.markdown(st.session_state.show_narrative)
            st.markdown("**조사 내용 보고 여부**")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("CIA에 보고를 결정한다.", key="report_yes", use_container_width=True):
                    st.session_state.reported_to_cia = True
                    adjust_trust(-5, "IMF의 위기 암시")
                    narrate_llm("CIA에 보고가 접수되는 장면. 이 정보가 향후 치명적 변수로 작동할 복선을 깔아라.", use_llm=True)
                    st.session_state.stage = "story1"
                    st.session_state.sub = "show_story1_intro"
                    st.rerun()
            with b2:
                if st.button("보고 없이 임무를 진행한다.", key="report_no", use_container_width=True):
                    st.session_state.reported_to_cia = False
                    adjust_trust(+10, "독자적 판단")
                    narrate_llm("보고 없이 움직이기로 결정. 향후 난관을 예고하는 분위기로 전환하라.", use_llm=True)
                    st.session_state.stage = "story1"
                    st.session_state.sub = "show_story1_intro"
                    st.rerun()

# ---- STORY1: 열쇠 A ----
if st.session_state.stage == "story1":
    if st.session_state.sub == "show_story1_intro":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_s1_mission_accept", use_container_width=True):
            st.session_state.sub = "accept_mission"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "accept_mission":
        st.markdown("**[스토리1: 열쇠 A]** 임무를 수락하시겠습니까?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("예", key="s1_accept_yes", use_container_width=True):
                adjust_trust(+10, "임무 수락")
                narrate_llm("알라나 변장을 준비하는 장면. 그런데 벤지의 가면 기계가 고장나 에단의 가면이 망가진 비상상황을 생생히 묘사하라.", use_llm=True)
                st.session_state.sub = "show_emergency1_narrative"
                st.rerun()
        with c2:
            if st.button("아니오", key="s1_accept_no", use_container_width=True):
                adjust_trust(-10, "임무 거부")
                narrate_llm("팀이 설득해 임무를 받아들이도록 유도하는 장면. 결국 임무로 이행.", use_llm=True)
                st.session_state.sub = "show_emergency1_narrative"
                st.rerun()
    elif st.session_state.sub == "show_emergency1_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_emergency1_line_intro", use_container_width=True):
            st.session_state.sub = "emergency1_line_intro"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "emergency1_line_intro":
        st.markdown("**🚨 첫 번째 비상상황**: 에단의 가면이 망가졌다. 어떻게 대처할까?")
        line = st.text_input("벤지의 호출에 대답하세요 (대사 한 줄):", key="s1_line")
        if st.button("대사 전송", key="s1_line_send", use_container_width=True):
            st.session_state.history.append(("user_line", line or "(무언)"))
            narrate_llm("에단이 알라나처럼 속이라고 지시하며 작전 개시. 이제 알라나를 재워야 한다는 긴박한 상황으로 연결하라.", use_llm=True)
            st.session_state.sub = "show_choice1_narrative"
            st.rerun()
    elif st.session_state.sub == "show_choice1_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice1_sleep", use_container_width=True):
            st.session_state.sub = "choice1_sleep"
            st.session_state.show_narrative = ""
            set_checkpoint("story1", "choice1_sleep") # 체크포인트
            st.rerun()
    elif st.session_state.sub == "choice1_sleep":
        st.markdown("**선택 상황1**: 알라나를 어떻게 재울까?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("약물로 재운다", key="s1_sleep_drug", use_container_width=True):
                adjust_trust(0, "무난한 선택")
                narrate_llm("약물로 알라나를 재우고 거래 장소로 향한다. 그녀는 거래 완료까지 깨어나지 않는다.", use_llm=True)
                st.session_state.sub = "show_choice2_narrative"
                st.rerun()
        with c2:
            if st.button("몸싸움으로 재운다", key="s1_sleep_fight", use_container_width=True):
                adjust_trust(-10, "무리한 방법")
                narrate_llm("몸싸움 끝에 알라나를 제압했지만, 거래 중 그녀가 깨어나 CIA 난입으로 체포, 미션 실패(첫 번째 체크포인트).", use_llm=True)
                st.session_state.sub = "s1_fail_narrative"
                st.session_state.allow_continue = True
                st.rerun()
    elif st.session_state.sub == "show_choice2_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice2_deal", use_container_width=True):
            st.session_state.sub = "choice2_deal"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "choice2_deal":
        st.markdown("**선택 상황2**: 키트리지가 천만 달러 송금을 제안한다. 받는가?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("받는다 (계좌 입력)", key="s1_deal_accept", use_container_width=True):
                adjust_trust(-10, "탐욕 노출")
                narrate_llm("계좌 추적으로 정체가 발각되어 체포, 미션 실패(두 번째 체크포인트).", use_llm=True)
                st.session_state.sub = "s1_fail_narrative"
                st.session_state.allow_continue = True
                set_checkpoint("story1", "choice2_deal") # 체크포인트
                st.rerun()
        with c2:
            if st.button("거래를 파기한다", key="s1_deal_refuse", use_container_width=True):
                adjust_trust(+10, "임무 우선")
                narrate_llm("거래를 중단하고 열쇠 A 회수에 집중한다. 직후, 하늘에서 에단이 낙하산으로 등장! 그러나 키는 키트리지에게 있다.", use_llm=True)
                st.session_state.sub = "show_emergency2_narrative"
                st.rerun()
    elif st.session_state.sub == "show_emergency2_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_emergency2_theft", use_container_width=True):
            st.session_state.sub = "emergency2_theft"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "emergency2_theft":
        st.markdown("**🚨 두 번째 비상상황**: 키트리지에게 있는 열쇠 A를 어떻게 할까?")
        ans = st.text_input("당신의 결정(키워드 포함 가능):", key="s1_em2")
        if st.button("결정 전송", key="s1_em2_send", use_container_width=True):
            st.session_state.attempt_em2 += 1
            txt = (ans or "").strip()
            if any(k in txt for k in ["도둑질", "훔", "훔친다", "훔쳐"]):
                st.session_state.history.append(("user_em2", ans))
                adjust_trust(+10, "과감한 기지")
                narrate_llm("절묘한 타이밍에 키를 슬쩍하는 장면을 영화적으로 묘사하고, 이어지는 열차 폭파 위기의 순간으로 전환.", use_llm=True)
                if "열쇠 A 획득" not in st.session_state.investigation:
                    st.session_state.investigation.append("열쇠 A 획득")
                st.session_state.sub = "show_emergency3_narrative"
                st.session_state.attempt_em2 = 0
                st.rerun()
            else:
                st.session_state.history.append(("user_em2_wrong", ans))
                adjust_trust(-10, "오답")
                if st.session_state.attempt_em2 >= 2:
                    st.info("힌트: 당신은 '도둑질'을 잘하기로 유명해서 국제 수배된 상태였다!")
                st.rerun()
        if st.session_state.attempt_em2 > 0:
            st.caption(f"시도 횟수: {st.session_state.attempt_em2}/무제한")
    elif st.session_state.sub == "show_emergency3_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_emergency3_train", use_container_width=True):
            st.session_state.sub = "emergency3_train"
            st.session_state.show_narrative = ""
            set_checkpoint("story1", "emergency3_train") # 체크포인트
            st.rerun()
    elif st.session_state.sub == "emergency3_train":
        st.markdown("**🚨 세 번째 비상상황**: 다리가 끊긴 열차! 어떻게 탈출할까?")
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("에단을 신뢰한다", key="s1_train_trust_ethan", use_container_width=True):
                adjust_trust(+10, "에단 신뢰")
                narrate_llm("에단과 합을 맞춰 극적으로 탈출. **첫 번째 미션 성공**을 선언하라.", use_llm=True)
                st.session_state.stage = "story2"
                st.session_state.sub = "show_s2_intro_narrative"
                st.rerun()
        with c2:
            if st.button("혼자 낙하산으로 탈출", key="s1_train_parachute", use_container_width=True):
                adjust_trust(-10, "팀워크 붕괴")
                narrate_llm("혼자 탈출을 시도하다 상황 악화로 미션 실패(세 번째 체크포인트).", use_llm=True)
                st.session_state.sub = "s1_fail_narrative"
                st.session_state.allow_continue = True
                st.rerun()
        with c3:
            if st.button("에단에게 키를 넘기고 도주", key="s1_train_givekey", use_container_width=True):
                adjust_trust(-10, "미션 실패")
                narrate_llm("에단에게 키를 넘기고 도주. 상황 악화로 미션 실패(세 번째 체크포인트).", use_llm=True)
                st.session_state.sub = "s1_fail_narrative"
                st.session_state.allow_continue = True
                st.rerun()
    elif st.session_state.sub == "s1_fail_narrative":
        st.markdown(st.session_state.show_narrative)
        st.error("미션 실패. 체크포인트에서 다시 시작하시겠습니까?")
        st.session_state.allow_continue = True

    st.stop()


# ---- STORY2: 열쇠 B ----
if st.session_state.stage == "story2":
    if st.session_state.sub == "show_s2_intro_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_emergency4_luther_narrative", use_container_width=True):
            st.session_state.sub = "emergency4_luther_narrative"
            st.session_state.show_narrative = ""
            narrate_llm("가브리엘의 은신처에 도착. 루터가 폭탄과 함께 동굴에 갇힌 긴박한 상황을 묘사하라. 루터가 자신을 희생하려 한다.", use_llm=True)
            st.rerun()
    elif st.session_state.sub == "emergency4_luther_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_emergency4_luther_choice", use_container_width=True):
            st.session_state.sub = "emergency4_luther_choice"
            st.session_state.show_narrative = ""
            set_checkpoint("story2", "emergency4_luther_choice")
            st.rerun()
    elif st.session_state.sub == "emergency4_luther_choice":
        st.markdown("**🚨 네 번째 비상상황**: 루터가 폭탄과 함께 동굴에 갇혔다.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("루터를 두고 3명만 탈출한다", key="s2_luther_leave", use_container_width=True):
                adjust_trust(-10, "희생의 결정")
                st.session_state.sub = "show_s2_choice3_narrative"
                narrate_llm("고통스러운 결단 끝에 루터를 잃는다. 그러나 작전은 계속된다.", use_llm=True)
                st.rerun()
        with c2:
            if st.button("루터 곁에 남는다(모두 사망, 실패)", key="s2_luther_stay", use_container_width=True):
                adjust_trust(-10, "무모한 선택")
                st.session_state.stage = "ending"
                st.session_state.sub = "fail"
                st.session_state.allow_continue = True
                narrate_llm("폭발로 전원이 사망, 미션 실패(네 번째 체크포인트).", use_llm=True)
                st.rerun()
    elif st.session_state.sub == "show_s2_choice3_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice3_benji_vs_ethan", use_container_width=True):
            st.session_state.sub = "choice3_benji_vs_ethan"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "choice3_benji_vs_ethan":
        st.markdown("**선택 상황3**: 가짜 신호 속 길찾기 — 누구의 판단을 따를까?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("벤지의 신호 추적", key="s2_choice3_benji", use_container_width=True):
                adjust_trust(+10, "팀 신뢰도 증가(경험치)")
                st.session_state.sub = "show_s2_choice4_narrative"
                narrate_llm("신호가 가짜였음을 확인, 한 바퀴 빙 돈 뒤 에단의 직감대로 길을 찾는다. 벤지 신뢰는 살짝 흔들린다.", use_llm=True)
                st.rerun()
        with c2:
            if st.button("에단의 직감", key="s2_choice3_ethan", use_container_width=True):
                adjust_trust(+12, "에단 신뢰 상승")
                st.session_state.sub = "show_s2_choice4_narrative"
                narrate_llm("숨겨진 통로를 찾아 곧장 중심부로 접근한다.", use_llm=True)
                st.rerun()
    elif st.session_state.sub == "show_s2_choice4_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice4_gabriel_taunt", use_container_width=True):
            st.session_state.sub = "choice4_gabriel_taunt"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "choice4_gabriel_taunt":
        st.markdown("**선택 상황4**: 가브리엘이 과거의 약점을 들춰 혼란을 조장한다.")
        if st.button("정면돌파(대화 시간 끌지 않음)", key="s2_choice4_force", use_container_width=True):
            adjust_trust(+10, "동요 억제")
            st.session_state.sub = "show_s2_choice5_narrative"
            narrate_llm("과거의 상처를 딛고 전투에 돌입한다.", use_llm=True)
            st.rerun()
        if st.button("대화로 시간 번다(해킹 시도)", key="s2_choice4_talk", use_container_width=True):
            adjust_trust(-10, "허위 정보에 막힘")
            st.session_state.sub = "show_s2_choice5_narrative"
            narrate_llm("벤지의 해킹이 허위 정보의 벽에 막히며 난관을 겪는다. 결국 전투로 전환.", use_llm=True)
            st.rerun()
    elif st.session_state.sub == "show_s2_choice5_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice5_get_keyB", use_container_width=True):
            st.session_state.sub = "choice5_get_keyB"
            st.session_state.show_narrative = ""
            set_checkpoint("story2", "choice5_get_keyB")
            st.rerun()
    elif st.session_state.sub == "choice5_get_keyB":
        st.markdown("**선택 상황5**: 열쇠 B를 어떻게 확보할까?")
        if st.session_state.info_seen["prophecy"]:
            st.caption("예언이 떠오른다: 힘으로 빼앗는 미래가 예측되어 있었다…")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("힘으로 빼앗는다", key="s2_choice5_force", use_container_width=True):
                adjust_trust(+5, "정면 승부")
                st.session_state.stage = "story3"
                st.session_state.sub = "show_s3_intro_narrative"
                narrate_llm("격전 끝에 가브리엘은 도주. 예측된 패턴대로 움직였다는 찝찝함이 남는다.", use_llm=True)
                if "열쇠 B 획득" not in st.session_state.investigation:
                    st.session_state.investigation.append("열쇠 B 획득")
                st.rerun()
        with c2:
            if st.button("가브리엘과 거래한다", key="s2_choice5_trade", use_container_width=True):
                adjust_trust(+12, "위험한 거래")
                st.session_state.stage = "story3"
                st.session_state.sub = "show_s3_intro_narrative"
                narrate_llm("일시적으로 열쇠를 손에 넣지만, 엔티티의 새로운 위협이 따라붙는다.", use_llm=True)
                if "열쇠 B 획득" not in st.session_state.investigation:
                    st.session_state.investigation.append("열쇠 B 획득")
                st.rerun()
        with c3:
            if st.button("다른 팀원에게 맡긴다(신뢰 65↑ 필요)", key="s2_choice5_delegate", use_container_width=True):
                if st.session_state.trust >= 65:
                    adjust_trust(+10, "책임 분담 성공")
                    st.session_state.stage = "story3"
                    st.session_state.sub = "show_s3_intro_narrative"
                    narrate_llm("협업으로 깔끔하게 열쇠 B를 확보한다.", use_llm=True)
                    if "열쇠 B 획득" not in st.session_state.investigation:
                        st.session_state.investigation.append("열쇠 B 획득")
                    st.rerun()
                else:
                    adjust_trust(-10, "불충분한 신뢰")
                    st.session_state.stage = "ending"
                    st.session_state.sub = "fail"
                    st.session_state.allow_continue = True
                    narrate_llm("신뢰가 부족해 실수가 발생, 가브리엘에게 역으로 빼앗겨 미션 실패.", use_llm=True)
                    st.rerun()
    elif st.session_state.sub == "s2_fail_narrative":
        st.markdown(st.session_state.show_narrative)
        st.error("미션 실패. 체크포인트에서 다시 시작하시겠습니까?")
        st.session_state.allow_continue = True


# ---- STORY3: 엔티티 붕괴 ----
if st.session_state.stage == "story3":
    if st.session_state.sub == "show_s3_intro_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice6_coords_narrative", use_container_width=True):
            st.session_state.sub = "choice6_coords_narrative"
            st.session_state.show_narrative = ""
            narrate_llm("엔티티 코어를 파괴하기 위한 마지막 임무. 에단이 잠수함에서 보내온 암호화된 좌표를 해독해야 한다.", use_llm=True)
            st.rerun()
    elif st.session_state.sub == "choice6_coords_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice6_coords", use_container_width=True):
            st.session_state.sub = "choice6_coords"
            st.session_state.show_narrative = ""
            set_checkpoint("story3", "choice6_coords")
            st.rerun()
    elif st.session_state.sub == "choice6_coords":
        st.markdown("**선택 상황6**: 좌표 해석 — [남위 82.5°, 서경 65.3°] (우리는 북극해)")
        ans = st.text_input("에단이 일부러 이렇게 보낸 이유는?", key="s3_s6")
        if st.button("해석 제출", key="s3_s6_submit", use_container_width=True):
            st.session_state.attempt_s6 += 1
            txt = (ans or "").strip()
            if any(k in txt for k in ["반대로", "정반대", "거꾸로"]):
                st.session_state.history.append(("user_s6", ans))
                adjust_trust(+10, "의도 간파")
                narrate_llm("남극/북극을 뒤집어 해석해 정확한 좌표를 파악, 에단과의 교신에 성공한다.", use_llm=True)
                st.session_state.sub = "show_s7_narrative"
                st.session_state.attempt_s6 = 0
                st.rerun()
            else:
                st.session_state.history.append(("user_s6_wrong", ans))
                adjust_trust(-10, "오해")
                if st.session_state.attempt_s6 >= 2:
                    st.info("힌트: 에단이 보낸 건 '남극해' 좌표. 당신이 있는 곳은 '북극해'.")
                st.rerun()
        if st.session_state.attempt_s6 > 0:
            st.caption(f"시도 횟수: {st.session_state.attempt_s6}/무제한")
    elif st.session_state.sub == "show_s7_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice7_timing_intro", use_container_width=True):
            st.session_state.sub = "choice7_timing_intro"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "choice7_timing_intro":
        st.markdown("**선택 상황7**: 네트워크 연결 '찰나'에 포이즌필을 뽑아야 한다.")
        st.write("미션 설명을 숙지했으면 준비를 눌러 타이머를 시작하세요. 준비 후 **10초 이내**에 '초록색'을 정확히 입력하면 성공!")
        if st.button(f"{st.session_state.player_name}. 준비되셨습니까?", key="s3_ready", use_container_width=True):
            st.session_state.s7_ready_time = time.time()
            st.session_state.sub = "choice7_timing"
            st.rerun()
    elif st.session_state.sub == "choice7_timing":
        ip = st.text_input("지금! 입력하세요 👉", key="s3_go_input")
        if st.button("전송", key="s3_go_send", use_container_width=True):
            elapsed = time.time() - st.session_state.s7_ready_time
            if ip.strip() == "초록색" and elapsed <= 10.0:
                adjust_trust(+10, f"완벽한 타이밍({elapsed:.1f}s)")
                narrate_llm("포이즌필이 적시에 뽑히며 엔티티의 통로가 봉쇄된다. 마지막 변수에 대비하라.", use_llm=True)
                st.session_state.sub = "show_s8_narrative"
            else:
                adjust_trust(-10, f"타이밍 실패({elapsed:.1f}s)")
                narrate_llm("타이밍을 놓쳐 연결이 길어졌고, 엔티티가 반격한다. 미션 실패(네 번째 체크포인트).", use_llm=True)
                st.session_state.sub = "s3_fail_narrative"
                st.session_state.allow_continue = True
            st.session_state.s7_ready_time = None
            st.rerun()
    elif st.session_state.sub == "s3_fail_narrative":
        st.markdown(st.session_state.show_narrative)
        st.error("미션 실패. 체크포인트에서 다시 시작하시겠습니까?")
        st.session_state.allow_continue = True
    elif st.session_state.sub == "show_s8_narrative":
        st.markdown(st.session_state.show_narrative)
        if st.button("다음 →", key="to_choice8_cia_end", use_container_width=True):
            st.session_state.sub = "choice8_cia_end"
            st.session_state.show_narrative = ""
            st.rerun()
    elif st.session_state.sub == "choice8_cia_end":
        st.markdown("**선택 상황8**: CIA의 등장과 결말")
        if st.session_state.reported_to_cia is True:
            st.caption("※ 당신은 2단계에서 CIA에 보고했습니다.")
            if st.session_state.trust >= 70:
                narrate_llm("키트리지가 전원을 체포. 포이즌필을 압수당해 **게임 실패**로 귀결된다.", use_llm=True)
                st.session_state.stage = "ending"
                st.session_state.sub = "fail"
                st.rerun()
            else:
                st.write("팀 신뢰도 70 미만 — 결단을 내려야 한다.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("배신하고 엔티티의 힘을 노린다", key="s3_choice8_betray", use_container_width=True):
                        adjust_trust(-10, "배신")
                        narrate_llm("도주를 시도했지만 헬기에 포위되어 체포된다. **미션 실패**.", use_llm=True)
                        st.session_state.stage = "ending"
                        st.session_state.sub = "fail"
                        st.rerun()
                with c2:
                    if st.button("팀과 함께 간다", key="s3_choice8_withteam", use_container_width=True):
                        adjust_trust(+5, "팀 동행")
                        narrate_llm("IMF는 체포되고 엔티티의 힘은 정부의 손으로. **미션 실패**.", use_llm=True)
                        st.session_state.stage = "ending"
                        st.session_state.sub = "fail"
                        st.rerun()
        else:
            st.caption("※ 당신은 2단계에서 CIA에 보고하지 않았습니다.")
            if st.session_state.trust >= 70:
                adjust_trust(+10, "에단의 기지")
                narrate_llm("에단이 논리로 반박에 성공, 포이즌필을 지키며 **미션 완수**.", use_llm=True)
                st.session_state.stage = "ending"
                st.session_state.sub = "success"
                st.rerun()
            else:
                st.write("팀 신뢰도 70 미만 — 결정 필요.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("배신하고 힘을 쥔다", key="s3_choice8_betray2", use_container_width=True):
                        adjust_trust(-10, "배신")
                        narrate_llm("도주를 시도했지만 헬기에 포위되어 체포된다. **미션 실패**.", use_llm=True)
                        st.session_state.stage = "ending"
                        st.session_state.sub = "fail"
                        st.rerun()
                with c2:
                    if st.button("팀과 함께 간다(에단 반박)", key="s3_choice8_withteam2", use_container_width=True):
                        adjust_trust(+10, "팀워크 회복")
                        narrate_llm("에단의 기지로 반박에 성공, 포이즌필과 함께 **미션 완수**.", use_llm=True)
                        st.session_state.stage = "ending"
                        st.session_state.sub = "success"
                        st.rerun()



# ---- ENDING & RESTART ----
if st.session_state.sub in ["ending_success", "ending_fail"]:
    if st.session_state.sub == "ending_success":
        st.success('**IMF, MISSION COMPLETE.**')
        narrate_llm("완수 엔딩의 여운과 팀에 남은 상처, 그러나 이어질 평화를 영화적 문체로 간결히 마무리하라.", use_llm=True)
        st.session_state.sub = "final_narrative"
        st.rerun()
    elif st.session_state.sub == "ending_fail":
        st.error("미션 실패. 체크포인트에서 다시 시작하시겠습니까?")
        st.session_state.allow_continue = True

if st.session_state.sub == "final_narrative":
    st.markdown(st.session_state.show_narrative)
    st.session_state.game_over = True
    st.stop()
    
if st.session_state.allow_continue:
    c1, c2 = st.columns(2)
    with c1:
        if st.button("체크포인트에서 재개", key="retry_checkpoint", use_container_width=True):
            restore_checkpoint()
            narrate_llm("가장 가까운 체크포인트로 복귀한다. 신뢰도는 50으로 리셋되었다.", use_llm=False)
            st.session_state.sub = st.session_state.checkpoint[1]
            st.rerun()
    with c2:
        if st.button("그만하기", key="retry_quit", use_container_width=True):
            st.session_state.game_over = True
            st.rerun()