// 이미 주입되었는지 체크
if (!window.__DOM_OBSERVER_SETUP_DONE) {
    window.__DOM_OBSERVER_SETUP_DONE = true;

    // 전역 예약 데이터 저장소 초기화
    window.__GLOBAL_BOOKING_DATA = null;

    // 예약 데이터 가져오는 함수 정의
    window.getBookingData = function () {
        return window.__GLOBAL_BOOKING_DATA || null;
    };

    // MutationObserver로 예약 팝업 감지
    const observer = new MutationObserver(() => {
        const popup = document.querySelector('.bookingPopup');
        if (!popup) return;

        const nameInput = popup.querySelector('.contents .name');
        if (nameInput && nameInput.value) {
            window.__GLOBAL_BOOKING_DATA = {
                name: nameInput.value.trim(),
                timestamp: Date.now()
            };
            console.log("[Observer] 예약 팝업 감지됨:", window.__GLOBAL_BOOKING_DATA);
        }
    });

    // DOM 변화 감시 시작
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log("[Observer] 예약 감지 스크립트 주입 완료");
}
