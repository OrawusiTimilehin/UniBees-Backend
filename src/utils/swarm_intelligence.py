import math
from datetime import datetime, timezone

def calculate_current_nectar(swarm, half_life_minutes=120):
    """
    Recalibrated Nectar Resolver.
    Ensures that activity (pheromones) is the primary driver but requires
    a higher threshold of community input to hit the 100% ceiling.
    """
    if not swarm.last_buzz_at:
        return 10.0 # Base floor for new swarms

    # 1. Calculate Temporal Decay (Evaporation)
    now = datetime.now(timezone.utc)
    last_buzz = swarm.last_buzz_at.replace(tzinfo=timezone.utc)
    delta_t = (now - last_buzz).total_seconds() / 60
    
    # 120min half-life: pheromones stay relevant for about 2 hours
    lmbda = math.log(2) / half_life_minutes
    
    # 2. Pheromone Component (Max contribution ~80-85 points)
    current_pheromones = (swarm.pheromone_base or 10.0) * math.exp(-lmbda * delta_t)
    
    # 3. Community Modifiers (Requires multiple users to hit true 100)
    # Upvotes are worth 1.0 each (Target: 10 upvotes for a max boost)
    upvote_boost = min(10.0, (swarm.upvotes or 0) * 1.0)
    
    # Density: Each member adds 0.25 (Target: 20 members for a max boost of 5)
    density_boost = min(5.0, len(swarm.members or []) * 0.25)
    
    total_n = current_pheromones + upvote_boost + density_boost
    
    return round(min(100.0, total_n), 2)