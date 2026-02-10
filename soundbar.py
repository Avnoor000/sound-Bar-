import pygame
import pyaudio
import numpy as np
import math

pygame.init()

# WINDOW
SIZE = WIDTH, HEIGHT = 700, 600
screen = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
pygame.display.set_caption('Voice Equalizer')
is_fullscreen = False

# Colors
black = [0, 0, 0]
white = [255, 255, 255]
gray = [100, 100, 100]

# Themes
themes = {
    "Neon": {
        "colors": [[138, 43, 226], [255, 105, 180], [0, 255, 255], [255, 255, 0]],
        "name": "Neon"
    },
    "Ocean": {
        "colors": [[0, 105, 148], [0, 168, 232], [64, 224, 208], [152, 251, 152]],
        "name": "Ocean"
    },
    "Fire": {
        "colors": [[139, 0, 0], [255, 69, 0], [255, 140, 0], [255, 215, 0]],
        "name": "Fire"
    },
    "Custom": {
        "colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]],
        "name": "Custom"
    }
}

current_theme = "Neon"
show_color_picker = False
current_color_index = 0

# Bar properties
num_bars = 60
bar_spacing = 2
min_bar_height = 5

def calculate_bar_properties():
    global bar_width, max_bar_height
    bar_width = WIDTH // (num_bars + 10)
    max_bar_height = HEIGHT // 2

calculate_bar_properties()

# Audio setup
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44400

# Initialize bars
bar_heights = [min_bar_height] * num_bars
target_heights = [min_bar_height] * num_bars

# Initialize PyAudio
p = pyaudio.PyAudio()

# Find default input device
try:
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=2)
    print("Microphone opened successfully!")
