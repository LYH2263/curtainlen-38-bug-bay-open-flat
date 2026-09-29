from typing import Optional
from pydantic import BaseModel

class BayUpdate(BaseModel):
    bay_enabled: bool
    bay_depth: Optional[float] = None
