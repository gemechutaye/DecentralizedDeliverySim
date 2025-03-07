# Decentralized Delivery Coordination Simulator

A Python-based simulation for CMSI 6998 (Spring 2025) exploring online algorithms and decentralized systems. This project models autonomous delivery agents finding moving customers in a grid, coordinating without a central server, and handling a Byzantine agent spreading false data.

## Features
- **Online Search**: Agents use a spiral pattern to locate moving customers.
- **Decentralized Consensus**: Agents share and vote on customer locations locally.
- **Byzantine Fault Tolerance**: Handles one malicious agent lying about positions.
- **Visualization**: Pygame shows agents (blue), customers (green), and the Byzantine agent (red).

## Requirements
- Python 3.11+
- Libraries: `pygame`, `numpy`
  - Install via: `pip install pygame numpy`

## How to Run
1. Clone or copy this directory to your machine.
2. Open a terminal in the `DecentralizedDeliverySim` folder.
3. Install dependencies: `pip install pygame numpy`.
4. Run the simulation: `python main.py`.
5. Watch the agents move! Close the Pygame window to end.

## Files
- `main.py`: Runs the simulation loop.
- `environment.py`: Manages the grid and customer movement.
- `agent.py`: Defines agent behavior (search, observation).
- `consensus.py`: Handles decentralized coordination and BFT.
- `visualize.py`: Renders the simulation with Pygame.
- `metrics.py`: Calculates performance (competitive ratio).

## Notes
- Grid: 20x20, 5 agents, 3 customers.
- Agent 0 is Byzantine (red circle).
- Simulation runs for 100 steps or until the window is closed.

## Future Enhancements
- Scale to more agents/customers.
- Add delivery completion logic.
- Optimize consensus for larger grids.

Created by Gemechu Taye for CMSI 6998, Spring 2025.