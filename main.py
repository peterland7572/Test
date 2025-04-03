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

    if command == "/일감":
        dialog_data = {
            "token": cmd_token,
            "triggerId": trigger_id,
            "callbackId": "work_task",
            "dialog": {
                "callbackId": "work_task",
                "title": "📌 새 업무 등록",
                "submitLabel": "등록",
                "elements": [
                    {"type": "text", "label": "제목", "name": "title", "optional": False},
                    {"type": "textarea", "label": "내용", "name": "content", "optional": False},
                    {"type": "text", "label": "기간", "name": "duration", "optional": False},
                    {"type": "text", "label": "기획서 (URL)", "name": "document", "optional": True},
                    {"type": "text", "label": "담당자 (Dooray ID)", "name": "assignee", "optional": False}  # 담당자 추가
                ]
            }
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}
        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)

        if response.status_code == 200:
            logger.info("✅ Dialog 생성 요청 성공")
            return jsonify({"responseType": "ephemeral", "text": "📢 업무 입력 창을 열었습니다."}), 200
        else:
            logger.error("❌ Dialog 생성 요청 실패: %s", response.text)
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 업무 입력 창을 여는 데 실패했습니다."}), 500

    elif command == "/jira":
        message_data = {
            "text": "📢 Jira 작업을 처리 중입니다...!",
            "channelId": channel_id,
            "triggerId": trigger_id,
            "replaceOriginal": "false",
            "responseType": "inChannel"
        }

        headers = {
            "token": cmd_token,
            "Content-Type": "application/json"
        }

        logger.info("🔹 Parsed Values:")
        logger.info("   - tenant_domain: %s", tenant_domain)
        logger.info("   - channel_id: %s", channel_id)
        logger.info("   - command: %s", command)
        logger.info("   - cmd_token: %s", cmd_token)
        logger.info("   - trigger_id: %s", trigger_id)
        logger.info("   - responseUrl: %s", responseUrl)

        logger.info("🔹 Sending Message Data: %s", message_data)
        logger.info("🔹 Headers: %s", headers)

        # Dooray 메시지 전송
        response = requests.post(responseUrl, json=message_data, headers=headers)
        # `/jira` 명령어 처리
        if response.status_code == 200:
            logger.info("✅ Dooray 메시지 전송 성공")
            return jsonify({"responseType": "inChannel", "replaceOriginal": "false",
                            "text": "(dooray://3570973280734982045/members/3790034441950345057 \"member\")" "✅ Jira 메시지가 전송되었습니다."}), 200
        else:
            logger.error("❌ Dooray 메시지 전송 실패: %s", response.text)
            return jsonify(
                {"responseType": "inChannel", "replaceOriginal": "false", "text": "❌ Jira 메시지 전송에 실패했습니다."}), 500

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

    # 만약 channel_id가 없으면, 다른 경로에서 가져오기
    if not channel_id:
        channel = data.get("channel")
        if channel:
            channel_id = channel.get("id")
            logger.info("📌 Found channel_id in 'channel' object: %s", channel_id)
        else:
            logger.warning("⚠️ channel_id is missing in both 'channelId' and 'channel' object!")

    logger.info("🔹 Final channel_id: %s", channel_id)

    # 만약 tenant_domain이 없으면, 다른 경로에서 가져오기
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
    # 로그 추가
    logger.info("🔄 Extracted callbackId: %s", callback_id)

    # 업무 등록 처리
    if callback_id == "work_task":
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
            "text": f"[@함기범 /SGE 품질검증팀](dooray://3570973280734982045/members/3790036926003681981 \"member\") "
                    f"[@조현웅/SGE 품질검증팀](dooray://3570973280734982045/members/3790034441950345057 \"member\")   "
                    f"n"                                                                                                                                                                  
                    f" **지라 일감 요청드립니다.!**\n\n\n"
                    
                    f" **제목:** {title}\n\n"
                    f" **내용:** {content}\n\n"
                    f" **기간:** {duration}\n\n"
                    f" **담당자:** {assignee}\n\n"
                    f" **기획서:** {document if document != '없음' else '없음'}"
        }

        # Dooray 메신저로 응답 보내기
        headers = {"token": cmd_token}
        logger.info("⚠️interactive_webhook(): 3 ⚠️")
        response = requests.post(responseUrl, json=response_data, headers=headers)

        if response.status_code == 200:
            logger.info("⚠️response.status_code == 200: ⚠️")
            return jsonify({"responseType": "inChannel", "text": "✅ 응답이 성공적으로 전송되었습니다!"}), 200
        else:
            logger.error("❌ 메시지 전송 실패: %s", response.text)
            return jsonify({"responseType": "ephemeral", "text": "❌ 응답 전송에 실패했습니다."}), 500

        logger.info("⚠️interactive_webhook(): 4 ⚠️")
        return jsonify({"responseType": "inChannel", "text": "✅ 메시지가 성공적으로 전송되었습니다!"}), 200

    else:
        logger.info("⚠️interactive_webhook(): 5 ⚠️")
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0")
