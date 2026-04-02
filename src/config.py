from pydantic import BaseModel


class AMDConfig(BaseModel):
    """Konfiguration für AMD."""
    API_KEY: str
    API_SECRET: str
    SYMBOL: str = "AMD"
    LEVERAGE: float = 3.0
    REG_WINDOW: int = 100
    BUY_DEVIATION: float = 0.14
    SELL_DEVIATION: float = 0.14
    STOP_LOSS: float = 0.20
    STOP_LOSS_ACTIVE: bool = True


class MUConfig(BaseModel):
    """Konfiguration für MU."""
    API_KEY: str
    API_SECRET: str
    SYMBOL: str = "MU"
    LEVERAGE: float = 3.0
    REG_WINDOW: int = 100
    BUY_DEVIATION: float = 0.08
    SELL_DEVIATION: float = 0.08
    STOP_LOSS: float = 0.10
    STOP_LOSS_ACTIVE: bool = True
