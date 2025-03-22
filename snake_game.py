"""
Nokia 3310 Snake Game
Version: v0.0.1
Date: March 22, 2025
Credits: uecoding

A recreation of the classic Snake game from the Nokia 3310 phone using Pyglet.
"""
import pyglet
import sys
import random
import time
from pyglet.window import key
from pyglet import shapes

# Constants
CELL_SIZE = 20
GRID_WIDTH = 21  # Nokia 3310's screen was 84x48 pixels
GRID_HEIGHT = 15  # We'll scale it up a bit for better visibility
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT
FPS = 8
PADDING = 1  # Number of cells to pad on each side

# Playable area constants (equal padding on all sides)
PLAY_AREA_X_MIN = PADDING
PLAY_AREA_Y_MIN = PADDING
PLAY_AREA_X_MAX = GRID_WIDTH - PADDING - 1
PLAY_AREA_Y_MAX = GRID_HEIGHT - PADDING - 1

# Colors - Using Nokia 3310 color palette
NOKIA_BG = (199, 240, 216)  # Light green background
NOKIA_FG = (15, 56, 15)     # Dark green foreground

# Direction constants - Fixed to make UP move up and DOWN move down on screen
UP = (0, 1)      # Changed from (0, -1) to (0, 1)
DOWN = (0, -1)   # Changed from (0, 1) to (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class SnakeGame(pyglet.window.Window):
    def __init__(self):
        super().__init__(width=WIDTH, height=HEIGHT, caption="Nokia 3310 Snake")
        self.batch = pyglet.graphics.Batch()
        
        # Set background color
        pyglet.gl.glClearColor(NOKIA_BG[0]/255, NOKIA_BG[1]/255, NOKIA_BG[2]/255, 1)
        
        self.reset_game()
        
        # Schedule the update function to be called every (1/FPS) seconds
        pyglet.clock.schedule_interval(self.update, 1/FPS)
        
        # Setup keyboard handling
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        
        # Phone frame elements
        self.frame_elements = []
        self.create_phone_frame()
        
        # Playable area border
        self.create_playable_area_border()
        
        # Text labels - Added more padding
        self.score_label = pyglet.text.Label(
            f'Score: {self.score}',
            font_name='Arial',
            font_size=14,
            x=30, y=HEIGHT-30,  # Increased padding from edges
            color=(NOKIA_FG[0], NOKIA_FG[1], NOKIA_FG[2], 255),
            batch=self.batch
        )
        
        self.game_over_labels = []
    
    def create_phone_frame(self):
        # Frame color
        color = (50, 50, 50)
        frame_thickness = 10
        
        # Top frame
        self.frame_elements.append(shapes.Rectangle(
            0, HEIGHT-frame_thickness, WIDTH, frame_thickness,
            color=color, batch=self.batch
        ))
        # Bottom frame
        self.frame_elements.append(shapes.Rectangle(
            0, 0, WIDTH, frame_thickness,
            color=color, batch=self.batch
        ))
        # Left frame
        self.frame_elements.append(shapes.Rectangle(
            0, 0, frame_thickness, HEIGHT,
            color=color, batch=self.batch
        ))
        # Right frame
        self.frame_elements.append(shapes.Rectangle(
            WIDTH-frame_thickness, 0, frame_thickness, HEIGHT,
            color=color, batch=self.batch
        ))
        
        # Nokia logo removed as requested
    
    def create_playable_area_border(self):
        # Create a 1-pixel border around the playable area
        border_color = NOKIA_FG
        border_thickness = 1
        
        # Calculate the actual pixel coordinates for the border
        # This needs to match the *actual* area where the snake can move
        # Since the snake wraps around *before* reaching PLAY_AREA_X_MAX and PLAY_AREA_Y_MAX,
        # we need to adjust the border to reflect this
        x1 = PLAY_AREA_X_MIN * CELL_SIZE
        y1 = PLAY_AREA_Y_MIN * CELL_SIZE
        
        # The snake can't actually reach PLAY_AREA_X_MAX or PLAY_AREA_Y_MAX due to wraparound,
        # so we need to subtract 1 from these values
        x2 = PLAY_AREA_X_MAX * CELL_SIZE  # Not +1 because snake never reaches this position
        y2 = PLAY_AREA_Y_MAX * CELL_SIZE  # Not +1 because snake never reaches this position
        
        # Create border using four thin rectangles
        # Top border
        self.frame_elements.append(shapes.Rectangle(
            x1, y2, x2 - x1, border_thickness,
            color=border_color, batch=self.batch
        ))
        # Bottom border
        self.frame_elements.append(shapes.Rectangle(
            x1, y1, x2 - x1, border_thickness,
            color=border_color, batch=self.batch
        ))
        # Left border
        self.frame_elements.append(shapes.Rectangle(
            x1, y1, border_thickness, y2 - y1,
            color=border_color, batch=self.batch
        ))
        # Right border
        self.frame_elements.append(shapes.Rectangle(
            x2 - border_thickness, y1, border_thickness, y2 - y1,
            color=border_color, batch=self.batch
        ))
    
    def reset_game(self):
        # Game state
        self.score = 0
        self.game_over = False
        
        # Snake properties
        self.snake_positions = [(PLAY_AREA_X_MIN + 1, PLAY_AREA_Y_MIN + 1)]
        self.snake_length = 3
        self.snake_direction = random.choice([UP, DOWN, LEFT, RIGHT])
        
        # Add starting body segments
        for i in range(1, self.snake_length):
            # Place the body in the opposite direction of movement
            x = self.snake_positions[0][0] - self.snake_direction[0]
            y = self.snake_positions[0][1] - self.snake_direction[1]
            self.snake_positions.append((x, y))
        
        # Food
        self.spawn_food()
        
        # Visual elements
        self.snake_shapes = []
        self.update_snake_shapes()
        self.food_shape = None
        self.update_food_shape()
    
    def spawn_food(self):
        # Create a new food at a random position within playable area
        while True:
            x = random.randint(PLAY_AREA_X_MIN, PLAY_AREA_X_MAX - 1)
            y = random.randint(PLAY_AREA_Y_MIN, PLAY_AREA_Y_MAX - 1)
            self.food_position = (x, y)
            # Make sure food doesn't spawn on the snake
            if self.food_position not in self.snake_positions:
                break
    
    def update_snake_shapes(self):
        # Clear previous shapes
        for shape in self.snake_shapes:
            shape.delete()
        self.snake_shapes = []
        
        # Create shapes for each snake segment
        for i, (x, y) in enumerate(self.snake_positions):
            # Draw rectangle for segment - ensure all snake segments are inside boundaries
            if (x >= PLAY_AREA_X_MIN and x <= PLAY_AREA_X_MAX and 
                y >= PLAY_AREA_Y_MIN and y <= PLAY_AREA_Y_MAX):
                segment = shapes.Rectangle(
                    x * CELL_SIZE, y * CELL_SIZE,
                    CELL_SIZE, CELL_SIZE,
                    color=NOKIA_FG, batch=self.batch
                )
                self.snake_shapes.append(segment)
                
                # For body segments, add inner pattern
                if i > 0:  # Not the head
                    inner = shapes.Rectangle(
                        x * CELL_SIZE + 4, y * CELL_SIZE + 4,
                        CELL_SIZE - 8, CELL_SIZE - 8,
                        color=NOKIA_BG, batch=self.batch
                    )
                    self.snake_shapes.append(inner)
    
    def update_food_shape(self):
        if self.food_shape is not None:
            self.food_shape.delete()
            self.food_inner_shape.delete()
        
        x, y = self.food_position
        
        # Make sure food is within playable area
        if (x >= PLAY_AREA_X_MIN and x <= PLAY_AREA_X_MAX and 
            y >= PLAY_AREA_Y_MIN and y <= PLAY_AREA_Y_MAX):
            # Outer square
            self.food_shape = shapes.Rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                CELL_SIZE, CELL_SIZE,
                color=NOKIA_FG, batch=self.batch
            )
            
            # Inner square (for Nokia style)
            self.food_inner_shape = shapes.Rectangle(
                x * CELL_SIZE + 6, y * CELL_SIZE + 6,
                CELL_SIZE - 12, CELL_SIZE - 12,
                color=NOKIA_BG, batch=self.batch
            )
    
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            pyglet.app.exit()
        
        if self.game_over and symbol == key.SPACE:
            self.reset_game()
            # Update score label
            self.score_label.text = f'Score: {self.score}'
            # Clear game over labels
            for label in self.game_over_labels:
                label.delete()
            self.game_over_labels = []
            return
        
        if not self.game_over:
            if symbol == key.UP and self.snake_direction != DOWN:
                self.next_direction = UP
            elif symbol == key.DOWN and self.snake_direction != UP:
                self.next_direction = DOWN
            elif symbol == key.LEFT and self.snake_direction != RIGHT:
                self.next_direction = LEFT
            elif symbol == key.RIGHT and self.snake_direction != LEFT:
                self.next_direction = RIGHT
    
    def check_collision(self):
        head_x, head_y = self.snake_positions[0]
        
        # Check if snake collided with itself
        if self.snake_positions[0] in self.snake_positions[1:]:
            return True
        
        return False
    
    def update(self, dt):
        if self.game_over:
            return
        
        # Update snake direction
        if hasattr(self, 'next_direction'):
            self.snake_direction = self.next_direction
            delattr(self, 'next_direction')
        
        # Move snake in current direction
        head_x, head_y = self.snake_positions[0]
        dir_x, dir_y = self.snake_direction
        
        # Calculate new head position with wrap-around within playable area
        new_x = head_x + dir_x
        new_y = head_y + dir_y
        
        # Handle wraparound within playable area
        if new_x < PLAY_AREA_X_MIN:
            new_x = PLAY_AREA_X_MAX - 1
        elif new_x >= PLAY_AREA_X_MAX:
            new_x = PLAY_AREA_X_MIN
        
        if new_y < PLAY_AREA_Y_MIN:
            new_y = PLAY_AREA_Y_MAX - 1
        elif new_y >= PLAY_AREA_Y_MAX:
            new_y = PLAY_AREA_Y_MIN
        
        # Add new head
        self.snake_positions.insert(0, (new_x, new_y))
        
        # Check if we ate food
        if self.snake_positions[0] == self.food_position:
            self.score += 1
            self.snake_length += 1
            self.score_label.text = f'Score: {self.score}'
            self.spawn_food()
            self.update_food_shape()
        else:
            # Remove tail if we didn't eat
            if len(self.snake_positions) > self.snake_length:
                self.snake_positions.pop()
        
        # Check for collision with self
        if self.check_collision():
            self.game_over = True
            self.show_game_over()
            return
        
        # Update visual representation
        self.update_snake_shapes()
    
    def show_game_over(self):
        # Create a background for better text visibility
        # First, make a background panel
        panel_width = WIDTH // 2
        panel_height = HEIGHT // 2
        panel_x = WIDTH // 4
        panel_y = HEIGHT // 4
        
        # Create background panel with border
        # Outer rectangle (border)
        outer_panel = shapes.Rectangle(
            panel_x, panel_y,
            panel_width, panel_height,
            color=NOKIA_FG,
            batch=self.batch
        )
        
        # Inner rectangle (background)
        inner_panel = shapes.Rectangle(
            panel_x + 3, panel_y + 3,
            panel_width - 6, panel_height - 6,
            color=NOKIA_BG,
            batch=self.batch
        )
        
        # Game Over text
        game_over_text = pyglet.text.Label(
            'GAME OVER',
            font_name='Arial',
            font_size=24,
            x=WIDTH//2, y=HEIGHT//2 + 30,
            anchor_x='center', anchor_y='center',
            color=(NOKIA_FG[0], NOKIA_FG[1], NOKIA_FG[2], 255),
            batch=self.batch
        )
        
        score_text = pyglet.text.Label(
            f'Score: {self.score}',
            font_name='Arial',
            font_size=18,
            x=WIDTH//2, y=HEIGHT//2,
            anchor_x='center', anchor_y='center',
            color=(NOKIA_FG[0], NOKIA_FG[1], NOKIA_FG[2], 255),
            batch=self.batch
        )
        
        restart_text = pyglet.text.Label(
            'Press SPACE to restart',
            font_name='Arial',
            font_size=14,
            x=WIDTH//2, y=HEIGHT//2 - 30,
            anchor_x='center', anchor_y='center',
            color=(NOKIA_FG[0], NOKIA_FG[1], NOKIA_FG[2], 255),
            batch=self.batch
        )
        
        self.game_over_labels = [outer_panel, inner_panel, game_over_text, score_text, restart_text]
    
    def on_draw(self):
        self.clear()
        self.batch.draw()

def main():
    game = SnakeGame()
    pyglet.app.run()

if __name__ == "__main__":
    main()
