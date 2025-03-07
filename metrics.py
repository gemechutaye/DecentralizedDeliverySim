from scipy.spatial import distance

def competitive_ratio(agents, env):
    total_steps = sum(agent.step for agent in agents)
    
    # Handle case when there are no customers left
    if not env.customers:
        return total_steps  # Just return total steps when all customers are delivered
    
    # Calculate minimum distance from each agent to any customer
    optimal = sum(min(distance.euclidean(agent.pos, c) for c in env.customers) for agent in agents)
    return total_steps / optimal if optimal > 0 else float('inf')
