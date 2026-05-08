import pygame
import random
import math

# ---------------------------
# Game Constants
# ---------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
FPS = 30
WORLD_WIDTH, WORLD_HEIGHT = 5000, 5000
BG_COLOR = (0, 0, 0)  # Black

# ---------------------------
# Ship Types Configuration
# ---------------------------
SHIP_TYPES = {
    "fighter": {
        "name": "Fighter",
        "class": "Fighter",
        "width": 40,
        "height": 20,
        "color": (100, 100, 200),
        "max_speed": 2.4,
        "turn_speed": 1.4,
        "health": 100,
        "armor": 0.0,
        "weapons": ["spray_laser", "rocket_missile"],
        "fire_rate": 8,
        "missile_fire_rate": 45,
        "value": 145,
        "description": "Fast and maneuverable with spray lasers and rocket missiles"
    },
    "frigate": {
        "name": "Frigate",
        "class": "Frigate",
        "width": 60,
        "height": 30,
        "color": (150, 100, 100),
        "max_speed": 1.8,
        "turn_speed": 1,
        "health": 120,
        "armor": 0.2,
        "weapons": ["double_laser", "standard_missile"],
        "fire_rate": 15,
        "missile_fire_rate": 60,
        "value": 220,
        "description": "Balanced ship with double lasers and standard missiles"
    },
    "cruiser": {
        "name": "Cruiser",
        "class": "Cruiser",
        "width": 80,
        "height": 40,
        "color": (100, 150, 100),
        "max_speed": 1.5,
        "turn_speed": 0.8,
        "health": 200,
        "armor": 0.3,
        "weapons": ["quad_laser", "heavy_missile"],
        "fire_rate": 25,
        "missile_fire_rate": 90,
        "value": 310,
        "description": "Heavy ship with quad lasers and heavy missiles"
    },
    "destroyer": {
        "name": "Destroyer",
        "class": "Destroyer",
        "width": 100,
        "height": 50,
        "color": (150, 150, 100),
        "max_speed": 1,
        "turn_speed": 0.5,
        "health": 280,
        "armor": 0.4,
        "weapons": ["beam_laser", "heavy_missile"],
        "fire_rate": 35,
        "missile_fire_rate": 120,
        "value": 510,
        "description": "Large, durable ship with beam weapon and heavy missiles"
    },
    "dreadnought": {
        "name": "Dreadnought",
        "class": "Dreadnought",
        "width": 120,
        "height": 60,
        "color": (150, 100, 150),
        "max_speed": 0.8,
        "turn_speed": 0.3,
        "health": 330,
        "armor": 0.5,
        "weapons": ["beam_laser", "mirv_missile"],
        "fire_rate": 50,
        "missile_fire_rate": 180,
        "value": 780,
        "description": "Massive capital ship with devastating beam weapon and MIRV missiles"
    }
}

# Upgrade Configuration
UPGRADES = {
    "laser_damage": {
        "name": "Laser Damage",
        "description": "Increases laser projectile damage.",
        "levels": [
            {"cost": 63, "effect": 0.25},  # +10% damage
            {"cost": 125, "effect": 0.6}, # +15% damage
            {"cost": 260, "effect": 1}   # +20% damage
        ]
    },
    "laser_fire_rate": {
        "name": "Laser Fire Rate",
        "description": "Decreases laser cooldown time.",
        "levels": [
            {"cost": 63, "effect": -0.25},  # -10% cooldown
            {"cost": 125, "effect": -0.6}, # -15% cooldown
            {"cost": 260, "effect": -1}   # -20% cooldown
        ]
    },
    "missile_damage": {
        "name": "Missile Damage",
        "description": "Increases missile projectile damage.",
        "levels": [
            {"cost": 63, "effect": 0.25}, # +15% damage
            {"cost": 125, "effect": 0.6},  # +20% damage
            {"cost": 260, "effect": 1}  # +25% damage
        ]
    },
    "missile_reload_speed": {
        "name": "Missile Reload Speed",
        "description": "Decreases missile reload time.",
        "levels": [
            {"cost": 63, "effect": -0.25}, # -15% cooldown
            {"cost": 125, "effect": -0.6},  # -20% cooldown
            {"cost": 260, "effect": -1}  # -25% cooldown
        ]
    }
}

