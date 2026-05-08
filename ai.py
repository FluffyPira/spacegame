import math
import random
from ship_config import SHIP_TYPES, create_ship_image
from modules.weapons import SprayLaser, DoubleLaser, QuadLaser, BeamLaser, StandardMissile, RocketMissile, HeavyMissile, MIRVMissile
from modules.ship import AIShip, Ship

# ---------------------------
# Game Constants
# ---------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
BG_COLOR = (10, 10, 30)  # deep space blue
WORLD_WIDTH, WORLD_HEIGHT = 2000, 2000

# ---------------------------
# Enemy AI
# ---------------------------
class EnemyAI:
    def __init__(self, ship, ai_weapons, ship_types):
        self.ship = ship
        self.ai_weapons = ai_weapons  # Reference to the game's laser list
        self.ship_types = ship_types  # Reference to the ship types configuration
        self.last_fired_time = 0
        self.fire_cooldown = 60  # Frames between weapon fires
        self.state = self.ship.behavior  # Set initial state from ship's behavior
        self.state_timer = 0
        self.target_angle = 0
        self.ai_fire_rate = 30  # Cooldown for the AI's firing decisions (reduced from 60 to 30)
        self.ai_reload_timer = 0

    def update(self, player_ship):
        if self.ai_reload_timer > 0:
            self.ai_reload_timer -= 1

        # Check for state transitions
        if self.ship.health < self.ship.max_health and self.state != "hostile":
            old_state = self.state
            self.state = "hostile"
            self.ship.behavior = "hostile" # Update ship's behavior for minimap

        # Calculate direction to player
        dx = player_ship.x - self.ship.x
        dy = player_ship.y - self.ship.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Calculate angle to player
            target_angle = math.degrees(math.atan2(dy, dx))

            # Call the appropriate AI method based on the current state
            if self.state == "hostile":
                self.hostile_ai(player_ship, target_angle, distance)
            elif self.state == "trader":
                self.trader_ai(player_ship, target_angle, distance)
            elif self.state == "observer":
                self.observer_ai(player_ship, target_angle, distance)
            else: # passive
                self.passive_ai(player_ship, target_angle, distance)

    def hostile_ai(self, player_ship, target_angle, distance):
        angle_diff = (target_angle - self.ship.angle + 180) % 360 - 180
        
        # Continuous turning towards player
        if abs(angle_diff) > 1:  # Even smaller tolerance for continuous turning
            if angle_diff > 0:
                self.ship.angle += self.ship.turn_speed
            else:
                self.ship.angle -= self.ship.turn_speed
        
        # Chase player if far, maintain optimal distance if close
        if distance > 300:  # If player is far, aggressively pursue
            self.ship.target_speed = self.ship.max_speed * 0.8
        elif distance < 80: # If player is too close, back off
            self.ship.target_speed = self.ship.max_speed * -0.5 # Back up
        else: # Optimal range for combat
            self.ship.target_speed = self.ship.max_speed * 0.3  # Moderate speed for maneuverability

        # Shooting logic - try to fire every frame when in range
        self.attempt_to_fire_weapons(player_ship, distance)

    def passive_ai(self, player_ship, target_angle, distance):
        # Passive ships maintain direction but slow down near player
        if distance < 200:
            self.ship.target_speed = max(0, self.ship.target_speed - 0.05)  # Slow down near player
        else:
            self.ship.target_speed = min(self.ship.max_speed * 0.5, self.ship.target_speed + 0.02)  # Maintain cruising speed

    def trader_ai(self, player_ship, target_angle, distance):
        # Trader ships maintain steady course
        self.ship.target_speed = self.ship.max_speed * 0.6

    def observer_ai(self, player_ship, target_angle, distance):
        # Observer ships keep a safe distance from the player and observe
        if distance > 400:
            self.ship.target_speed = self.ship.max_speed * 0.5
        elif distance < 300:
            self.ship.target_speed = -self.ship.max_speed * 0.5
        else:
            self.ship.target_speed = 0

    def fighter_ai(self, player_ship, target_angle, distance):
        """AI for smaller, more maneuverable ships - aggressive hit-and-run"""
        # Always try to face the player for quick attacks
        angle_diff = (target_angle - self.ship.angle + 180) % 360 - 180
        if abs(angle_diff) > 5:
            if angle_diff > 0:
                self.ship.angle += self.ship.turn_speed
            else:
                self.ship.angle -= self.ship.turn_speed
        
        # Aggressive movement - get into attack range
        if distance > 300:
            # Far away, aggressively pursue
            self.ship.target_speed = self.ship.max_speed
        elif distance < 80:
            # Too close, back off but keep facing player
            self.ship.target_speed = -self.ship.max_speed * 0.5
        else:
            # In attack range, slow down to line up shot
            self.ship.target_speed = self.ship.max_speed * 0.3

    def broadside_ai(self, player_ship, target_angle, distance):
        """AI for medium ships - focus on broadside positioning"""
        # Calculate broadside angles (90 degrees from player's facing)
        right_broadside = target_angle + 90
        left_broadside = target_angle - 90
        
        # Determine which broadside position is closer
        angle_to_right = (right_broadside - self.ship.angle + 180) % 360 - 180
        angle_to_left = (left_broadside - self.ship.angle + 180) % 360 - 180
        
        # Choose the closer broadside angle
        if abs(angle_to_right) < abs(angle_to_left):
            desired_angle = right_broadside
            angle_diff = angle_to_right
        else:
            desired_angle = left_broadside
            angle_diff = angle_to_left
        
        # Turn toward broadside position
        if abs(angle_diff) > 5:
            if angle_diff > 0:
                self.ship.angle += self.ship.turn_speed * 0.8
            else:
                self.ship.angle -= self.ship.turn_speed * 0.8
        
        # Move to optimal broadside distance (150-250 pixels)
        if distance < 150:
            # Too close, back off
            self.ship.target_speed = -self.ship.max_speed * 0.4
        elif distance > 250:
            # Too far, move closer
            self.ship.target_speed = self.ship.max_speed * 0.8
        else:
            # In optimal range, slow down to maintain position
            self.ship.target_speed *= 0.8

    def ramming_ai(self, player_ship, target_angle, distance):
        """AI for large ships - ram when advantageous, otherwise broadside"""
        # Calculate if we should ram or use weapons
        should_ram = (
            distance < 150 and 
            self.ship.health > self.ship.max_health * 0.3 and 
            (player_ship.health < player_ship.max_health * 0.5 or 
             (self.ship.health > player_ship.health * 1.5))
        )
        
        if should_ram and distance < 100:
            # Ramming mode - charge directly at the player
            angle_diff = (target_angle - self.ship.angle + 180) % 360 - 180
            if abs(angle_diff) > 3:
                if angle_diff > 0:
                    self.ship.angle += self.ship.turn_speed * 0.7
                else:
                    self.ship.angle -= self.ship.turn_speed * 0.7
            self.ship.target_speed = self.ship.max_speed  # Full speed ahead!
        else:
            # Standard broadside approach
            self.broadside_ai(player_ship, target_angle, distance)

    def attempt_to_fire_weapons(self, player_ship, distance):
        """Attempt to fire weapons when in range and not on cooldown"""
        if self.ai_reload_timer > 0:
            return

        print(f"DEBUG: Ship {self.ship.id} attempting to fire weapons, distance: {distance:.1f}, reload timers - laser: {self.ship.reload_timer}, missile: {self.ship.missile_reload_timer}")

        # Check if we can fire (cooldown and range)
        # Made range more forgiving - increased from 400 to 600
        if distance < 600:
            # Check if we're at a good firing angle
            dx = player_ship.x - self.ship.x
            dy = player_ship.y - self.ship.y
            player_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = abs((player_angle - self.ship.angle + 180) % 360 - 180)

            # For broadside ships, fire when we're roughly at 90 degrees to the player
            # For other ships, fire when we're facing the target
            should_fire_laser = False
            should_fire_missile = False
            if self.ship.ship_class in ["Cruiser", "Destroyer", "Dreadnought"]:
                # Broadside ships fire when at broadside angle - made more forgiving
                # Extended range to allow firing even when not perfectly at 90 degrees
                if 30 < angle_diff < 150:
                    should_fire_laser = True
                    should_fire_missile = True
                    print(f"DEBUG: Ship {self.ship.id} (broadside) - angle {angle_diff:.1f}° is in firing range")
                # Also allow firing when very close to player (desperation firing)
                elif distance < 150:
                    should_fire_laser = True
                    should_fire_missile = True
                    print(f"DEBUG: Ship {self.ship.id} (broadside) - close range desperation firing, distance: {distance:.1f}")
            else:
                # Other ships fire when facing the target - made more forgiving
                if angle_diff < 60:
                    should_fire_laser = True
                    should_fire_missile = True
                    print(f"DEBUG: Ship {self.ship.id} (non-broadside) - angle {angle_diff:.1f}° is in firing range")
                # Also allow firing when very close to player (desperation firing)
                elif distance < 150:
                    should_fire_laser = True
                    should_fire_missile = True
                    print(f"DEBUG: Ship {self.ship.id} (non-broadside) - close range desperation firing, distance: {distance:.1f}")

            # If ships are close but not in perfect firing position, they should still fire
            if distance < 200:
                should_fire_laser = True
                should_fire_missile = True

            # Track if we actually fired any weapons
            fired_any_weapon = False

            if should_fire_laser and self.ship.reload_timer <= 0:
                print(f"DEBUG: Ship {self.ship.id} attempting to fire lasers, reload timer: {self.ship.reload_timer}")
                # Determine which weapons this ship has
                if "spray_laser" in self.ship.available_weapons:
                    # Fighter - fire spray lasers (multiple projectiles)
                    for _ in range(3):  # Fire 3 spray projectiles
                        laser = self.ship.fire_laser("left")
                        if laser:
                            self.ai_weapons.append(laser)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired left spray laser")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire left spray laser")
                        laser = self.ship.fire_laser("right")
                        if laser:
                            self.ai_weapons.append(laser)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired right spray laser")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire right spray laser")
                elif "double_laser" in self.ship.available_weapons:
                    # Frigate - fire double lasers
                    laser_left = self.ship.fire_laser("left")
                    if laser_left:
                        self.ai_weapons.append(laser_left)
                        fired_any_weapon = True
                        print(f"DEBUG: Ship {self.ship.id} fired left double laser")
                    else:
                        print(f"DEBUG: Ship {self.ship.id} failed to fire left double laser")
                    laser_right = self.ship.fire_laser("right")
                    if laser_right:
                        self.ai_weapons.append(laser_right)
                        fired_any_weapon = True
                        print(f"DEBUG: Ship {self.ship.id} fired right double laser")
                    else:
                        print(f"DEBUG: Ship {self.ship.id} failed to fire right double laser")
                elif "quad_laser" in self.ship.available_weapons:
                    # Cruiser - fire quad lasers
                    # Front lasers
                    laser_front_left = self.ship.fire_laser("left")
                    if laser_front_left:
                        self.ai_weapons.append(laser_front_left)
                        fired_any_weapon = True
                        print(f"DEBUG: Ship {self.ship.id} fired front left quad laser")
                    else:
                        print(f"DEBUG: Ship {self.ship.id} failed to fire front left quad laser")
                    laser_front_right = self.ship.fire_laser("right")
                    if laser_front_right:
                        self.ai_weapons.append(laser_front_right)
                        fired_any_weapon = True
                        print(f"DEBUG: Ship {self.ship.id} fired front right quad laser")
                    else:
                        print(f"DEBUG: Ship {self.ship.id} failed to fire front right quad laser")
                elif "beam_laser" in self.ship.available_weapons:
                    # Destroyer/Dreadnought - fire beam laser
                    # Beam weapons are so powerful we only need one
                    if self.ship.ship_class == "Dreadnought":
                        # Dreadnought fires a super powerful beam
                        laser = self.ship.fire_laser("left")  # Only one beam needed
                        if laser:
                            self.ai_weapons.append(laser)
                            fired_any_weapon = True
                            print(f"DEBUG: Dreadnought {self.ship.id} fired beam laser")
                        else:
                            print(f"DEBUG: Dreadnought {self.ship.id} failed to fire beam laser")
                    else:
                        # Destroyer fires a regular beam
                        laser = self.ship.fire_laser("left")
                        if laser:
                            self.ai_weapons.append(laser)
                            fired_any_weapon = True
                            print(f"DEBUG: Destroyer {self.ship.id} fired beam laser")
                        else:
                            print(f"DEBUG: Destroyer {self.ship.id} failed to fire beam laser")
                else:
                    # Default to basic laser behavior
                    if self.ship.ship_class in ["Cruiser", "Destroyer", "Dreadnought"]:
                        # Fire lasers from both sides for maximum effect
                        laser_left = self.ship.fire_laser("left")
                        if laser_left:
                            self.ai_weapons.append(laser_left)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired left laser")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire left laser")
                        laser_right = self.ship.fire_laser("right")
                        if laser_right:
                            self.ai_weapons.append(laser_right)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired right laser")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire right laser")
                    else:
                        # For smaller ships, determine which side is closer to target
                        left_side_angle = (self.ship.angle - 90) % 360
                        right_side_angle = (self.ship.angle + 90) % 360
                        left_diff = abs((player_angle - left_side_angle + 180) % 360 - 180)
                        right_diff = abs((player_angle - right_side_angle + 180) % 360 - 180)
                        if left_diff <= right_diff:
                            laser = self.ship.fire_laser("left")
                        else:
                            laser = self.ship.fire_laser("right")
                        if laser:
                            self.ai_weapons.append(laser)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired laser")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire laser")

            if should_fire_missile and self.ship.missile_reload_timer <= 0:
                print(f"DEBUG: Ship {self.ship.id} attempting to fire missiles, missile reload timer: {self.ship.missile_reload_timer}")
                # Determine which missiles this ship has
                if "rocket_missile" in self.ship.available_weapons and self.ship.ship_class == "Fighter":
                    # Fighter - fire forward rocket missiles
                    missile = self.ship.fire_missile("forward")  # Special forward fire for fighters
                    if missile:
                        if hasattr(missile, 'target'):
                            missile.target = player_ship
                        self.ai_weapons.append(missile)
                        fired_any_weapon = True
                        print(f"DEBUG: Fighter {self.ship.id} fired forward rocket missile")
                    else:
                        print(f"DEBUG: Fighter {self.ship.id} failed to fire forward rocket missile")
                elif "standard_missile" in self.ship.available_weapons:
                    # Frigate - fire standard missiles
                    if self.ship.ship_class in ["Cruiser", "Destroyer", "Dreadnought"]:
                        # Fire missiles from both sides
                        missile_left = self.ship.fire_missile("left")
                        if missile_left:
                            if hasattr(missile_left, 'target'):
                                missile_left.target = player_ship
                            self.ai_weapons.append(missile_left)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired left standard missile")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire left standard missile")
                        missile_right = self.ship.fire_missile("right")
                        if missile_right:
                            if hasattr(missile_right, 'target'):
                                missile_right.target = player_ship
                            self.ai_weapons.append(missile_right)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired right standard missile")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire right standard missile")
                    else:
                        # For smaller ships, determine which side is closer to target
                        left_side_angle = (self.ship.angle - 90) % 360
                        right_side_angle = (self.ship.angle + 90) % 360
                        left_diff = abs((player_angle - left_side_angle + 180) % 360 - 180)
                        right_diff = abs((player_angle - right_side_angle + 180) % 360 - 180)
                        if left_diff <= right_diff:
                            missile = self.ship.fire_missile("left")
                        else:
                            missile = self.ship.fire_missile("right")
                        if missile:
                            if hasattr(missile, 'target'):
                                missile.target = player_ship
                            self.ai_weapons.append(missile)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired standard missile")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire standard missile")
                elif "heavy_missile" in self.ship.available_weapons:
                    # Cruiser/Destroyer - fire heavy missiles
                    if self.ship.ship_class in ["Cruiser", "Destroyer", "Dreadnought"]:
                        # Fire missiles from both sides
                        missile_left = self.ship.fire_missile("left")
                        if missile_left:
                            if hasattr(missile_left, 'target'):
                                missile_left.target = player_ship
                            self.ai_weapons.append(missile_left)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired left heavy missile")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire left heavy missile")
                        missile_right = self.ship.fire_missile("right")
                        if missile_right:
                            if hasattr(missile_right, 'target'):
                                missile_right.target = player_ship
                            self.ai_weapons.append(missile_right)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired right heavy missile")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire right heavy missile")
                    else:
                        # For smaller ships, determine which side is closer to target
                        left_side_angle = (self.ship.angle - 90) % 360
                        right_side_angle = (self.ship.angle + 90) % 360
                        left_diff = abs((player_angle - left_side_angle + 180) % 360 - 180)
                        right_diff = abs((player_angle - right_side_angle + 180) % 360 - 180)
                        if left_diff <= right_diff:
                            missile = self.ship.fire_missile("left")
                        else:
                            missile = self.ship.fire_missile("right")
                        if missile:
                            if hasattr(missile, 'target'):
                                missile.target = player_ship
                            self.ai_weapons.append(missile)
                            fired_any_weapon = True
                            print(f"DEBUG: Ship {self.ship.id} fired heavy missile")
                        else:
                            print(f"DEBUG: Ship {self.ship.id} failed to fire heavy missile")
                elif "mirv_missile" in self.ship.available_weapons:
                    # Dreadnought - fire MIRV missiles
                    # MIRV missiles are so powerful we only need one
                    missile = self.ship.fire_missile("left")  # Only one needed
                    if missile:
                        if hasattr(missile, 'target'):
                            missile.target = player_ship
                        self.ai_weapons.append(missile)
                        fired_any_weapon = True
                        print(f"DEBUG: Dreadnought {self.ship.id} fired MIRV missile")
                    else:
                        print(f"DEBUG: Dreadnought {self.ship.id} failed to fire MIRV missile")

            # Only set reload timer if we actually fired any weapon
            if fired_any_weapon:
                self.ai_reload_timer = 5  # Reduced from 30 to 5 for more aggressive firing
                print(f"DEBUG: Ship {self.ship.id} fired weapons, resetting AI reload timer to 5")

