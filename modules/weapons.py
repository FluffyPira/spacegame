#!/usr/bin/env python3

"""
Simplified Live Pirate Game
A modular version of the live pirate game with improved performance
"""

import pygame
import math
import random

# ---------------------------
# Projectile Classes
# ---------------------------
class Projectile:
    def __init__(self, x, y, angle, projectile_type="laser"):
        self.x = x
        self.y = y
        self.angle = angle
        self.projectile_type = projectile_type
        self.distance_traveled = 0
        self.hit = False
        
        if projectile_type == "laser":
            self.speed = 8
            self.damage = 15
            self.color = (255, 50, 50)
            self.size = 3
        else:  # missile
            self.speed = 4
            self.damage = 30
            self.color = (200, 200, 50)
            self.size = 6
            
    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
    def draw(self, screen, offset_x=0, offset_y=0):

        screen_x = self.x - offset_x
        screen_y = self.y - offset_y

        
        if self.projectile_type == "laser":
            # Draw laser beam
            end_x = screen_x + math.cos(math.radians(self.angle)) * 10
            end_y = screen_y + math.sin(math.radians(self.angle)) * 10
            pygame.draw.line(screen, self.color, (screen_x, screen_y), (end_x, end_y), self.size)
            # Glow effect
            pygame.draw.circle(screen, (255, 150, 150), (int(screen_x), int(screen_y)), self.size + 2)
        else:  # missile
            # Draw missile
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)
            # Engine glow
            rad = math.radians(self.angle)
            engine_x = screen_x - math.cos(rad) * 8
            engine_y = screen_y - math.sin(rad) * 8
            
    def is_off_screen(self, camera_x, camera_y, screen_width, screen_height):
        # Check if projectile is outside the camera's view
        return (self.x < camera_x - 100 or self.x > camera_x + screen_width + 100 or 
                self.y < camera_y - 100 or self.y > camera_y + screen_height + 100)
                
    def collides_with(self, ship):
        """Check if projectile collides with a ship"""

        if self.distance_traveled < 50:
            return False, None
        # Only prevent collision with owner if it's a player-owned projectile
        # Allow AI projectiles to hit other ships (player or AI)
        if ship == self.owner and hasattr(self.owner, 'is_player') and self.owner.is_player:
            return False, None
        dx = self.x - ship.x
        dy = self.y - ship.y
        distance = math.sqrt(dx*dx + dy*dy)
        collision_radius = ship.width * 0.2
        if distance < collision_radius:
            self.hit = True
            if random.random() < 0.5:
                return True, "weapons"
            else:
                return True, "sensors"
        else:
            return False, None

