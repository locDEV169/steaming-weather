"""WHO global solar UV index categories.

Half-open [low, high); 11 and above is extreme.
https://www.who.int/news-room/questions-and-answers/item/radiation-the-ultraviolet-(uv)-index
"""

UV_BANDS: tuple[tuple[float, str], ...] = (
    (3.0, "low"),
    (6.0, "moderate"),
    (8.0, "high"),
    (11.0, "very_high"),
)

UV_SUMMARY: dict[str, dict[str, str]] = {
    "low": {
        "level_vi": "Thấp",
        "level_en": "Low",
        "meaning_vi": "Chỉ số UV thấp, ít cần che chắn khi ở ngoài trời.",
        "meaning_en": "UV is low. Little protection is needed outdoors.",
    },
    "moderate": {
        "level_vi": "Trung bình",
        "level_en": "Moderate",
        "meaning_vi": "Nên đội mũ, bôi kem chống nắng và tìm bóng râm giữa trưa.",
        "meaning_en": "Wear a hat and sunscreen, and seek shade around midday.",
    },
    "high": {
        "level_vi": "Cao",
        "level_en": "High",
        "meaning_vi": "Hạn chế nắng giữa trưa; mũ, kính và kem chống nắng là cần thiết.",
        "meaning_en": "Limit midday sun. A hat, sunglasses, and sunscreen are needed.",
    },
    "very_high": {
        "level_vi": "Rất cao",
        "level_en": "Very High",
        "meaning_vi": "Tránh ra nắng giữa trưa; che chắn kỹ nếu phải ở ngoài.",
        "meaning_en": "Avoid midday sun. Cover up if you must be outside.",
    },
    "extreme": {
        "level_vi": "Cực cao",
        "level_en": "Extreme",
        "meaning_vi": "Tránh ra ngoài giữa trưa; che chắn toàn bộ nếu phải ra nắng.",
        "meaning_en": "Avoid being outside at midday. Cover up fully if you must.",
    },
}
