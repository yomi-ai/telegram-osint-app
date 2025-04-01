from pydantic_settings import BaseSettings
from src.utils.channel_encoder import decode_channel
from src.providers.telegram.channel_constants import (
    HEBRON_OUTPUT_CHANNEL_ENCODED,
    ETZION_OUTPUT_CHANNEL_ENCODED,
)


class TelegramSettings(BaseSettings):
    SESSION_NAME: str = "session_name"
    FETCH_LIMIT: int = 1000
    MESSAGE_FILTER_INTERVAL_MINUTES: int = 10


# Hebron configuration
HEBRON_CHANNELS = [
    "From_hebron",
    "HebMix",
    "HebronNewss",
    "abn_alkhalil",
    "khalelnews",
    "baninaem24",
    "baninaeim22",
    "dahriyah3",
    "DuraCity",
    "doura2000",
    "alsamou_alhadth",
    "Alsamo3News",
    "bietommar",
    "S3EERR",
    "saeare",
]

HEBRON_KEYWORDS = [
    "الظاهرية",
    "دورا",
    "الخليل",
    "حلحول",
    "يطا",
    "مجالس محلية",
    "إذنا",
    "السموع",
    "بيت عوا",
    "بيت أولا",
    "بيت أمر",
    "بني نعيم",
    "دير سامت",
    "خاراس",
    "نوبا",
    "سعير",
    "صوريف",
    "تفوح",
    "ترقوميا",
    "الدوّارة",
    "الطبقة",
    "البقعة",
    "البرج",
    "الحيلة",
    "الكوم",
    "قيلة",
    "أمريش",
    "الريحية",
    "الشيوخ",
    "بيت الروش الفوقا",
    "بيت كاحل",
    "بيت عمرة",
    "بيت عنون",
    "جبع",
    "دير العسل الفوقا",
    "خلة المية",
    "حدب الفوار",
    "حوريس",
    "خربة السيميا",
    "خربة العدسية",
    "خربة كرمة",
    "خربة صفا",
    "خرسا",
    "كريسة الشرقية",
    "قلقاس",
    "رابود",
    "الرماضين",
    "شيوخ العروب",
    "العروب",
    "الفوار",
]

# Etzion configuration
ETZION_CHANNELS = [
    "tuqualhadath",
    "tequa7",
    "Teqoua_Now",
    "bethlahem_alhadath",
    "BethlehemCommunityCh",
    "bethlehemnewss",
    "Aidacamp67",
    "KutlaBU",
    "bethlahemnow",
    "dheisheh_event19486",
    "dheisheh_Hadath",
    "dheisheh_event48",
    "dheisheh_event194867",
    "beitommar9",
    "Hebron_Beit_Ommer",
    "beitommer",
    "bietommar",
    "sgfxxc",  # Nahhalin
    "marahrabahnow",
    "ahrarsurif",
    "Aidacamp48",
    "halhul2024",
    "alawaelnewsagancy",
    "baninaeim22",
    "saeare",
    "S3EERR",
]

ETZION_KEYWORDS = [
    # City names in Arabic
    "حوسان",  # Husan
    "تقوع",  # Teqoa
    "بيت لحم",  # Bethlehem
    "الدهيشة",  # Dheisheh
    "بيت أمر",  # Beit Ummar
    "نحالين",  # Nahhalin
    "مراح رباح",  # Marah Rabah
    "صوريف",  # Surif
    "مخيم العايدة",  # Aida Camp
    "العيزرية",  # Al-Eizariya
    "بني نعيم",  # Bani Naim
    "سعير",  # Sa'ir
    "حلحول",  # Halhul
    # Additional keywords (translated to Arabic)
    "إضراب",  # Strike
    "حاجز",  # Checkpoint
    "إغلاق",  # Closure/blockade
    "حادث",  # Accident
    "مصاب",  # Injured
    "جريح",  # Wounded
    "قتيل",  # Killed
    "شهيد",  # Martyr/holy
    "شهداء",  # Martyrs/holy ones
    "عملية",  # Operation/attack
    "مستهدف",  # Targeted
    "إرهابي",  # Terrorist
    "أسير",  # Prisoner
    "الأسير",  # The prisoner
    "تحرير",  # Liberation/release
    "الله أكبر",  # Allah Akbar
    "مسيرة",  # March/procession
    "مسيرات",  # Marches/processions
    "جيش الاحتلال",  # Occupation army
    "جيش في القرية",  # Army in the village
    "وجود قوات",  # Presence of forces
    "وجود الجيش",  # Presence of army
    "هدم",  # Demolition
]

# Words to exclude from Etzion messages
ETZION_EXCLUDE_WORDS = [
    "جنين",  # Jenin
    "غزة",  # Gaza
    "لبنان",  # Lebanon
    "تركيا",  # Turkey
    "رئيس",  # President
    "ترامب",  # Trump
    "أمريكا",  # America/USA
    "إطلاق",  # Launches/firing
    "طولكرم",  # Tulkarm
    "قباطية",  # Qabatiya
    "إسرائيل",  # Israel
    "رئيس الوزراء",  # Prime Minister
]

# For backwards compatibility
CHANNELS = HEBRON_CHANNELS
KEY_WORDS = HEBRON_KEYWORDS

# Channel configuration mapping
CHANNEL_CONFIGS = {
    "hebron": {
        "input_channels": HEBRON_CHANNELS,
        "keywords": HEBRON_KEYWORDS,
        "exclude_words": [],
        "output_channel": lambda: decode_channel(HEBRON_OUTPUT_CHANNEL_ENCODED),
    },
    "etzion": {
        "input_channels": ETZION_CHANNELS,
        "keywords": ETZION_KEYWORDS,
        "exclude_words": ETZION_EXCLUDE_WORDS,
        "output_channel": lambda: decode_channel(ETZION_OUTPUT_CHANNEL_ENCODED),
    },
}
