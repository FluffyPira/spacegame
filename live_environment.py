import pygame
import math
import random
import pygame.gfxdraw # Import for anti-aliased drawing

# ---------------------------
# Game Constants
# ---------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
FPS = 30
WORLD_WIDTH, WORLD_HEIGHT = 5000, 5000

# ---------------------------
# Live Environment with Dynamic Ships
# ---------------------------
class LiveEnvironment:
    def __init__(self):
        self.width = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        self.camera_x = 0
        self.camera_y = 0
        self.stars = []
        self.nebulae = [] # Initialize nebulae list
        self.generate_background()
        
    def generate_background(self):
        """Generate background elements"""
        # Create stars for parallax effect
        for _ in range(300):
            self.stars.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(1, 3),
                'brightness': random.randint(150, 255),
                'layer': random.randint(1, 3)
            })

        # Generate nebulae
        for _ in range(random.randint(5, 10)): # 5 to 10 nebulae
            color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)) # Brighter colors
            radius = random.randint(200, 800)
            alpha = random.randint(100, 180) # Higher alpha for more visibility (approx 0.4 to 0.7)

            # Create a surface for the nebula with per-pixel alpha
            nebula_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            
            # Draw multiple overlapping circles to create a puffy effect
            for _ in range(random.randint(5, 10)): # Draw 5 to 10 smaller circles
                sub_radius = random.randint(radius // 4, int(radius * 0.75))
                sub_x = random.randint(int(radius * 2 - radius * 1.5), int(radius * 2 + radius * 1.5))
                sub_y = random.randint(int(radius * 2 - radius * 1.5), int(radius * 2 + radius * 1.5))
                sub_alpha = random.randint(alpha // 2, alpha)
                
                pygame.gfxdraw.filled_circle(nebula_surface, sub_x, sub_y, sub_radius, (*color, sub_alpha))
                pygame.gfxdraw.aacircle(nebula_surface, sub_x, sub_y, sub_radius, (*color, sub_alpha))

            self.nebulae.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'radius': radius,
                'color': color,
                'alpha': alpha,
                'layer': random.uniform(0.05, 0.2), # Slower parallax for nebulae
                'surface': nebula_surface # Store the pre-rendered surface
            })
            
    def update(self, player_x, player_y):
        """Update environment based on player position"""
        # Center camera on player
        self.camera_x = player_x - SCREEN_WIDTH // 2
        self.camera_y = player_y - SCREEN_HEIGHT // 2
        
        # Keep camera within world bounds
        self.camera_x = max(0, min(self.camera_x, self.width - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.height - SCREEN_HEIGHT))
            
    def draw(self, screen):
        """Draw the environment"""
        # Draw nebulae with parallax effect
        for nebula in self.nebulae:
            parallax_x = nebula['x'] - (self.camera_x * nebula['layer'])
            parallax_y = nebula['y'] - (self.camera_y * nebula['layer'])

            screen_x = parallax_x - self.camera_x
            screen_y = parallax_y - self.camera_y

            # Only draw if on screen (check bounding box overlap)
            if screen_x + nebula['radius'] * 2 > 0 and screen_x - nebula['radius'] * 2 < SCREEN_WIDTH and \
               screen_y + nebula['radius'] * 2 > 0 and screen_y - nebula['radius'] * 2 < SCREEN_HEIGHT:
                
                # Blit the pre-rendered nebula surface to the main screen
                screen.blit(nebula['surface'], (int(screen_x - nebula['radius'] * 2), int(screen_y - nebula['radius'] * 2)))
        # Draw stars with parallax effect
        for star in self.stars:
            # Apply parallax based on star layer
            parallax_x = star['x'] - (self.camera_x * (star['layer'] * 0.1))
            parallax_y = star['y'] - (self.camera_y * (star['layer'] * 0.1))
            
            # Only draw if on screen
            screen_x = parallax_x - self.camera_x
            screen_y = parallax_y - self.camera_y
            if 0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT:
                pygame.draw.circle(screen, 
                                  (255, 255, 255), 
                                  (int(screen_x), int(screen_y)), 
                                  star['size'])

