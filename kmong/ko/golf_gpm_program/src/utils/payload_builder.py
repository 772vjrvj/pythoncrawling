from src.utils.config import CRAWLING_SITE
from src.utils.time import to_iso_format  # to_iso_format은 별도 유틸로 가정

class PayloadBuilder:

    @staticmethod
    def compact(payload: dict) -> dict:
        """None, 빈 문자열, 빈 리스트는 제거한 dict 반환"""
        return {k: v for k, v in payload.items() if v not in (None, "", [])}

    @staticmethod
    def register_or_edit(req_json, external_id, machine_number, reserve_no=None) -> dict:
        payload = {
            "externalId"    : str(external_id),
            "roomId"        : str(machine_number),
            "crawlingSite"  : CRAWLING_SITE,
            "name"          : str(req_json.get("bookingName")),
            "phone"         : req_json.get("cellNumber"),
            "requests"      : req_json.get("bookingMemo"),
            "paymented"     : req_json.get("paymentYn", "N") == "Y",
            "partySize"     : int(req_json.get("bookingCnt", 1)),
            "paymentAmount" : int(req_json.get("paymentAmount", 0)),
            "startDate"     : to_iso_format(req_json.get("bookingStartDt")),
            "endDate"       : to_iso_format(req_json.get("bookingEndDt")),
        }

        if reserve_no:
            payload["externalGroupId"] = str(reserve_no)

        return PayloadBuilder.compact(payload)

    @staticmethod
    def edit_move(req_json) -> dict:
        payload = {
            "externalId"  : str(req_json.get("bookingNumber")),
            "roomId"      : str(req_json.get("machineNumber")),
            "startDate"   : to_iso_format(req_json.get("bookingStartDt")),
            "endDate"     : to_iso_format(req_json.get("bookingEndDt")),
            "crawlingSite": CRAWLING_SITE
        }
        return PayloadBuilder.compact(payload)

    @staticmethod
    def delete(reason: str, *, external_id=None, group_id=None) -> dict:
        payload = {
            "crawlingSite": CRAWLING_SITE,
            "reason": reason
        }
        if external_id:
            payload["externalId"]      = str(external_id)
        if group_id:
            payload["externalGroupId"] = str(group_id)
        return PayloadBuilder.compact(payload)


    @staticmethod
    def extract_entities(resp_json) -> list:
        return resp_json.get("entitys") or resp_json.get("entity") or []
