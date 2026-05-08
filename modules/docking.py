#!/usr/bin/env python3

"""
Docking Menu Module
Handles docking menu system and station services
"""

import pygame
import math
import random
from ship_config import WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, UPGRADES
from title_screen import GAME_FONT

# ---------------------------
# Station Class
# ---------------------------
class Station:
    def __init__(self, x, y, name="Station"):
        self.x = x
        self.y = y
        self.name = name
        self.width = 60
        self.height = 40
        self.color = (100, 200, 100)  # Green for stations
        
    def draw(self, screen, camera_x, camera_y):
        """Draw the station"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Only draw if on screen
        if -50 <= screen_x <= SCREEN_WIDTH + 50 and -50 <= screen_y <= SCREEN_HEIGHT + 50:
            # Draw station building
            pygame.draw.rect(screen, self.color, 
                            (screen_x - self.width//2, screen_y - self.height//2, self.width, self.height))
            pygame.draw.rect(screen, (80, 180, 80), 
                            (screen_x - self.width//2, screen_y - self.height//2, self.width, self.height), 3)
            
            # Draw station name
            font = pygame.font.Font(GAME_FONT, 18)
            name_text = font.render(self.name, True, (255, 255, 255))
            screen.blit(name_text, (screen_x - name_text.get_width()//2, screen_y - self.height//2 - 30))
            
    def check_collision(self, ship_x, ship_y):
        """Check if ship is close enough to dock"""
        dx = self.x - ship_x
        dy = self.y - ship_y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < 50  # Docking range

# ---------------------------
# Station Manager
# ---------------------------
class StationManager:
    def __init__(self):
        self.stations = []
        self.generate_stations()
        
    def generate_stations(self):
        """Generate stations in the world"""
        station_names = ["Alpha Station", "Beta Station", "Gamma Station", "Delta Station", "Epsilon Station", "Fornax Station", "Gemini Station", "Hydra Station"]
        num_stations_to_generate = random.randint(4, 5)
        min_station_spacing = 500  # Minimum distance between stations

        for _ in range(num_stations_to_generate):
            placed = False
            attempts = 0
            while not placed and attempts < 100: # Limit attempts to prevent infinite loops
                x = random.randint(200, WORLD_WIDTH - 200)
                y = random.randint(200, WORLD_HEIGHT - 200)
                name = random.choice(station_names)

                # Check distance to existing stations
                is_too_close = False
                for existing_station in self.stations:
                    dx = x - existing_station.x
                    dy = y - existing_station.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance < min_station_spacing:
                        is_too_close = True
                        break
                
                if not is_too_close:
                    self.stations.append(Station(x, y, name))
                    placed = True
                attempts += 1
            if not placed:
                print(f"Warning: Could not place a station after {attempts} attempts. Consider reducing min_station_spacing or increasing WORLD_WIDTH/HEIGHT.")
            
    def update(self):
        """Update stations (currently no dynamic behavior)"""
        pass
        
    def draw(self, screen, camera_x, camera_y):
        """Draw all stations"""
        for station in self.stations:
            station.draw(screen, camera_x, camera_y)
            
    def check_docking(self, ship_x, ship_y):
        """Check if player ship can dock at any station"""
        for station in self.stations:
            if station.check_collision(ship_x, ship_y):
                return station
        return None

# ---------------------------
# Docking Menu System
# ---------------------------
class DockingMenu:
    def __init__(self, screen, station, player):
        self.screen = screen
        self.station = station
        self.player = player
        self.active = True
        self.selected_option = 0
        self.main_menu_options = ["Repairs", "Upgrades", "Quests/Bounties", "Exit"]
        self.current_menu = "main"
        self.upgrade_options = list(UPGRADES.keys())
        self.selected_upgrade_option = 0

        # Initialize player upgrade levels
        self.player_upgrades = {
            "laser_damage": 0,
            "laser_fire_rate": 0,
            "missile_damage": 0,
            "missile_reload_speed": 0
        }
        
    def handle_input(self, event):
        """Handle docking menu input"""
        if event.type == pygame.KEYDOWN:
            if self.current_menu == "main":
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.main_menu_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.main_menu_options)
                elif event.key == pygame.K_a:
                    self.select_option()
                elif event.key == pygame.K_b:
                    self.active = False

            elif self.current_menu == "upgrades":
                if event.key == pygame.K_UP:
                    self.selected_upgrade_option = (self.selected_upgrade_option - 1) % len(self.upgrade_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_upgrade_option = (self.selected_upgrade_option + 1) % len(self.upgrade_options)
                elif event.key == pygame.K_a:
                    self.select_upgrade_option()
                elif event.key == pygame.K_b:
                    self.current_menu = "main"
                    self.selected_upgrade_option = 0
                
    def select_option(self):
        """Handle option selection"""
        selected_main_option = self.main_menu_options[self.selected_option]

        if selected_main_option == "Repairs":
            self.perform_repairs()
        elif selected_main_option == "Upgrades":
            self.current_menu = "upgrades"
            self.selected_upgrade_option = 0 # Reset selection for upgrade menu
        elif selected_main_option == "Quests/Bounties":
            self.show_quests_menu()
        elif selected_main_option == "Exit":
            self.active = False

    def select_upgrade_option(self):
        """Handle upgrade option selection"""
        upgrade_key = self.upgrade_options[self.selected_upgrade_option]
        upgrade_info = UPGRADES[upgrade_key]
        current_level = self.player_upgrades[upgrade_key]

        if current_level < len(upgrade_info["levels"]):
            next_level_info = upgrade_info["levels"][current_level]
            cost = next_level_info["cost"]

            if self.player.credits >= cost:
                self.player.credits -= cost
                self.player_upgrades[upgrade_key] += 1

                # Apply upgrade effect to player ship


        else:
            pass            
    def perform_repairs(self):
        """Perform ship repairs at station"""

        # Calculate repair costs
        health_damage = self.player.max_health - self.player.health
        health_repair_cost = max(0, int(health_damage * 0.5))  # 50 credits per health point
        
        # Calculate subsystem repair costs
        subsystem_repair_cost = 0
        for subsystem, health in self.player.subsystems.items():
            if health < 1.0:
                subsystem_repair_cost += int((1.0 - health) * 20)  # 20 credits per 10% damage
                
        # Calculate total repair cost
        total_repair_cost = health_repair_cost + subsystem_repair_cost
        
        # Check if player can afford repairs
        if self.player.credits >= total_repair_cost and total_repair_cost > 0:
            # Perform repairs
            self.player.credits -= total_repair_cost
            self.player.health = self.player.max_health
            
            # Repair subsystems
            for subsystem in self.player.subsystems:
                self.player.subsystems[subsystem] = 1.0
                
            # Refill weapons (reset cooldowns)
            self.player.reload_timer = 0
            self.player.missile_reload_timer = 0
            

        elif total_repair_cost > 0:
            pass
        else:
            pass




    def apply_upgrade_effect(self, upgrade_key, effect_value):
        """Apply the effect of a purchased upgrade to the player's ship"""
        if upgrade_key == "laser_damage":
            self.player.laser_damage_multiplier += effect_value

        elif upgrade_key == "laser_fire_rate":
            self.player.fire_rate_multiplier -= effect_value # Decrease cooldown
            self.player.reload_time = self.player.fire_rate / self.player.fire_rate_multiplier

        elif upgrade_key == "missile_damage":
            self.player.missile_damage_multiplier += effect_value

        elif upgrade_key == "missile_reload_speed":
            self.player.missile_reload_speed_multiplier -= effect_value # Decrease cooldown
            self.player.missile_reload_time = self.player.missile_fire_rate / self.player.missile_reload_speed_multiplier


    def show_upgrades_menu(self):
        """Show ship upgrades menu"""

        # For now, just close the menu
        self.active = False
        
    def show_quests_menu(self):
        """Show quests and bounties menu"""

        # For now, just close the menu
        self.active = False
        
    def draw(self):
        """Draw the docking menu"""
        if not self.active:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with 200 alpha (semi-transparent)
        self.screen.blit(overlay, (0, 0))
        
        # Menu title
        font_large = pygame.font.Font(GAME_FONT, 24)
        font_medium = pygame.font.Font(GAME_FONT, 18)
        font_small = pygame.font.Font(GAME_FONT, 12)
        
        # Draw station name
        station_title = font_large.render(f"{self.station.name}", True, (255, 255, 255))
        self.screen.blit(station_title, (SCREEN_WIDTH // 2 - station_title.get_width() // 2, 50))
        
        # Draw player credits
        credits_text = font_large.render(f"{self.player.credits}đ", True, (255, 255, 100))
        self.screen.blit(credits_text, (SCREEN_WIDTH // 2 - credits_text.get_width() // 2, 80))
        
        menu_y = 200

        if self.current_menu == "main":
            options_to_display = self.main_menu_options
            selected_index = self.selected_option
            title_text = "MAIN MENU"
        elif self.current_menu == "upgrades":
            options_to_display = []
            for key in self.upgrade_options:
                upgrade_info = UPGRADES[key]
                current_level = self.player_upgrades[key]
                display_text = f"{upgrade_info['name']} Lv{current_level}"
                if current_level < len(upgrade_info["levels"]):
                    next_level_info = upgrade_info["levels"][current_level]
                    display_text += f" - Cost: {next_level_info['cost']} Credits"
                else:
                    display_text += " - MAX LEVEL"
                options_to_display.append(display_text)
            selected_index = self.selected_upgrade_option
            title_text = "UPGRADES"

        # Draw menu options
        for i, option in enumerate(options_to_display):
            # Highlight selected option
            color = (255, 255, 100) if i == selected_index else (200, 200, 200)
            option_text = font_medium.render(option, True, color)
            
            # Draw background for selected option
            if i == selected_index:
                pygame.draw.rect(self.screen, (100, 100, 150), 
                                (SCREEN_WIDTH // 2 - option_text.get_width() // 2 - 10, 
                                 menu_y - 5, 
                                 option_text.get_width() + 20, 
                                 option_text.get_height() + 10))
            
            self.screen.blit(option_text, (SCREEN_WIDTH // 2 - option_text.get_width() // 2, menu_y))
            menu_y += 50
            
        # Draw instructions
        instructions = [
            "UP/DOWN: Navigate Options",
            "A: Select Option",
            "V: Exit Menu"
        ]
        
        instr_y = SCREEN_HEIGHT - 100
        for instruction in instructions:
            instr_text = font_small.render(instruction, True, (150, 150, 150))
            self.screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, instr_y))
            instr_y += 25