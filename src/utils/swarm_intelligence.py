import math
from datetime import datetime, timezone

def calculate_current_nectar(swarm, half_life_minutes=120):
    """
    Implements Asymptotic Decay: P = P0 * e^(-lambda * t)
    Makes energy vanish gradually over a 2-hour half-life.
    """
    if not swarm.last_buzz_at:
        return 0.0

    # 1. Calculate time delta
    now = datetime.now(timezone.utc)
    # Ensure last_buzz_at is timezone aware for the math
    last_buzz = swarm.last_buzz_at.replace(tzinfo=timezone.utc)
    delta_t = (now - last_buzz).total_seconds() / 60
    
    # 2. The Decay Constant (Lambda)
    lmbda = math.log(2) / half_life_minutes
    
    # 3. Apply Exponential Decay to Pheromones
    current_pheromones = swarm.pheromone_base * math.exp(-lmbda * delta_t)
    
    # 4. Add "Waggle Dance" factors (Upvotes + Population)
    upvote_boost = swarm.upvotes * 0.5
    density_boost = len(swarm.members) * 0.2
    
    # Total Nectar Quality (Cap at 100)
    total_n = current_pheromones + upvote_boost + density_boost
    return round(min(100.0, total_n), 2)