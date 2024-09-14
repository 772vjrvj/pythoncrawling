Sub RunWebScraping_WinHTTP()
    Dim WinHttpReq As Object
    Dim url As String
    Dim query2 As String
    Dim entpName As String
    Dim itemNoFullname As String
    Dim pageNum As String
    Dim nowPageNum As String
    Dim responseText As String
    Dim json As Object
    Dim result_list As Object
    Dim result_total As Long
    Dim ws As Worksheet
    Dim startRow As Long
    Dim i As Long

    ' 엑셀에서 C2, C3, C4, C5, C6 셀의 값을 가져오기
    query2 = Range("C2").Value
    entpName = Range("C3").Value
    itemNoFullname = Range("C4").Value
    pageNum = Range("E3").Value
    If pageNum > 1 Then
        nowPageNum = (pageNum - 1) * 10
    Else
        nowPageNum = 1
    End If


    ' 로그 출력 (Immediate Window에 출력)
    Debug.Print "query2: " & query2
    Debug.Print "entpName: " & entpName
    Debug.Print "itemNoFullname: " & itemNoFullname
    Debug.Print "pageNum: " & pageNum
    Debug.Print "nowPageNum: " & nowPageNum


    ' POST 데이터 생성
    postData = "query2=" & query2 & "&item_no_fullname=" & itemNoFullname & "&entp_Name=" & entpName & "&page_num=" & pageNum & "&now_page_num=" & nowPageNum

    ' 요청할 URL 정의
    url = "http://127.0.0.1:8080/api/data"

    ' WinHTTP 요청 준비
    Set WinHttpReq = CreateObject("WinHttp.WinHttpRequest.5.1")

    ' 요청 설정 (POST)
    WinHttpReq.Open "POST", url, False
    WinHttpReq.setRequestHeader "Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"

    ' POST 데이터 전송
    WinHttpReq.send postData

    ' 응답 받기
    responseText = WinHttpReq.responseText
    ' MsgBox responseText  ' 서버 응답 확인

    ' 응답을 JSON으로 파싱 (JsonConverter 사용)
    Set json = JsonConverter.ParseJson(responseText)

    ' result_list와 result_total 추출
    Set result_list = json("result_list")
    result_total = json("result_total")

    ' 결과 시트에 기록할 준비
    Set ws = ThisWorkbook.Sheets("Sheet1")
    startRow = 7  ' 데이터 입력 시작 행 (A7부터)

    ' 데이터 초기화
    ws.Rows(startRow & ":" & startRow + 9).ClearContents

    ' 데이터를 엑셀에 기록
    i = 0
    For Each item In result_list
        ws.Cells(startRow + i, 1).Value = item("순번")
        ws.Cells(startRow + i, 2).Value = item("업체명")
        ws.Cells(startRow + i, 3).Value = item("품목명")
        ws.Cells(startRow + i, 4).Value = item("품목허가번호")
        ws.Cells(startRow + i, 5).Value = item("품목등급")
        ws.Cells(startRow + i, 6).Value = item("품목상태")
        ws.Cells(startRow + i, 7).Value = item("취소/취하일시")
        i = i + 1
    Next item

    ' result_total을 10으로 나눈 몫 + 1을 E4 (ws.Cells(4, 6))에 기록
    totalPages = Int(result_total / 10) + 1
    ws.Cells(4, 5).Value = totalPages

    ws.Cells(4, 7).Value = result_total


    ' MsgBox로 result_total 출력
    ' MsgBox "총 데이터 수: " & result_total
End Sub


Sub RunWebScraping_Clear()
    Dim ws As Worksheet
    Dim startRow As Long
    Dim endRow As Long

    ' 초기화할 시트와 시작/끝 행 설정
    Set ws = ThisWorkbook.Sheets("Sheet1")
    startRow = 7   ' 데이터 입력 시작 행
    endRow = startRow + 9  ' 초기화할 범위 (예: 10개의 행을 초기화)

    ' 데이터 초기화 (startRow부터 endRow까지의 내용 삭제)
    ws.Rows(startRow & ":" & endRow).ClearContents
End Sub
