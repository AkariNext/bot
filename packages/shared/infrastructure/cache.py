from packages.shared.bentocache.cache import BentoCache
from packages.shared.bentocache.strategy.memory import MemoryStrategy

cache = BentoCache({
    'l1_layer': MemoryStrategy(),
})
