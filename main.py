import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOORAY_DIALOG_URL = "https://{tenantDomain}/messenger/api/channels/{channelId}/dialogs"

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    """Dooray에서 받은 명령을 처리하는 엔드포인트"""
    data = request.json
    logger.info("📥 Received Data: %s", data)

    command = data.get("command", "").strip()
    cmd_token = data.get("cmdToken", "")
    trigger_id = data.get("triggerId", "")

    if command == "/업무":
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
                    {"type": "text", "label": "기획서 (URL)", "name": "document", "optional": True}
                ]
            }
        }

        headers = {"token": cmd_token}
        response = requests.post(DOORAY_DIALOG_URL, json=dialog_data, headers=headers)

        if response.status_code == 200:
            logger.info("✅ Dialog 생성 요청 성공")
            return jsonify({"responseType": "ephemeral", "text": "📢 업무 입력 창을 열었습니다."}), 200
        else:
            logger.error("❌ Dialog 생성 요청 실패: %s", response.text)
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 업무 입력 창을 여는 데 실패했습니다."}), 500

    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400


@app.route("/interactive-webhook", methods=["POST"])
def interactive_webhook():
    """Dooray Interactive Message 요청을 처리하는 웹훅"""
    data = request.json
    logger.info("📥 Received Interactive Action: %s", data)

    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")

    if not tenant_domain or not channel_id:
        logger.error("❌ tenantDomain 또는 channelId 누락")
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 잘못된 요청입니다. (tenantDomain 또는 channelId 없음)"}), 400

    # Dooray 다이얼로그 URL 구성
    dooray_dialog_url = f"https://{tenant_domain}/messenger/api/channels/{channel_id}/dialogs"
    logger.info("🌐 Dooray API URL: %s", dooray_dialog_url)

    callback_id = data.get("callbackId")

    if callback_id == "work_task":
        submission = data.get("submission", {})
        title = submission.get("title", "제목 없음")
        content = submission.get("content", "내용 없음")
        duration = submission.get("duration", "미정")
        document = submission.get("document", "없음")

        response_data = {
            "responseType": "inChannel",
            "text": f"📌 **새 업무 요청이 등록되었습니다!**\n"
                    f"📍 **제목:** {title}\n"
                    f"📍 **내용:** {content}\n"
                    f"📍 **기간:** {duration}\n"
                    f"📍 **기획서:** {document if document != '없음' else '없음'}"
        }

        logger.info("✅ 업무 요청이 정상적으로 등록되었습니다: %s", response_data)
        return jsonify(response_data), 200

    else:
        logger.warning("⚠️ 알 수 없는 callbackId: %s", callback_id)
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400




if __name__ == "__main__":
    app.run(host="0.0.0.0")