# Specialized projectile classes
class SprayLaser(Projectile):
    def __init__(self, x, y, angle):
        super().__init__(x, y, angle + random.uniform(-5, 5), "laser")  # Spread angle
        self.speed = 15
        self.damage = 8  # Lower damage but more projectiles
        self.size = random.randint(2, 3)  # Random size for visual effect
        self.ttl = 60
    def draw(self, screen, offset_x=0, offset_y=0):

        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        pygame.draw.circle(screen, (255, 200, 50), (int(screen_x), int(screen_y)), self.size)
        # Add a trail effect
        if self.distance_traveled > 10:
            trail_x = self.x - math.cos(math.radians(self.angle)) * 5
            trail_y = self.y - math.sin(math.radians(self.angle)) * 5
            pygame.draw.circle(screen, (255, 150, 50), (int(trail_x - offset_x), int(trail_y - offset_y)), self.size//2)

class DoubleLaser(Projectile):
    def __init__(self, x, y, angle, offset_direction=1):
        super().__init__(x, y, angle, "laser")
        self.speed = 10
        self.damage = 10  # Higher damage
        self.offset_direction = offset_direction  # -1 for left, 1 for right
        
    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
    def draw(self, screen, offset_x=0, offset_y=0):

        # Draw a thicker, more powerful laser
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        offset = 3 * self.offset_direction
        start_x = screen_x + math.cos(math.radians(self.angle + 90)) * offset
        start_y = screen_y + math.sin(math.radians(self.angle + 90)) * offset
        end_x = start_x + math.cos(math.radians(self.angle)) * 15
        end_y = start_y + math.sin(math.radians(self.angle)) * 15
        pygame.draw.line(screen, (50, 150, 255), (start_x, start_y), (end_x, end_y), 4)
        # Add glow effect
        for i in range(2):
            width = 6 - i*2
            pygame.draw.circle(screen, (100, 180, 255), (int(start_x), int(start_y)), width)

class QuadLaser(Projectile):
    def __init__(self, x, y, angle, position="front_left"):
        super().__init__(x, y, angle, "laser")
        self.speed = 10
        self.damage = 12
        self.position = position  # "front_left", "front_right", "back_left", "back_right"
        
    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
    def draw(self, screen, offset_x=0, offset_y=0):

        # Draw a very powerful laser
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        # Position offset based on laser position
        offsets = {
            "front_left": (-5, -2),
            "front_right": (5, -2),
            "back_left": (-5, 2),
            "back_right": (5, 2)
        }
        offset_x_val, offset_y_val = offsets.get(self.position, (0, 0))
        
        start_x = screen_x + offset_x_val
        start_y = screen_y + offset_y_val
        end_x = start_x + math.cos(math.radians(self.angle)) * 20
        end_y = start_y + math.sin(math.radians(self.angle)) * 20
        pygame.draw.line(screen, (255, 50, 150), (start_x, start_y), (end_x, end_y), 5)
        # Add intense glow effect
        for i in range(3):
            width = 8 - i*2
            pygame.draw.circle(screen, (255, 100, 200), (int(start_x), int(start_y)), width)

class BeamLaser(Projectile):
    def __init__(self, x, y, angle):
        super().__init__(x, y, angle, "laser")
        self.speed = 0  # Instant hit
        self.damage = 15  # Very high damage
        self.max_range = 600
        self.beam_width = 8
        self.life_time = 30  # Frames the beam exists
        
    def update(self):
        self.life_time -= 1
        self.distance_traveled += 1
        
    def draw(self, screen, offset_x=0, offset_y=0):
        # Draw a wide beam effect
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        end_x = screen_x + math.cos(math.radians(self.angle)) * self.max_range
        end_y = screen_y + math.sin(math.radians(self.angle)) * self.max_range
        
        # Draw the main beam
        pygame.draw.line(screen, (255, 255, 100), (screen_x, screen_y), (end_x, end_y), self.beam_width)
        
        # Draw glow effect
        for i in range(3):
            width = self.beam_width + 4 - i*2
            alpha = 200 - i*50
            pygame.draw.line(screen, (255, 200, 100), (screen_x, screen_y), (end_x, end_y), width)
            
    def is_off_screen(self, camera_x, camera_y, screen_width, screen_height):
        return self.life_time <= 0
        
    def collides_with(self, ship):
        if ship == self.owner:
            return False, None
            
        # For beam weapons, we'll do a line collision check
        dx = ship.x - self.x
        dy = ship.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Calculate beam start and end points in world coordinates
        beam_start_x = self.x
        beam_start_y = self.y
        beam_end_x = self.x + math.cos(math.radians(self.angle)) * self.max_range
        beam_end_y = self.y + math.sin(math.radians(self.angle)) * self.max_range

        # Calculate perpendicular distance from ship's center to the beam line segment
        # Vector for the beam
        v_x = beam_end_x - beam_start_x
        v_y = beam_end_y - beam_start_y

        # Vector from beam start to ship
        w_x = ship.x - beam_start_x
        w_y = ship.y - beam_start_y

        # Dot product
        c1 = w_x * v_x + w_y * v_y

        # Length squared of beam
        c2 = v_x * v_x + v_y * v_y

        if c2 == 0: # Beam is a point, check distance to start point
            distance_to_beam = math.sqrt(w_x**2 + w_y**2)
            closest_x = beam_start_x
            closest_y = beam_start_y
        elif c1 < 0: # Closest point is beam_start
            distance_to_beam = math.sqrt(w_x**2 + w_y**2)
            closest_x = beam_start_x
            closest_y = beam_start_y
        elif c1 > c2: # Closest point is beam_end
            distance_to_beam = math.sqrt((ship.x - beam_end_x)**2 + (ship.y - beam_end_y)**2)
            closest_x = beam_end_x
            closest_y = beam_end_y
        else: # Closest point is on the segment
            b = c1 / c2
            closest_x = beam_start_x + b * v_x
            closest_y = beam_start_y + b * v_y
            distance_to_beam = math.sqrt((ship.x - closest_x)**2 + (ship.y - closest_y)**2)

        # Check if the ship is within the beam's width and within the beam's length
        # Approximate ship as a circle with radius ship.width / 2
        

        if distance_to_beam < (self.beam_width / 2) + (ship.width / 2):
            # Ship is hit by the beam
            subsystems = ["engines", "weapons", "sensors"]
            return True, random.choice(subsystems)
        return False, None

class StandardMissile(Projectile):
    def __init__(self, x, y, angle, target=None):
        super().__init__(x, y, angle, "missile")
        self.speed = 6
        self.damage = 10
        self.target = target
        self.homing_strength = 0.1
        self.ttl = 120  # Time to live in frames
        self.turn_speed = 2  # Degrees per frame
        
    def update(self):
        self.ttl -= 1
        if self.ttl <= 0:
            self.hit = True

        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
        # Homing behavior
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += angle_diff * self.homing_strength
    def draw(self, screen, offset_x=0, offset_y=0):
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        rad = math.radians(self.angle)
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)
        
        # Draw fins
        fin_length = 8
        fin_angle1 = rad + math.pi/2
        fin_angle2 = rad - math.pi/2
        fin1_x = screen_x + math.cos(fin_angle1) * fin_length
        fin1_y = screen_y + math.sin(fin_angle1) * fin_length
        fin2_x = screen_x + math.cos(fin_angle2) * fin_length
        fin2_y = screen_y + math.sin(fin_angle2) * fin_length
        pygame.draw.line(screen, (180, 180, 100), (screen_x, screen_y), (fin1_x, fin1_y), 3)
        pygame.draw.line(screen, (180, 180, 100), (screen_x, screen_y), (fin2_x, fin2_y), 3)
        
        # Draw engine glow
        engine_x = screen_x - math.cos(rad) * 8
        engine_y = screen_y - math.sin(rad) * 8
        pygame.draw.circle(screen, (255, 150, 50), (int(engine_x), int(engine_y)), 4)
        
        # Draw lock-on indicator if tracking a target
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < 300:
                pygame.draw.line(screen, (255, 50, 50, 100), (screen_x, screen_y), (self.target.x - offset_x, self.target.y - offset_y), 1)
                pygame.draw.circle(screen, (255, 50, 50), (int(self.target.x - offset_x), int(self.target.y - offset_y)), 10, 2)

