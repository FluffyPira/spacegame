#!/usr/bin/env python3

"""
Main Game Module
Ties all modules together into a cohesive game
"""

import pygame
import sys
import math
import random

# Import our modules
from ship_config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WORLD_WIDTH, WORLD_HEIGHT, BG_COLOR, SHIP_TYPES
from modules.ship import Ship, AIShip
from modules.weapons import SprayLaser, DoubleLaser, QuadLaser, BeamLaser, StandardMissile, RocketMissile, HeavyMissile, MIRVMissile
from modules.docking import StationManager, DockingMenu
from title_screen import TitleScreen, GAME_FONT
from live_environment import LiveEnvironment, ShipSpawner
from ai import EnemyAI

# ---------------------------
# Game Environment Classes
# ---------------------------

# ... [rest of the environment classes that were in the original file]

# ---------------------------
# Main Game Class
# ---------------------------
class LivePirateGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()  # Initialize font module
        self.screen_width = 640
        self.screen_height = 480
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("LIVE PIRATE ADVENTURES")
        self.clock = pygame.time.Clock()

        # Show title screen first
        self.title_screen = TitleScreen(self.screen)


        # Game entities
        self.player = Ship(1000, 1000, is_player=True, ship_type="fighter")

        self.environment = LiveEnvironment()
        self.player_weapons = []  # Track player-fired weapons
        self.ai_weapons = []      # Track AI-fired weapons
        self.ship_spawner = ShipSpawner(self.player, self.ai_weapons)
        self.station_manager = StationManager()  # Add station manager
        self.enemy_ais = {}

        self.enemy_kills = 0

        self.map_visible = True
        self.last_d_key_state = False  # Track docking key state
        
        # Docking menu system
        self.docking_menu = None
        self.docking_menu_active = False

        self.running = True
        self.game_state = "title"
        self.firing_laser = False # New flag for auto-fire

    def handle_input(self):
        """Handle player input"""
        keys = pygame.key.get_pressed()

        # Rotate
        if keys[pygame.K_LEFT]:
            self.player.angle -= self.player.turn_speed
        if keys[pygame.K_RIGHT]:
            self.player.angle += self.player.turn_speed

        # Accelerate / decelerate
        if keys[pygame.K_UP]:
            self.player.target_speed = min(self.player.max_speed, self.player.target_speed + self.player.accel_rate)
        elif keys[pygame.K_DOWN]:
            self.player.target_speed = max(-self.player.max_speed, self.player.target_speed - self.player.accel_rate)
        else:
            # Apply friction to target speed when no keys are pressed
            if self.player.target_speed > 0:
                self.player.target_speed = max(0, self.player.target_speed - self.player.friction_rate)
            elif self.player.target_speed < 0:
                self.player.target_speed = min(0, self.player.target_speed + self.player.friction_rate)

        # Handle docking key press (only when not in docking menu)
        if not self.docking_menu_active:
            current_d_key_state = keys[pygame.K_SPACE]
            if current_d_key_state and not self.last_d_key_state:
                # Player pressed dock key

                # Check for station docking
                station = self.station_manager.check_docking(self.player.x, self.player.y)
                if station:
                    # Show docking menu
                    self.docking_menu = DockingMenu(self.screen, station, self.player)
                    self.docking_menu_active = True
            self.last_d_key_state = current_d_key_state

    def clamp_player_health(self):
        """Ensure player health doesn't go negative or exceed max"""
        if self.player.health <= 0:
            self.game_state = "title" # Return to title screen
            # Reset game state for new game
            self.player = Ship(1000, 1000, is_player=True, ship_type="fighter") # Reinitialize player
            self.player_weapons = []
            self.ai_weapons = []
            self.ship_spawner = ShipSpawner(self.player, self.ai_weapons)
            self.enemy_ais = {}
            self.enemy_kills = 0
            self.docking_menu = None
            self.docking_menu_active = False
        elif self.player.health > self.player.max_health:
            self.player.health = self.player.max_health

    def check_ship_collisions(self):
        """Check for collisions between player ship and AI ships"""
        for ship in self.ship_spawner.ships[:]:
            if self.ships_collide(self.player, ship):
                self.apply_ramming_damage(self.player, ship)

    def ships_collide(self, ship1, ship2):
        """Check if two ships are colliding"""
        dx = ship1.x - ship2.x
        dy = ship1.y - ship2.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Collision threshold based on ship sizes
        collision_distance = (ship1.width + ship2.width) * 0.4
        
        return distance < collision_distance

    def apply_ramming_damage(self, ship1, ship2):
        """Apply ramming damage between two ships, considering boost and speed differences"""

        # Skip dead ships
        if getattr(ship1, "health", 0) <= 0 or getattr(ship2, "health", 0) <= 0:
            return

        # Absolute speeds
        ship1_speed = abs(ship1.speed)
        ship2_speed = abs(ship2.speed)

        # Relative speed difference
        speed_difference = ship1_speed - ship2_speed

        # Base damage: use own speed times opponent size
        ship1_damage = (ship2.width / 10) * (ship1_speed * 1.5)
        ship2_damage = (ship1.width / 10) * (ship2_speed * 1.5)

        # Apply speed difference bonus **after boost reduction**
        if speed_difference > 0:
            ship1_damage *= 1.0 + (speed_difference / 5)
        elif speed_difference < 0:
            ship2_damage *= 1.0 + (-speed_difference / 5)

        # Apply boost damage reduction first
        boost_reduction_factor = 0.5  # 50% damage taken while boosting
        if getattr(ship1, "boost_timer", 0) > 0:
            ship1_damage *= boost_reduction_factor
        if getattr(ship2, "boost_timer", 0) > 0:
            ship2_damage *= boost_reduction_factor

        # Dreadnought multipliers
        if ship2.ship_class == "Dreadnought":
            ship1_damage *= 1.5
        if ship1.ship_class == "Dreadnought":
            ship2_damage *= 1.5

        # Clamp damage to **at most current health** to avoid instant negative overkill
        ship1_damage = min(ship1_damage, ship1.health)
        ship2_damage = min(ship2_damage, ship2.health)

        # Apply damage to ship1 only if ship2 is alive
        if ship2.health > 0:
            ship1.health = max(0, ship1.health - ship1_damage)
        else:
            ship1.health = max(0, ship1.health)  # optionally no damage if opponent dead

        # Apply damage to ship2 only if ship1 is alive
        if ship1.health > 0:
            ship2.health = max(0, ship2.health - ship2_damage)
        else:
            ship2.health = max(0, ship2.health)

        # Mark dead ships
        if ship1.health <= 0:
            ship1.alive = False

        if ship2.health <= 0:
            ship2.alive = False


        # Apply subsystem damage
        for subsystem in ship1.subsystems:
            ship1.take_damage_to_subsystem(subsystem, ship1_damage * 0.1)
        for subsystem in ship2.subsystems:
            ship2.take_damage_to_subsystem(subsystem, ship2_damage * 0.4)

        # Separate ships to avoid overlap
        dx = ship1.x - ship2.x
        dy = ship1.y - ship2.y
        distance = math.sqrt(dx * dx + dy * dy) or 1  # prevent division by zero
        dx /= distance
        dy /= distance

        # Recompute relative speed for push
        relative_speed = (ship1_speed + ship2_speed) / 2
        push_force = relative_speed * 5 + ((ship1.width + ship2.width) / 2)
        ship1_push = (ship2.width / (ship1.width + ship2.width)) * push_force
        ship2_push = (ship1.width / (ship1.width + ship2.width)) * push_force

        ship1.x += dx * ship1_push
        ship1.y += dy * ship1_push
        ship2.x -= dx * ship2_push
        ship2.y -= dy * ship2_push

        # Reduce forward momentum after impact
        ship1.target_speed *= 0.3
        ship2.target_speed *= 0.3

        # Debug output



    def draw_ui(self):
        """Draw user interface elements"""
        font = pygame.font.Font(GAME_FONT, 20)
        
        # Draw player health, credits, and crew in top left

        
        credits_text = font.render(f"{self.player.credits}đ", True, (255, 255, 100))
        self.screen.blit(credits_text, (10, 30))
        
        # Draw weapon cooldowns at bottom
        # Laser cooldown (bottom left)
        boost_ratio = self.player.boost_energy / self.player.boost_max_energy

        if boost_ratio < 1:
            pygame.draw.rect(self.screen, (100, 100, 100), (10, self.screen_height - 30, 100, 20))
            pygame.draw.rect(self.screen, (0, 200, 0), (10, self.screen_height - 30, int(100 * boost_ratio), 20))
            pygame.draw.rect(self.screen, (255, 255, 255), (10, self.screen_height - 30, 100, 20), 2)
            #self.screen.blit(cooldown_text, (15, self.screen_height - 28))
        
        # Missile cooldown (bottom right)
        if self.player.missile_reload_timer > 0:
            missile_cooldown_ratio = 1.0 - (self.player.missile_reload_timer / self.player.missile_reload_time) if self.player.missile_reload_time > 0 else 1.0
            pygame.draw.rect(self.screen, (100, 100, 100), (self.screen_width - 110, self.screen_height - 30, 100, 20))
            pygame.draw.rect(self.screen, (200, 100, 0), (self.screen_width - 110, self.screen_height - 30, int(100 * missile_cooldown_ratio), 20))
            pygame.draw.rect(self.screen, (255, 255, 255), (self.screen_width - 110, self.screen_height - 30, 100, 20), 2)
            #self.screen.blit(cooldown_text, (self.screen_width - 105, self.screen_height - 28))

    def draw_map_overlay(self):
        """Draw a simple map overlay in top right corner"""
        # Semi-transparent overlay
        map_surface = pygame.Surface((200, 150), pygame.SRCALPHA)
        map_surface.fill((0, 12, 50, 180))
        self.screen.blit(map_surface, (self.screen_width - 210, 10))
        
        # Draw player position on map (scaled down)
        player_x = int((self.player.x / WORLD_WIDTH) * 200)
        player_y = int((self.player.y / WORLD_HEIGHT) * 150)
        pygame.draw.circle(self.screen, (0, 255, 0), (self.screen_width - 210 + player_x, 10 + player_y), 3)
        
        # Draw nearby ships
        for ship in self.ship_spawner.ships:
            ship_x = int((ship.x / WORLD_WIDTH) * 200)
            ship_y = int((ship.y / WORLD_HEIGHT) * 150)
            color = (255, 50, 50) if ship.behavior == "hostile" else (50, 255, 50)
            pygame.draw.circle(self.screen, color, (self.screen_width - 210 + ship_x, 10 + ship_y), 2)

        # Draw stations
        for station in self.station_manager.stations:
            station_x = int((station.x / WORLD_WIDTH) * 200)
            station_y = int((station.y / WORLD_HEIGHT) * 150)
            pygame.draw.circle(self.screen, (150, 150, 150), (self.screen_width - 210 + station_x, 10 + station_y), 4) # Larger grey dot
            
        # Draw map label
        font = pygame.font.Font(GAME_FONT, 12)
        map_label = font.render("MAP", True, (255, 255, 255))
        self.screen.blit(map_label, (self.screen_width - 210, 10))

    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.firing_laser = True
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.firing_laser = False

                if self.game_state == "title":
                    self.title_screen.handle_input(event)
                elif self.game_state == "game":
                    # Handle docking menu events
                    if self.docking_menu_active and self.docking_menu:
                        self.docking_menu.handle_input(event)
                        if not self.docking_menu.active:
                            self.docking_menu_active = False
                            self.docking_menu = None
                    elif event.type == pygame.KEYDOWN:  # Corrected from original
                        if event.key == pygame.K_b:
                            # Fire missile
                            missile = self.player.fire_missile("left")
                            if missile:
                                self.player_weapons.append(missile)
                        if event.key == pygame.K_x:
                            # Show map (toggle)
                            self.map_visible = not self.map_visible

                        if event.key == pygame.K_y:
                            # Boost!
                            self.player.boost()

            if self.game_state == "title":
                self.title_screen.draw()
                if self.title_screen.start_game:
                    self.game_state = "game"
                    self.title_screen.start_game = False  # Reset for next time
            elif self.game_state == "game":
                self.screen.fill(BG_COLOR)  # Clear screen for game state

                # Draw environment
                self.environment.draw(self.screen)

                # Draw player ship
                self.player.draw(
                    self.screen,
                    offset_x=self.environment.camera_x,
                    offset_y=self.environment.camera_y,
                )

                # Draw AI ships
                for ship in self.ship_spawner.ships:
                    ship.draw(
                        self.screen,
                        offset_x=self.environment.camera_x,
                        offset_y=self.environment.camera_y,
                    )

                # Draw stations
                self.station_manager.draw(
                    self.screen,
                    self.environment.camera_x,
                    self.environment.camera_y,
                )

                # Update game state (only if docking menu is not active)
                if not self.docking_menu_active:
                    self.handle_input()

                    # Auto-fire laser if 'A' is held down
                    if self.firing_laser:
                        # Fire lasers - for fighters, both buttons fire forward
                        laser = self.player.fire_laser("forward")
                        if laser:
                            self.player_weapons.append(laser)

                    self.player.update()
                    self.clamp_player_health()  # Ensure player health doesn't go negative

                    # Check for ship collisions
                    self.check_ship_collisions()

                    # Update player weapons and check collisions
                    for weapon in self.player_weapons[:]:  # Iterate over a copy
                        weapon.update()

                        # Check collisions with AI ships
                        for ship in self.ship_spawner.ships[:]:
                            collision_result = weapon.collides_with(ship)
                            if collision_result[0]:  # If there's a collision
                                subsystem_hit = collision_result[1]

                                # Apply armor reduction
                                damage = weapon.damage * (1 - ship.armor)

                                # Apply damage to overall health
                                ship.health -= damage



                                if ship.health <= 0:
                                    ship.health = 0
                                    # Enemy destroyed - level up player
                                    self.enemy_kills += 1
                                    self.player.level_up()
                                    # Respawn enemy at random position and type
                                    new_ship_x = random.randint(50, SCREEN_WIDTH - 50)
                                    new_ship_y = random.randint(50, SCREEN_HEIGHT - 50)
                                    ship_types = list(SHIP_TYPES.keys())
                                    new_type = random.choice(ship_types)
                                    new_ship = AIShip(new_ship_x, new_ship_y, ship_type=new_type)
                                    self.ship_spawner.ships.append(new_ship)
                                    self.ship_spawner.ships.remove(ship)
                                break # Break out of inner loop once a weapon hits a ship

                    # Filter out weapons that have hit a ship, exceeded range, or are off-screen
                    self.player_weapons = [weapon for weapon in self.player_weapons if not weapon.hit and not (weapon.distance_traveled > 2000 or weapon.is_off_screen(
                        self.environment.camera_x,
                        self.environment.camera_y,
                        self.screen_width,
                        self.screen_height,
                    ))]

                self.environment.update(self.player.x, self.player.y)
                self.ship_spawner.update() # This calls AIShip.update, which appends to self.ai_weapons

                # Update enemy AIs
                # Remove AIs for ships that no longer exist
                existing_ship_ids = [ship.id for ship in self.ship_spawner.ships]
                for ship_id in list(self.enemy_ais.keys()):
                    if ship_id not in existing_ship_ids:
                        del self.enemy_ais[ship_id]

                # Create AIs for new ships and update existing ones
                for ship in self.ship_spawner.ships:
                    if ship.id not in self.enemy_ais:
                        self.enemy_ais[ship.id] = EnemyAI(ship, self.ai_weapons, SHIP_TYPES)
                    self.enemy_ais[ship.id].update(self.player)
                
                # Remove dead ships
                for ship in self.ship_spawner.ships[:]:
                    if getattr(ship, "alive", True) is False or ship.health <= 0:
                        if ship.id in self.enemy_ais:
                            del self.enemy_ais[ship.id]
                        self.ship_spawner.ships.remove(ship)


                self.station_manager.update()  # Update station manager

                # Update AI weapons
                # Update remaining weapons and check collisions
                for weapon in self.ai_weapons:
                    weapon.update()
                    # Check collisions with player
                    if weapon.collides_with(self.player)[0]:
                        self.player.health -= weapon.damage

                        if self.player.health <= 0:

                            self.game_state = "title" # Return to title screen
                            # Reset game state for new game
                            self.player = Ship(1000, 1000, is_player=True, ship_type="fighter") # Reinitialize player
                            self.player_weapons = []
                            self.ai_weapons = []
                            self.ship_spawner = ShipSpawner(self.player, self.ai_weapons)
                            self.enemy_ais = {}
                            self.enemy_kills = 0
                            self.docking_menu = None
                            self.docking_menu_active = False

                # Filter out expired weapons
                self.ai_weapons[:] = [weapon for weapon in self.ai_weapons if not weapon.hit and not (
                    weapon.distance_traveled > 5000 # or weapon.is_off_screen(
                        # self.environment.camera_x,
                        # self.environment.camera_y,
                        # self.screen_width,
                        # self.screen_height,
                    # )
                )]

                # Draw player weapons
                for weapon in self.player_weapons:
                    weapon.draw(
                        self.screen,
                        offset_x=self.environment.camera_x,
                        offset_y=self.environment.camera_y,
                    )

                # Draw AI weapons
                for weapon in self.ai_weapons:
                    weapon.draw(
                        self.screen,
                        offset_x=self.environment.camera_x,
                        offset_y=self.environment.camera_y,
                    )

                # Draw docking menu if active
                if self.docking_menu_active and self.docking_menu:
                    self.docking_menu.draw()

                # Draw UI
                self.draw_ui()

                # Draw map if visible
                if self.map_visible:
                    self.draw_map_overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        game = LivePirateGame()
        game.run()
    except Exception as e:
        print(f"An error occurred: {e}")
