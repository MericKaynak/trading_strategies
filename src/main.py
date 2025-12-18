import os
import time
import schedule
import pytz
from src.strategy import run_regression_strategy
from src.config import AMDConfig
from dotenv import load_dotenv
# Konfiguration aus Umgebungsvariablen laden

load_dotenv()
API_KEY = os.getenv("KEY")
API_SECRET = os.getenv("SECRET")

amd_settings = AMDConfig(API_KEY=API_KEY, API_SECRET=API_SECRET)

def job():
    # Wir übergeben das gesamte Pydantic-Objekt
    run_regression_strategy(amd_settings)

# Scheduling
timezone = pytz.timezone("Europe/Berlin")
schedule.every().day.at("18:00").do(job)

print(f"--- BOT GESTARTET ---")
print(f"Symbol: {amd_settings.SYMBOL}")
print(f"Hebel:  {amd_settings.LEVERAGE}")
print(f"Modus:  {'PAPER' if amd_settings.PAPER else 'LIVE'}")
print(f"Nächster Check: Täglich 18:00 CET")

# Falls du beim Starten sofort testen willst:
# job()

while True:
    schedule.run_pending()
    time.sleep(60)