except Exception as e:
    print(f"Error opening microphone: {e}")
    print("Available audio devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"{i}: {info['name']} - Inputs: {info['maxInputChannels']}")
    pygame.quit()
    exit()

clock = pygame.time.Clock()

class ColorPicker:
    def __init__(self):
        self.update_position()
        self.r_slider = 128
        self.g_slider = 128
        self.b_slider = 128
        self.active_slider = None
    
    def update_position(self):
        self.x = WIDTH // 2 - 200
        self.y = HEIGHT // 2 - 150
        self.width = 400
        self.height = 300
        
    def draw(self, surface):
        # Background
        pygame.draw.rect(surface, [40, 40, 40], (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, white, (self.x, self.y, self.width, self.height), 2)
        
        # Title
        font = pygame.font.Font(None, 32)
        title = font.render(f"Customize Color {current_color_index + 1}", True, white)
        surface.blit(title, (self.x + 20, self.y + 20))
        
        # Preview color
        preview_color = [self.r_slider, self.g_slider, self.b_slider]
        pygame.draw.rect(surface, preview_color, (self.x + 20, self.y + 60, 100, 100))
        pygame.draw.rect(surface, white, (self.x + 20, self.y + 60, 100, 100), 2)
        
        # Sliders
        slider_y = self.y + 80
        slider_x = self.x + 140
        slider_width = 200
        
        font_small = pygame.font.Font(None, 24)
        
        # Red slider
        r_text = font_small.render(f"R: {self.r_slider}", True, white)
        surface.blit(r_text, (slider_x, slider_y - 5))
        pygame.draw.rect(surface, [255, 0, 0], (slider_x + 60, slider_y, slider_width, 10))
        r_pos = slider_x + 60 + (self.r_slider / 255) * slider_width
        pygame.draw.circle(surface, white, (int(r_pos), slider_y + 5), 8)
        
        # Green slider
        slider_y += 40
        g_text = font_small.render(f"G: {self.g_slider}", True, white)
        surface.blit(g_text, (slider_x, slider_y - 5))
        pygame.draw.rect(surface, [0, 255, 0], (slider_x + 60, slider_y, slider_width, 10))
        g_pos = slider_x + 60 + (self.g_slider / 255) * slider_width
        pygame.draw.circle(surface, white, (int(g_pos), slider_y + 5), 8)
        
        # Blue slider
        slider_y += 40
        b_text = font_small.render(f"B: {self.b_slider}", True, white)
        surface.blit(b_text, (slider_x, slider_y - 5))
        pygame.draw.rect(surface, [0, 0, 255], (slider_x + 60, slider_y, slider_width, 10))
        b_pos = slider_x + 60 + (self.b_slider / 255) * slider_width
        pygame.draw.circle(surface, white, (int(b_pos), slider_y + 5), 8)
        
        # Buttons
        button_y = self.y + self.height - 60
        
        # Save button
        save_rect = pygame.Rect(self.x + 50, button_y, 120, 40)
        pygame.draw.rect(surface, [0, 200, 0], save_rect)
        pygame.draw.rect(surface, white, save_rect, 2)
        save_text = font_small.render("Save", True, white)
        surface.blit(save_text, (save_rect.x + 35, save_rect.y + 10))
        
        # Cancel button
        cancel_rect = pygame.Rect(self.x + 230, button_y, 120, 40)
        pygame.draw.rect(surface, [200, 0, 0], cancel_rect)
        pygame.draw.rect(surface, white, cancel_rect, 2)
        cancel_text = font_small.render("Cancel", True, white)
        surface.blit(cancel_text, (cancel_rect.x + 25, cancel_rect.y + 10))
        
        return save_rect, cancel_rect
    
    def handle_click(self, pos):
        slider_y = self.y + 80
        slider_x = self.x + 140
        slider_width = 200
        
        # Check sliders
        for i, slider_val in enumerate([self.r_slider, self.g_slider, self.b_slider]):
            y = slider_y + i * 40
            if slider_x + 60 <= pos[0] <= slider_x + 60 + slider_width and y - 10 <= pos[1] <= y + 20:
                return i  # Return which slider was clicked
        return None
    
    def update_slider(self, slider_idx, pos):
        slider_x = self.x + 140
        slider_width = 200
        value = max(0, min(255, int((pos[0] - slider_x - 60) / slider_width * 255)))
        
        if slider_idx == 0:
            self.r_slider = value
        elif slider_idx == 1:
            self.g_slider = value
        elif slider_idx == 2:
            self.b_slider = value

color_picker = ColorPicker()

def get_audio_bars():
    """Get frequency bars from microphone"""
    try:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Apply FFT to get frequency spectrum
        fft = np.fft.fft(audio_data)
        fft = np.abs(fft[:CHUNK//2])
        
        # Divide into frequency bands
        band_size = len(fft) // num_bars
        bars = []
        
        for i in range(num_bars):
            start = i * band_size
            end = start + band_size
            bar_value = np.mean(fft[start:end])
            bar_height = min(bar_value / 100, max_bar_height)
            bars.append(max(bar_height, min_bar_height))
        
        return bars
    except Exception as e:
        print(f"Audio error: {e}")
        return [min_bar_height] * num_bars

def interpolate_color(height, max_height, theme_colors):
    """Create gradient color based on bar height"""
    ratio = height / max_height
    
    if ratio < 0.25:
        return theme_colors[0]
    elif ratio < 0.5:
        return theme_colors[1]
    elif ratio < 0.75:
        return theme_colors[2]
    else:
        return theme_colors[3]

def draw_theme_selector():
    """Draw theme selection UI"""
    y_offset = 10
    font = pygame.font.Font(None, 22)
    
    # Semi-transparent background
    bg_rect = pygame.Rect(5, 5, 250, 150)
    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
    bg_surface.set_alpha(200)
    bg_surface.fill([20, 20, 20])
    screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
    
    for idx, (theme_name, theme_data) in enumerate(themes.items()):
        x = 10
        y = y_offset + idx * 35
        
        # Checkbox
        checkbox_rect = pygame.Rect(x, y, 20, 20)
        if theme_name == current_theme:
            pygame.draw.rect(screen, theme_data["colors"][2], checkbox_rect)
        else:
            pygame.draw.rect(screen, gray, checkbox_rect)
        pygame.draw.rect(screen, white, checkbox_rect, 2)
        
        # Theme name
        text = font.render(theme_name, True, white)
        screen.blit(text, (x + 30, y + 2))
        
        # Color preview
        if theme_name != "Custom":
            for i, color in enumerate(theme_data["colors"]):
                color_x = x + 120 + i * 25
                pygame.draw.rect(screen, color, (color_x, y, 20, 20))
                pygame.draw.rect(screen, white, (color_x, y, 20, 20), 1)
        else:
            # Custom theme button
            custom_button = pygame.Rect(x + 120, y, 100, 20)
            pygame.draw.rect(screen, [50, 50, 150], custom_button)
            pygame.draw.rect(screen, white, custom_button, 2)
            btn_text = font.render("Edit Colors", True, white)
            screen.blit(btn_text, (custom_button.x + 8, custom_button.y + 2))
    
    # Fullscreen button
    fs_button = pygame.Rect(10, 155, 120, 30)
    pygame.draw.rect(screen, [50, 100, 50] if not is_fullscreen else [100, 50, 50], fs_button)
    pygame.draw.rect(screen, white, fs_button, 2)
    fs_text = font.render("Fullscreen (F)", True, white)
    screen.blit(fs_text, (fs_button.x + 8, fs_button.y + 7))
    
    return fs_button

def handle_theme_click(pos):
    """Handle clicks on theme selector"""
    global current_theme, show_color_picker, current_color_index, is_fullscreen, WIDTH, HEIGHT, screen
    
    y_offset = 10
    
    # Check fullscreen button
    fs_button = pygame.Rect(10, 155, 120, 30)
    if fs_button.collidepoint(pos):
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            WIDTH, HEIGHT = screen.get_size()
        else:
            screen = pygame.display.set_mode((700, 600), pygame.RESIZABLE)
            WIDTH, HEIGHT = 700, 600
        color_picker.update_position()
        return True
    
    for idx, theme_name in enumerate(themes.keys()):
        y = y_offset + idx * 35
        checkbox_rect = pygame.Rect(10, y, 20, 20)
        
        if checkbox_rect.collidepoint(pos):
            current_theme = theme_name
            return True
        
        # Check if custom edit button clicked
        if theme_name == "Custom":
            custom_button = pygame.Rect(130, y, 100, 20)
            if custom_button.collidepoint(pos):
                show_color_picker = True
                current_color_index = 0
                color = themes["Custom"]["colors"][0]
                color_picker.r_slider = color[0]
                color_picker.g_slider = color[1]
                color_picker.b_slider = color[2]
                color_picker.update_position()
                return True
    
    return False

run = True
frame_count = 0

while run:
    clock.tick(60)
    frame_count += 1
    
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        
        if event.type == pygame.VIDEORESIZE:
            if not is_fullscreen:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                color_picker.update_position()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f or event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    WIDTH, HEIGHT = screen.get_size()
                else:
                    screen = pygame.display.set_mode((700, 600), pygame.RESIZABLE)
                    WIDTH, HEIGHT = 700, 600
                color_picker.update_position()
            elif event.key == pygame.K_ESCAPE and is_fullscreen:
                is_fullscreen = False
                screen = pygame.display.set_mode((700, 600), pygame.RESIZABLE)
                WIDTH, HEIGHT = 700, 600
                color_picker.update_position()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if show_color_picker:
                save_rect, cancel_rect = color_picker.draw(screen)
                
                if save_rect.collidepoint(mouse_pos):
                    # Save color
                    themes["Custom"]["colors"][current_color_index] = [
                        color_picker.r_slider,
                        color_picker.g_slider,
                        color_picker.b_slider
                    ]
                    current_color_index += 1
                    
                    if current_color_index >= 4:
                        show_color_picker = False
                        current_theme = "Custom"
                    else:
                        color = themes["Custom"]["colors"][current_color_index]
                        color_picker.r_slider = color[0]
                        color_picker.g_slider = color[1]
                        color_picker.b_slider = color[2]
                
                elif cancel_rect.collidepoint(mouse_pos):
                    show_color_picker = False
                else:
                    slider = color_picker.handle_click(mouse_pos)
                    if slider is not None:
                        color_picker.active_slider = slider
            else:
                handle_theme_click(mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if show_color_picker:
                color_picker.active_slider = None
        
        if event.type == pygame.MOUSEMOTION:
            if show_color_picker and color_picker.active_slider is not None:
                color_picker.update_slider(color_picker.active_slider, mouse_pos)
    
    # Get audio data
    target_heights = get_audio_bars()
    
    # Recalculate bar properties for current window size
    calculate_bar_properties()
    
    # Smooth transition
    for i in range(num_bars):
        bar_heights[i] += (target_heights[i] - bar_heights[i]) * 0.3
    
    # Clear screen
    screen.fill(black)
    
    # Draw bars
    total_width = num_bars * (bar_width + bar_spacing)
    start_x = (WIDTH - total_width) // 2
    center_bar = num_bars // 2
    theme_colors = themes[current_theme]["colors"]
    
    for i in range(num_bars):
        if i < center_bar:
            height = bar_heights[center_bar - i - 1]
        else:
            height = bar_heights[i - center_bar]
        
        x = start_x + i * (bar_width + bar_spacing)
        y = HEIGHT // 2 - height // 2
        
        color = interpolate_color(height, max_bar_height, theme_colors)
        pygame.draw.rect(screen, color, (x, y, bar_width, height))
        
        glow_surface = pygame.Surface((bar_width + 4, height + 4))
        glow_surface.set_alpha(50)
        glow_surface.fill(color)
        screen.blit(glow_surface, (x - 2, y - 2))
    
    # Draw center line
    pygame.draw.line(screen, [50, 50, 50], (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 2)
    
    # Draw theme selector
    if not show_color_picker:
        draw_theme_selector()
    
    # Draw instructions
    font = pygame.font.Font(None, 24)
    instruction = font.render("Speak or play music to see the equalizer react!", True, [150, 150, 150])
    screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT - 40))
    
    # Draw color picker if active
    if show_color_picker:
        color_picker.draw(screen)
    
    pygame.display.update()

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()
pygame.quit()