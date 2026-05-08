import pygame
import sys
import random
from ship_config import SHIP_TYPES

# ---------------------------
# UI Constants
# ---------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
FPS = 30

# ---------------------------
# Title Screen
# ---------------------------
def show_title_screen(screen):
    """Display the title screen with game instructions"""
    screen.fill((10, 10, 30))  # Deep space blue
    
    # Draw stars in the background
    for _ in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.randint(1, 3)
        brightness = random.randint(150, 255)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
    
    # Draw title
    title_font = pygame.font.SysFont(None, 64)
    subtitle_font = pygame.font.SysFont(None, 32)
    instruction_font = pygame.font.SysFont(None, 24)
    
    title = title_font.render("SPACE BATTLE", True, (200, 200, 255))
    subtitle = subtitle_font.render("Asteroids Meets Pirates in Space", True, (150, 150, 200))
    
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
    screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 180))
    
    # Draw instructions
    instructions = [
        "CONTROLS:",
        "Arrow Keys: Move and Rotate Your Ship",
        "A: Fire Lasers from Left Side",
        "D: Fire Lasers from Right Side", 
        "S: Fire Tracking Missile",
        "",
        "WEAPONS:",
        "Lasers: Fast Firing, Short Range, Moderate Damage",
        "Missiles: Slow Firing, Long Range, High Damage, Tracking",
        "",
        "SHIP SYSTEMS:",
        "Engines: Controls movement speed",
        "Weapons: Affects firing rate and accuracy",
        "Sensors: Affects targeting capability",
        "Damage to subsystems affects their performance",
        "",
        "OBJECTIVE:",
        "Destroy Enemy Ships to Level Up",
        "Don't Let Your Health Reach Zero",
        "",
        "Press ENTER to Start"
    ]
    
    for i, text in enumerate(instructions):
        text_surface = instruction_font.render(text, True, (200, 200, 200))
        screen.blit(text_surface, (SCREEN_WIDTH//2 - text_surface.get_width()//2, 250 + i * 30))
    
    pygame.display.flip()
    
    # Wait for user to press ENTER
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    waiting = False
                if event.key == pygame.K_b:
                    pygame.quit()
                    sys.exit()

# ---------------------------
# Ship Selection Screen
# ---------------------------
def show_ship_selection_screen(screen):
    """Display the ship selection screen"""
    screen.fill((10, 10, 30))  # Deep space blue
    
    # Draw stars in the background
    for _ in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.randint(1, 3)
        brightness = random.randint(150, 255)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
    
    # Draw title
    title_font = pygame.font.SysFont(None, 48)
    instruction_font = pygame.font.SysFont(None, 24)
    
    title = title_font.render("SELECT YOUR SHIP", True, (200, 200, 255))
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
    
    # Draw ship options
    ship_types = list(SHIP_TYPES.keys())
    selected_index = 0
    
    while True:
        screen.fill((10, 10, 30))
        
        # Redraw stars
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            brightness = random.randint(150, 255)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
        
        # Draw title
        title = title_font.render("SELECT YOUR SHIP", True, (200, 200, 255))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Draw ship options
        for i, ship_type in enumerate(ship_types):
            config = SHIP_TYPES[ship_type]
            color = (255, 255, 100) if i == selected_index else (200, 200, 200)
            
            # Highlight selected ship
            if i == selected_index:
                pygame.draw.rect(screen, (100, 100, 150), 
                                (SCREEN_WIDTH//2 - 200, 150 + i * 100, 400, 90), 3)
            
            # Draw ship name, class, and stats
            name_text = instruction_font.render(f"{config['name']} ({config['class']})", True, color)
            stats_text = instruction_font.render(
                f"Health: {config['health']} | Speed: {config['max_speed']:.1f} | Armor: {config['armor']:.0%} | Laser Rate: {config['fire_rate']}", 
                True, color)
            desc_text = instruction_font.render(config['description'], True, color)
            
            screen.blit(name_text, (SCREEN_WIDTH//2 - name_text.get_width()//2, 150 + i * 100))
            screen.blit(stats_text, (SCREEN_WIDTH//2 - stats_text.get_width()//2, 170 + i * 100))
            screen.blit(desc_text, (SCREEN_WIDTH//2 - desc_text.get_width()//2, 190 + i * 100))
        
        # Draw instructions
        instructions = [
            "UP/DOWN: Select Ship",
            "ENTER: Confirm Selection",
            "ESCAPE: Quit"
        ]
        
        for i, text in enumerate(instructions):
            text_surface = instruction_font.render(text, True, (200, 200, 200))
            screen.blit(text_surface, (SCREEN_WIDTH//2 - text_surface.get_width()//2, 550 + i * 25))
        
        pygame.display.flip()
        
        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(ship_types)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(ship_types)
                elif event.key == pygame.K_a:
                    return ship_types[selected_index]
                elif event.key == pygame.K_b:
                    pygame.quit()
                    sys.exit()
        
        pygame.time.Clock().tick(FPS)