class RocketMissile(Projectile):
    def __init__(self, x, y, angle, target=None):
        super().__init__(x, y, angle, "missile")
        self.speed = 6  # Faster than regular missiles
        self.damage = 20  # Moderate damage
        self.target = target
        self.homing_strength = 0.05  # Limited homing - seeks rear of ships
        self.trail_particles = []
        
    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
        # Add trail particles
        if len(self.trail_particles) > 10:
            self.trail_particles.pop(0)
        self.trail_particles.append((self.x, self.y))
        
        # Limited homing - aim for the rear of the target
        if self.target:
            # Calculate position behind the target
            rear_x = self.target.x - math.cos(math.radians(self.target.angle)) * 30
            rear_y = self.target.y - math.sin(math.radians(self.target.angle)) * 30
            dx = rear_x - self.x
            dy = rear_y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += angle_diff * self.homing_strength
            
    def draw(self, screen, offset_x=0, offset_y=0):
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        rad = math.radians(self.angle)
        pygame.draw.circle(screen, (220, 100, 100), (int(screen_x), int(screen_y)), 5)
        
        # Draw fins
        fin_length = 6
        fin_angle1 = rad + math.pi/2
        fin_angle2 = rad - math.pi/2
        fin1_x = screen_x + math.cos(fin_angle1) * fin_length
        fin1_y = screen_y + math.sin(fin_angle1) * fin_length
        fin2_x = screen_x + math.cos(fin_angle2) * fin_length
        fin2_y = screen_y + math.sin(fin_angle2) * fin_length
        pygame.draw.line(screen, (180, 80, 80), (screen_x, screen_y), (fin1_x, fin1_y), 2)
        pygame.draw.line(screen, (180, 80, 80), (screen_x, screen_y), (fin2_x, fin2_y), 2)
        
        # Draw engine glow
        engine_x = screen_x - math.cos(rad) * 6
        engine_y = screen_y - math.sin(rad) * 6
        pygame.draw.circle(screen, (255, 180, 50), (int(engine_x), int(engine_y)), 3)
        
        # Draw trail
        for i, (trail_x, trail_y) in enumerate(self.trail_particles):
            alpha = int(255 * (i / len(self.trail_particles)))
            radius = max(1, int(3 * (i / len(self.trail_particles))))
            pygame.draw.circle(screen, (255, 150, 50), (int(trail_x - offset_x), int(trail_y - offset_y)), radius)

