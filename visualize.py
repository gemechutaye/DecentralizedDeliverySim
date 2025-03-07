import pygame
import math
import os
import time
import random

# Initialize pygame
pygame.init()

class RealisticVisualizer:
    def __init__(self, size=20, window_size=800):
        self.grid_size = size
        self.window_size = window_size
        self.cell_size = window_size // size
        
        # Colors
        self.colors = {
            "sky": (135, 206, 235),      # Sky blue background
            "ground": (34, 139, 34),     # Forest green for ground
            "roads": (169, 169, 169),    # Dark gray for roads
            "buildings": (210, 180, 140), # Light brown for buildings
            "water": (65, 105, 225),     # Royal blue for water
            "normal_drone": (65, 105, 225),  # Blue for normal drones
            "byzantine_drone": (220, 20, 60),  # Red for byzantine drone
            "signal": (255, 255, 255, 128),  # White for drone signals
            "text": (44, 62, 80),        # Dark slate for text
            "panel": (236, 240, 241),    # Light panel background
            "button_run": (46, 204, 113),   # Green for run button
            "button_close": (231, 76, 60),  # Red for close button
            "battery_good": (46, 204, 113), # Green for good battery
            "battery_med": (243, 156, 18),  # Orange for medium battery
            "battery_low": (231, 76, 60)    # Red for low battery
        }
        
        # Initialize fonts
        self.title_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.header_font = pygame.font.SysFont('Arial', 18, bold=True)
        self.info_font = pygame.font.SysFont('Arial', 16)
        self.small_font = pygame.font.SysFont('Arial', 12)
        
        # Prepare the screen
        self.screen = pygame.display.set_mode((window_size, window_size + 150))  # Extra 150px for dashboard
        pygame.display.set_caption("Drone Delivery Management System")
        
        # Track animation effects
        self.delivery_animations = []  # List of active delivery animations
        self.communication_signals = []  # List of active communication signals
        self.weather_effects = []  # Wind, rain, etc.
        self.drone_paths = {}  # Store drone paths for visualization
        
        # Create pygame Clock for controlling FPS
        self.clock = pygame.time.Clock()
        
        # Results panel elements
        self.simulation_history = []
        self.show_results_panel = False
        self.run_button_rect = pygame.Rect(0, 0, 0, 0)
        self.close_button_rect = pygame.Rect(0, 0, 0, 0)
        
        # Wind effects
        self.wind_direction = random.randint(0, 359)  # Wind direction in degrees
        self.wind_strength = random.uniform(0, 0.3)   # Wind strength (0-1)
        self.wind_update_timer = 0
        
        # Time of day simulation
        self.time_of_day = 0  # 0-23 hours
        self.day_cycle_speed = 0.05  # How quickly time passes (hours per step)
        
        # Load or create assets
        self.images = self._prepare_assets()
        
        # Generate environment (roads, buildings, obstacles)
        self.environment = self._generate_environment()
        
        # Create a camera object for map panning/zooming (future enhancement)
        self.camera_offset = [0, 0]
        self.zoom = 1.0

    def _prepare_assets(self):
        """Create or load visual assets for the simulation"""
        images = {}
        
        # Create drone surface with propellers
        def create_drone(color, size, is_damaged=False):
            """Create a drone sprite with spinning propellers"""
            drone_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Drone body
            body_radius = size // 3
            pygame.draw.circle(drone_surface, color, (size//2, size//2), body_radius)
            
            # Add propellers
            propeller_positions = [(size//4, size//4), (3*size//4, size//4), 
                                  (size//4, 3*size//4), (3*size//4, 3*size//4)]
            for x, y in propeller_positions:
                pygame.draw.circle(drone_surface, (50, 50, 50), (x, y), size//8)
                pygame.draw.line(drone_surface, (200, 200, 200), 
                               (x, y), (x + size//10, y), 2)
                pygame.draw.line(drone_surface, (200, 200, 200), 
                               (x, y), (x - size//10, y), 2)
            
            # Add warning symbol for damaged/byzantine drone
            if is_damaged:
                warning_font = pygame.font.SysFont('Arial', size//3, bold=True)
                warning = warning_font.render("!", True, (255, 255, 255))
                warning_rect = warning.get_rect(center=(size//2, size//2))
                drone_surface.blit(warning, warning_rect)
                
                # Add some visual damage
                for _ in range(3):
                    damage_x = random.randint(0, size)
                    damage_y = random.randint(0, size)
                    damage_size = random.randint(2, 5)
                    pygame.draw.circle(drone_surface, (30, 30, 30), 
                                     (damage_x, damage_y), damage_size)
            
            return drone_surface
        
        # Create building with windows
        def create_building(size, windows=True):
            """Create a building with optional windows"""
            building = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Main building structure
            building_color = (random.randint(180, 220), 
                            random.randint(160, 200), 
                            random.randint(120, 160))
            pygame.draw.rect(building, building_color, (0, 0, size, size), border_radius=2)
            
            # Add windows
            if windows:
                window_color = (240, 230, 140)  # Light yellow for lit windows
                window_rows = random.randint(1, 3)
                window_cols = random.randint(1, 3)
                window_size = size // (window_cols + 2)
                window_margin = (size - (window_cols * window_size)) // (window_cols + 1)
                
                for row in range(window_rows):
                    for col in range(window_cols):
                        x = window_margin + col * (window_size + window_margin)
                        y = window_margin + row * ((size - 2*window_margin) // window_rows)
                        # Randomly determine if window is lit
                        if random.random() > 0.3:
                            pygame.draw.rect(building, window_color, 
                                          (x, y, window_size, window_size))
            
            return building
        
        # Create package sprite
        def create_package(size):
            """Create a package/parcel sprite"""
            package = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Box
            pygame.draw.rect(package, (139, 69, 19), (0, 0, size, size), border_radius=2)  # Brown box
            
            # Tape/markings
            pygame.draw.rect(package, (168, 86, 27), (0, size//3, size, size//4))
            pygame.draw.line(package, (70, 40, 10), (size//2, 0), (size//2, size), 1)
            
            return package
            
        # Create delivery animation
        def create_delivery_effect(size):
            """Create a success/completion animation"""
            effect = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            
            # Create a starburst effect
            center = (size, size)
            for angle in range(0, 360, 15):
                rad = math.radians(angle)
                x1 = center[0] + math.cos(rad) * (size//4)
                y1 = center[1] + math.sin(rad) * (size//4)
                x2 = center[0] + math.cos(rad) * size
                y2 = center[1] + math.sin(rad) * size
                pygame.draw.line(effect, (60, 220, 60, 150), (x1, y1), (x2, y2), 3)
            
            # Add a check mark
            pygame.draw.lines(effect, (255, 255, 255, 200), False, 
                           [(size*0.6, size), (size*0.8, size*1.2), (size*1.4, size*0.6)], 4)
            
            return effect
        
        # Create signal/communication visual
        def create_signal_wave(size):
            """Create a radar-like signal wave animation"""
            signal = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
            
            # Draw expanding concentric circles
            for radius in range(size//2, size*2, size//4):
                alpha = 255 - (radius * 255 // (size*2))
                pygame.draw.circle(signal, (255, 255, 255, alpha), 
                                 (size*2, size*2), radius, 1)
            
            return signal
            
        # Load all assets
        images["normal_drone"] = create_drone(self.colors["normal_drone"], self.cell_size)
        images["byzantine_drone"] = create_drone(self.colors["byzantine_drone"], 
                                                self.cell_size, is_damaged=True)
        images["building"] = create_building(self.cell_size - 4)
        images["package"] = create_package(self.cell_size // 2)
        images["delivery_effect"] = create_delivery_effect(self.cell_size)
        images["signal_wave"] = create_signal_wave(self.cell_size)
        
        # Create propeller animation frames (for future enhancement)
        images["propeller_frames"] = []
        for angle in range(0, 360, 30):
            prop = pygame.Surface((self.cell_size//8, self.cell_size//8), pygame.SRCALPHA)
            rad = math.radians(angle)
            center = (self.cell_size//16, self.cell_size//16)
            x1 = center[0] + math.cos(rad) * (self.cell_size//16)
            y1 = center[1] + math.sin(rad) * (self.cell_size//16)
            x2 = center[0] - math.cos(rad) * (self.cell_size//16)
            y2 = center[1] - math.sin(rad) * (self.cell_size//16)
            pygame.draw.line(prop, (200, 200, 200), (x1, y1), (x2, y2), 2)
            images["propeller_frames"].append(prop)
            
        return images

    def _generate_environment(self):
        """Generate a realistic environment with roads, buildings, and obstacles"""
        environment = {}
        environment["buildings"] = []
        environment["roads"] = []
        environment["obstacles"] = []
        
        # Generate a grid of roads
        road_spacing = 4  # Roads every 4 cells
        for i in range(0, self.grid_size, road_spacing):
            # Horizontal roads
            road_h = {"start": (0, i), "end": (self.grid_size-1, i), "width": 1}
            environment["roads"].append(road_h)
            
            # Vertical roads
            road_v = {"start": (i, 0), "end": (i, self.grid_size-1), "width": 1}
            environment["roads"].append(road_v)
        
        # Place buildings between roads
        for i in range(1, self.grid_size // road_spacing):
            for j in range(1, self.grid_size // road_spacing):
                block_x = i * road_spacing - road_spacing//2
                block_y = j * road_spacing - road_spacing//2
                
                # Add buildings with slight randomization
                max_buildings = random.randint(1, 3)  # 1-3 buildings per block
                for _ in range(max_buildings):
                    building_x = block_x + random.randint(-1, 1)
                    building_y = block_y + random.randint(-1, 1)
                    
                    # Keep buildings within bounds
                    building_x = max(0, min(self.grid_size-1, building_x))
                    building_y = max(0, min(self.grid_size-1, building_y))
                    
                    # Ensure buildings don't overlap with roads
                    if building_x % road_spacing != 0 and building_y % road_spacing != 0:
                        building = {
                            "pos": (building_x, building_y),
                            "size": random.choice([1, 1, 2]),  # Most buildings are size 1, some are 2
                            "type": random.choice(["residential", "commercial", "industrial"])
                        }
                        environment["buildings"].append(building)
        
        # Add some random obstacles (trees, power lines, etc.)
        for _ in range(self.grid_size // 2):
            obstacle_x = random.randint(0, self.grid_size-1)
            obstacle_y = random.randint(0, self.grid_size-1)
            
            # Don't place obstacles on roads or buildings
            is_on_road = any(
                (obstacle_x == road["start"][0] or obstacle_x == road["end"][0] or 
                obstacle_y == road["start"][1] or obstacle_y == road["end"][1])
                for road in environment["roads"]
            )
            
            is_on_building = any(
                (abs(obstacle_x - building["pos"][0]) < building["size"] and 
                abs(obstacle_y - building["pos"][1]) < building["size"])
                for building in environment["buildings"]
            )
            
            if not is_on_road and not is_on_building:
                obstacle = {
                    "pos": (obstacle_x, obstacle_y),
                    "type": random.choice(["tree", "pole", "antenna"])
                }
                environment["obstacles"].append(obstacle)
        
        return environment

    def _draw_environment(self):
        """Draw the realistic city environment"""
        # Fill the sky background based on time of day
        self._draw_sky()
        
        # Draw roads
        for road in self.environment["roads"]:
            start_x, start_y = road["start"]
            end_x, end_y = road["end"]
            
            if start_x == end_x:  # Vertical road
                pygame.draw.rect(self.screen, self.colors["roads"],
                              (start_x * self.cell_size - road["width"]/2, 
                               start_y * self.cell_size,
                               self.cell_size * road["width"], 
                               (end_y - start_y + 1) * self.cell_size))
            else:  # Horizontal road
                pygame.draw.rect(self.screen, self.colors["roads"],
                              (start_x * self.cell_size, 
                               start_y * self.cell_size - road["width"]/2,
                               (end_x - start_x + 1) * self.cell_size, 
                               self.cell_size * road["width"]))
                
            # Add road markings
            if start_x == end_x:  # Vertical road
                for y in range(start_y, end_y+1, 2):
                    pygame.draw.rect(self.screen, (255, 255, 255),
                                  (start_x * self.cell_size, 
                                   y * self.cell_size + self.cell_size//2,
                                   self.cell_size//8, self.cell_size//4))
            else:  # Horizontal road
                for x in range(start_x, end_x+1, 2):
                    pygame.draw.rect(self.screen, (255, 255, 255),
                                  (x * self.cell_size + self.cell_size//2, 
                                   start_y * self.cell_size,
                                   self.cell_size//4, self.cell_size//8))
        
        # Draw buildings
        for building in self.environment["buildings"]:
            pos_x, pos_y = building["pos"]
            size = building["size"]
            building_img = pygame.transform.scale(
                self.images["building"], 
                (self.cell_size * size - 4, self.cell_size * size - 4)
            )
            self.screen.blit(building_img, 
                           (pos_y * self.cell_size + 2, pos_x * self.cell_size + 2))
        
        # Draw obstacles
        for obstacle in self.environment["obstacles"]:
            pos_x, pos_y = obstacle["pos"]
            obstacle_type = obstacle["type"]
            
            if obstacle_type == "tree":
                # Draw tree trunk
                pygame.draw.rect(self.screen, (101, 67, 33),  # Brown
                              (pos_y * self.cell_size + self.cell_size//2 - 2,
                               pos_x * self.cell_size + self.cell_size//2,
                               4, self.cell_size//2))
                
                # Draw tree top (circle)
                pygame.draw.circle(self.screen, (0, 100, 0),  # Dark green
                                 (pos_y * self.cell_size + self.cell_size//2,
                                  pos_x * self.cell_size + self.cell_size//3),
                                 self.cell_size//3)
            
            elif obstacle_type == "pole":
                # Power/telephone pole
                pygame.draw.rect(self.screen, (90, 90, 90),  # Dark gray
                              (pos_y * self.cell_size + self.cell_size//2 - 2,
                               pos_x * self.cell_size + self.cell_size//4,
                               4, self.cell_size//2))
                
                # Crossbar
                pygame.draw.rect(self.screen, (60, 60, 60),  # Darker gray
                              (pos_y * self.cell_size + self.cell_size//4,
                               pos_x * self.cell_size + self.cell_size//3,
                               self.cell_size//2, 3))
                
            elif obstacle_type == "antenna":
                # Base
                pygame.draw.rect(self.screen, (150, 150, 150),  # Light gray
                              (pos_y * self.cell_size + self.cell_size//2 - 2,
                               pos_x * self.cell_size + self.cell_size//4,
                               4, self.cell_size//2))
                
                # Antenna parts
                pygame.draw.lines(self.screen, (100, 100, 100), False,
                               [(pos_y * self.cell_size + self.cell_size//2,
                                 pos_x * self.cell_size + self.cell_size//4),
                                (pos_y * self.cell_size + self.cell_size//2,
                                 pos_x * self.cell_size + self.cell_size//8),
                                (pos_y * self.cell_size + self.cell_size//2 + self.cell_size//4,
                                 pos_x * self.cell_size + self.cell_size//8)], 2)
                
                pygame.draw.lines(self.screen, (100, 100, 100), False,
                               [(pos_y * self.cell_size + self.cell_size//2,
                                 pos_x * self.cell_size + self.cell_size//4),
                                (pos_y * self.cell_size + self.cell_size//2,
                                 pos_x * self.cell_size + self.cell_size//8),
                                (pos_y * self.cell_size + self.cell_size//2 - self.cell_size//4,
                                 pos_x * self.cell_size + self.cell_size//8)], 2)

    def _draw_sky(self):
        """Draw sky with time-of-day effects"""
        # Calculate sky color based on time of day (0-23 hours)
        if 6 <= self.time_of_day < 18:
            # Daytime - blue sky
            day_progress = abs(self.time_of_day - 12) / 6  # 0 at noon, 1 at 6am/6pm
            
            # Lighter blue at midday, darker at dawn/dusk
            r = int(135 - day_progress * 30)
            g = int(206 - day_progress * 40)
            b = int(235 - day_progress * 30)
            sky_color = (r, g, b)
        else:
            # Night time - dark blue to black
            night_progress = min(abs(self.time_of_day - 0), abs(self.time_of_day - 24)) / 6
            # Darkest at midnight, lighten toward dawn/dusk
            r = int(25 + night_progress * 30)
            g = int(25 + night_progress * 40)
            b = int(50 + night_progress * 50)
            sky_color = (r, g, b)
            
        # Fill background with sky color
        self.screen.fill(sky_color)
        
        # Add sun or moon
        if 6 <= self.time_of_day < 18:
            # Sun position (moves across the sky)
            sun_progress = (self.time_of_day - 6) / 12  # 0-1 from dawn to dusk
            sun_x = int(sun_progress * self.window_size)
            sun_y = int(100 + math.sin(math.pi * sun_progress) * -200)
            
            # Draw sun
            pygame.draw.circle(self.screen, (255, 255, 190), (sun_x, sun_y), 30)
            # Add glow
            for r in range(35, 55, 5):
                pygame.draw.circle(self.screen, (255, 255, 190, 50), (sun_x, sun_y), r)
        else:
            # Moon position
            moon_progress = (self.time_of_day - 18) / 12 if self.time_of_day >= 18 else (self.time_of_day + 6) / 12
            moon_x = int(moon_progress * self.window_size)
            moon_y = int(100 + math.sin(math.pi * moon_progress) * -200)
            
            # Draw moon
            pygame.draw.circle(self.screen, (230, 230, 230), (moon_x, moon_y), 20)
            
            # Add a few stars at night
            for _ in range(50):
                star_x = random.randint(0, self.window_size)
                star_y = random.randint(0, self.window_size // 2)
                brightness = random.randint(150, 255)
                # Twinkle effect - some stars are brighter
                if random.random() < 0.1:
                    pygame.draw.circle(self.screen, (brightness, brightness, brightness), (star_x, star_y), 2)
                else:
                    pygame.draw.circle(self.screen, (brightness, brightness, brightness), (star_x, star_y), 1)
        
        # Update time of day for next frame
        self.time_of_day = (self.time_of_day + self.day_cycle_speed) % 24

    def _draw_drone_paths(self, agents):
        """Draw drone flight paths with realistic effects"""
        for agent in agents:
            if agent.id in self.drone_paths:
                path = self.drone_paths[agent.id]
                if len(path) > 1:
                    # Set path color based on agent type
                    path_color = self.colors["byzantine_drone"] if agent.is_byzantine else self.colors["normal_drone"]
                    
                    # Draw with decreasing alpha for older segments
                    for i in range(len(path) - 1):
                        # Calculate alpha based on segment age
                        alpha = min(255, int(180 * (i + 1) / len(path)))
                        
                        # Draw line segment
                        pygame.draw.line(
                            self.screen,
                            (*path_color[:3], alpha),
                            (path[i][1] * self.cell_size + self.cell_size // 2, 
                             path[i][0] * self.cell_size + self.cell_size // 2),
                            (path[i+1][1] * self.cell_size + self.cell_size // 2, 
                             path[i+1][0] * self.cell_size + self.cell_size // 2),
                            max(1, 3 - (len(path) - i) // 5)  # Thicker for newer segments
                        )

    def _draw_drones(self, agents):
        """Draw drones on the map with status indicators"""
        for agent in agents:
            # Update drone paths for visualization
            if agent.id not in self.drone_paths:
                self.drone_paths[agent.id] = []
            
            # Only add new positions to reduce memory usage
            if not self.drone_paths[agent.id] or self.drone_paths[agent.id][-1] != agent.pos:
                self.drone_paths[agent.id].append(agent.pos)
                # Limit path length to prevent performance issues
                if len(self.drone_paths[agent.id]) > 30:
                    self.drone_paths[agent.id] = self.drone_paths[agent.id][-30:]
            
            # Simulated flight altitude using shadow
            shadow_y_offset = 5  # Pixels below the drone
            shadow_alpha = 100   # Transparency of shadow
            
            # Draw shadow
            shadow_surface = pygame.Surface((self.cell_size // 2, self.cell_size // 4), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, shadow_alpha), 
                              (0, 0, self.cell_size // 2, self.cell_size // 4))
            self.screen.blit(shadow_surface, 
                           (agent.pos[1] * self.cell_size + self.cell_size // 4, 
                            agent.pos[0] * self.cell_size + self.cell_size // 2 + shadow_y_offset))
            
            # Draw the drone
            if agent.is_byzantine:
                self.screen.blit(self.images["byzantine_drone"], 
                               (agent.pos[1] * self.cell_size, agent.pos[0] * self.cell_size))
            else:
                self.screen.blit(self.images["normal_drone"], 
                               (agent.pos[1] * self.cell_size, agent.pos[0] * self.cell_size))
            
            # Draw battery status indicator
            battery_level = max(0, 1 - (agent.step / 120))  # Battery depletes as drone moves
            battery_width = self.cell_size // 2
            battery_height = 3
            
            # Battery color changes with level
            if battery_level > 0.6:
                battery_color = self.colors["battery_good"]
            elif battery_level > 0.3:
                battery_color = self.colors["battery_med"]
            else:
                battery_color = self.colors["battery_low"]
            
            # Draw battery outline
            pygame.draw.rect(self.screen, (50, 50, 50), 
                           (agent.pos[1] * self.cell_size + self.cell_size // 4, 
                            agent.pos[0] * self.cell_size - battery_height - 2,
                            battery_width, battery_height), 1)
            
            # Draw battery fill
            pygame.draw.rect(self.screen, battery_color, 
                           (agent.pos[1] * self.cell_size + self.cell_size // 4 + 1, 
                            agent.pos[0] * self.cell_size - battery_height - 1,
                            int(battery_width * battery_level) - 2, battery_height - 2))
            
            # Draw drone ID
            id_text = self.small_font.render(f"D{agent.id}", True, (255, 255, 255))
            id_rect = id_text.get_rect(center=(
                agent.pos[1] * self.cell_size + self.cell_size // 2,
                agent.pos[0] * self.cell_size + self.cell_size // 2
            ))
            self.screen.blit(id_text, id_rect)
            
            # Occasionally show communication signal animation
            if not agent.is_byzantine and agent.knowledge and random.random() < 0.05:
                self._add_communication_signal(agent.pos, 15)

    def _draw_customers(self, customers):
        """Draw customers (delivery locations) on the map"""
        for i, (cx, cy) in enumerate(customers):
            # Draw building with package
            building_img = self.images["building"]
            self.screen.blit(building_img, 
                           (cy * self.cell_size + (self.cell_size - building_img.get_width()) // 2, 
                            cx * self.cell_size + (self.cell_size - building_img.get_height()) // 2))
            
            # Draw package on top of building
            package_img = self.images["package"]
            self.screen.blit(package_img, 
                           (cy * self.cell_size + (self.cell_size - package_img.get_width()) // 2, 
                            cx * self.cell_size + (self.cell_size - package_img.get_height()) // 4))
            
            # Draw customer ID
            id_text = self.small_font.render(f"C{i}", True, (255, 255, 255))
            id_rect = id_text.get_rect(center=(
                cy * self.cell_size + self.cell_size // 2,
                cx * self.cell_size + self.cell_size // 2 - self.cell_size // 4
            ))
            self.screen.blit(id_text, id_rect)
            
            # Draw person waiting (stick figure)
            pygame.draw.circle(self.screen, (200, 150, 150), 
                             (cy * self.cell_size + self.cell_size // 2, 
                              cx * self.cell_size + self.cell_size // 2 + self.cell_size // 8), 
                             3)  # Head
            
            pygame.draw.line(self.screen, (200, 150, 150), 
                           (cy * self.cell_size + self.cell_size // 2, 
                            cx * self.cell_size + self.cell_size // 2 + self.cell_size // 8 + 3),
                           (cy * self.cell_size + self.cell_size // 2, 
                            cx * self.cell_size + self.cell_size // 2 + self.cell_size // 4), 2)  # Body
            
            # Occasionally make the person wave to show they're waiting
            if random.random() < 0.1:
                # Wave arm up
                pygame.draw.line(self.screen, (200, 150, 150), 
                               (cy * self.cell_size + self.cell_size // 2, 
                                cx * self.cell_size + self.cell_size // 2 + self.cell_size // 8 + 5),
                               (cy * self.cell_size + self.cell_size // 2 + 5, 
                                cx * self.cell_size + self.cell_size // 2 + self.cell_size // 8 - 2), 2)  # Arm up
            else:
                # Normal arm position
                pygame.draw.line(self.screen, (200, 150, 150), 
                               (cy * self.cell_size + self.cell_size // 2, 
                                cx * self.cell_size + self.cell_size // 2 + self.cell_size // 8 + 5),
                               (cy * self.cell_size + self.cell_size // 2 + 5, 
                                cx * self.cell_size + self.cell_size // 2 + self.cell_size // 8 + 5), 2)  # Arm

    def _add_communication_signal(self, pos, frames=20):
        """Add a new communication signal animation"""
        self.communication_signals.append({
            "pos": pos,
            "time": frames,
            "frames": frames
        })

    def _process_animations(self):
        """Update and draw all animations"""
        # Process delivery animations
        remaining_deliveries = []
        for anim in self.delivery_animations:
            # Update animation
            anim["time"] -= 1
            
            # Draw animation
            if anim["time"] > 0:
                # Scale the animation based on time
                scale = 1.0 - (anim["frames"] - anim["time"]) / anim["frames"]
                size = int(self.cell_size * 2 * scale)
                if size > 0:
                    scaled_surface = pygame.transform.scale(
                        self.images["delivery_effect"], (size, size))
                    
                    pos_x = anim["pos"][1] * self.cell_size + self.cell_size // 2 - size // 2
                    pos_y = anim["pos"][0] * self.cell_size + self.cell_size // 2 - size // 2
                    self.screen.blit(scaled_surface, (pos_x, pos_y))
                    
                    # Draw text
                    delivered_text = self.info_font.render("Delivered!", True, (255, 255, 255))
                    text_rect = delivered_text.get_rect(center=(
                        anim["pos"][1] * self.cell_size + self.cell_size // 2,
                        anim["pos"][0] * self.cell_size + self.cell_size // 2 - 5
                    ))
                    self.screen.blit(delivered_text, text_rect)
                    
                    # Keep animation active
                    remaining_deliveries.append(anim)
                    
        self.delivery_animations = remaining_deliveries
        
        # Process communication signals
        remaining_signals = []
        for signal in self.communication_signals:
            # Update animation
            signal["time"] -= 1
            
            # Draw animation
            if signal["time"] > 0:
                # Scale the animation based on time
                scale = (signal["frames"] - signal["time"]) / signal["frames"]
                size = int(self.cell_size * 3 * scale)
                if size > 0:
                    # Create signal wave on-the-fly
                    signal_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                    alpha = 150 * (1 - scale)
                    pygame.draw.circle(signal_surface, (255, 255, 255, int(alpha)), 
                                     (size//2, size//2), size//2, 1)
                    
                    pos_x = signal["pos"][1] * self.cell_size + self.cell_size // 2 - size // 2
                    pos_y = signal["pos"][0] * self.cell_size + self.cell_size // 2 - size // 2
                    self.screen.blit(signal_surface, (pos_x, pos_y))
                    
                    # Keep animation active
                    remaining_signals.append(signal)
        
        self.communication_signals = remaining_signals

    def update_wind(self):
        """Update wind direction and strength periodically"""
        self.wind_update_timer += 1
        if self.wind_update_timer >= 10:  # Update every 10 steps
            self.wind_update_timer = 0
            # Gradually change wind
            self.wind_direction = (self.wind_direction + random.randint(-20, 20)) % 360
            self.wind_strength = max(0, min(0.5, self.wind_strength + random.uniform(-0.1, 0.1)))

    def _draw_dashboard(self, step, competitive_ratio, delivered=0, total=3):
        """Draw detailed dashboard at the bottom"""
        # Dashboard background
        pygame.draw.rect(self.screen, self.colors["panel"], 
                        (0, self.window_size, self.window_size, 150))
        pygame.draw.line(self.screen, (150, 150, 150),
                        (0, self.window_size),
                        (self.window_size, self.window_size), 2)
        
        # Dashboard title
        title = self.title_font.render("Drone Delivery Management System", True, self.colors["text"])
        self.screen.blit(title, (20, self.window_size + 10))
        
        # Display time of day
        time_hours = int(self.time_of_day)
        time_minutes = int((self.time_of_day - time_hours) * 60)
        am_pm = "AM" if time_hours < 12 else "PM"
        display_hours = time_hours % 12
        if display_hours == 0:
            display_hours = 12
            
        time_text = self.header_font.render(
            f"Time: {display_hours:02d}:{time_minutes:02d} {am_pm}", 
            True, self.colors["text"])
        self.screen.blit(time_text, (self.window_size - 150, self.window_size + 10))
        
        # Main metrics section
        metrics_y = self.window_size + 45
        
        # Step count
        step_text = self.info_font.render(f"Flight Time: {step} minutes", True, self.colors["text"])
        self.screen.blit(step_text, (20, metrics_y))
        
        # Competitive ratio
        ratio_text = self.info_font.render(f"Efficiency Rating: {competitive_ratio:.2f}", True, self.colors["text"])
        self.screen.blit(ratio_text, (20, metrics_y + 25))
        
        # Delivery status
        delivery_text = self.info_font.render(f"Deliveries: {delivered}/{total}", 
                                            True, self.colors["text"])
        self.screen.blit(delivery_text, (20, metrics_y + 50))
        
        # Weather information section
        weather_x = self.window_size - 200
        
        # Wind indicator
        wind_text = self.info_font.render("Wind:", True, self.colors["text"])
        self.screen.blit(wind_text, (weather_x, metrics_y))
        
        # Draw wind direction arrow
        wind_strength_text = ["Calm", "Light", "Moderate", "Strong"][
            min(3, int(self.wind_strength * 8))]
        wind_center = (weather_x + 100, metrics_y + 12)
        wind_length = 20 * self.wind_strength
        wind_end_x = wind_center[0] + wind_length * math.cos(math.radians(self.wind_direction))
        wind_end_y = wind_center[1] + wind_length * math.sin(math.radians(self.wind_direction))
        
        # Arrow line
        pygame.draw.line(self.screen, self.colors["text"], 
                       wind_center, (wind_end_x, wind_end_y), 2)
        
        # Arrow head
        arrow_angle1 = math.radians(self.wind_direction + 140)
        arrow_angle2 = math.radians(self.wind_direction - 140)
        arrow_head1 = (wind_end_x + 8 * math.cos(arrow_angle1), 
                      wind_end_y + 8 * math.sin(arrow_angle1))
        arrow_head2 = (wind_end_x + 8 * math.cos(arrow_angle2), 
                      wind_end_y + 8 * math.sin(arrow_angle2))
        pygame.draw.line(self.screen, self.colors["text"], 
                       (wind_end_x, wind_end_y), arrow_head1, 2)
        pygame.draw.line(self.screen, self.colors["text"], 
                       (wind_end_x, wind_end_y), arrow_head2, 2)
        
        # Wind strength text
        strength_text = self.small_font.render(wind_strength_text, True, self.colors["text"])
        self.screen.blit(strength_text, (weather_x + 50, metrics_y + 25))
        
        # System status
        status_text = self.info_font.render("System Status: Normal", True, self.colors["battery_good"])
        self.screen.blit(status_text, (weather_x, metrics_y + 50))
        
        # Add instructions
        instructions = self.small_font.render(
            "Press SPACE to pause/resume | ESC to exit", True, self.colors["text"])
        self.screen.blit(instructions, (20, self.window_size + 120))

    def add_delivery_animation(self, pos):
        """Add a new delivery animation at the given position"""
        self.delivery_animations.append({
            "pos": pos,
            "time": 20,  # Animation frames
            "frames": 20
        })

    def show_results(self, steps, competitive_ratio, delivered, total_customers):
        """Show results panel with simulation statistics and history"""
        self.show_results_panel = True
        
        # Add current simulation to history
        self.simulation_history.append({
            'steps': steps,
            'ratio': competitive_ratio,
            'delivered': delivered,
            'total': total_customers,
            'timestamp': time.strftime("%H:%M:%S", time.localtime())
        })

    def draw_results_panel(self):
        """Draw the results panel with history and buttons"""
        if not self.show_results_panel:
            return
        
        # Create panel surface
        panel_width = self.window_size - 100
        panel_height = self.window_size - 100
        panel = pygame.Surface((panel_width, panel_height))
        panel.fill((250, 250, 250))  # White background
        
        # Add border and header styling
        pygame.draw.rect(panel, (100, 100, 100), (0, 0, panel_width, panel_height), 2)
        pygame.draw.rect(panel, (52, 73, 94), (0, 0, panel_width, 50))
        
        # Add title
        title = self.title_font.render("Drone Delivery Mission Report", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=panel_width//2, centery=25)
        panel.blit(title, title_rect)
        
        # Add latest result details
        latest = self.simulation_history[-1]
        latest_y = 70
        
        # Success indicator
        success_rate = latest['delivered'] / latest['total'] * 100
        if success_rate >= 90:
            status_text = "MISSION SUCCESSFUL"
            status_color = (46, 204, 113)
        elif success_rate >= 50:
            status_text = "MISSION PARTIAL SUCCESS"
            status_color = (243, 156, 18)
        else:
            status_text = "MISSION NEEDS IMPROVEMENT"
            status_color = (231, 76, 60)
            
        status = self.header_font.render(status_text, True, status_color)
        status_rect = status.get_rect(centerx=panel_width//2, y=latest_y)
        panel.blit(status, status_rect)
        
        # Draw latest simulation results
        result_text = [
            f"Drone Fleet Mission #{len(self.simulation_history)} - {latest['timestamp']}",
            f"Flight Time: {latest['steps']} minutes",
            f"Efficiency Rating: {latest['ratio']:.2f}",
            f"Deliveries Completed: {latest['delivered']}/{latest['total']} ({success_rate:.1f}%)"
        ]
        
        for i, text in enumerate(result_text):
            result_line = self.info_font.render(text, True, self.colors["text"])
            panel.blit(result_line, (30, latest_y + 30 + i * 30))
        
        # Draw efficiency chart (simple bar)
        chart_y = latest_y + 150
        chart_label = self.header_font.render("Efficiency Analysis", True, self.colors["text"])
        panel.blit(chart_label, (30, chart_y))
        
        # Draw bar
        bar_width = 200
        bar_height = 20
        bar_x = 30
        bar_y = chart_y + 30
        # Background bar (gray)
        pygame.draw.rect(panel, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height))
        
        # Calculate efficiency percentage (competitive ratio of 1 is perfect, >3 is poor)
        efficiency = max(0, min(1, 1 / latest['ratio']))
        
        # Colored progress bar
        if efficiency > 0.7:
            bar_color = self.colors["battery_good"]
        elif efficiency > 0.4:
            bar_color = self.colors["battery_med"]
        else:
            bar_color = self.colors["battery_low"]
            
        pygame.draw.rect(panel, bar_color, (bar_x, bar_y, int(bar_width * efficiency), bar_height))
        
        # Add percentage text
        pct_text = self.small_font.render(f"{efficiency*100:.1f}%", True, (255, 255, 255))
        panel.blit(pct_text, (bar_x + 5, bar_y + 2))
        
        # Rating text
        rating_text = ["Poor", "Fair", "Good", "Excellent"][min(3, int(efficiency * 4))]
        rating = self.info_font.render(f"Rating: {rating_text}", True, self.colors["text"])
        panel.blit(rating, (bar_x + bar_width + 20, bar_y))
        
        # Draw history section
        history_y = chart_y + 80
        history_title = self.header_font.render("Mission History", True, self.colors["text"])
        panel.blit(history_title, (30, history_y))
        
        # Show history entries
        history_entries_y = history_y + 40
        max_entries = 6  # Maximum number of history entries to display
        start_idx = max(0, len(self.simulation_history) - max_entries)
        
        # Column headers
        header_text = self.small_font.render(
            f"{'#':3} {'Time':10} {'Duration':10} {'Efficiency':12} {'Deliveries':12} {'Rating':10}", 
            True, (100, 100, 100))
        panel.blit(header_text, (30, history_entries_y - 20))
        
        for i, hist in enumerate(self.simulation_history[start_idx:]):
            # Calculate efficiency and rating
            eff = max(0, min(1, 1 / hist['ratio']))
            rating = ["Poor", "Fair", "Good", "Excellent"][min(3, int(eff * 4))]
            
            # Format text
            history_line = self.small_font.render(
                f"{start_idx + i + 1:2} {hist['timestamp']:10} {hist['steps']:8}m {hist['ratio']:10.2f} "
                f"{hist['delivered']}/{hist['total']} ({hist['delivered']/hist['total']*100:.0f}%) {rating:10}",
                True, self.colors["text"]
            )
            panel.blit(history_line, (30, history_entries_y + i * 25))
        
        # Draw buttons
        button_y = panel_height - 70
        
        # Run Again button (green)
        pygame.draw.rect(panel, self.colors["button_run"], 
                        (panel_width//4 - 100, button_y, 180, 40), border_radius=5)
        run_text = self.info_font.render("Launch New Mission", True, (255, 255, 255))
        run_text_rect = run_text.get_rect(center=(panel_width//4 - 10, button_y + 20))
        panel.blit(run_text, run_text_rect)
        
        # Close button (red)
        pygame.draw.rect(panel, self.colors["button_close"], 
                        (3*panel_width//4 - 80, button_y, 180, 40), border_radius=5)
        close_text = self.info_font.render("Exit System", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=(3*panel_width//4 + 10, button_y + 20))
        panel.blit(close_text, close_text_rect)
        
        # Display panel centered on screen
        panel_x = (self.window_size - panel_width) // 2
        panel_y = (self.window_size - panel_height) // 2
        self.screen.blit(panel, (panel_x, panel_y))
        
        # Store button rectangles for click detection
        self.run_button_rect = pygame.Rect(
            panel_x + panel_width//4 - 100,
            panel_y + button_y, 
            180, 40
        )
        self.close_button_rect = pygame.Rect(
            panel_x + 3*panel_width//4 - 80,
            panel_y + button_y,
            180, 40
        )

    def update_display(self, env, agents, step, competitive_ratio, delivered=0):
        """Update the entire display"""
        # Update environment states
        self.update_wind()
        
        # Draw everything
        self._draw_sky()
        self._draw_environment()
        self._draw_drone_paths(agents)
        self._draw_customers(env.customers)
        self._draw_drones(agents)
        self._process_animations()
        self._draw_dashboard(step, competitive_ratio, delivered, len(env.customers) + delivered)
        
        # Draw results panel if active
        if self.show_results_panel:
            self.draw_results_panel()
        
        # Update display and maintain framerate
        pygame.display.flip()
        self.clock.tick(10)  # 10 FPS

    def reset_for_new_simulation(self):
        """Reset visualization state for a new simulation run"""
        self.drone_paths = {}
        self.delivery_animations = []
        self.communication_signals = []
        self.show_results_panel = False
        
        # Regenerate a new environment with different building placements
        self.environment = self._generate_environment()


def visualize(env, agents, step=0, competitive_ratio=0.0, delivered=0):
    """Main visualization function - compatibility with original simulation"""
    # Initialize if not already done
    if not hasattr(visualize, "viz"):
        visualize.viz = RealisticVisualizer(env.size)
        pygame.display.set_caption("Drone Delivery Management System")
        
    # Update the display
    visualize.viz.update_display(env, agents, step, competitive_ratio, delivered)
    
    # Check for delivery and add animation
    for agent in agents:
        for i, (cx, cy) in enumerate(env.customers[:]):
            if agent.pos == (cx, cy):
                visualize.viz.add_delivery_animation((cx, cy))
                
    return visualize.viz