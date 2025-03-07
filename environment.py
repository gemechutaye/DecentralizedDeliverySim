import numpy as np

class Environment:
    def __init__(self, size=20, num_customers=3):
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.customers = [(np.random.randint(0, size), np.random.randint(0, size)) 
                         for _ in range(num_customers)]
        self.step_count = 0

    def move_customers(self):
        if self.step_count % 5 == 0:  # Move every 5 steps
            for i, (x, y) in enumerate(self.customers):
                dx, dy = np.random.choice([-1, 0, 1]), np.random.choice([-1, 0, 1])
                new_x, new_y = max(0, min(self.size-1, x + dx)), max(0, min(self.size-1, y + dy))
                self.customers[i] = (new_x, new_y)
        self.step_count += 1