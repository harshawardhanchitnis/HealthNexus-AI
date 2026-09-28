from math import prod

COUNTRIES = ('IN', 'BR', 'RU', 'CN', 'ZA')
MODEL_VERSION = 'federated-footfall-mlp-v1'
FEATURES = ('horizon_fraction', 'weekday_sin', 'weekday_cos', 'annual_sin', 'annual_cos',
    'trend_half_years', 'lag1_ratio', 'lag7_ratio', 'lag14_ratio', 'mean7_ratio',
    'mean14_ratio', 'std28_ratio', 'growth7', 'primary', 'community', 'hospital')
SHAPES = {'0.weight': (16, len(FEATURES)), '0.bias': (16,), '2.weight': (8, 16),
    '2.bias': (8,), '4.weight': (1, 8), '4.bias': (1,)}
PARAMETER_COUNT = sum(prod(s) for s in SHAPES.values())
LEARNING_RATE = .03
BATCH_SIZE = 1024
CPU_THREADS = 2
NOTICE = 'Raw operational training records remain local in this prototype; model parameters and aggregate metadata are exchanged.'
PHASE6_STATUS = 'Implementation complete; live provider acceptance pending due to Gemini service availability.'
