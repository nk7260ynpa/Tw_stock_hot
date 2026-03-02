"""台股綜合熱度平台主程式。"""

import logging

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/hot.log", encoding="utf-8"),
    ],
)

if __name__ == "__main__":
    uvicorn.run("tw_stock_hot.web.app:app", host="0.0.0.0", port=5050)
