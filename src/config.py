from pydantic import BaseModel
from pydantic import Field

class AMDConfig(BaseModel):
    # Pydantic sucht automatisch nach Umgebungsvariablen mit diesen Namen
    # Wenn keine gefunden werden, nutzt es die Default-Werte
    API_KEY: str
    API_SECRET: str
    PAPER: bool = True
    
    SYMBOL: str = "AMD"
    LEVERAGE: float = 2.0
    REG_WINDOW: int = 100
    BUY_DEVIATION: float = 0.14
    SELL_DEVIATION: float = 0.13
