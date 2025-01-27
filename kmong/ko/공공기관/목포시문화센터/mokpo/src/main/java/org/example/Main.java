package org.example;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.text.StringEscapeUtils;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class Main {

    public static void main(String[] args) {
        // 스케줄러 함수 호출
        startScheduler("2024-09-01"); // 원하는 달 전달

        // 9월까지 json data 가져오기
        JsonObject jsonData = getScheduleBetweenDates("2024-01-01", "2024-09-01");
        System.out.println(jsonData);
    }

    /**
     * 스케줄러를 실행하여 지정된 날짜마다 크롤링 작업을 수행합니다.
     * @param date 크롤링을 시작할 기준 날짜입니다.
     */
    public static void startScheduler(final String date) {
        // 스케줄러 생성 (1시간마다 크롤링 실행)
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

        // 스케줄러에서 실행할 작업 정의
        Runnable task = new Runnable() {
            @Override
            public void run() {
                try {
                    // 날짜가 null이거나 공백이면 오늘이 포함된 달 생성
                    String effectiveDate = date;
                    if (StringUtils.isBlank(date)) {
                        effectiveDate = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
                    }

                    // 크롤링 작업 실행 및 결과 출력
                    JsonArray result = crawlMokpoArtSchedule(effectiveDate);

                    // 결과 로그 출력 및 데이터베이스에 삽입 가능
                    for (int i = 0; i < result.size(); i++) {
                        JsonObject jsonObject = result.get(i).getAsJsonObject();
                        System.out.println("Object " + (i + 1) + ": " + jsonObject.toString());
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        };

        // 1시간마다 크롤링 작업 실행
        // 원하는 시간은 설정하시면 됩니다.
        scheduler.scheduleAtFixedRate(task, 0, 1, TimeUnit.HOURS);

        // 프로그램이 종료되지 않도록 유지
        try {
            Thread.sleep(Long.MAX_VALUE);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.out.println("Scheduler interrupted.");
        }
    }

    /**
     * 주어진 날짜에 맞춰 목포 예술 공연 정보를 크롤링합니다.
     * @param date 크롤링할 날짜 (형식: yyyy-MM-dd) (dd는 01 시작일로 고정)
     * @return 공연 정보를 담은 JsonArray 객체를 반환
     */
    public static JsonArray crawlMokpoArtSchedule(String date) {
        JsonArray jsonArray = new JsonArray();
        String url = "https://www.mokpo.go.kr/art/performance/schedule?date=" + date;

        try {
            // Jsoup을 사용하여 URL 연결 및 문서 가져오기
            Document doc = Jsoup.connect(url)
                    .header("Accept-Encoding", "identity") // GZIP 비활성화
                    .get();

            // month_calendar 클래스의 tbody 안의 tr들을 찾기
            Elements trs = doc.select("table.month_calendar tbody tr");

            // tr을 순차적으로 탐색하여 각 td의 공연 정보를 가져옴
            for (Element tr : trs) {
                Elements tds = tr.select("td"); // 각 tr 안의 td들을 가져옴

                for (int i = 0; i < tds.size(); i++) {
                    Element td = tds.get(i);

                    // ul 태그가 없으면 continue로 다음 td로 넘어감
                    if (td.select("ul").isEmpty()) {
                        continue;
                    }

                    // 요일 값 계산 (일요일 ~ 토요일)
                    String week = String.valueOf(i);

                    // ul 태그를 탐색
                    Elements uls = td.select("ul");
                    for (Element ul : uls) {
                        JsonObject jsonObject = new JsonObject();

                        // 기본값 설정 및 week 값 추가
                        jsonObject.addProperty("title", "");
                        jsonObject.addProperty("date", "");
                        jsonObject.addProperty("sdate", "");
                        jsonObject.addProperty("edate", "");
                        jsonObject.addProperty("week", week);
                        jsonObject.addProperty("content", "");
                        jsonObject.addProperty("url", "");

                        // data-idx 값을 추출하여 id로 저장
                        Elements viewPopupElements = ul.select(".view_popup");
                        if (!viewPopupElements.isEmpty()) {
                            String dataIdx = viewPopupElements.attr("data-idx");
                            jsonObject.addProperty("id", dataIdx);
                        }

                        // jsonArray에 추가
                        jsonArray.add(jsonObject);
                    }
                }
            }

            // 상세 정보 가져오기
            for (int i = 0; i < jsonArray.size(); i++) {
                JsonObject jsonObject = jsonArray.get(i).getAsJsonObject();
                fillEventDetails(jsonObject);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

        return jsonArray;
    }

    /**
     * 각 공연에 대한 세부 정보를 채워 넣습니다.
     * @param jsonObject 공연 세부 정보를 저장할 JSON 객체
     */
    public static void fillEventDetails(JsonObject jsonObject) {
        // data-idx 값을 사용하여 상세 페이지 URL 구성
        String dataIdx = jsonObject.get("id").getAsString();
        String detailUrl = "https://www.mokpo.go.kr/art/performance/schedule?mode=view&idx=" + dataIdx;

        try {
            // 상세 페이지를 연결하여 Jsoup으로 문서 가져오기
            Document detailDoc = Jsoup.connect(detailUrl)
                    .header("Accept-Encoding", "identity")
                    .get();

            // 제목 추출
            String title = detailDoc.select("div.board_wrapper h3").text();
            if (!title.isEmpty()) {
                jsonObject.addProperty("title", StringEscapeUtils.unescapeHtml4(title));
            }

            // 등록일 (날짜) 추출 및 포맷팅
            Elements ddElements = detailDoc.select("div.board_wrapper dd");
            if (!ddElements.isEmpty()) {
                String regDate = ddElements.get(0).text().trim().replace(".", "");
                if (!regDate.isEmpty()) {
                    jsonObject.addProperty("date", regDate);
                }
            }

            // 행사 기간 추출 및 시작일/종료일 저장
            Elements infoElements = detailDoc.select("ul.info-box li");
            if (!infoElements.isEmpty()) {
                Elements spans = infoElements.get(0).select("span");
                if (spans.size() > 1) {
                    String dateRange = spans.get(1).text().trim();
                    String[] dates = dateRange.split("~");
                    if (dates.length == 2) {
                        String sdate = dates[0].trim().replace("-", "");
                        String edate = dates[1].trim().replace("-", "");
                        jsonObject.addProperty("sdate", sdate);
                        jsonObject.addProperty("edate", edate);
                    }
                }
            }

            // 공연 내용(content) 추출
            String content = detailDoc.select("div.text_viewbox").html();
            if (!content.isEmpty()) {
                content = StringEscapeUtils.unescapeHtml4(content);
                jsonObject.addProperty("content", content);
            }

            // url 추가
            String url = StringEscapeUtils.unescapeHtml4(detailUrl);
            jsonObject.addProperty("url", url);
            jsonObject.remove("id"); // id 제거

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /**
     * 시작일과 종료일 사이의 데이터를 수집하고 병합하여 반환하는 함수
     * @param startDate 시작일 (yyyy-MM-dd)
     * @param endDate 종료일 (yyyy-MM-dd)
     * @return 시작일과 종료일 사이의 데이터를 담은 JsonObject
     */
    public static JsonObject getScheduleBetweenDates(String startDate, String endDate) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        LocalDate start = LocalDate.parse(startDate, formatter);
        LocalDate end = LocalDate.parse(endDate, formatter);

        // 최종적으로 반환할 JsonObject 생성
        JsonObject jsonData = new JsonObject();

        // 모든 월의 데이터를 담을 JsonArray
        JsonArray finalResult = new JsonArray();

        // 날짜가 종료일까지 반복
        while (!start.isAfter(end)) {
            // 현재 월의 데이터를 크롤링
            String currentDate = start.format(formatter);
            System.out.println("========== 시작 currentDate : " + currentDate + " ==========");
            JsonArray currentMonthData = crawlMokpoArtSchedule(currentDate);

            // 크롤링한 데이터를 최종 결과에 추가
            finalResult.addAll(currentMonthData);
            System.out.println("========== 끝 currentDate : " + currentDate + " ==========");

            // 다음 달로 이동
            start = start.plusMonths(1);
        }

        // data라는 키로 결과 저장
        jsonData.add("data", finalResult);

        return jsonData;  // 최종 결과 반환
    }
}
