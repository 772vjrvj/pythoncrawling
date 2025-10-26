import datetime
import io
import json
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from interfaces.admin_management_menu import (AdminMenuMainContainer,
                                              InfoMainView)
from interfaces.commands import ManagementModal
from interfaces.user_startup_menu import VendingView
from modules.bot import CryptoExchangeBot
from modules.database import Database
from modules.log import send_discord_log
from modules.nh_client import (AccountInfo, BankCredentials, DateRange,
                               NHChargeClient)
from modules.utils import (format_utc_time_to_kst, get_env_config,
                           is_successful_withdrawal, parse_binance_apply_time,
                           parse_date, parse_date_to_string)

config = get_env_config()

NH_LOGIN_ID = config.nh_login_id
NH_LOGIN_PW = config.nh_login_pw

CHARGE_BANK_CODE = config.charge_bank_code
CHARGE_BANK_NUMBER = config.charge_bank_number

AUTO_CHARGE_API_KEY = config.auto_charge_api_key

ERROR_LOG_WEBHOOK = config.error_log_webhook
OWNER_DISCORD_IDS = config.owner_discord_ids

def is_owner(interaction: discord.Interaction) -> bool:
    """관리자 권한 체크 함수"""
    config = get_env_config()
    return interaction.user.id in config.owner_discord_ids

