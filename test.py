import logging
from therapists_recommender import recommend, resolve_nearest_major_city

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    logging.info("=== Starting Therapist Recommender Test ===")

    sample_text = "Tôi ở Đà Nẵng, cần trị liệu tâm lý trầm cảm, ưu tiên online."
    logging.info(f"User input: {sample_text}")

    # Phát hiện thành phố gần nhất
    city = resolve_nearest_major_city(sample_text)
    logging.info(f"Detected nearest major city: {city}")

    # Gọi recommender
    try:
        logging.info("Running recommendation engine...")
        result = recommend(sample_text, top_k=3)
        logging.info("Recommendation complete.")
    except Exception as e:
        logging.error(f"Error occurred during recommendation: {e}")
        raise

    # In kết quả
    logging.info("=== Results ===")
    for i, provider in enumerate(result.get("results", []), 1):
        name = provider.get("name", "Unknown")
        address = provider.get("address", "No address")
        rating = provider.get("rating", "?")
        logging.info(f"{i}. {name} | {address} | Rating: {rating}")

    logging.info("Test finished successfully.")