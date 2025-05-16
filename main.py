import requests
import logging
import re
import json
from flask import Flask, request, jsonify

DOORAY_ADMIN_API_URL = "https://admin-api.dooray.com/admin/v1/members"
DOORAY_ADMIN_API_TOKEN = "r4p8dpn3tbv7:SVKeev3aTaerG-q5jyJUgg"  # 토큰

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_members():
    logger.info(" Dooray 전체 멤버 조회 시작")

    base_url = "https://admin-api.dooray.com/admin/v1/members?size=100"
    headers = {
        "Authorization": f"dooray-api {DOORAY_ADMIN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    all_members = []
    page = 0

    while True:
        paged_url = f"{base_url}&page={page}"
        try:
            response = requests.get(paged_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(" 멤버 조회 실패 (page %d): %s", page, str(e))
            break

        result = response.json().get("result", [])
        logger.info("📦 받은 멤버 수 (page %d): %d", page, len(result))

        if not result:
            break

        all_members.extend(result)
        '''
        for i, member in enumerate(result, start=page * 100 + 1):
            name = member.get("name", "이름 없음")
            nickname = member.get("nickname", "닉네임 없음")
            user_code = member.get("userCode", "코드 없음")
            email = member.get("emailAddress", "이메일 없음")
            position = member.get("position", "직책 없음")
            department = member.get("department", "부서 없음")
            joined_at = member.get("joinedAt", "입사일 없음")
            role = member.get("tenantMemberRole", "역할 없음")

            logger.info(f"[{i}] 이름: {name}, 닉네임: {nickname}, 코드: {user_code}, 이메일: {email}, "
                        f"직책: {position}, 부서: {department}, 입사일: {joined_at}, 역할: {role}")
        '''
        if len(result) < 100:
            break

        page += 1

    logger.info(" 전체 멤버 수: %d", len(all_members))
    return all_members


def get_member_id_by_name(name):
    logger.info("🔍 이름으로 멤버 조회 시작: '%s'", name)

    members = get_all_members()
    logger.info(" 가져온 멤버 수: %d", len(members))

    for i, m in enumerate(members):
        m_name = m.get("name")
        m_id = m.get("id")

        logger.debug("🔎 [%d] 이름: '%s', ID: %s", i, m_name, m_id)

        if m_name == name:
            logger.info(" 일치하는 멤버 발견: '%s' (id=%s)", m_name, m_id)
            return m_id

    logger.warning(" 이름과 일치하는 멤버를 찾지 못함: '%s'", name)
    return None


def extract_member_ids_and_roles(mention_text):
    """
    mention_text에서 (dooray://.../members/{id} "role") 형태로 되어 있는 멘션들을 파싱하여
    member_id와 role 리스트로 반환
    """
    pattern = r'\(dooray://\d+/members/(\d+)\s+"(member|admin)"\)'
    matches = re.findall(pattern, mention_text)
    return matches  # List of (member_id, role)


def get_member_name_by_id(member_id: str) -> str:
    """Dooray Admin API로 구성원 이름을 조회"""
    api_url = f"https://admin-api.dooray.com/admin/v1/members/{member_id}"
    headers = {
        "Authorization": f"dooray-api {DOORAY_ADMIN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    logger.info("🔍 get_member_name_by_id(): 시작 - member_id=%s", member_id)
    logger.info("요청 URL: %s", api_url)
    logger.info("요청 헤더: %s", headers)

    try:
        response = requests.get(api_url, headers=headers)
        logger.info("응답 상태 코드: %s", response.status_code)
        logger.debug("응답 바디 (raw): %s", response.text)

        if response.status_code == 200:
            data = response.json()
            logger.debug(" 파싱된 JSON: %s", data)

            result = data.get("result")
            if result:
                name = result.get("name")
                if name:
                    logger.info(" 이름 추출 성공: %s", name)
                    return name
                else:
                    logger.warning(" 이름 필드가 존재하지 않음. result=%s", result)
            else:
                logger.warning(" 'result' 키가 응답에 없음. data=%s", data)
        else:
            logger.error(" Dooray API 요청 실패. status_code=%s, 응답=%s", response.status_code, response.text)

    except Exception as e:
        logger.exception(" 예외 발생: %s", e)

    return "알 수 없음"


@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    """Dooray에서 받은 명령을 처리하는 엔드포인트"""
    data = request.json
    logger.info("📥 Received Data: %s", data)

    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    command = data.get("command", "").strip()
    cmd_token = data.get("cmdToken", "")
    trigger_id = data.get("triggerId", "")
    dooray_dialog_url = f"https://{tenant_domain}/messenger/api/channels/{channel_id}/dialogs"
    responseUrl = data.get("responseUrl", "")

    # 각 명령어에 대응하는 callbackId 설정
    callback_ids = {
        "/클라일감": "client_task",
        "/기획일감": "planning_task",
        "/품질일감": "qa_task",
        "/캐릭터일감": "character_task",
        "/배경일감": "background_task",
        "/컨셉일감": "concept_task",
        "/애니일감": "animation_task",
        "/이펙트일감": "effect_task",
        "/아트일감": "art_task",
        "/서버일감": "server_task",
        "/TA일감": "ta_task",
        "/테스트일감": "test_task",
        "/UI일감": "ui_task",
    }

    #  Heartbeat 커맨드 추가
    if command == "/heartbeat":
        logger.info("💓 Heartbeat 요청 수신됨")
        return jsonify({"status": "alive"}), 200

    # logger.info("📌 Received command: %s", command)
    # logger.info("📌 Mapped callbackId: %s", callback_ids[command])

    if command in callback_ids:
        dialog_data = {
            "token": cmd_token,
            "triggerId": trigger_id,
            "callbackId": callback_ids[command],  # 변경된 callbackId 사용
            "dialog": {
                "callbackId": callback_ids[command],  # 변경된 callbackId 사용
                "title": "새 업무 등록",
                "submitLabel": "등록",
                "elements": [
                    {"type": "text", "label": "제목", "name": "title", "optional": False},
                    {"type": "textarea", "label": "내용", "name": "content", "optional": False},
                    {"type": "text", "label": "기간", "name": "duration", "optional": True},
                    {"type": "text", "label": "기획서 (URL)", "name": "document", "optional": True},
                    {"type": "text", "label": "담당자 (실명)", "name": "assignee", "optional": False}
                ]
            }
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}
        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)

        # logger.info("⚠️⚠️⚠️- dialog_data: %s", dialog_data) #
        # 최종적으로 설정된 callbackId 값을 다시 확인하는 로그
        # logger.info("📌 Final dialog_data.callbackId: %s", dialog_data["callbackId"])
        # logger.info("📌 Final dialog_data.dialog.callbackId: %s", dialog_data["dialog"]["callbackId"])

        if response.status_code == 200:
            logger.info(f"✅ Dialog 생성 요청 성공 ({command})")
            return jsonify({"responseType": "ephemeral", "text": "업무 요청이 성공적으로 전송되었습니다!"}), 200
        else:
            logger.error(f"❌ Dialog 생성 요청 실패 ({command}): {response.text}")
            return jsonify({"responseType": "ephemeral", "text": "업무 요청이 전송이 실패했습니다."}), 500

    elif command == "/모임요청":
        logger.info("/모임요청 진입")

        input_text = data.get("text", "").strip()
        logger.info("🔹 원본 텍스트: %s", input_text)

        # 담당자 텍스트 가공
        member_roles = extract_member_ids_and_roles(input_text)

        assignee_text = ""
        if member_roles:
            mentions = []
            for member_id, role in member_roles:
                name = get_member_name_by_id(member_id)
                if name:
                    logger.info(" 이름 조회 결과: member_id=%s, name=%s", member_id, name)
                    mentions.append(f"@{name}")
                else:
                    logger.warning("⚠️ 이름 조회 실패: member_id=%s", member_id)
                    mentions.append(f"[unknown:{member_id}]")
            assignee_text = " ".join(mentions)
        else:
            logger.warning("⚠️ 멘션 포맷 아님 또는 파싱 실패, 그대로 사용")
            assignee_text = input_text

        dialog_data = {
            "token": cmd_token,
            "triggerId": trigger_id,
            "callbackId": "meeting_review_dialog",
            "dialog": {
                "callbackId": "meeting_review_dialog",
                "title": "모임요청",
                "submitLabel": "보내기",
                "elements": [
                    {
                        "type": "text",
                        "label": "담당자",
                        "name": "assignee",
                        "optional": False,
                        "value": assignee_text
                    },
                    {"type": "text", "label": "제목", "name": "title", "optional": False},
                    {"type": "text", "label": "기획서 링크", "name": "document", "optional": True},
                    {"type": "textarea", "label": "내용", "name": "content", "optional": True}
                ]
            }
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}
        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)
        if response.status_code == 200:
            logger.info("모임요청Dialog 생성 성공")
            return jsonify({
                "responseType": "ephemeral",
                "text": "모임요청 요청을 위한 창이 열렸습니다!"
            }), 200

        else:
            logger.error(" 모임요청 Dialog 생성 실패: %s", response.text)
            return jsonify({
                "responseType": "ephemeral",
                "text": "모임요청에 실패했습니다."
            }), 500

    elif command == "/jira":
        message_data = {
            "text": "📢 Jira 작업을 처리 중입니다...!",
            "channelId": channel_id,
            "triggerId": trigger_id,
            "replaceOriginal": "false",
            "responseType": "inChannel",
            "tenantId": "3570973279848255571"
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}

        logger.info("🔹 Sending Message Data: %s", message_data)

        # Dooray 메시지 전송
        response = requests.post(responseUrl, json=message_data, headers=headers)

        # Jira Webhook URL
        jira_webhook_url = "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q"

        jira_response = requests.post(jira_webhook_url, json=message_data, headers={"Content-Type": "application/json"})

        if jira_response.status_code == 200:
            logger.info("✅ Jira 메시지 전송 성공")
        else:
            logger.error("❌ Jira 메시지 전송 실패: %s", jira_response.text)
            return jsonify({"responseType": "inChannel", "replaceOriginal": "false",
                            "text": "❌ Jira 메시지 전송에 실패했습니다."}), 500

        if response.status_code == 200:
            logger.info("✅ Dooray 메시지 전송 성공")
            return jsonify({"responseType": "inChannel", "replaceOriginal": "false",
                            "text": "(dooray://3570973280734982045/members/3790034441950345057 \"member\")" "✅ Jira 메시지가 전송되었습니다."}), 200
        else:
            logger.error("❌ Dooray 메시지 전송 실패: %s", response.text)
            return jsonify({"responseType": "inChannel", "replaceOriginal": "false",
                            "text": "❌ Jira 메시지 전송에 실패했습니다."}), 500

    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400


# request URL = Webserveraddurl + /interactive-webhook
@app.route("/interactive-webhook", methods=["POST"])
def interactive_webhook():
    """Dooray Interactive Message 요청을 처리하는 웹훅"""

    logger.info("⚠️interactive_webhook(): 1 ⚠️")
    data = request.json
    logger.info("📥 Received Interactive Action: %s", data)

    # 필수 데이터 추출
    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    callback_id = data.get("callbackId")
    trigger_id = data.get("triggerId", "")
    submission = data.get("submission", {})
    cmd_token = data.get("cmdToken", "")
    responseUrl = data.get("responseUrl", "")
    commandRequestUrl = data.get("commandRequestUrl", "")

    logger.info("🔹 Final callback_id: %s", callback_id)

    # 채널 ID 확인 및 보정
    if not channel_id:
        channel = data.get("channel")
        if channel:
            channel_id = channel.get("id")
            logger.info("📌 Found channel_id in 'channel' object: %s", channel_id)
        else:
            logger.warning("⚠️ channel_id is missing in both 'channelId' and 'channel' object!")

    logger.info("🔹 Final channel_id: %s", channel_id)

    # 테넌트 도메인 확인 및 보정
    if not tenant_domain:
        tenant = data.get("tenant")
        if tenant:
            tenant_domain = tenant.get("domain")
            logger.info("📌 Found tenant_domain in 'tenant' object: %s", tenant_domain)
        else:
            logger.warning("⚠️ tenant_domain is missing in both 'tenantDomain' and 'tenant' object!")

    logger.info("🔹 Parsed Values:")
    logger.info("   - tenant_domain: %s", tenant_domain)
    logger.info("   - channel_id: %s", channel_id)
    logger.info("   - commandRequestUrl: %s", commandRequestUrl)
    logger.info("   - cmd_token: %s", cmd_token)
    logger.info("   - trigger_id: %s", trigger_id)
    logger.info("   - responseUrl: %s", responseUrl)

    # callback_id와 Dooray Webhook URL 매핑
    jira_webhook_urls = {
        "client_task": "https://projectg.dooray.com/services/3570973280734982045/4038470401618441955/cpWtEVnySIi3mgsxkQT6pA",
        "planning_task": "https://projectg.dooray.com/services/3570973280734982045/4038470695754931917/jX5SWNi7Q5iXgEqMgNT9cw",
        "qa_task": "https://projectg.dooray.com/services/3570973280734982045/4038470969246771241/NHigIPVnSPuHAJpZoR9leg",
        "character_task": "https://projectg.dooray.com/services/3570973280734982045/4038471209127296285/w_ASw7jCSVKOSHdtoGr5ew",
        "background_task": "https://projectg.dooray.com/services/3570973280734982045/4038471696860408308/ITjgr3H5SRipPTObiGKzVA",
        "concept_task": "https://projectg.dooray.com/services/3570973280734982045/4038471868662054018/s65TjLKoQh6_0ZlpMg67NQ",
        "animation_task": "https://projectg.dooray.com/services/3570973280734982045/4038472061012612260/XfHUIwd0Tl6WNYxfJ2ObMw",
        "effect_task": "https://projectg.dooray.com/services/3570973280734982045/4038472364848021171/qMxeiFzTQtKKVcZlEa-Zsg",
        "art_task": "https://projectg.dooray.com/services/3570973280734982045/4038472628237942380/7_dU3COwRUaIOPF02WokmA",
        "server_task": "https://projectg.dooray.com/services/3570973280734982045/4038473828248998749/ZfjTPl4yTLC6Z-qf7dqfYg",
        "ta_task": "https://projectg.dooray.com/services/3570973280734982045/4038474691102299050/GtqG3T4ZQPqmE12IOhypPQ",
        "test_task": "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q",
        "ui_task": "https://projectg.dooray.com/services/3570973280734982045/4040776735936393535/RWVwpEfTSVaDscwM0mIa2A",
    }

    # callbackId가 존재할 경우 해당 URL 할당
    if callback_id in jira_webhook_urls:
        jira_webhook_url = jira_webhook_urls[callback_id]
    else:
        logger.warning("⚠️ Unrecognized callback_id: %s", callback_id)
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400

    logger.info("⚠️⚠️⚠️- jira_webhook_url: %s", jira_webhook_url)

    # 업무 등록 처리
    if callback_id in jira_webhook_urls:
        if not submission:
            logger.info("⚠️interactive_webhook(): 2 ⚠️")
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 입력된 데이터가 없습니다."}), 400
        logger.info("⚠️inside work_task ⚠️")

        title = submission.get("title", "제목 없음")
        content = submission.get("content", "내용 없음")
        duration = submission.get("duration", "미정")
        document = submission.get("document", "없음")
        assignee = submission.get("assignee", "미정")  # 담당자 추가

        # callback_id에 따른 제목 접두어 설정
        title_prefix = {
            "server_task": "서버-",
            "ta_task": "TA-",
            "client_task": "클라-",
            "planning_task": "기획-",
            "qa_task": "품질-",
            "character_task": "캐릭터-",
            "background_task": "배경-",
            "concept_task": "컨셉-",
            "animation_task": "애니-",
            "effect_task": "VFX-",
            "art_task": "UI-",
            "test_task": "테스트-",
            "ui_task": "UI-",
        }.get(callback_id, "")

        response_data = {
            "text": f"[@홍석기C/SGE PM팀](dooray://3570973279848255571/members/3571008351482084031 \"admin\") "
                    f"[@노승한/SGE PM팀](dooray://3570973279848255571/members/3571008626725314977 \"admin\") "
                    f"[@김주현D/SGE PM팀](dooray://3570973279848255571/members/3898983631689925324 \"member\") \n"
                    f"**지라 일감 요청드립니다!**\n"
                    f" 제목: {title_prefix}{title}\n"
                    f" 내용: {content}\n"
                    f" 기간: {duration}\n"
                    f" 담당자: {assignee}\n"
                    f" 기획서: {document if document != '없음' else '없음'}"
        }

        # Dooray 메신저로 응답 보내기
        headers = {"Content-Type": "application/json"}
        logger.info("⚠️interactive_webhook(): 3 ⚠️")

        jira_response = requests.post(jira_webhook_url, json=response_data, headers=headers)

        if jira_response.status_code == 200:
            logger.info("⚠️jira_response.status_code == 200: ⚠️")
            return jsonify({"responseType": "inChannel", "text": "✅ 응답이 성공적으로 전송되었습니다!"}), 200
        
        else:
            logger.error("❌ 메시지 전송 실패: %s", jira_response.text)
            return jsonify({"responseType": "ephemeral", "text": "❌ 응답 전송에 실패했습니다."}), 500

    logger.info("⚠️interactive_webhook(): 5 ⚠️")
    return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400


@app.route("/interactive-webhook2", methods=["POST"])
def interactive_webhook2():
    """Dooray /meeting_review 요청을 처리하는 웹훅"""

    logger.info("⚠️interactive_webhook2(): 시작 ⚠️")
    data = request.json
    logger.info("📥 Received Interactive Action (meeting_review): %s", data)

    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    callback_id = data.get("callbackId")
    trigger_id = data.get("triggerId", "")
    submission = data.get("submission", {})
    cmd_token = data.get("cmdToken", "")
    response_url = data.get("responseUrl", "")
    command_request_url = data.get("commandRequestUrl", "")

    if not submission:
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 입력된 데이터가 없습니다."}), 400

    # 폼 입력값 처리
    title = submission.get("title", "제목 없음")
    content = submission.get("content", "내용 없음")
    document = submission.get("document", "없음")
    assignee_tags = submission.get("assignee", "")  # ex) "@김철수 @박영희/기획팀"

    # '@이름' 형식 추출 (공백 포함된 이름 전체 추출)
    # mention_pattern = r'@([^\n,@]+)'  # '@조현웅/SGE 품질검증팀' → '조현웅/SGE 품질검증팀'
    # names = re.findall(mention_pattern, assignee_tags)
    mention_pattern = r'@([^\n,@]+)'
    names = [name.strip() for name in re.findall(mention_pattern, assignee_tags)]

    logger.info("🔍 추출된 이름 목록: %s", names)

    '''
    mentions = []
    for name in names:
        logger.info("🔎 이름 처리 중: %s", name)
        member_id = get_member_id_by_name(name)
        if member_id:
            mention = f"[@{name}](dooray://3570973280734982045/members/{member_id} \"member\")"
            logger.info("멘션 생성 완료: %s", mention)
            mentions.append(mention)
        else:
            logger.warning("⚠️ member_id를 찾을 수 없음: %s", name)
            mentions.append(f"@{name} (찾을 수 없음)")
    '''
    # 1. 전체 멤버 정보 불러오기
    all_members = get_all_members()

    # 2. 이름 → ID 매핑 (이름 공백 제거)
    name_to_id = {
        member.get("name", "").strip(): member.get("id")
        for member in all_members if member.get("name") and member.get("id")
    }

    # 3. 이름 리스트 준비 (이름 공백 제거 포함)
    names = [name.strip() for name in names]  # 기존 names 리스트에서 strip 적용

    # 4. 한번의 루프로 멘션 텍스트 생성
    mentions = [
        f"[@{name}](dooray://3570973279848255571/members/{name_to_id[name]} \"member\")"
        if name in name_to_id else f"@{name} (찾을 수 없음)"
        for name in names
    ]

    # 5. 결과 문자열로 조합
    assignee_text = "".join(mentions) if mentions else "없음"
    logger.info("✅ 최종 assignee_text: %s", assignee_text)

    # ✅ 메시지 구성
    response_data = {
        "responseType": "inChannel",
        "channelId": channel_id,
        "triggerId": trigger_id,
        "replaceOriginal": "false",
        "text": f"**[기획 리뷰 요청드립니다.]**\n"
                f"제목: << {title} >>\n"
                f"기획서: {document if document != '없음' else '없음'}\n"
                f"내용: {content}\n"
                f"담당자: {assignee_text}\n"
                f"참조: [@홍석기C/SGE PM팀](dooray://3570973279848255571/members/3571008351482084031 \"admin\") "  # [@홍석기C/SGE PM팀]
                f"[@노승한/SGE PM팀](dooray://3570973279848255571/members/3571008626725314977 \"admin\") "  # [@노승한/SGE PM팀]
                f"[@김주현D/SGE PM팀](dooray://3570973279848255571/members/3898983631689925324 \"member\") \n"
        # [@김주현D/SGE PM팀]
    }
    # 기획서 리뷰방
    webhook_url = "https://projectg.dooray.com/services/3570973280734982045/4041534465982137794/rHV6ZWAeSuCnMRko9whNWg"
    # 테스트방(jira-task)
    # webhook_url = "https://projectg.dooray.com/services/3570973280734982045/4041752041730033522/0MRxm-OGSsuVzsgm0IEI3A"

    headers = {"Content-Type": "application/json"}

    response = requests.post(webhook_url, json=response_data, headers=headers)

    if response.status_code == 200:
        logger.info("미팅 검토 메시지 전송 성공")
        return jsonify({"responseType": "inChannel", "text": "미팅 요청이 전송되었습니다!"}), 200
    else:
        logger.error("미팅 검토 메시지 전송 실패: %s", response.text)
        return jsonify({"responseType": "ephemeral", "text": "미팅 요청이 전송에 실패했습니다."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0")