class CommandsCog(commands.Cog):
    def __init__(self, bot: CryptoExchangeBot):
        self.bot = bot

    @app_commands.command(name="계산기", description="수수료를 계산합니다.")
    async def calculator(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "수수료 계산 결과: 아직 지원하지 않는 기능입니다.",
            ephemeral=True
        )

    @app_commands.command(name="vending", description="관리자 전용 명령어입니다.")
    @app_commands.allowed_contexts(guilds=True, dms=False)
    async def vending(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 권한 부족",
                    description="관리자만 사용할 수 있는 명령어입니다.",
                    color=0xe74c3c
                ), ephemeral=True
            )
            return
            
        if interaction.channel is None or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 출력에 실패했어요",
                    description="길드 채널에서만 명령어를 사용하실 수 있어요.",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return
        
        view = VendingView()
        await view.create()
  
        message = await interaction.channel.send(view=view)

        self.bot.panel_messages.append(message)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ 출력에 성공했어요",
                description=f"<#{interaction.channel.id}> 채널에 자판기를 출력했어요.",
                color=0xffffff
            ).set_footer(
                text="env 파일 안에 메시지, 채널 아이디를 수정하셔야 새로고침이 시작됩니다."
            ),
            ephemeral=True
        )

    @app_commands.command(name="관리", description="관리자 전용 명령어입니다.")
    @app_commands.describe(target="관리할 사용자")
    async def manage(self, inter: discord.Interaction, target: discord.User):
        if not is_owner(inter):
            await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ 권한 부족",
                    description="관리자만 사용할 수 있는 명령어입니다.",
                    color=0xe74c3c
                ), ephemeral=True
            )
            return
        user_data = await Database.get_user_info(str(target.id), True)
        if not user_data:
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ 조회 실패",
                    description="봇에 가입이 완료된 유저만 조회하실 수 있어요.",
                    color=0xffffff
                ), ephemeral=True
            )
        userRank = await Database.get_user_rank(user_data.discordId)
        transactions = await Database.get_recent_crypto_transactions(user_data.discordId)
        container = AdminMenuMainContainer(user_data, userRank, transactions)
        await inter.response.send_message(view=InfoMainView(container), ephemeral=True)

    @app_commands.command(name="calculate", description="관리자 전용 명령어입니다.")
    async def calculate(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 권한 부족",
                    description="관리자만 사용할 수 있는 명령어입니다.",
                    color=0xe74c3c
                ), ephemeral=True
            )
            return
        await interaction.response.send_modal(ManagementModal(self.bot, interaction.user.id))

    @app_commands.command(name="거래내역", description="관리자 전용 명령어입니다.")
    @app_commands.describe(
        start_date="시작 날짜 (20250807, 2025-08-07 등) - 기본값: 7일 전",
        end_date="종료 날짜 (20250807, 2025-08-07 등) - 기본값: 오늘"
    )
    async def recentTransactions(self, interaction: discord.Interaction, start_date: str | None = None, end_date: str | None = None):
        if not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 권한 부족",
                    description="관리자만 사용할 수 있는 명령어입니다.",
                    color=0xe74c3c
                ), ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)

        # 날짜 범위 처리 - 기본값: 7일 전부터 오늘까지
        date_range: DateRange | None = None
        if start_date is None and end_date is None:
            # 기본값: 오늘부터 7일 전까지
            today = datetime.datetime.now()
            seven_days_ago = today - datetime.timedelta(days=7)
            
            date_range = {
                "start": seven_days_ago.strftime("%Y-%m-%d"),
                "end": today.strftime("%Y-%m-%d")
            }
        elif start_date and end_date:
            try:
                # 날짜 형식 검증 및 변환
                formatted_start = parse_date_to_string(start_date)
                formatted_end = parse_date_to_string(end_date)
                
                date_range = {
                    "start": formatted_start,
                    "end": formatted_end
                }
            except ValueError as e:
                print("날짜 파싱 오류:", e)
                return await interaction.followup.send(
                    f"❌ {str(e)}\n\n"
                    f"**지원하는 날짜 형식:**\n"
                    f"• `20250807` (YYYYMMDD)\n"
                    f"• `2025-08-07` (YYYY-MM-DD)\n"
                    f"• `2025.08.07` (YYYY.MM.DD)\n"
                    f"• `2025/08/07` (YYYY/MM/DD)",
                    ephemeral=True
                )
        elif start_date or end_date:
            return await interaction.followup.send(
                "❌ 시작 날짜와 종료 날짜를 모두 입력해주세요.",
                ephemeral=True
            )

        client = NHChargeClient(AUTO_CHARGE_API_KEY)
        account: AccountInfo = {
            "number": CHARGE_BANK_NUMBER,
            "bankCode": CHARGE_BANK_CODE
        }
        creds: BankCredentials = {
            "id": NH_LOGIN_ID,
            "password": NH_LOGIN_PW
        }

        result = await client.fetchRecentTransactions(account, creds, date_range)
        await client.client.aclose()

        if not result["success"]:
            return await interaction.followup.send(
                f"❌ 거래내역 조회 실패: {result['message']}",
                ephemeral=True
            )

        data = result["data"]
        txs = data["transactions"]
        if not txs:
            return await interaction.followup.send(
                "해당 기간에 거래 내역이 없습니다.",
                ephemeral=True
            )

        # 제목에 날짜 범위 정보 추가
        title = "최근 거래 내역"
        if date_range:
            title += f" ({date_range['start']} ~ {date_range['end']})"
        
        embed = discord.Embed(
            title=title,
            color=0x00ff00,
            description=f"**총 {data['totalCount']}건의 거래**"
        )
        
        # 계좌 정보 추가
        embed.add_field(
            name="📊 조회 정보",
            value=(
                f"**은행:** {data['account']['bankCode']}\n"
                f"**계좌번호:** {data['account']['number']}\n"
                f"**조회 범위:** {data['range']['start']} ~ {data['range']['end']}"
            ),
            inline=False
        )

        # JSON 파일 생성을 위한 상세 데이터
        json_data = {
            "query_info": {
                "start_date": date_range['start'] if date_range else "N/A",
                "end_date": date_range['end'] if date_range else "N/A",
                "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_count": data['totalCount']
            },
            "account_info": {
                "bank_code": data['account']['bankCode'],
                "account_number": data['account']['number']
            },
            "query_range": {
                "start": data['range']['start'],
                "end": data['range']['end']
            },
            "transactions": []
        }

        # 모든 거래 내역을 JSON에 추가
        for tx in txs:
            transaction_detail = {
                "id": tx['id'],
                "type": tx['type'],
                "name": tx['name'],
                "amount": tx['amount'],
                "date": tx['date'],
                "date_formatted": datetime.datetime.fromtimestamp(round(tx["date"]/ 1000)).strftime("%Y-%m-%d %H:%M:%S")
            }
            json_data["transactions"].append(transaction_detail)

        # 거래 내역이 많을 경우 요약 처리
        MAX_TRANSACTIONS = 10  # 최대 표시 건수
        
        if len(txs) > MAX_TRANSACTIONS:
            # 요약 통계 추가
            total_deposits = sum(tx['amount'] for tx in txs if tx['type'] == '입금')
            total_withdrawals = sum(tx['amount'] for tx in txs if tx['type'] == '출금')
            deposit_count = len([tx for tx in txs if tx['type'] == '입금'])
            withdrawal_count = len([tx for tx in txs if tx['type'] == '출금'])
            
            # JSON에 요약 통계 추가
            json_data["summary"] = {
                "total_deposits": total_deposits,
                "total_withdrawals": total_withdrawals,
                "deposit_count": deposit_count,
                "withdrawal_count": withdrawal_count,
                "net_deposit": total_deposits - total_withdrawals
            }
            
            embed.add_field(
                name="📈 거래 요약",
                value=(
                    f"**총 입금:** {total_deposits:,}원 ({deposit_count}건)\n"
                    f"**총 출금:** {total_withdrawals:,}원 ({withdrawal_count}건)\n"
                    f"**순 입금:** {(total_deposits - total_withdrawals):,}원"
                ),
                inline=False
            )
            
            # 최근 거래만 표시
            recent_txs = txs[:MAX_TRANSACTIONS]
            embed.add_field(
                name=f"🕒 최근 {MAX_TRANSACTIONS}건 상세 내역",
                value=f"전체 {len(txs)}건 중 최근 {len(recent_txs)}건만 표시됩니다.",
                inline=False
            )
        else:
            recent_txs = txs
        
        for tx in recent_txs:
            when = datetime.datetime.fromtimestamp(round(tx["date"]/ 1000)).strftime("%Y-%m-%d %H:%M:%S")
            embed.add_field(
                name=f"{tx['type']}  {tx['amount']:,}원",
                value=(
                    f"거래종류: {tx['type']}\n"
                    f"입금자명: {tx['name']}\n"
                    f"거래일시: {when}\n"
                    f"거래금액: {tx['amount']:,}원\n"
                    f"txId: `{tx['id']}`"
                ),
                inline=False
            )

        # JSON 파일 생성
        filename = f"transactions_{date_range['start']}_{date_range['end']}.json" if date_range else f"transactions_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        file = None
        
        try:
            # 메모리에서 JSON 데이터를 바이트 스트림으로 변환
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            json_bytes = json_str.encode('utf-8')
            json_buffer = io.BytesIO(json_bytes)
            
            # Discord 파일 객체 생성
            file = discord.File(json_buffer, filename=filename)
            
        except Exception as file_error:
            print(f"JSON 파일 생성 오류: {file_error}")

        # 거래가 많을 때 안내 메시지
        if len(txs) > MAX_TRANSACTIONS:
            embed.set_footer(text=f"💡 전체 내역을 보려면 더 짧은 기간으로 조회해주세요. (총 {len(txs)}건)\n📄 모든 거래 내역이 JSON 파일에 포함되어 있습니다.")
        else:
            embed.set_footer(text="모든 거래 내역이 표시되었습니다.\n📄 상세 내역이 JSON 파일에 포함되어 있습니다.")

        # JSON 파일 첨부 정보 추가
        if file:
            embed.add_field(
                name="📄 상세 보고서",
                value=f"모든 거래 내역의 상세 정보가 `{filename}` 파일에 저장되었습니다.",
                inline=False
            )

        # 메시지 전송 (파일 첨부 포함)
        if file:
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="statistics", description="관리자 전용 명령어입니다.")
    @app_commands.describe(
        start_date="시작 날짜 (20250807, 2025-08-07 등)", 
        end_date="종료 날짜 (20250807, 2025-08-07 등)"
    )
    async def statistics(self, interaction: discord.Interaction, start_date: str | None = None, end_date: str | None = None):
        if not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 권한 부족",
                    description="관리자만 사용할 수 있는 명령어입니다.",
                    color=0xe74c3c
                ), ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)

        try:
            # 날짜 파싱 (기본값: 오늘)
            if start_date:
                start_dt = parse_date(start_date)
            else:
                start_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if end_date:
                end_dt = parse_date(end_date).replace(hour=23, minute=59, second=59)
            else:
                end_dt = datetime.datetime.now().replace(hour=23, minute=59, second=59)

            # 바이낸스 API를 위한 타임스탬프 변환
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)

            # 데이터베이스에서 통계 조회
            from modules.database import Database
            db_stats = await Database.get_statistics_by_date_range(start_dt, end_dt)

            # 실제 계좌 거래내역에서 총 충전 금액 조회
            client = NHChargeClient(AUTO_CHARGE_API_KEY)
            account: AccountInfo = {
                "number": CHARGE_BANK_NUMBER,
                "bankCode": CHARGE_BANK_CODE
            }
            creds: BankCredentials = {
                "id": NH_LOGIN_ID,
                "password": NH_LOGIN_PW
            }
            
            # 날짜 범위 설정
            date_range: DateRange = {
                "start": start_dt.strftime("%Y-%m-%d"),
                "end": end_dt.strftime("%Y-%m-%d")
            }
            
            # 실제 계좌 거래내역 조회
            bank_result = await client.fetchRecentTransactions(account, creds, date_range)
            await client.client.aclose()
            
            actual_deposit_total = 0
            actual_deposit_count = 0
            if bank_result["success"]:
                for tx in bank_result["data"]["transactions"]:
                    if tx["type"] == "입금":
                        actual_deposit_total += tx["amount"]
                        actual_deposit_count += 1

            # 바이낸스 PNL 조회
            from modules.binance import Binance
            async with Binance() as binance:
                pnl_data = await binance.get_pnl_by_date_range(start_timestamp, end_timestamp)

            # Embed 생성
            embed = discord.Embed(
                title="📊 통계 정보",
                description=f"**기간:** {start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}",
                color=0x00ff00,
                timestamp=datetime.datetime.now()
            )

            # 바이낸스 PNL 정보 (간소화)
            pnl_field = (
                f"**총 PNL:** {pnl_data['total_pnl_krw']:,}원\n"
                f"**현재 포트폴리오:** {pnl_data['current_portfolio_krw']:,}원"
            )
            if 'error' in pnl_data:
                pnl_field += f"\n⚠️ **오류:** {pnl_data['error']}"
            
            embed.add_field(name="🔸 바이낸스 포트폴리오 PNL", value=pnl_field, inline=False)

            # KRW 충전 현황 (DB + 실제 계좌)
            charge_field = (
                f"**실제 계좌 입금:** {actual_deposit_total:,}원 ({actual_deposit_count:,}회)\n"
                f"**DB상 계좌 입금:** {db_stats['total_charge_amount']:,}원 ({db_stats['charge_count']:,}회)"
            )
            
            embed.add_field(name="💰 KRW 충전 현황", value=charge_field, inline=True)

            # DB상 암호화폐 출금 통계 (사용자가 KRW로 구매한 암호화폐 출금)
            transaction_field = (
                f"**총 출금액 (KRW 기준):** {db_stats['total_transaction_amount']:,}원\n"
                f"**예상 수수료 수익:** {db_stats['total_revenue']:,}원\n"
                f"**출금 건수:** {db_stats['transaction_count']:,}회"
            )
            
            embed.add_field(name="🪙 DB상 암호화폐 출금", value=transaction_field, inline=True)

            # 자금 흐름 요약
            detection_field = (
                f"**실제 계좌 충전 총액:** {actual_deposit_total:,}원\n"
                f"**바이낸스 출금 총액:** {db_stats['total_transaction_amount']:,}원\n"
                f"**예상 수수료 수익:** {db_stats['total_revenue']:,}원"
            )

            embed.add_field(name="📊 자금 흐름 요약", value=detection_field, inline=False)

            # # 암호화폐별 거래 상세
            # if db_stats['crypto_stats']:
            #     crypto_details = []
            #     for symbol, stats in list(db_stats['crypto_stats'].items())[:5]:  # 상위 5개만 표시
            #         crypto_details.append(
            #             f"**{symbol}:** {stats['count']:,}회 | {stats['total_krw']:,}원 | 수수료: {stats['revenue']:,}원"
            #         )
                
            #     crypto_field = "\n".join(crypto_details)
            #     if len(db_stats['crypto_stats']) > 5:
            #         crypto_field += f"\n... 외 {len(db_stats['crypto_stats']) - 5}개"
                
            #     embed.add_field(name="📈 암호화폐별 거래량 (상위 5개)", value=crypto_field, inline=False)

            # 종합 수익성 분석
            bot_revenue = db_stats['total_revenue']
            convert_fees = pnl_data['total_convert_fees_krw']
            
            # 실제 수익 계산: 충전액 - 출금액 = 수수료 수익
            actual_revenue = actual_deposit_total - db_stats['total_transaction_amount']

            summary_field = (
                f"**예상 수수료 총액:** {bot_revenue:,}원\n"
                f"**실제 수수료 수익:** {actual_revenue:,}원\n"
                f"**바이낸스 컨버트 수수료:** {convert_fees:,}원\n"
                f"**순수익:** {actual_revenue:,}원"
            )

            # 수익률 계산 (실제 입금 기준)
            if actual_deposit_total > 0:
                actual_roi = ((actual_revenue / actual_deposit_total) * 100)
                summary_field += f"\n**수익률:** {actual_roi:.2f}%"
            
            embed.add_field(name="📊 종합 수익성", value=summary_field, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            print("오류 발생:", e)
            error_msg = str(e)
            await interaction.followup.send(
                f"❌ {error_msg}\n\n"
                f"**지원하는 날짜 형식:**\n"
                f"• `20250807` (YYYYMMDD)\n"
                f"• `2025-08-07` (YYYY-MM-DD)\n"
                f"• `2025.08.07` (YYYY.MM.DD)\n"
                f"• `2025/08/07` (YYYY/MM/DD)",
                ephemeral=True
            )
        except Exception as e:
            print("Unexpected error in statistics command:", e)
            tb = traceback.format_exc()
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=f"Unexpected error in statistics command: {str(e)}\n\n{tb}",
                level="ERROR",
                webhook_url=ERROR_LOG_WEBHOOK
            )
            await interaction.followup.send(
                f"❌ 통계 조회 중 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="getsus", description="관리자 전용 명령어입니다.")
    @app_commands.describe(
        start_date="시작 날짜 (20250807, 2025-08-07 등)", 
        end_date="종료 날짜 (20250807, 2025-08-07 등)"
    )
    async def getsus(self, interaction: discord.Interaction, start_date: str | None = None, end_date: str | None = None):
        if not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 권한 부족",
                    description="관리자만 사용할 수 있는 명령어입니다.",
                    color=0xe74c3c
                ), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # 날짜 파싱 (기본값: 오늘)
            if start_date:
                start_dt = parse_date(start_date)
            else:
                start_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if end_date:
                end_dt = parse_date(end_date).replace(hour=23, minute=59, second=59)
            else:
                end_dt = datetime.datetime.now().replace(hour=23, minute=59, second=59)

            # 바이낸스 API를 위한 타임스탬프 변환
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)

            # 바이낸스에서 출금 내역 조회
            from modules.binance import Binance
            async with Binance() as binance:
                withdrawal_result = await binance.get_withdrawals(start_timestamp, end_timestamp)

            if not withdrawal_result["success"]:
                return await interaction.followup.send(
                    f"❌ 바이낸스 출금 내역 조회 실패: {withdrawal_result['error']}",
                    ephemeral=True
                )

            all_withdrawals = withdrawal_result["data"]

            # 성공한 출금만 필터링 (status=6)하고 날짜 범위에 맞는 출금만 필터링
            binance_withdrawals = []
            for withdrawal in all_withdrawals:
                # 먼저 성공한 출금인지 확인
                if not is_successful_withdrawal(withdrawal):
                    continue
                    
                # 날짜 범위 확인
                timestamp = parse_binance_apply_time(withdrawal)
                if start_timestamp <= timestamp <= end_timestamp:
                    binance_withdrawals.append(withdrawal)

            # 바이낸스 출금 내역을 시간순(오래된 순)으로 정렬
            binance_withdrawals.sort(key=parse_binance_apply_time)
            
            if binance_withdrawals:
                oldest_withdrawal = binance_withdrawals[0]
                newest_withdrawal = binance_withdrawals[-1]
                # 표시용 시간 변환
                oldest_time_display = format_utc_time_to_kst(oldest_withdrawal.get("applyTime", ""))
                newest_time_display = format_utc_time_to_kst(newest_withdrawal.get("applyTime", ""))
            else:
                oldest_time_display = "N/A"
                newest_time_display = "N/A"

            # DB에서 해당 기간의 CryptoTransaction 조회
            from modules.database import Database
            db_transactions = await Database.get_crypto_transactions_by_date_range(start_dt, end_dt)

            # DB에 기록된 withdrawalId 목록 생성
            db_withdrawal_ids = set()
            for tx in db_transactions:
                if tx.binanceWithdrawalId:
                    db_withdrawal_ids.add(str(tx.binanceWithdrawalId))

            # 의심스러운 출금 찾기 (바이낸스에는 있지만 DB에는 없는 출금)
            suspicious_withdrawals = []
            total_suspicious_amount = 0.0

            for withdrawal in binance_withdrawals:
                withdrawal_id = str(withdrawal.get("id", ""))
                
                # 이미 성공한 출금만 필터링되었으므로 여기서는 DB 확인만
                if withdrawal_id not in db_withdrawal_ids:
                    suspicious_withdrawals.append(withdrawal)
                    
                    # 의심스러운 출금 금액 합계 (USD 기준으로 계산)
                    try:
                        amount = float(withdrawal.get("amount", 0))
                        coin = withdrawal.get("coin", "")
                        
                        try:
                            async with Binance() as binance_price:
                                if coin == "USDT":
                                    total_suspicious_amount += amount
                                else:
                                    price_info = await binance_price.get_price(coin)
                                    total_suspicious_amount += amount * price_info["USD"]
                        except:
                            pass  # 가격 조회 실패시 스킵
                    except (ValueError, TypeError):
                        pass  # amount 변환 실패시 스킵

            # 결과 출력
            embed = discord.Embed(
                title="🚨 의심스러운 출금 내역",
                # oldest_time_display ~ newest_time_display (한국 시간으로 표시)
                description=f"**조회 기간:** {oldest_time_display} ~ {newest_time_display}",
                color=0xff0000 if suspicious_withdrawals else 0x00ff00,
                timestamp=datetime.datetime.now()
            )

            # 통계 정보
            embed.add_field(
                name="📊 조회 결과",
                value=(
                    f"**바이낸스 총 출금:** {len(binance_withdrawals)}건\n"
                    f"**DB 기록된 출금:** {len(db_transactions)}건\n"
                    f"**의심스러운 출금:** {len(suspicious_withdrawals)}건"
                ),
                inline=False
            )

            if suspicious_withdrawals:
                # 의심스러운 출금 금액 정보
                from modules.kebhana import get_usd_price
                usd_rate = await get_usd_price()
                total_suspicious_krw = int(total_suspicious_amount * usd_rate)
                
                embed.add_field(
                    name="💰 의심스러운 출금 총액",
                    value=f"**${total_suspicious_amount:.2f}** (약 {total_suspicious_krw:,}원)",
                    inline=False
                )

                # JSON 파일 생성을 위한 상세 정보 수집
                json_data = {
                    "query_info": {
                        "start_date": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        "end_date": end_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "usd_krw_rate": usd_rate
                    },
                    "summary": {
                        "total_binance_withdrawals": len(binance_withdrawals),
                        "total_db_transactions": len(db_transactions),
                        "suspicious_withdrawals_count": len(suspicious_withdrawals),
                        "total_suspicious_amount_usd": round(total_suspicious_amount, 6),
                        "total_suspicious_amount_krw": total_suspicious_krw
                    },
                    "suspicious_withdrawals": [],
                    "all_binance_withdrawals": [],
                    "db_withdrawal_ids": list(db_withdrawal_ids)
                }

                # 의심스러운 출금 상세 정보
                for withdrawal in suspicious_withdrawals:
                    try:
                        withdrawal_detail = {
                            "id": str(withdrawal.get("id", "")),
                            "coin": withdrawal.get("coin", ""),
                            "amount": float(withdrawal.get("amount", 0)),
                            "address": withdrawal.get("address", ""),
                            "network": withdrawal.get("network", ""),
                            "transactionFee": float(withdrawal.get("transactionFee", 0)),
                            "status": withdrawal.get("status", 0),
                            "applyTime": withdrawal.get("applyTime", ""),  # UTC time
                            "txId": withdrawal.get("txId", ""),
                            "transferType": withdrawal.get("transferType", 0),  # 1 for internal, 0 for external
                            "confirmNo": withdrawal.get("confirmNo", 0),
                            "walletType": withdrawal.get("walletType", 1),  # 1: Funding Wallet, 0: Spot Wallet
                            "txKey": withdrawal.get("txKey", "")
                        }
                        
                        # 선택적 필드들 (존재할 때만 추가)
                        if "withdrawOrderId" in withdrawal:
                            withdrawal_detail["withdrawOrderId"] = withdrawal.get("withdrawOrderId", "")
                        
                        if "info" in withdrawal:
                            withdrawal_detail["info"] = withdrawal.get("info", "")
                        
                        # completeTime은 성공한 출금(status=6)에만 존재
                        if withdrawal.get("status", 0) == 6 and "completeTime" in withdrawal:
                            withdrawal_detail["completeTime"] = withdrawal.get("completeTime", "")
                            
                    except (ValueError, TypeError) as e:
                        print(f"출금 데이터 파싱 오류: {e}")
                        # 기본값으로 처리
                        withdrawal_detail = {
                            "id": str(withdrawal.get("id", "")),
                            "coin": withdrawal.get("coin", ""),
                            "amount": 0.0,
                            "address": withdrawal.get("address", ""),
                            "network": withdrawal.get("network", ""),
                            "transactionFee": 0.0,
                            "status": withdrawal.get("status", 0),
                            "applyTime": withdrawal.get("applyTime", ""),
                            "txId": withdrawal.get("txId", ""),
                            "transferType": withdrawal.get("transferType", 0),
                            "confirmNo": withdrawal.get("confirmNo", 0),
                            "walletType": withdrawal.get("walletType", 1),
                            "txKey": withdrawal.get("txKey", "")
                        }
                        
                        # 선택적 필드들
                        if "withdrawOrderId" in withdrawal:
                            withdrawal_detail["withdrawOrderId"] = withdrawal.get("withdrawOrderId", "")
                        if "info" in withdrawal:
                            withdrawal_detail["info"] = withdrawal.get("info", "")
                        if withdrawal.get("status", 0) == 6 and "completeTime" in withdrawal:
                            withdrawal_detail["completeTime"] = withdrawal.get("completeTime", "")
                    
                    # applyTime과 completeTime 시간 변환 처리
                    if withdrawal_detail["applyTime"]:
                        try:
                            # "YYYY-MM-DD HH:MM:SS" 형식을 UTC 타임스탬프로 변환
                            apply_dt = datetime.datetime.strptime(withdrawal_detail["applyTime"], "%Y-%m-%d %H:%M:%S")
                            apply_dt = apply_dt.replace(tzinfo=datetime.timezone.utc)
                            withdrawal_detail["applyTime_timestamp"] = int(apply_dt.timestamp() * 1000)
                            # 한국 시간으로 변환하여 표시용 추가
                            kst_dt = apply_dt.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                            withdrawal_detail["applyTime_kst"] = kst_dt.strftime("%Y-%m-%d %H:%M:%S KST")
                        except (ValueError, TypeError):
                            withdrawal_detail["applyTime_timestamp"] = 0
                            withdrawal_detail["applyTime_kst"] = withdrawal_detail["applyTime"]
                    
                    # completeTime은 성공한 출금에만 존재
                    if "completeTime" in withdrawal_detail and withdrawal_detail["completeTime"]:
                        try:
                            complete_dt = datetime.datetime.strptime(withdrawal_detail["completeTime"], "%Y-%m-%d %H:%M:%S")
                            complete_dt = complete_dt.replace(tzinfo=datetime.timezone.utc)
                            withdrawal_detail["completeTime_timestamp"] = int(complete_dt.timestamp() * 1000)
                            # 한국 시간으로 변환하여 표시용 추가
                            kst_dt = complete_dt.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                            withdrawal_detail["completeTime_kst"] = kst_dt.strftime("%Y-%m-%d %H:%M:%S KST")
                        except (ValueError, TypeError):
                            withdrawal_detail["completeTime_timestamp"] = 0
                            withdrawal_detail["completeTime_kst"] = withdrawal_detail["completeTime"]
                    
                    # USD 값 계산
                    try:
                        async with Binance() as binance_price:
                            if withdrawal_detail["coin"] == "USDT":
                                withdrawal_detail["amount_usd"] = withdrawal_detail["amount"]
                            else:
                                price_info = await binance_price.get_price(withdrawal_detail["coin"])
                                withdrawal_detail["amount_usd"] = withdrawal_detail["amount"] * price_info["USD"]
                                withdrawal_detail["price_per_coin_usd"] = price_info["USD"]
                    except:
                        withdrawal_detail["amount_usd"] = 0
                        withdrawal_detail["price_per_coin_usd"] = 0
                    
                    withdrawal_detail["amount_krw"] = int(withdrawal_detail["amount_usd"] * usd_rate)
                    
                    json_data["suspicious_withdrawals"].append(withdrawal_detail)

                # 의심스러운 출금을 시간순(오래된 순)으로 정렬
                suspicious_withdrawals.sort(key=lambda x: parse_binance_apply_time(x))

                # 모든 바이낸스 출금 내역 (참고용)
                for withdrawal in binance_withdrawals:
                    try:
                        withdrawal_summary = {
                            "id": str(withdrawal.get("id", "")),
                            "coin": withdrawal.get("coin", ""),
                            "amount": float(withdrawal.get("amount", 0)),
                            "address": withdrawal.get("address", ""),
                            "network": withdrawal.get("network", ""),
                            "status": withdrawal.get("status", 0),
                            "applyTime": withdrawal.get("applyTime", ""),  # 이미 문자열 형식
                            "is_suspicious": str(withdrawal.get("id", "")) not in db_withdrawal_ids
                        }
                    except (ValueError, TypeError):
                        withdrawal_summary = {
                            "id": str(withdrawal.get("id", "")),
                            "coin": withdrawal.get("coin", ""),
                            "amount": 0.0,
                            "address": withdrawal.get("address", ""),
                            "network": withdrawal.get("network", ""),
                            "status": withdrawal.get("status", 0),
                            "applyTime": withdrawal.get("applyTime", ""),
                            "is_suspicious": str(withdrawal.get("id", "")) not in db_withdrawal_ids
                        }
                    
                    # applyTime은 이미 문자열 형식이므로 그대로 저장
                    # 필요시 타임스탬프 변환 추가
                    if withdrawal_summary["applyTime"]:
                        try:
                            apply_dt = datetime.datetime.strptime(withdrawal_summary["applyTime"], "%Y-%m-%d %H:%M:%S")
                            apply_dt = apply_dt.replace(tzinfo=datetime.timezone.utc)
                            withdrawal_summary["applyTime_timestamp"] = int(apply_dt.timestamp() * 1000)
                            # 한국 시간으로 변환하여 표시용 추가
                            kst_dt = apply_dt.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                            withdrawal_summary["applyTime_kst"] = kst_dt.strftime("%Y-%m-%d %H:%M:%S KST")
                        except (ValueError, TypeError):
                            withdrawal_summary["applyTime_timestamp"] = 0
                            withdrawal_summary["applyTime_kst"] = withdrawal_summary["applyTime"]
                    
                    json_data["all_binance_withdrawals"].append(withdrawal_summary)

                # JSON 파일로 저장
                filename = f"suspicious_withdrawals_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.json"
                
                try:
                    # 메모리에서 JSON 데이터를 바이트 스트림으로 변환
                    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                    json_bytes = json_str.encode('utf-8')
                    json_buffer = io.BytesIO(json_bytes)
                    
                    # Discord 파일 객체 생성 (임시 파일 없이)
                    file = discord.File(json_buffer, filename=filename)
                    
                    embed.add_field(
                        name="📄 상세 보고서",
                        value=f"의심스러운 출금의 모든 상세 정보가 `{filename}` 파일에 저장되었습니다.",
                        inline=False
                    )
                    
                except Exception as file_error:
                    print(f"JSON 파일 생성 오류: {file_error}")
                    embed.add_field(
                        name="⚠️ 파일 생성 오류",
                        value="상세 보고서 파일 생성에 실패했습니다.",
                        inline=False
                    )
                    file = None

                # 개별 의심스러운 출금 상세 (최대 10개만 표시)
                MAX_SHOW = 10
                show_withdrawals = suspicious_withdrawals[:MAX_SHOW]
                
                for i, withdrawal in enumerate(show_withdrawals, 1):
                    withdrawal_id = withdrawal.get("id", "N/A")
                    coin = withdrawal.get("coin", "N/A")
                    try:
                        amount = float(withdrawal.get("amount", 0))
                    except (ValueError, TypeError):
                        amount = 0.0
                    
                    address = withdrawal.get("address", "N/A")
                    network = withdrawal.get("network", "N/A")
                    
                    try:
                        tx_fee = float(withdrawal.get("transactionFee", 0))
                    except (ValueError, TypeError):
                        tx_fee = 0.0
                    
                    apply_time_str = format_utc_time_to_kst(withdrawal.get("applyTime", ""))  # 한국 시간으로 변환
                    tx_id = withdrawal.get("txId", "N/A")
                    transfer_type = "내부" if withdrawal.get("transferType", 0) == 1 else "외부"
                    wallet_type = "펀딩 지갑" if withdrawal.get("walletType", 1) == 1 else "현물 지갑"
                    
                    # status=6(성공)이지만 info에 내용이 있는 경우 - 경고성 메시지로 표시
                    info_msg = withdrawal.get("info", "")
                    status_info = ""
                    if info_msg and info_msg.strip():  # 빈 문자열이 아닌 경우만
                        status_info = f"\n⚠️ **경고:** {info_msg}"

                    embed.add_field(
                        name=f"🚨 의심스러운 출금 #{i}",
                        value=(
                            f"**ID:** `{withdrawal_id}`\n"
                            f"**코인:** {coin} ({network})\n"
                            f"**수량:** {amount}\n"
                            f"**주소:** `{address[:20]}...`\n"
                            f"**TxID:** `{tx_id[:20]}...`\n"
                            f"**수수료:** {tx_fee}\n"
                            f"**시간:** {apply_time_str}\n"
                            f"**전송 유형:** {transfer_type} | **지갑:** {wallet_type}{status_info}"
                        ),
                        inline=True
                    )

                if len(suspicious_withdrawals) > MAX_SHOW:
                    embed.add_field(
                        name="⚠️ 추가 정보",
                        value=f"총 {len(suspicious_withdrawals)}건 중 {MAX_SHOW}건만 표시됩니다.\n전체 내역은 첨부된 JSON 파일을 확인하세요.",
                        inline=False
                    )

                embed.set_footer(text="⚠️ 이 출금들은 DB에 기록되지 않은 의심스러운 거래입니다.")
                
                # 메시지 전송 (파일 첨부 포함)
                if file:
                    await interaction.followup.send(embed=embed, file=file, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed.add_field(
                    name="✅ 결과",
                    value="해당 기간에 의심스러운 출금이 발견되지 않았습니다.\n모든 바이낸스 출금이 DB에 정상적으로 기록되어 있습니다.",
                    inline=False
                )
                embed.set_footer(text="✅ 모든 출금이 정상적으로 처리되었습니다.")
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print("오류 발생:", e)
            error_msg = str(e)
            await interaction.followup.send(
                f"❌ {error_msg}\n\n"
                f"**지원하는 날짜 형식:**\n"
                f"• `20250807` (YYYYMMDD)\n"
                f"• `2025-08-07` (YYYY-MM-DD)\n"
                f"• `2025.08.07` (YYYY.MM.DD)\n"
                f"• `2025/08/07` (YYYY/MM/DD)",
                ephemeral=True
            )
            return

async def setup(bot: CryptoExchangeBot):
    await bot.add_cog(CommandsCog(bot))