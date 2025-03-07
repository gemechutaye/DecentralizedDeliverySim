import pygame
import time
import random
import math
from environment import Environment
from agent import Agent
from consensus import Consensus
from metrics import competitive_ratio
from visualize import visualize  # Import visualization module

def main():
    # Initialize environment and agents
    grid_size = 20
    env = Environment(size=grid_size, num_customers=3)
    
    # Initialize pygame
    pygame.init()
    
    # Application state variables
    running = True             # Controls the entire application
    simulation_active = True   # Controls the current simulation
    
    # Main application loop (continues until user closes)
    while running:
        # Reset simulation variables
        step = 0
        paused = False
        delivered_count = 0
        
        # Create a new environment and agents for each simulation
        if not simulation_active:
            env = Environment(size=grid_size, num_customers=3)
            
        # Store initial customer count for metrics
        initial_customer_count = len(env.customers)
        
        # Create agents (Agent 0 is Byzantine)
        agents = [Agent(i, (i*4, i*4), is_byzantine=(i == 0)) for i in range(5)]
        consensus = Consensus(agents)
        
        # Create and initialize visualization
        viz = visualize(env, agents)
        
        # Reset visualization state if starting a new simulation
        if not simulation_active:
            viz.reset_for_new_simulation()
            simulation_active = True
        
        # Simulation loop (runs until simulation completes or user exits)
        while running and simulation_active:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    simulation_active = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        simulation_active = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if results panel is active and buttons are clicked
                    if viz.show_results_panel:
                        if viz.run_button_rect.collidepoint(event.pos):
                            # Start a new simulation
                            simulation_active = False
                            break  # Exit the simulation loop to start a new one
                        elif viz.close_button_rect.collidepoint(event.pos):
                            running = False  # Exit the application
                            break
            
            # Skip updating if paused
            if not paused and simulation_active:
                # Update environment - customers move every 5 steps
                if step % 5 == 0:
                    env.move_customers()
                
                # Update agent positions
                for agent in agents:
                    # Apply wind effects to agent movement (slight randomization)
                    if hasattr(viz, 'wind_direction') and hasattr(viz, 'wind_strength'):
                        if random.random() < viz.wind_strength * 0.5:
                            # Calculate wind vector
                            wind_dx = math.cos(math.radians(viz.wind_direction)) * viz.wind_strength
                            wind_dy = math.sin(math.radians(viz.wind_direction)) * viz.wind_strength
                            
                            # Apply wind effect by adjusting agent position slightly
                            agent.apply_wind(wind_dx, wind_dy)
                    
                    # Move the agent
                    agent.move(env)
                
                # Update consensus knowledge among agents
                consensus.update_knowledge()
                
                # Check for deliveries
                for agent in agents:
                    for i, (cx, cy) in enumerate(env.customers[:]):  # Use a copy to safely modify
                        if agent.pos == (cx, cy):
                            # Remove delivered customer
                            env.customers.pop(i)
                            delivered_count += 1
                            break
                
                # Calculate current competitive ratio
                current_ratio = competitive_ratio(agents, env)
                
                # Update visualization
                viz.update_display(env, agents, step, current_ratio, delivered_count)
                
                # Increment step
                step += 1
                
                # Check if simulation is complete
                if step >= 100 or len(env.customers) == 0:
                    # End current simulation
                    final_ratio = competitive_ratio(agents, env)
                    
                    # Print results to terminal
                    print(f"Simulation completed after {step} steps")
                    print(f"Competitive Ratio: {final_ratio:.2f}")
                    print(f"Customers delivered: {delivered_count}/{initial_customer_count}")
                    
                    # Show results panel
                    viz.show_results(step, final_ratio, delivered_count, initial_customer_count)
                    
                    # Keep the simulation active but show results panel
                    paused = True
            else:
                # If paused, just update the display
                if simulation_active:
                    current_ratio = competitive_ratio(agents, env)
                    viz.update_display(env, agents, step, current_ratio, delivered_count)
                    
                    # Display "PAUSED" message if not showing results
                    if not viz.show_results_panel:
                        font = pygame.font.SysFont('Arial', 48, bold=True)
                        text = font.render("PAUSED", True, (200, 0, 0))
                        text_rect = text.get_rect(center=(grid_size*20//2, grid_size*20//2))
                        pygame.display.get_surface().blit(text, text_rect)
                        pygame.display.flip()
            
            # Control simulation speed
            pygame.time.Clock().tick(10)  # 10 FPS
    
    # Clean exit
    pygame.quit()

if __name__ == "__main__":
    main()