def create_ship_image(ship_type, width, height, color):
    """Create a pygame surface with the appropriate ship design based on type"""
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw different ship shapes based on type
    if ship_type == "fighter":
        # Nimble fighter design
        pygame.draw.polygon(
            image,
            color,
            [
                (width, height // 2),  # nose
                (width * 0.7, 0),           # top front
                (width * 0.3, 0),           # top back
                (0, height // 2),           # back
                (width * 0.3, height), # bottom back
                (width * 0.7, height)  # bottom front
            ]
        )
        # Cockpit
        pygame.draw.ellipse(image, (150, 200, 255, 150), 
                           (width * 0.6, height * 0.3, 
                            width * 0.3, height * 0.4))
    elif ship_type == "frigate":
        # Balanced frigate design
        pygame.draw.polygon(
            image,
            color,
            [
                (width, height // 2),  # nose
                (width * 0.8, height * 0.1),  # top front
                (width * 0.6, 0),           # top middle
                (width * 0.3, height * 0.1),  # top back
                (0, height // 2),           # back
                (width * 0.3, height * 0.9),  # bottom back
                (width * 0.6, height), # bottom middle
                (width * 0.8, height * 0.9),  # bottom front
            ]
        )
        # Turrets
        pygame.draw.circle(image, (100, 100, 150), 
                          (width * 0.7, height * 0.3), 5)
        pygame.draw.circle(image, (100, 100, 150), 
                          (width * 0.7, height * 0.7), 5)
    elif ship_type == "cruiser":
        # Heavy cruiser design
        pygame.draw.polygon(
            image,
            color,
            [
                (width, height // 2),  # nose
                (width * 0.9, height * 0.1),  # top front
                (width * 0.7, 0),           # top middle front
                (width * 0.4, 0),           # top middle back
                (width * 0.2, height * 0.1),  # top back
                (0, height // 2),           # back
                (width * 0.2, height * 0.9),  # bottom back
                (width * 0.4, height), # bottom middle back
                (width * 0.7, height), # bottom middle front
                (width * 0.9, height * 0.9),  # bottom front
            ]
        )
        # Superstructure
        pygame.draw.rect(image, (100, 120, 150, 150), 
                        (width * 0.5, height * 0.2, 
                         width * 0.3, height * 0.6))
    elif ship_type == "destroyer":
        # Large destroyer design
        pygame.draw.polygon(
            image,
            color,
            [
                (width, height // 2),  # nose
                (width * 0.95, height * 0.1),  # top front
                (width * 0.8, 0),           # top middle front
                (width * 0.5, 0),           # top middle
                (width * 0.2, 0),           # top middle back
                (width * 0.05, height * 0.1),  # top back
                (0, height // 2),           # back
                (width * 0.05, height * 0.9),  # bottom back
                (width * 0.2, height), # bottom middle back
                (width * 0.5, height), # bottom middle
                (width * 0.8, height), # bottom middle front
                (width * 0.95, height * 0.9),  # bottom front
            ]
        )
        # Multiple decks
        pygame.draw.rect(image, (120, 120, 120, 150), 
                        (width * 0.4, height * 0.3, 
                         width * 0.4, height * 0.4))
    else:  # dreadnought or default
        # Massive dreadnought design
        pygame.draw.polygon(
            image,
            color,
            [
                (width, height // 2),  # nose
                (width * 0.98, height * 0.1),  # top front
                (width * 0.9, 0),           # top front middle
                (width * 0.7, 0),           # top middle front
                (width * 0.4, 0),           # top middle
                (width * 0.1, 0),           # top middle back
                (width * 0.02, height * 0.1),  # top back
                (0, height // 2),           # back
                (width * 0.02, height * 0.9),  # bottom back
                (width * 0.1, height), # bottom middle back
                (width * 0.4, height), # bottom middle
                (width * 0.7, height), # bottom middle front
                (width * 0.9, height), # bottom front middle
                (width * 0.98, height * 0.9),  # bottom front
            ]
        )
        # Multiple superstructures
        pygame.draw.rect(image, (130, 100, 130, 150), 
                        (width * 0.3, height * 0.2, 
                         width * 0.2, height * 0.6))
        pygame.draw.rect(image, (130, 100, 130, 150), 
                        (width * 0.6, height * 0.2, 
                         width * 0.2, height * 0.6))
                         
    return image
