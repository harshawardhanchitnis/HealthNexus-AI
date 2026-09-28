from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.provenance import CountryCode
from app.federation.config import MODEL_VERSION


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class RunRequest(Strict):
    rounds: int = Field(default=5, ge=1, le=10, strict=True)
    local_epochs: int = Field(default=1, ge=1, le=5, strict=True)
    seed: int = Field(default=42, ge=0, le=2**31-1, strict=True)
    policy: Literal['sample-weighted', 'balanced-country'] = 'sample-weighted'


class Metric(Strict):
    samples: int = Field(gt=0, strict=True)
    absolute_error: float = Field(ge=0)
    squared_error: float = Field(ge=0)
    target_total: float = Field(ge=0)
    mae: float = Field(ge=0)
    rmse: float = Field(ge=0)
    wape: float | None = Field(default=None, ge=0)
    normalized_mae: float = Field(ge=0)

    @model_validator(mode='after')
    def consistent(self):
        import math
        if not math.isclose(self.mae, self.absolute_error/self.samples, rel_tol=1e-6, abs_tol=1e-8):
            raise ValueError('Inconsistent MAE')
        if not math.isclose(self.rmse, math.sqrt(self.squared_error/self.samples), rel_tol=1e-6, abs_tol=1e-8):
            raise ValueError('Inconsistent RMSE')
        expected = self.absolute_error/self.target_total if self.target_total else None
        if (expected is None) != (self.wape is None) or (expected is not None and not math.isclose(expected,self.wape,rel_tol=1e-6,abs_tol=1e-8)):
            raise ValueError('Inconsistent WAPE')
        return self


class Parameter(Strict):
    shape: list[int] = Field(min_length=1, max_length=2)
    values: list[float] = Field(min_length=1, max_length=4096)
    dtype: Literal['float32'] = 'float32'


class ClientUpdate(Strict):
    country_id: CountryCode
    round: int = Field(ge=1, le=10, strict=True)
    sample_count: int = Field(gt=0, strict=True)
    model_version: str = MODEL_VERSION
    starting_checksum: str = Field(pattern='^[0-9a-f]{64}$')
    parameter_checksum: str = Field(pattern='^[0-9a-f]{64}$')
    parameters: dict[str, Parameter]
    parameter_count: int = Field(gt=0, strict=True)
    parameter_bytes: int = Field(gt=0, strict=True)
    bytes_transferred: int = Field(ge=0, strict=True)
    raw_records_shared: Literal[0] = 0
    validation: Metric
    train_loss_before: float = Field(ge=0)
    train_loss_after: float = Field(ge=0)
    local_epochs: int = Field(ge=1, le=5, strict=True)
    training_seconds: float = Field(ge=0)
