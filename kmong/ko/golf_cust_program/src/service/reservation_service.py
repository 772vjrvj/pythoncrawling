from src.utils.payload_builder import PayloadBuilder
from src.api.action import send_to_external_api_action

class ReservationService:
    def __init__(self, token: str, store_id: str):
        self.token = token
        self.store_id = store_id

    def register(self, req_json=None, resp_json=None):
        for entity in PayloadBuilder.extract_entities(resp_json):
            external_id = entity.get("bookingNumber", [None])[0]
            machine_number = entity.get("machineNumber")
            reserve_no = req_json.get("reserveNo") or None
            payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number, reserve_no)
            send_to_external_api_action(self.token, self.store_id, "register", payload)

    def edit(self, req_json=None, resp_json=None):
        entities = PayloadBuilder.extract_entities(resp_json)
        reserve_no = req_json.get("reserveNo") or None

        if reserve_no:
            payload = PayloadBuilder.delete("고객 취소", group_id=reserve_no)
        else:
            external_id = req_json.get("bookingNumber")
            payload = PayloadBuilder.delete("추가 수정시 기존 취소", external_id=external_id)
        send_to_external_api_action(self.token, self.store_id, "delete", payload)

        if entities:
            for entity in entities:
                external_id = entity.get("bookingNumber", [None])[0]
                machine_number = entity.get("machineNumber")
                payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number, reserve_no)
                send_to_external_api_action(self.token, self.store_id, "register", payload)
        else:
            external_id = req_json.get("bookingNumber")
            machine_number = req_json.get("machineNumber")
            payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number)
            send_to_external_api_action(self.token, self.store_id, "edit", payload)

    def edit_move(self, req_json=None, resp_json=None):
        payload = PayloadBuilder.edit_move(req_json)
        send_to_external_api_action(self.token, self.store_id, "edit", payload)

    def delete_admin(self, req_json, resp_json):
        booking_nums = req_json.get("bookingNums", [])
        if isinstance(booking_nums, str):
            booking_nums = [booking_nums]
        for booking_number in booking_nums:
            payload = PayloadBuilder.delete("운영자 취소", external_id=booking_number)
            send_to_external_api_action(self.token, self.store_id, "delete", payload)

    def delete_mobile(self, req_json=None, resp_json=None):
        reserve_no = resp_json.get("entity", {}).get("destroy", [{}])[0].get("reserveNo", "")
        if reserve_no:
            payload = PayloadBuilder.delete("고객 취소", group_id=reserve_no)
            send_to_external_api_action(self.token, self.store_id, "delete", payload)
