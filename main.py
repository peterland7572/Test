import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    }

    logger.info("📌 Received command: %s", command)
    logger.info("📌 Mapped callbackId: %s", callback_ids[command])

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
                    {"type": "text", "label": "기간", "name": "duration", "optional": False},
                    {"type": "text", "label": "기획서 (URL)", "name": "document", "optional": True},
                    {"type": "text", "label": "담당자 (Dooray ID)", "name": "assignee", "optional": False}
                ]
            }
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}
        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)

        logger.info("⚠️⚠️⚠️- dialog_data: %s", dialog_data) # 
        # 최종적으로 설정된 callbackId 값을 다시 확인하는 로그
        logger.info("📌 Final dialog_data.callbackId: %s", dialog_data["callbackId"])
        logger.info("📌 Final dialog_data.dialog.callbackId: %s", dialog_data["dialog"]["callbackId"])


        if response.status_code == 200:
            logger.info(f"✅ Dialog 생성 요청 성공 ({command})")
            return "", 200  # 아무 응답도 보내지 않음 (창이 조용히 닫힘)
        else:
            logger.error(f"❌ Dialog 생성 요청 실패 ({command}): {response.text}")
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 업무 입력 창을 여는 데 실패했습니다."}), 500

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
        "test_task": "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q"
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

        response_data = {
            "responseType": "inChannel",
            "channelId": channel_id,
            "triggerId": trigger_id,
            "replaceOriginal": "false",
            "text": f"**지라 일감 요청드립니다.!**\n\n"
                    f" 제목: \n\t\t{title}\n\n"
                    f" 내용: \n\t\t{content}\n\n"
                    f" 기간: \n\t\t{duration}\n\n"
                    f" 담당자: \n\t\t{assignee}\n\n"
                    f" 기획서: \n\t\t{document if document != '없음' else '없음'}"
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



if __name__ == "__main__":
    app.run(host="0.0.0.0")