class HeavyMissile(Projectile):
    def __init__(self, x, y, angle, target=None):
        super().__init__(x, y, angle, "missile")
        self.speed = 3  # Slower but more powerful
        self.damage = 50  # High damage
        self.target = target
        self.homing_strength = 0.15  # Stronger homing
        self.size = 10  # Larger visual size
        self.can_be_destroyed = True  # Can be shot down
        self.health = 20  # Health points for destruction
        
    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += angle_diff * self.homing_strength
            
    def draw(self, screen, offset_x=0, offset_y=0):
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        rad = math.radians(self.angle)
        # Draw heavy missile body
        pygame.draw.circle(screen, (100, 200, 100), (int(screen_x), int(screen_y)), self.size)
        
        # Draw larger fins
        fin_length = 12
        fin_angle1 = rad + math.pi/2
        fin_angle2 = rad - math.pi/2
        fin1_x = screen_x + math.cos(fin_angle1) * fin_length
        fin1_y = screen_y + math.sin(fin_angle1) * fin_length
        fin2_x = screen_x + math.cos(fin_angle2) * fin_length
        fin2_y = screen_y + math.sin(fin_angle2) * fin_length
        pygame.draw.line(screen, (80, 180, 80), (screen_x, screen_y), (fin1_x, fin1_y), 4)
        pygame.draw.line(screen, (80, 180, 80), (screen_x, screen_y), (fin2_x, fin2_y), 4)
        
        # Draw engine glow
        engine_x = screen_x - math.cos(rad) * 10
        engine_y = screen_y - math.sin(rad) * 10
        pygame.draw.circle(screen, (150, 255, 100), (int(engine_x), int(engine_y)), 6)
        
        # Draw lock-on indicator if tracking a target
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < 400:
                pygame.draw.line(screen, (100, 255, 100, 150), (screen_x, screen_y), (self.target.x - offset_x, self.target.y - offset_y), 2)
                pygame.draw.circle(screen, (100, 255, 100), (int(self.target.x - offset_x), int(self.target.y - offset_y)), 15, 3)
                
    def take_damage(self, damage):
        """Allow missile to be destroyed by enemy fire"""
        self.health -= damage
        return self.health <= 0

