#!/usr/bin/env python3

"""
Ship Classes Module
"""

import pygame
import math
import random
from ship_config import SHIP_TYPES, WORLD_WIDTH, WORLD_HEIGHT
from modules.weapons import SprayLaser, DoubleLaser, QuadLaser, BeamLaser, StandardMissile, RocketMissile, HeavyMissile, MIRVMissile

class Ship:
    next_id = 0
    def __init__(self, x, y, angle=0, is_player=False, ship_type="fighter"):
        self.id = Ship.next_id
        Ship.next_id += 1
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0
        self.target_speed = 0  # Target speed for inertia
        
        # Get ship configuration
        config = SHIP_TYPES.get(ship_type, SHIP_TYPES["fighter"])
        self.ship_type = ship_type
        self.ship_name = config["name"]
        self.ship_class = config["class"]
        self.width = config["width"]
        self.height = config["height"]
        self.color = config["color"]
        self.max_speed = config["max_speed"]
        self.turn_speed = config["turn_speed"] if is_player else config["turn_speed"] * 1.2
        self.health = config["health"]
        self.max_health = config["health"]
        self.armor = config["armor"]
        self.available_weapons = config["weapons"]
        self.fire_rate = config["fire_rate"]
        self.missile_fire_rate = config["missile_fire_rate"]
        self.accel_rate = 0.1      # normal acceleration per frame
        self.friction_rate = 0.05  # normal friction
        self.boost_max_energy = 100   # Maximum boost energy
        self.boost_energy = self.boost_max_energy  # Current energy
        self.boost_cost = 50          # Energy consumed per boost
        self.boost_recharge_rate = 0.25  # Energy per frame
        self.boost_cooldown = 30       # Frames until next boost allowed

        
        # Inertia factor (larger ships have more inertia)
        self.inertia = 0.02 + (self.width / 200) * 0.05  # Larger ships have more inertia
        
        # Subsystem health (as percentage of total health)
        self.subsystems = {
            "engines": 1.0,      # Movement capability
            "weapons": 1.0,      # Weapon functionality
            "sensors": 1.0       # Vision/targeting
        }
        
        # Weapon cooldowns
        self.reload_time = self.fire_rate
        self.missile_reload_time = self.missile_fire_rate
        self.reload_timer = 0
        self.missile_reload_timer = 0
        
        self.is_player = is_player
        self.level = 1 if is_player else 0  # Player starts at level 1

        # Player-specific attributes
        if is_player:
            self.credits = 640  # Starting credits
            self.max_credits = 100000  # Maximum credits player can hold
            
            # Player upgrades
            self.weapon_damage_multiplier = 1.0  # Weapon damage multiplier
            self.engine_speed_multiplier = 1.0    # Engine speed multiplier
            self.armor_multiplier = 1.0         # Armor protection multiplier
            self.hull_integrity = 1.0             # Hull integrity multiplier

            # Upgrade multipliers
            self.laser_damage_multiplier = 1.0
            self.fire_rate_multiplier = 1.0
            self.missile_damage_multiplier = 1.0
            self.missile_reload_speed_multiplier = 1.0
            
            # Player quests and bounties
            self.active_quests = []              # List of active quests
            self.completed_quests = []           # List of completed quests
            self.bounties = []                   # List of active bounties
            
        # Create ship image based on type
        self.create_ship_image()
        
    def create_ship_image(self):
        """Create a pygame surface with the appropriate ship design based on type"""
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw different ship shapes based on type
        if self.ship_type == "fighter":
            # Nimble fighter design
            pygame.draw.polygon(
                self.image,
                self.color,
                [
                    (self.width, self.height // 2),  # nose
                    (self.width * 0.7, 0),           # top front
                    (self.width * 0.3, 0),           # top back
                    (0, self.height // 2),           # back
                    (self.width * 0.3, self.height), # bottom back
                    (self.width * 0.7, self.height)  # bottom front
                ]
            )
            # Cockpit
            pygame.draw.ellipse(self.image, (150, 200, 255, 150), 
                               (self.width * 0.6, self.height * 0.3, 
                                self.width * 0.3, self.height * 0.4))
        elif self.ship_type == "frigate":
            # Balanced frigate design
            pygame.draw.polygon(
                self.image,
                self.color,
                [
                    (self.width, self.height // 2),  # nose
                    (self.width * 0.8, self.height * 0.1),  # top front
                    (self.width * 0.6, 0),           # top middle
                    (self.width * 0.3, self.height * 0.1),  # top back
                    (0, self.height // 2),           # back
                    (self.width * 0.3, self.height * 0.9),  # bottom back
                    (self.width * 0.6, self.height), # bottom middle
                    (self.width * 0.8, self.height * 0.9),  # bottom front
                ]
            )
            # Turrets
            pygame.draw.circle(self.image, (100, 100, 150), 
                              (self.width * 0.7, self.height * 0.3), 5)
            pygame.draw.circle(self.image, (100, 100, 150), 
                              (self.width * 0.7, self.height * 0.7), 5)
        elif self.ship_type == "cruiser":
            # Heavy cruiser design
            pygame.draw.polygon(
                self.image,
                self.color,
                [
                    (self.width, self.height // 2),  # nose
                    (self.width * 0.9, self.height * 0.1),  # top front
                    (self.width * 0.7, 0),           # top middle front
                    (self.width * 0.4, 0),           # top middle back
                    (self.width * 0.2, self.height * 0.1),  # top back
                    (0, self.height // 2),           # back
                    (self.width * 0.2, self.height * 0.9),  # bottom back
                    (self.width * 0.4, self.height), # bottom middle back
                    (self.width * 0.7, self.height), # bottom middle front
                    (self.width * 0.9, self.height * 0.9),  # bottom front
                ]
            )
            # Superstructure
            pygame.draw.rect(self.image, (100, 120, 150, 150), 
                            (self.width * 0.5, self.height * 0.2, 
                             self.width * 0.3, self.height * 0.6))
        elif self.ship_type == "destroyer":
            # Large destroyer design
            pygame.draw.polygon(
                self.image,
                self.color,
                [
                    (self.width, self.height // 2),  # nose
                    (self.width * 0.95, self.height * 0.1),  # top front
                    (self.width * 0.8, 0),           # top middle front
                    (self.width * 0.5, 0),           # top middle
                    (self.width * 0.2, 0),           # top middle back
                    (self.width * 0.05, self.height * 0.1),  # top back
                    (0, self.height // 2),           # back
                    (self.width * 0.05, self.height * 0.9),  # bottom back
                    (self.width * 0.2, self.height), # bottom middle back
                    (self.width * 0.5, self.height), # bottom middle
                    (self.width * 0.8, self.height), # bottom middle front
                    (self.width * 0.95, self.height * 0.9),  # bottom front
                ]
            )
            # Multiple decks
            pygame.draw.rect(self.image, (120, 120, 120, 150), 
                            (self.width * 0.4, self.height * 0.3, 
                             self.width * 0.4, self.height * 0.4))
        else:  # dreadnought or default
            # Massive dreadnought design
            pygame.draw.polygon(
                self.image,
                self.color,
                [
                    (self.width, self.height // 2),  # nose
                    (self.width * 0.98, self.height * 0.1),  # top front
                    (self.width * 0.9, 0),           # top front middle
                    (self.width * 0.7, 0),           # top middle front
                    (self.width * 0.4, 0),           # top middle
                    (self.width * 0.1, 0),           # top middle back
                    (self.width * 0.02, self.height * 0.1),  # top back
                    (0, self.height // 2),           # back
                    (self.width * 0.02, self.height * 0.9),  # bottom back
                    (self.width * 0.1, self.height), # bottom middle back
                    (self.width * 0.4, self.height), # bottom middle
                    (self.width * 0.7, self.height), # bottom middle front
                    (self.width * 0.9, self.height), # bottom front middle
                    (self.width * 0.98, self.height * 0.9),  # bottom front
                ]
            )
            # Multiple superstructures
            pygame.draw.rect(self.image, (130, 100, 130, 150), 
                            (self.width * 0.3, self.height * 0.2, 
                             self.width * 0.2, self.height * 0.6))
            pygame.draw.rect(self.image, (130, 100, 130, 150), 
                            (self.width * 0.6, self.height * 0.2, 
                             self.width * 0.2, self.height * 0.6))
                             
    def update(self):
        """Update ship state"""
        # Apply inertia - gradually move toward target speed
        if self.target_speed > self.speed:
            self.speed = min(self.target_speed, self.speed + self.inertia)
        elif self.target_speed < self.speed:
            self.speed = max(self.target_speed, self.speed - self.inertia)
        
        # Apply engine damage effect (reduced speed)
        effective_speed = self.speed * self.subsystems["engines"]
        
        # Simple forward movement based on angle + speed
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * effective_speed
        self.y += math.sin(rad) * effective_speed

        # Clamp inside world

        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

        # Reduce reload timers
        if self.reload_timer > 0:
            self.reload_timer -= 1

        if self.missile_reload_timer > 0:
            self.missile_reload_timer -= 1

        # --- Handle boost decay ---
        if self.is_player and hasattr(self, "boost_timer") and self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer <= 0:
                self.max_speed = self.original_max_speed

        # Reduce boost cooldown
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1

        # Reduce boost timer
        if hasattr(self, "boost_timer") and self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer <= 0:
                self.max_speed = self.original_max_speed
                self.accel_rate = self.original_accel_rate

        # Recharge boost energy
        if self.boost_energy < self.boost_max_energy:
            self.boost_energy = min(self.boost_max_energy, self.boost_energy + self.boost_recharge_rate)

            
    def draw(self, screen, offset_x=0, offset_y=0):
        screen_x = self.x - offset_x
        screen_y = self.y - offset_y
        """Draw the ship"""
        # Draw engine trails if moving
        if abs(self.speed) > 0.1:
            # Draw engine exhaust
            rad = math.radians(self.angle)
            # Position at the back of the ship
            trail_x = self.x - math.cos(rad) * (self.width * 0.3) - offset_x
            trail_y = self.y - math.sin(rad) * (self.width * 0.3) - offset_y
            
            # Draw multiple trail particles
            for i in range(3):
                offset_x_rand = random.randint(-3, 3)
                offset_y_rand = random.randint(-3, 3)
                size = random.randint(2, 5)
                pygame.draw.circle(screen, (255, 150, 50), 
                                  (int(trail_x + offset_x_rand), int(trail_y + offset_y_rand)), size)

        # rotate sprite
        rotated = pygame.transform.rotate(self.image, -self.angle)
        rect = rotated.get_rect(center=(self.x - offset_x, self.y - offset_y))
        screen.blit(rotated, rect)

        # Draw health bar only for player ship (fixed position at top-left)
        if self.is_player:
            bar_w = 100
            bar_h = 20
            health_ratio = self.health / self.max_health
            # Background
            pygame.draw.rect(screen, (100, 100, 100), (10, 10, bar_w, bar_h))
            # Health
            pygame.draw.rect(screen, (0, 255, 0), (10, 10, int(bar_w * health_ratio), bar_h))
            # Border
            pygame.draw.rect(screen, (255, 255, 255), (10, 10, bar_w, bar_h), 2)
            
            font = pygame.font.SysFont(None, 24)
            

            

        
        # Draw subsystem status bars for player ship (top-left)
        if self.is_player:
            bar_y_offset = 70
            for subsystem, health in self.subsystems.items():
                # Different colors for different subsystems
                colors = {
                    "engines": (255, 100, 100),    # Red
                    "weapons": (100, 255, 100),    # Green
                    "sensors": (100, 100, 255)     # Blue
                }
                
                color = colors.get(subsystem, (200, 200, 200))
                # Background
                pygame.draw.rect(screen, (100, 100, 100), (10, bar_y_offset, 60, 10))
                # Health
                pygame.draw.rect(screen, color, (10, bar_y_offset, int(60 * health), 10))
                # Border
                pygame.draw.rect(screen, (255, 255, 255), (10, bar_y_offset, 60, 10), 1)
                
                # Subsystem name
                font = pygame.font.SysFont(None, 16)
                name_text = font.render(subsystem[:3].upper(), True, (255, 255, 255))
                screen.blit(name_text, (12, bar_y_offset))
                
                bar_y_offset += 15
        
        # Draw weapon cooldown indicators for player at bottom of screen
        if self.is_player:
            font = pygame.font.SysFont(None, 24)
            
            # Draw laser cooldown (bottom left)
            if self.reload_time > 0:
                laser_cooldown_ratio = 1.0 - (self.reload_timer / self.reload_time) if self.reload_time > 0 else 1.0
                pygame.draw.rect(screen, (100, 100, 100), (10, 600 - 30, 100, 20))
                pygame.draw.rect(screen, (0, 200, 0), (10, 600 - 30, int(100 * laser_cooldown_ratio), 20))
                pygame.draw.rect(screen, (255, 255, 255), (10, 600 - 30, 100, 20), 2)
                cooldown_text = font.render("LASER", True, (255, 255, 255))
                screen.blit(cooldown_text, (15, 600 - 28))
            
            # Draw missile cooldown (bottom right)
            if self.missile_reload_time > 0:
                missile_cooldown_ratio = 1.0 - (self.missile_reload_timer / self.missile_reload_time) if self.missile_reload_time > 0 else 1.0
                pygame.draw.rect(screen, (100, 100, 100), (800 - 110, 600 - 30, 100, 20))
                pygame.draw.rect(screen, (200, 100, 0), (800 - 110, 600 - 30, int(100 * missile_cooldown_ratio), 20))
                pygame.draw.rect(screen, (255, 255, 255), (800 - 110, 600 - 30, 100, 20), 2)
                cooldown_text = font.render("MISSILE", True, (255, 255, 255))
                screen.blit(cooldown_text, (800 - 105, 600 - 28))

    def fire_laser(self, side="left"):
        """Fire a laser from this ship"""
        # Check if weapons are damaged
        if self.subsystems["weapons"] < 0.1:
            return None  # Weapons completely destroyed
            
        # Apply weapon damage effect (increased cooldown)
        effective_reload_time = self.reload_time / self.subsystems["weapons"]
        if self.reload_timer > 0:
            return None  # still reloading

        self.reload_timer = effective_reload_time

        # spawn position offset
        offset = 15  # distance from center (adjusted for new ship shape)
        rad = math.radians(self.angle)

        # Special case for fighters - fire forward with both buttons
        if self.ship_class == "Fighter" and side == "forward":
            # Fighters fire forward
            laser_x = self.x + math.cos(rad) * (self.width / 2 - 5)
            laser_y = self.y + math.sin(rad) * (self.width / 2 - 5)
            angle = self.angle
        else:
            # perpendicular vectors for other ships or non-forward firing
            if side == "left":
                perp_angle = rad - math.pi / 2
            else:
                perp_angle = rad + math.pi / 2

            # spawn laser slightly outside the ship
            laser_x = self.x + math.cos(perp_angle) * offset
            laser_y = self.y + math.sin(perp_angle) * offset
            angle = math.degrees(perp_angle)

        # Create appropriate laser based on ship type
        if "spray_laser" in self.available_weapons and (self.ship_class == "Fighter" and side == "forward"):
            # Fighter forward spray laser
            laser = SprayLaser(laser_x, laser_y, angle)
            laser.owner = self
            return laser
        elif "spray_laser" in self.available_weapons:
            # Other ships spray laser
            laser = SprayLaser(laser_x, laser_y, angle)
            laser.owner = self
            return laser
        elif "double_laser" in self.available_weapons:
            # Frigate - double laser
            offset_dir = -1 if side == "left" else 1
            laser = DoubleLaser(laser_x, laser_y, angle, offset_dir)
            laser.owner = self
            return laser
        elif "quad_laser" in self.available_weapons:
            # Cruiser - quad laser
            position = f"front_{side}"
            laser = QuadLaser(laser_x, laser_y, angle, position)
            laser.owner = self
            return laser
        elif "beam_laser" in self.available_weapons:
            # Destroyer/Dreadnought - beam laser
            laser = BeamLaser(laser_x, laser_y, angle)
            laser.owner = self
            return laser
            
    def fire_missile(self, side="left"):
        """Fire a missile from this ship"""
        # Check if weapons are damaged
        if self.subsystems["weapons"] < 0.1:
            return None  # Weapons completely destroyed

            
        # Apply weapon damage effect (increased cooldown)
        effective_missile_reload_time = self.missile_reload_time / self.subsystems["weapons"]
        if self.missile_reload_timer > 0:
            return None  # still reloading

        self.missile_reload_timer = effective_missile_reload_time

        # spawn position offset
        offset = 15  # distance from center (adjusted for new ship shape)
        rad = math.radians(self.angle)

        # Special case for fighters - always fire forward
        if self.ship_class == "Fighter":
            missile_x = self.x + math.cos(rad) * (self.width / 2)
            missile_y = self.y + math.sin(rad) * (self.width / 2)
            angle = self.angle
        else:
            # perpendicular vectors for other ships
            if side == "left":
                perp_angle = rad - math.pi / 2
            else:
                perp_angle = rad + math.pi / 2

            # spawn missile slightly outside the ship
            missile_x = self.x + math.cos(perp_angle) * offset
            missile_y = self.y + math.sin(perp_angle) * offset
            angle = math.degrees(perp_angle)

        # Create appropriate missile based on ship type
        if "rocket_missile" in self.available_weapons and self.ship_class == "Fighter":
            # Fighter - rocket missile
            missile = RocketMissile(missile_x, missile_y, angle)
            missile.owner = self
            return missile
        elif "standard_missile" in self.available_weapons:
            # Frigate - standard missile
            missile = StandardMissile(missile_x, missile_y, angle)
            missile.owner = self
            return missile
        elif "heavy_missile" in self.available_weapons:
            # Cruiser/Destroyer - heavy missile
            missile = HeavyMissile(missile_x, missile_y, angle)
            missile.owner = self
            return missile
        elif "mirv_missile" in self.available_weapons:
            # Dreadnought - MIRV missile
            missile = MIRVMissile(missile_x, missile_y, angle)
            missile.owner = self
            return missile

    def boost(self, speed_mult=3.0, accel_mult=1.0, duration=90, instant_accel=True):
        """Temporarily increase max speed if enough energy and not cooling down."""
        if not self.is_player:
            return

        # Only allow boost if energy is enough and cooldown is 0
        if self.boost_energy < self.boost_cost or self.boost_cooldown > 0:
            return

        # Consume energy and start cooldown
        self.boost_energy -= self.boost_cost
        self.boost_cooldown = 30  # frames until next boost

        # Setup temporary boost
        if not hasattr(self, "boost_timer"):
            self.boost_timer = 0
            self.original_max_speed = self.max_speed
            self.original_accel_rate = self.accel_rate

        # Apply boost regardless of current boost_timer
        self.max_speed = self.original_max_speed * speed_mult
        self.accel_rate = self.original_accel_rate * accel_mult
        self.boost_timer = duration

        # Instant acceleration
        if instant_accel:
            self.speed = self.max_speed
            self.target_speed = self.max_speed

    def level_up(self):
        if not self.is_player:
            return
            
        self.level += 1
        self.max_speed += 0.2  # Increase speed with each level
        
    def take_damage_to_subsystem(self, subsystem, damage):
        """Apply damage to a specific subsystem"""
        if subsystem in self.subsystems:
            # Reduce subsystem health
            self.subsystems[subsystem] = max(0.0, self.subsystems[subsystem] - (damage / self.max_health))

class AIShip(Ship):
    def __init__(self, x, y, angle=0, ship_type="fighter", behavior="passive"):
        super().__init__(x, y, angle, is_player=False, ship_type=ship_type)
        self.behavior = behavior  # hostile, passive, trader
        
        # Set team and color based on behavior
        if behavior == "hostile":
            self.team = random.choice(["British", "French", "Spanish", "Dutch"])
            self.color = self.get_team_color()
        elif behavior == "passive":
            self.team = "Trader"
            self.color = (100, 200, 100)  # Green for traders
        else:  # trader
            self.team = "Neutral"
            self.color = (200, 200, 100)  # Yellow for neutral ships
            
        # Recreate ship image with team color
        self.create_ship_image()

    def get_team_color(self):
        """Get color based on team"""
        colors = {
            "British": (100, 100, 255),   # Blue
            "French": (255, 100, 100),    # Red
            "Spanish": (255, 255, 100),   # Yellow
            "Dutch": (100, 255, 100)      # Green
        }
        return colors.get(self.team, (200, 200, 200))
