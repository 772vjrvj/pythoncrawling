from bip_utils import (Bip39MnemonicGenerator, Bip39MnemonicValidator,
                       Bip39SeedGenerator, Bip39WordsNum, Bip44, Bip44Changes,
                       Bip44Coins)

# --- 니모닉 / 시드 기본 ---

def generate_mnemonic(words_num: Bip39WordsNum = Bip39WordsNum.WORDS_NUM_12) -> str:
    """
    BIP-39 니모닉 생성 (기본 12단어).
    """
    return str(Bip39MnemonicGenerator().FromWordsNumber(words_num))


def validate_mnemonic(mnemonic: str) -> bool:
    """
    니모닉이 유효한지 검증. (체크섬 등 포함)
    """
    try:
        Bip39MnemonicValidator().Validate(mnemonic)
        return True
    except Exception:
        return False


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """
    니모닉 + (선택적) 패스프레이즈로부터 BIP-39 시드(64바이트) 생성.
    """
    if not validate_mnemonic(mnemonic):
        raise ValueError("Invalid mnemonic phrase.")
    return Bip39SeedGenerator(mnemonic).Generate(passphrase)


# --- BIP44 기반 파생 ---

def _change_enum_from_int(change: int) -> Bip44Changes:
    """
    0 -> external (CHAIN_EXT), 1 -> internal (CHAIN_INT)
    """
    if change == 0:
        return Bip44Changes.CHAIN_EXT
    elif change == 1:
        return Bip44Changes.CHAIN_INT
    else:
        raise ValueError("Change must be 0 (external) or 1 (internal).")


def derive_bip44_private_key(
    mnemonic: str,
    coin: Bip44Coins,
    account: int = 0,
    change: int = 0,
    address_index: int = 0,
    passphrase: str = "",
) -> bytes:
    """
    주어진 BIP-39 니모닉에서 BIP-44 규칙에 따라 특정 코인의 private key raw bytes 파생.

    :param mnemonic: BIP-39 니모닉 문구
    :param coin: bip_utils.Bip44Coins enum (예: Bip44Coins.SOLANA, Bip44Coins.ETHEREUM, Bip44Coins.BITCOIN)
    :param account: 계정 인덱스 (hardened)
    :param change: change 값 (0=external, 1=internal)
    :param address_index: 주소 인덱스
    :param passphrase: optional BIP-39 패스프레이즈
    :return: 파생된 private key raw bytes (코인/곡선에 따라 의미가 다름)
    """
    seed_bytes = mnemonic_to_seed(mnemonic, passphrase)
    bip44_ctx = Bip44.FromSeed(seed_bytes, coin)
    derived = (
        bip44_ctx
        .Purpose()              # m/44'
        .Coin()                 # /coin'
        .Account(account)       # /account'
        .Change(_change_enum_from_int(change))  # /change
        .AddressIndex(address_index)  # /address_index
    )
    # PrivateKey().Raw().ToBytes() 는 ed25519 또는 secp256k1 기준 private key material
    return derived.PrivateKey().Raw().ToBytes()