class MIRVMissile(Projectile):
    def __init__(self, x, y, angle, target=None):
        super().__init__(x, y, angle, "missile")
        self.speed = 2  # Very slow but devastating
        self.damage = 30  # Base damage for main warhead
        self.target = target
        self.homing_strength = 0.08  # Moderate homing
        self.size = 15  # Very large visual size
        self.exploded = False  # Whether it has exploded
        self.submunitions = []  # Submunitions after explosion
        self.max_range = 800  # Maximum range before exploding
        
    def update(self):
        if self.exploded:
            # Update submunitions
            for sub in self.submunitions[:]:
                sub.update()
                if sub.distance_traveled > 200:  # Use a fixed value instead of accessing sub.max_range
                    self.submunitions.remove(sub)
            return
            
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
        # Check if we should explode (close to target or max range)
        should_explode = False
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < 100:  # Explode when close to target
                should_explode = True
        elif self.distance_traveled > self.max_range * 0.8:  # Explode near max range
            should_explode = True
            
        if should_explode:
            self.explode()
            
        if self.target and not self.exploded:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += angle_diff * self.homing_strength
            
    def explode(self):
        """Create submunitions when missile explodes"""
        self.exploded = True
        # Create 8 submunitions in different directions
        for i in range(8):
            sub_angle = self.angle + (i * 45)  # 8 directions, 45 degrees apart
            sub = MIRVSubmunition(self.x, self.y, sub_angle)
            sub.owner = self.owner
            self.submunitions.append(sub)

    def draw(self, screen, offset_x=0, offset_y=0):
        if self.exploded:
            # Draw submunitions
            for sub in self.submunitions:
                sub.draw(screen, offset_x, offset_y)
            return

        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        rad = math.radians(self.angle)
        # Draw MIRV missile body
        pygame.draw.circle(screen, (200, 100, 200), (int(screen_x), int(screen_y)), self.size)
        
        # Draw large fins
        fin_length = 15
        fin_angle1 = rad + math.pi/3
        fin_angle2 = rad - math.pi/3
        fin_angle3 = rad + math.pi/1.5
        fin_angle4 = rad - math.pi/1.5
        fins = [(fin_angle1, fin_length), (fin_angle2, fin_length), 
                (fin_angle3, fin_length/2), (fin_angle4, fin_length/2)]
        for fin_angle, length in fins:
            fin_x = screen_x + math.cos(fin_angle) * length
            fin_y = screen_y + math.sin(fin_angle) * length
            pygame.draw.line(screen, (180, 80, 180), (screen_x, screen_y), (fin_x, fin_y), 5)
        
        # Draw engine glow
        engine_x = screen_x - math.cos(rad) * 12
        engine_y = screen_y - math.sin(rad) * 12
        pygame.draw.circle(screen, (255, 150, 255), (int(engine_x), int(engine_y)), 8)
        
        # Draw warning indicator
        pygame.draw.circle(screen, (255, 200, 255), (int(screen_x), int(screen_y)), self.size + 5, 2)
        
    def is_off_screen(self, camera_x, camera_y, screen_width, screen_height):
        if self.exploded:
            return len(self.submunitions) == 0
        return (self.x < camera_x - 100 or self.x > camera_x + screen_width + 100 or 
                self.y < camera_y - 100 or self.y > camera_y + screen_height + 100)
                
    def collides_with(self, ship):
        if self.exploded:
            # Check submunitions for collisions
            for sub in self.submunitions[:]:
                hit, subsystem = sub.collides_with(ship)
                if hit:
                    return True, subsystem
            return False, None
            
        if ship == self.owner:
            return False, None
        dx = self.x - ship.x
        dy = self.y - ship.y
        distance = math.sqrt(dx*dx + dy*dy)
        collision_radius = 40

        if distance < collision_radius:
            subsystems = ["engines", "weapons", "sensors"]
            return True, random.choice(subsystems)
        return False, None

class MIRVSubmunition:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 6  # Fast submunitions
        self.damage = 15  # Lower damage per submunition
        self.owner = None
        self.distance_traveled = 0
        self.max_range = 200
        self.size = 3
        
    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed
        
    def draw(self, screen, offset_x=0, offset_y=0):
        # Draw small explosive submunition
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        pygame.draw.circle(screen, (255, 50, 150), (int(screen_x), int(screen_y)), self.size)
        pygame.draw.circle(screen, (255, 200, 255), (int(screen_x), int(screen_y)), self.size//2)
        
    def is_off_screen(self, camera_x, camera_y, screen_width, screen_height):
        return (self.x < camera_x - 100 or self.x > camera_x + screen_width + 100 or 
                self.y < camera_y - 100 or self.y > camera_y + screen_height + 100)
                
    def collides_with(self, ship):
        if ship == self.owner:
            return False, None
        dx = self.x - ship.x
        dy = self.y - ship.y
        distance = math.sqrt(dx*dx + dy*dy)
        collision_radius = 15

        if distance < collision_radius:
            subsystems = ["engines", "weapons", "sensors"]
            return True, random.choice(subsystems)
        return False, None
