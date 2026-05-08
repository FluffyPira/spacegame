import pygame
import os
import random

TITLE_FONT = os.path.join(os.path.dirname(__file__), "assets", "Tourney.ttf")
GAME_FONT = os.path.join(os.path.dirname(__file__), "assets", "NovaMono.ttf")

class TitleScreen:
    def __init__(self, screen):
        self.screen = screen
        self.start_game = False

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.start_game = True

    def draw(self):
        screen_width, screen_height = self.screen.get_size()
        
        # Draw title screen background
        self.screen.fill((0, 0, 0))  # Deep space blue
        
        # Draw stars in the background
        for _ in range(15):
            x = random.randint(0, screen_width)
            y = random.randint(0, screen_height)
            size = random.randint(1, 3)
            brightness = random.randint(100, 200)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), size)

        clock = pygame.time.Clock()
        
        # Draw title
        title_font = pygame.font.Font(TITLE_FONT, 88)
        subtitle_font = pygame.font.Font(GAME_FONT, 32)
        instruction_font = pygame.font.Font(GAME_FONT, 18)
        
        title = title_font.render("SPACEGAME", True, (230, 200, 255))
        subtitle = subtitle_font.render("Navigate the Stars", True, (230, 200, 255))
        
        self.screen.blit(title, (screen_width//2 - title.get_width()//2, 80))
        self.screen.blit(subtitle, (screen_width//2 - subtitle.get_width()//2, 180))
        
        # Draw game instructions
        instructions = [
            "ARROW KEYS: Move/Steer",
            "A: Fire Lasers",
            "B: Fire Missiles",
            "X: Toggle Minimap View", 
            "Y: Rocket Boost",
            "SPACE: Dock With Nearby Ships or Ports",
            "",
            "Press ENTER to Start Your Adventure"
        ]
        
        for i, text in enumerate(instructions):
            text_surface = instruction_font.render(text, True, (200, 200, 200))
            self.screen.blit(text_surface, (screen_width//2 - text_surface.get_width()//2, 240 + i * 30))
        
        pygame.display.flip()

    