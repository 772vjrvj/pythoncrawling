if (!window.__DOM_OBSERVER_SETUP_DONE) {
    window.__DOM_OBSERVER_SETUP_DONE = true;

    window.__GLOBAL_BOOKING_DATA = null;

    window.getBookingData = function () {
        return window.__GLOBAL_BOOKING_DATA || null;
    };

    const nxMap = {
        "NX1": 37204,
        "NX2": 37205,
        "NX3": 37206,
        "NX4": 37203,
        "NX5": 37209,
        "NX6": 37208,
        "NX7": 37207,
        "NX8": 37210,
        "NX9(좌타)": 37211
    };

    document.body.addEventListener('click', (e) => {
        const target = e.target.closest('.bookingPopup .buttons .modify, .bookingPopup .buttons .cancle');
        if (!target) return;

        e.preventDefault();      // 👉 필수: 기본 동작 중단 (a 태그 등)
        e.stopPropagation();     // 👉 필수: 이벤트 전파 중단 (상위 리스너 개입 차단)

        try {
            const popup = document.querySelector('.bookingPopup');
            if (!popup) return;

            const nameInput = popup.querySelector('.contents .name');
            const phoneInput = popup.querySelector('.contents .phone');

            const name = nameInput ? nameInput.value.trim() : '';
            const phone = phoneInput ? phoneInput.value.trim() : '';

            const machineNumbers = [];
            const roomInfo = popup.querySelector('.roomInfo');
            if (roomInfo) {
                const selectedAnchors = roomInfo.querySelectorAll('a.select');
                selectedAnchors.forEach(anchor => {
                    const fullText = anchor.innerText.trim();
                    const nxName = fullText.replace(/^TVNX\s*/, '');
                    const mapped = nxMap[nxName];
                    if (mapped) {
                        machineNumbers.push(mapped);
                    }
                });
            }
            // 🔽 버튼 텍스트에 따른 타입 매핑
            // 🔽 버튼 텍스트에 따른 타입 매핑
            const buttonText = target.innerText.trim();
            let type = null;
            if (buttonText === '예약 등록') type = 'register';
            else if (buttonText === '예약 변경') type = 'edit';
            else if (buttonText === '예약 취소') type = 'delete';

            window.__GLOBAL_BOOKING_DATA = {
                name,
                phone,
                machineNumbers,
                type,           // ⬅️ 추가된 필드
                timestamp: Date.now()
            };

            console.log('[Observer] 예약 버튼 클릭됨 → 데이터 저장:', window.__GLOBAL_BOOKING_DATA);
        } catch (err) {
            console.error("[Observer] 예약 버튼 처리 중 오류 발생:", err);
        }
    });

    console.log('[Observer] 예약 클릭 감지 스크립트 주입 완료');
}
