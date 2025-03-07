from scipy.spatial import distance
import numpy as np

class Consensus:
    def __init__(self, agents):
        self.agents = agents

    def update_knowledge(self):
        for agent in self.agents:
            shared = {}
            for other in self.agents:
                if distance.euclidean(agent.pos, other.pos) <= 5 and agent != other:
                    shared.update(other.share_knowledge())
            for cid in shared:
                positions = [pos for a in self.agents for c, pos in a.knowledge.items() if c == cid]
                if positions:
                    avg_pos = np.mean(positions, axis=0)
                    if len([p for p in positions if distance.euclidean(p, avg_pos) < 3]) >= len(self.agents) // 2:
                        agent.knowledge[cid] = tuple(avg_pos.astype(int))
