import numpy as np
import random
import math
from collections import defaultdict

class Agent:
    def __init__(self, id, pos, is_byzantine=False):
        self.id = id
        self.pos = pos  # (x, y) tuple
        self.is_byzantine = is_byzantine
        self.knowledge = {}  # {customer_id: (x, y)}
        self.step = 0
        
        # Path-finding and movement patterns
        self.direction = 0  # 0: right, 1: down, 2: left, 3: up
        self.spiral_directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, down, left, up
        self.spiral_length = 1  # Current length of spiral arm
        self.steps_in_current_direction = 0
        self.turns_taken = 0
        
        # Agent state and attributes
        self.battery = 100.0  # Battery percentage (0-100)
        self.battery_drain_rate = random.uniform(0.08, 0.12)  # Battery drain per step
        self.carrying_package = False
        self.target_customer = None
        self.returning_to_base = False
        
        # Physical simulation properties
        self.max_speed = 1.0
        self.current_speed = 1.0
        self.rotation = 0.0  # in degrees, 0 = east, 90 = south
        self.acceleration = 0.1
        self.turning_rate = 15  # degrees per step
        
        # Visual elements for simulation
        self.last_positions = []  # Track position history for path visualization
        self.message_cooldown = 0  # Cooldown for showing messages
        self.delivery_attempt = False  # Flag for delivery animation
        
        # Byzantine behavior settings (if is_byzantine)
        self.lie_probability = 0.7  # Probability of reporting false information
        self.distortion_range = (-5, 5)  # Range for distorting coordinates

    def drain_battery(self):
        """Simulate battery drainage"""
        # Higher speed = more battery usage
        speed_factor = self.current_speed / self.max_speed
        self.battery -= self.battery_drain_rate * speed_factor * random.uniform(0.9, 1.1)
        self.battery = max(0, self.battery)
        return self.battery > 0  # Return True if battery is not depleted

    def apply_wind(self, wind_dx, wind_dy):
        """Apply wind effects to drone position"""
        # Only apply if the drone is actually moving
        if self.current_speed > 0:
            # Calculate random wind effect (more pronounced at higher altitudes)
            # For simplicity, we'll just add a small offset to the position
            x, y = self.pos
            x += wind_dx * random.uniform(0, 0.5)
            y += wind_dy * random.uniform(0, 0.5)
            
            # Ensure position remains within grid
            x = max(0, min(int(x), 19))
            y = max(0, min(int(y), 19))
            self.pos = (x, y)

    def move(self, env):
        """Move based on knowledge and state"""
        # Check if battery is depleted
        if not self.drain_battery():
            # Battery is dead, drone cannot move
            return
        
        # Byzantine agents sometimes move erratically
        if self.is_byzantine and random.random() < 0.1:
            self._move_random(env)
            return
            
        # Choose movement strategy based on knowledge
        if self.knowledge and not self.is_byzantine:
            # Target-seeking movement when we know customer locations
            self._move_toward_target(env)
        else:
            # Spiral search pattern when we don't know targets or if Byzantine
            self._move_spiral(env)
            
        # Observe environment after moving
        self.observe(env)
        
        # Keep track of position history (for visualization)
        self.last_positions.append(self.pos)
        if len(self.last_positions) > 20:  # Limit history length
            self.last_positions.pop(0)

    def _move_random(self, env):
        """Move randomly - used by Byzantine agents occasionally"""
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        
        # Update position within grid bounds
        new_x = max(0, min(env.size-1, self.pos[0] + dx))
        new_y = max(0, min(env.size-1, self.pos[1] + dy))
        self.pos = (new_x, new_y)
        self.step += 1

    def _move_toward_target(self, env):
        """Move toward the nearest known customer with realistic movement"""
        # Find nearest customer from our knowledge
        nearest_customer_id = None
        nearest_distance = float('inf')
        
        for cid, pos in self.knowledge.items():
            distance = math.sqrt((pos[0] - self.pos[0])**2 + (pos[1] - self.pos[1])**2)  # Euclidean
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_customer_id = cid
        
        if nearest_customer_id is not None:
            target = self.knowledge[nearest_customer_id]
            
            # Calculate direction to target 
            dx = target[0] - self.pos[0]
            dy = target[1] - self.pos[1]
            
            # Calculate target angle
            target_angle = math.degrees(math.atan2(dy, dx))
            if target_angle < 0:
                target_angle += 360
                
            # Gradually turn toward target (realistic turning)
            angle_diff = ((target_angle - self.rotation + 180) % 360) - 180
            if abs(angle_diff) > self.turning_rate:
                # Cannot turn instantly, turn gradually
                if angle_diff > 0:
                    self.rotation = (self.rotation + self.turning_rate) % 360
                else:
                    self.rotation = (self.rotation - self.turning_rate) % 360
            else:
                # Close enough to target angle, set exactly
                self.rotation = target_angle
            
            # Move forward in current rotation direction
            move_dx = math.cos(math.radians(self.rotation)) * self.current_speed
            move_dy = math.sin(math.radians(self.rotation)) * self.current_speed
            
            # Add small random movement occasionally to avoid getting stuck
            if random.random() < 0.1:
                move_dx += random.uniform(-0.2, 0.2)
                move_dy += random.uniform(-0.2, 0.2)
            
            # Update position within grid bounds
            new_x = max(0, min(env.size-1, int(self.pos[0] + move_dx)))
            new_y = max(0, min(env.size-1, int(self.pos[1] + move_dy)))
            self.pos = (new_x, new_y)
            self.step += 1
        else:
            # Fall back to spiral search if no valid target
            self._move_spiral(env)

    def _move_spiral(self, env):
        """Move in an outward spiral pattern to search efficiently"""
        # Get current direction vector
        dx, dy = self.spiral_directions[self.direction]
        
        # Calculate new position
        new_x = max(0, min(env.size-1, self.pos[0] + dx))
        new_y = max(0, min(env.size-1, self.pos[1] + dy))
        
        # Update rotation based on direction
        target_rotations = [0, 90, 180, 270]  # Right, down, left, up
        target_rotation = target_rotations[self.direction]
        
        # Gradually turn to target rotation
        angle_diff = ((target_rotation - self.rotation + 180) % 360) - 180
        if abs(angle_diff) > self.turning_rate:
            # Turn gradually
            if angle_diff > 0:
                self.rotation = (self.rotation + self.turning_rate) % 360
            else:
                self.rotation = (self.rotation - self.turning_rate) % 360
        else:
            # Close enough to target rotation
            self.rotation = target_rotation
        
        # Check if we hit a boundary and need to adjust
        if new_x == self.pos[0] and new_y == self.pos[1]:
            # We couldn't move in the desired direction (hit boundary)
            # Change direction and try again
            self.direction = (self.direction + 1) % 4
            dx, dy = self.spiral_directions[self.direction]
            new_x = max(0, min(env.size-1, self.pos[0] + dx))
            new_y = max(0, min(env.size-1, self.pos[1] + dy))
        
        # Update position
        self.pos = (new_x, new_y)
        self.step += 1
        
        # Increment steps in current direction
        self.steps_in_current_direction += 1
        
        # Check if we need to turn
        if self.steps_in_current_direction >= self.spiral_length:
            self.direction = (self.direction + 1) % 4
            self.steps_in_current_direction = 0
            self.turns_taken += 1
            
            # Increase spiral arm length every 2 turns
            if self.turns_taken % 2 == 0:
                self.spiral_length += 1

    def observe(self, env):
        """Observe customers within sensing range"""
        for i, (cx, cy) in enumerate(env.customers):
            # Check if customer is within sensing range (Euclidean distance ≤ 3)
            distance = math.sqrt((cx - self.pos[0])**2 + (cy - self.pos[1])**2)
            
            if distance <= 3:
                if not self.is_byzantine:
                    # Honest agent reports true coordinates
                    self.knowledge[i] = (cx, cy)
                    self.message_cooldown = 5  # Show message for 5 steps
                else:
                    # Byzantine agent may lie
                    if random.random() < self.lie_probability:
                        # Report false position
                        fake_x = cx + random.randint(*self.distortion_range)
                        fake_y = cy + random.randint(*self.distortion_range)
                        # Keep within grid bounds
                        fake_x = max(0, min(env.size-1, fake_x))
                        fake_y = max(0, min(env.size-1, fake_y))
                        self.knowledge[i] = (fake_x, fake_y)
                    else:
                        # Occasionally report true position
                        self.knowledge[i] = (cx, cy)
                    self.message_cooldown = 5

    def share_knowledge(self):
        """Share knowledge with other agents"""
        # Reduce message cooldown if active
        if self.message_cooldown > 0:
            self.message_cooldown -= 1
            
        # Battery low agents may not always be able to communicate reliably
        if self.battery < 20 and random.random() < 0.3:
            # Battery too low to transmit reliable data
            return {}
            
        return self.knowledge.copy()  # Return a copy to prevent inadvertent modifications