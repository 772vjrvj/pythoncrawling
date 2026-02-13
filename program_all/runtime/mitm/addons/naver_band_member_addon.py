# runtime/mitm/addons/naver_band_member_addon.py
import os
import json
from mitmproxy import http, ctx


class NaverBandMemberAddon:
    def __init__(self):
        try:
            ctx.log.info("[INIT] addon loaded")
        except Exception:
            pass

    def response(self, flow: http.HTTPFlow):
        try:
            host = flow.request.pretty_host or ""
            path = flow.request.path or ""

            # ✅ 일단 band.us만 찍어보기
            if "band.us" not in host:
                return

            ctx.log.info("[HIT] %s%s" % (host, path))

            if "/v2.0.0/get_members_of_band" not in path:
                return

            raw = flow.response.content
            if not raw:
                return

            try:
                data = json.loads(raw.decode("utf-8", errors="replace"))
            except Exception:
                ctx.log.warn("[ERR] json parse fail")
                return

            inbox_dir = os.environ.get("HOOK_INBOX_DIR") or os.path.abspath("./out/inbox")
            if not os.path.isdir(inbox_dir):
                os.makedirs(inbox_dir)

            fp = os.path.join(inbox_dir, "naver_band_member.json")
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            ctx.log.info("[SAVE] %s" % fp)

        except Exception as e:
            try:
                ctx.log.warn("[ERR] %s" % str(e))
            except Exception:
                pass


addons = [NaverBandMemberAddon()]