# ---------------------------
# Dynamic Ship Spawner
# ---------------------------
class ShipSpawner:
    def __init__(self, player_ship, lasers_list):
        self.player_ship = player_ship
        self.lasers_list = lasers_list
        self.ships = []
        self.spawn_timer = 0
        self.spawn_rate = 120  # Spawn every 2 seconds at 60 FPS
        
    def update(self):
        """Update ship spawning and existing ships"""
        self.spawn_timer += 1
        
        # Spawn new ships
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            self.spawn_ship()
            
        # Update existing ships
        for ship in self.ships[:]:
            ship.update()
            
            # Remove ships that are too far from player or outside world bounds
            dx = ship.x - self.player_ship.x
            dy = ship.y - self.player_ship.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Check if ship is too far from player or outside world bounds
            if distance > 800 or \
               ship.x < -50 or ship.x > WORLD_WIDTH + 50 or \
               ship.y < -50 or ship.y > WORLD_HEIGHT + 50:  # Add a small buffer
                if ship in self.ships:
                    self.ships.remove(ship)
                
    def spawn_ship(self):
        """Spawn a new ship in the world"""
        from modules.ship import AIShip
        # Determine spawn position (outside screen bounds but near player's view)
        side = random.randint(0, 3)  # 0=top, 1=right, 2=bottom, 3=left
        spawn_distance = max(SCREEN_WIDTH, SCREEN_HEIGHT) // 2 + 100 # Spawn just outside screen + margin

        if side == 0:  # Top
            x = random.randint(int(self.player_ship.x - spawn_distance), int(self.player_ship.x + spawn_distance))
            y = self.player_ship.y - spawn_distance
        elif side == 1:  # Right
            x = self.player_ship.x + spawn_distance
            y = random.randint(int(self.player_ship.y - spawn_distance), int(self.player_ship.y + spawn_distance))
        elif side == 2:  # Bottom
            x = random.randint(int(self.player_ship.x - spawn_distance), int(self.player_ship.x + spawn_distance))
            y = self.player_ship.y + spawn_distance
        else:  # Left
            x = self.player_ship.x - spawn_distance
            y = random.randint(int(self.player_ship.y - spawn_distance), int(self.player_ship.y + spawn_distance))

        # Clamp spawn position to world bounds
        x = max(0, min(x, WORLD_WIDTH))
        y = max(0, min(y, WORLD_HEIGHT))
            
        # Choose ship type (weighted toward smaller ships)
        from ship_config import SHIP_TYPES
        ship_types = list(SHIP_TYPES.keys())
        weights = [40, 30, 20, 7, 3]  # Fighter, Frigate, Cruiser, Destroyer, Dreadnought
        ship_type = random.choices(ship_types, weights=weights, k=1)[0]
        
        # Create ship with random behavior
        behavior = random.choices(['trader', 'observer', 'passive', 'hostile'], weights=[40, 15, 15, 30], k=1)[0]
        new_ship = AIShip(x, y, ship_type=ship_type, behavior=behavior)
        
        # Set initial direction based on behavior
        if behavior == 'hostile':
            # Point toward player
            dx = self.player_ship.x - x
            dy = self.player_ship.y - y
            new_ship.angle = math.degrees(math.atan2(dy, dx))
            new_ship.speed = new_ship.max_speed * 0.7
        elif behavior == 'passive':
            # Point away from player
            dx = x - self.player_ship.x
            dy = y - self.player_ship.y
            new_ship.angle = math.degrees(math.atan2(dy, dx))
            new_ship.speed = new_ship.max_speed * 0.5
        else: # trader
            # Move in random direction
            new_ship.angle = random.randint(0, 360)
            new_ship.speed = new_ship.max_speed * 0.6
            
        self.ships.append(new_ship)
        
    def draw(self, screen, camera_x, camera_y):
        """Draw all spawned ships"""
        for ship in self.ships:
            # Convert world coordinates to screen coordinates
            screen_x = ship.x - camera_x
            screen_y = ship.y - camera_y
            
            # Only draw if on screen
            if -50 <= screen_x <= SCREEN_WIDTH + 50 and -50 <= screen_y <= SCREEN_HEIGHT + 50:
                ship.draw(screen, offset_x=-camera_x, offset_y=-camera_y)
