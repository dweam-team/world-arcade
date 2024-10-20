import pygame


# Mapping from JavaScript key codes to Pygame key constants
JS_TO_PYGAME_KEY_MAP = {
    13: pygame.K_RETURN,
    27: pygame.K_ESCAPE,
    32: pygame.K_SPACE,
    37: pygame.K_LEFT,  
    38: pygame.K_UP,    
    39: pygame.K_RIGHT, 
    40: pygame.K_DOWN,  
    87: pygame.K_w,
    65: pygame.K_a,
    83: pygame.K_s,
    68: pygame.K_d,
    69: pygame.K_e,
    77: pygame.K_m,
    75: pygame.K_k,
    73: pygame.K_i,
    81: pygame.K_q,
    82: pygame.K_r,
    84: pygame.K_t,
    70: pygame.K_f,
    71: pygame.K_g,
    72: pygame.K_h,
    74: pygame.K_j,
    76: pygame.K_l,
    79: pygame.K_o,
    80: pygame.K_p,
    85: pygame.K_u,
    86: pygame.K_v,
    88: pygame.K_x,
    89: pygame.K_y,
    90: pygame.K_z,
    190: pygame.K_PERIOD,
    49: pygame.K_1,
    50: pygame.K_2,
    51: pygame.K_3,
}

# New mouse button mapping
JS_TO_PYGAME_BUTTON_MAP = {
    0: pygame.BUTTON_LEFT,  # Left button
    1: pygame.BUTTON_MIDDLE,  # Middle button
    2: pygame.BUTTON_RIGHT,  # Right button
    # Add additional mappings if needed
}
