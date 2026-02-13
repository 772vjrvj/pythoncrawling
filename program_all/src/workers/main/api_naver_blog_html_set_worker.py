import os
import json
import time
import random
import re
from urllib.parse import unquote, urlparse, parse_qsl, urlencode, urlunparse

from bs4 import BeautifulSoup

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker
from PIL import Image
import os
import html as _html

class ApiNaverBlogHtmlSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()
        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0.0

        self.site_name = "naver_blog"
        self.site_list_url = "https://blog.naver.com/PostTitleListAsync.naver"

        self.blog_id = "dent0123"
        self.category_no = "7"
        self.count_per_page = 30

        self.headers_list = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "charset": "utf-8",
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "pragma": "no-cache",
            "referer": f"https://blog.naver.com/PostList.naver?from=postList&blogId={self.blog_id}&categoryNo={self.category_no}&currentPage=1",
            "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }

        self.headers_detail = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br",  # zstd 제거(디코딩 이슈 방지)
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }

        self.excel_driver = None
        self.file_driver = None
        self.api_client = None

        self.csv_filename = None

        self.out_root = None
        self.posts_dir = None
        self.assets_dir = None

        self.posts = []  # 최종 객체 배열

        # === 신규 === 이미지 추출/다운로드 옵션
        self.max_images_per_post = 200
        self.img_timeout_sec = 30

    def init(self):
        self.driver_set()
        return True

    def stop(self):
        self.running = False

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(1)
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()

    def driver_set(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)


    _DROP_QUERY_KEYS_IMG = {
        "type", "w", "width", "h", "height", "quality", "q",
        "crop", "scale", "autoRotate", "rotate", "r",
    }

    def _log_saved_img(self, path, url):
        try:
            with Image.open(path) as im:
                w, h = im.size
            sz = os.path.getsize(path)
            self.log_signal_func(f"[IMG-SAVED] {os.path.basename(path)} {w}x{h} bytes={sz} url={url}")
        except Exception as e:
            self.log_signal_func(f"[IMG-SAVED] FAIL path={path} url={url} err={e}")

    def optimize_naver_image_url(self, url: str) -> str:

        if not url:
            return url

        # CDN → 원본 서버 변경
        if "postfiles.pstatic.net" in url:
            url = url.replace("postfiles.pstatic.net", "blogfiles.pstatic.net")

        # type 제거 (리사이즈 방지)
        url = re.sub(r"[?&]type=[^&]+", "", url)

        return url

    def _normalize_image_url(self, url: str) -> str:
        if not url:
            return ""
        u = str(url).strip()
        if not u or u.startswith("data:"):
            return ""
        if u.startswith("//"):
            u = "https:" + u
        u = u.replace("&amp;", "&")

        try:
            p = urlparse(u)
            host = (p.netloc or "").lower()

            # path에 /type=... 제거는 너무 위험해서 빼는게 낫다 (일단 제거하지 말자)
            path = p.path

            q = parse_qsl(p.query, keep_blank_values=True)

            # ✅ postfiles면 type/w/h류 제거해서 원본화
            if "postfiles.pstatic.net" in host:
                q2 = [(k, v) for (k, v) in q if k not in self._DROP_QUERY_KEYS_IMG]
            else:
                q2 = q  # ✅ 다른 호스트는 쿼리 유지

            new_query = urlencode(q2, doseq=True)
            return urlunparse((p.scheme, p.netloc, path, p.params, new_query, p.fragment))
        except Exception:
            return u

    def _guess_ext(self, url: str) -> str:
        try:
            p = urlparse(url)
            path = (p.path or "").lower()
            for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
                if path.endswith(ext):
                    return ext.lstrip(".")
        except Exception:
            pass
        return "jpg"

    # ----------------------------
    # list
    # ----------------------------
    def _fetch_page(self, page_no):
        params = {
            "blogId": self.blog_id,
            "viewdate": "",
            "currentPage": page_no,
            "categoryNo": self.category_no,
            "parentCategoryNo": "",
            "countPerPage": self.count_per_page,
        }
        resp = self.api_client.get(self.site_list_url, params=params, headers=self.headers_list)
        resp = (resp or "").strip().replace("\\'", "'")  # pagingHtml 때문에 필요
        return json.loads(resp)

    def fetch_posts_list(self):
        posts = []
        seen = set()

        page_no = 1
        last_sig = ""

        while self.running:
            data = self._fetch_page(page_no)

            if page_no == 1:
                self.total_cnt = int(str(data.get("totalCount") or "0").strip() or "0")
                self.log_signal_func("totalCount = " + str(self.total_cnt))

            post_list = data.get("postList") or []
            if not post_list:
                break

            page_lognos = []
            for p in post_list:
                ln = p.get("logNo")
                if ln:
                    page_lognos.append(str(ln))
            sig = "|".join(page_lognos)
            if sig == last_sig:
                break
            last_sig = sig

            new_added = 0
            for p in post_list:
                ln = p.get("logNo")
                if not ln:
                    continue
                ln = str(ln)
                if ln in seen:
                    continue
                seen.add(ln)

                title = p.get("title") or ""
                title = unquote(title).replace("+", " ")

                add_date = (p.get("addDate") or "").replace(" ", "").rstrip(".")

                url = f"https://blog.naver.com/PostView.naver?blogId={self.blog_id}&logNo={ln}"

                posts.append({
                    "logNo": ln,
                    "url": url,
                    "title": title,
                    "addDate": add_date,
                })
                new_added += 1

            self.log_signal_func(f"page={page_no} 신규={new_added} 누적={len(posts)}")

            if self.total_cnt > 0 and len(posts) >= self.total_cnt:
                break
            if new_added == 0:
                break

            page_no += 1
            time.sleep(random.uniform(0.2, 0.6))

        return posts

    # ----------------------------
    # detail + html
    # ----------------------------
    def _fetch_detail_html(self, logNo):
        self.headers_detail["referer"] = f"https://blog.naver.com/{self.blog_id}/{logNo}"

        url = "https://blog.naver.com/PostView.naver"
        params = {
            "blogId": self.blog_id,
            "logNo": logNo,
            "redirect": "Dlog",
            "widgetTypeCall": "true",
            "noTrackingCode": "true",
            "directAccess": "false",
        }
        return self.api_client.get(url, params=params, headers=self.headers_detail)

    def _extract_body(self, html):
        soup = BeautifulSoup(html or "", "html.parser")
        body = soup.find(id="postListBody")
        return body

    def _remove_buttons(self, body_tag):
        for el in body_tag.select(".post-btn.post_btn2"):
            el.decompose()

    def _extract_text(self, body_tag):
        t = body_tag.get_text("\n", strip=True)
        return t

    def _download_and_replace_images(self, body_tag, post_no_4, logNo):

        img_dir = os.path.join(self.assets_dir, post_no_4)
        os.makedirs(img_dir, exist_ok=True)

        images = []
        seen = set()

        seq = 1

        for img in body_tag.select("img"):

            if seq > int(self.max_images_per_post):
                break

            # ✅ 그냥 src만 사용
            src = (img.get("src") or "").strip()

            src = self.optimize_naver_image_url(src)   # ✅ 이 줄 추가

            if not src:
                continue

            # protocol-relative 처리
            if src.startswith("//"):
                src = "https:" + src

            if src.startswith("data:"):
                continue

            if src in seen:
                continue
            seen.add(src)

            ext = self._guess_ext(src)
            filename = f"{str(seq).zfill(4)}.{ext}"

            img_headers = dict(self.headers_detail or {})
            img_headers["accept"] = "image/*,*/*;q=0.8"
            img_headers["referer"] = f"https://blog.naver.com/{self.blog_id}/{logNo}"

            saved = self.file_driver.save_image(
                folder_path=img_dir,
                filename=filename,
                image_url=src,
                headers=img_headers,
                timeout=30
            )

            if saved:
                self._log_saved_img(saved, src)

                rel = f"../assets/{post_no_4}/{filename}"
                img["src"] = rel

                images.append(filename)
                seq += 1

            time.sleep(random.uniform(0.05, 0.15))

        image_path = os.path.abspath(img_dir)
        return images, image_path


    def _build_post_html_doc(self, title, addDate, body_html):

        return f"""<!doctype html>
                <html lang="ko">
                <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                
                <style>
                
                body {{
                    margin:0;
                    background:#f6f7f9;
                    font-family:
                        -apple-system,
                        BlinkMacSystemFont,
                        "Segoe UI",
                        Roboto,
                        "Apple SD Gothic Neo",
                        "Malgun Gothic",
                        sans-serif;
                }}
                
                .wrap {{
                    max-width:900px;
                    margin:40px auto;
                    background:white;
                    padding:40px;
                    border-radius:14px;
                
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                }}
                
                .content {{
                    width:100%;
                    text-align:center;
                }}
                
                .content * {{
                    text-align:center !important;
                }}
                
                img {{
                    display:block;
                    margin:25px auto;
                    max-width:100%;
                    height:auto;
                }}
                
                </style>
                </head>
                
                <body>
                
                <div class="wrap">
                
                <h2>{self._esc(title)}</h2>
                
                <div style="color:#666;margin-bottom:25px;">
                {self._esc(addDate)}
                </div>
                
                <div class="content">
                {body_html}
                </div>
                
                </div>
                
                </body>
                </html>
    """


    def _esc(self, s):
        s = "" if s is None else str(s)
        return (s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def process_detail_and_save(self, base_posts):
        out = []

        for i, p in enumerate(base_posts, start=1):
            if not self.running:
                break

            no = str(i).zfill(4)     # ✅ 글번호(폴더번호도 동일)
            logNo = p["logNo"]
            url = p["url"]
            title = p["title"]
            addDate = p["addDate"]

            safe_title = self.file_driver.safe_name(title, max_len=60)
            file_name = f"{no}_{safe_title}.html"
            file_path = os.path.abspath(os.path.join(self.posts_dir, file_name))

            html = self._fetch_detail_html(logNo)
            body = self._extract_body(html)  # id="postListBody"

            content = ""
            images = []
            image_path = os.path.abspath(os.path.join(self.assets_dir, no))

            if body:
                self._remove_buttons(body)
                content = self._extract_text(body)

                # === 수정 === 이미지: assets/{no}/0001.jpg..., 본문 img src도 상대경로로 치환
                images, image_path = self._download_and_replace_images(body, no, logNo)

                post_doc = self._build_post_html_doc(title, addDate, str(body))
                self.file_driver.save_file(self.posts_dir, file_name, post_doc)
            else:
                post_doc = self._build_post_html_doc(title, addDate, "<div>본문을 찾지 못했습니다.</div>")
                self.file_driver.save_file(self.posts_dir, file_name, post_doc)

            row_data = {
                "번호": no,
                "로그번호": logNo,
                "제목": title,
                "내용": content,
                "작성자": self.blog_id,
                "작성일": addDate,
                "URL": url,
                "파일명": file_name,
                "파일경로": file_path,
                "이미지목록": json.dumps(images, ensure_ascii=False),
                "이미지폴더": image_path,
            }

            out.append(row_data)

            self.excel_driver.append_row_to_csv(
                self.csv_filename,
                row_data,
                self.columns
            )

            self.current_cnt = i
            if self.total_cnt > 0:
                pro_value = (self.current_cnt / float(self.total_cnt)) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

            self.log_signal_func(f"[{no}] 저장: {file_name} / imgs={len(images)}")
            time.sleep(random.uniform(0.2, 0.6))

        return out

    # ----------------------------
    # index (offline search)
    # ----------------------------
    def build_index_html(self, posts):
        js_posts = json.dumps(posts, ensure_ascii=False)

        index_html = f"""
        <!doctype html>
        <html lang="ko">
        <head>
          <meta charset="utf-8"/>
          <meta name="viewport" content="width=device-width, initial-scale=1"/>
          <title>블로그 아카이브 - {self.blog_id}</title>
        
          <style>
            body{{
              font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;
              margin:0;
              background:#f6f7f9;
            }}
        
            .wrap{{
              max-width:1100px;
              margin:0 auto;
              padding:18px;
            }}
        
            .card{{
              background:#fff;
              border:1px solid #e5e7eb;
              border-radius:10px;
              padding:14px;
            }}
        
            .top{{
              display:flex;
              gap:10px;
              align-items:center;
              margin-bottom:12px;
            }}
        
            input{{
              flex:1;
              padding:10px 12px;
              border:1px solid #d1d5db;
              border-radius:8px;
              font-size:14px;
            }}
        
            .row{{
              display:flex;
              gap:10px;
              padding:10px 8px;
              border-bottom:1px solid #eef2f7;
            }}
        
            .row:last-child{{
              border-bottom:none;
            }}
        
            .no{{
              width:60px;
              color:#6b7280;
              font-variant-numeric: tabular-nums;
            }}
        
            .meta{{
              width:110px;
              color:#6b7280;
            }}
        
            a{{
              color:#111827;
              text-decoration:none;
            }}
        
            a:hover{{
              text-decoration:underline;
            }}
        
            .title{{
              flex:1;
            }}
        
            .small{{
              color:#6b7280;
              font-size:12px;
              margin-top:4px;
            }}
          </style>
        </head>
                            
        <body>
          <div class="wrap">
            <div class="card">
              <div class="top">
                <input id="q" placeholder="검색: 제목 또는 본문(내용)" />
                <div class="small" id="stat"></div>
              </div>
              <div id="list"></div>
            </div>
          </div>
        
        <script>
        const POSTS = {js_posts};
        
        function esc(s){{
          return String(s ?? "")
            .replaceAll("&","&amp;")
            .replaceAll("<","&lt;")
            .replaceAll(">","&gt;")
            .replaceAll('"',"&quot;")
            .replaceAll("'","&#39;");
        }}
        
        function norm(s){{ return (s ?? "").toString().toLowerCase(); }}
        
        function imgCountFrom(p){{
          const s = p?.["이미지목록"] ?? "[]";
          try {{
            const arr = JSON.parse(s);
            return Array.isArray(arr) ? arr.length : 0;
          }} catch(e) {{
            return 0;
          }}
        }}
        
        function render(items){{
          const el = document.getElementById("list");
          const stat = document.getElementById("stat");
          stat.textContent = items.length + " / " + POSTS.length;
        
          let html = "";
          for(const p of items){{
            const fileName = p?.["파일명"] || "";
            const href = "posts/" + fileName;
        
            html += `
              <div class="row">
                <div class="no">${{esc(p?.["번호"] || "")}}</div>
                <div class="meta">${{esc(p?.["작성일"] || "")}}</div>
                <div class="title">
                  <a href="${{href}}">${{esc(p?.["제목"] || "")}}</a>
                  <div class="small">logNo: ${{esc(p?.["로그번호"] || "")}} / imgs: ${{imgCountFrom(p)}}</div>
                </div>
              </div>
            `;
          }}
          el.innerHTML = html;
        }}
        
        const input = document.getElementById("q");
        input.addEventListener("input", () => {{
          const q = norm(input.value).trim();
          if(!q) return render(POSTS);
        
          const filtered = POSTS.filter(p => {{
            const t = norm(p?.["제목"]);
            const c = norm(p?.["내용"]);
            return t.includes(q) || c.includes(q);
          }});
          render(filtered);
        }});
        
        render(POSTS);
        </script>
        </body>
        </html>
        """
        return index_html

    def main(self):
        self.running = True
        self.log_signal_func("시작합니다.")

        # 출력 폴더 구성
        self.out_root = self.file_driver.create_folder(f"{self.site_name}_archive")
        self.posts_dir = os.path.join(self.out_root, "posts")
        self.assets_dir = os.path.join(self.out_root, "assets")
        os.makedirs(self.posts_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)

        # csv
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.excel_driver.init_csv(self.csv_filename, self.columns)

        # 1) 목록
        base_posts = self.fetch_posts_list()
        self.log_signal_func("목록 수집 완료: " + str(len(base_posts)) + "개")

        # 2) 상세 처리 + html 저장 + 이미지 로컬화 + content 수집
        self.posts = self.process_detail_and_save(base_posts)

        # 3) index.html
        index_html = self.build_index_html(self.posts)
        self.file_driver.save_file(self.out_root, "index.html", index_html)

        self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)

        self.log_signal_func("완료: " + os.path.abspath(self.out_root))
        return True
