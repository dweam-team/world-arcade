import glob
import subprocess
import os
import re
from PIL import Image
import yaml
import pydantic


# def get_game_list(games_js_path) -> list[Game]:
#     with open(games_js_path, 'r') as file:
#         content = yaml.safe_load(file)
#     return pydantic.TypeAdapter(GamesConfig).validate_python(content).games


# def generate_gif_for_game(game: Game, num_frames=50, fps=15, size=640, output_dir='dweam_web/public/thumbnails', force=False):
#     os.makedirs(output_dir, exist_ok=True)

#     gif_path = os.path.join(output_dir, f"{game.id}.gif")
#     if os.path.exists(gif_path) and not force:
#         print(f"GIF already exists for {game.id}")
#         return gif_path
    
#     # Prepare the game using prepare_play_mode_impl
#     if game.id == 'csgo':
#         from diamond_csgo.play import prepare_play_mode_impl
#         game_obj = prepare_play_mode_impl(
#             pretrained=True,
#             record=True,
#             num_steps_initial_collect=1000,
#             store_denoising_trajectory=False,
#             store_original_obs=False,
#             fps=fps,
#             size=size,
#             no_header=True,
#             record_frames=30 * 10,
#             # record_frames=num_frames,
#             human_player=False,
#         )
#     else:
#         from diamond.play import prepare_play_mode_impl
#         game_obj = prepare_play_mode_impl(
#             pretrained=True,
#             id=game.id,
#             record=True,
#             num_steps_initial_collect=1000,
#             store_denoising_trajectory=False,
#             store_original_obs=False,
#             fps=fps,
#             size=size,
#             no_header=True,
#             record_frames=num_frames,
#             human_player=False,
#         )
    
#     # Run the game and record frames
#     game_obj.run()
    
#     # Retrieve frames and save as GIF
#     frames = game_obj.frames
#     frames = [frame.transpose((1, 0, 2)) for frame in frames]  # Convert frames for saving
    
#     # Save frames as GIF
#     pil_frames = [Image.fromarray(frame) for frame in frames]
#     pil_frames[0].save(
#         gif_path,
#         save_all=True,
#         append_images=pil_frames[1:],
#         duration=int(1000/fps),
#         loop=0
#     )

#     return gif_path
    

# def generate_thumbnail_gifs(force=False):
#     # TODO this is outdated
#     games_js_path = 'games_config.yaml'
#     games = get_game_list(games_js_path)
    
#     paths = []
#     for game in games:
#         print(f"Generating GIF for {game}")
#         path = generate_gif_for_game(game, force=force)
#         paths.append(path)
#         print(f"Saved GIF to {path}")
#     return paths


def convert_gifs(force=False):
    paths = glob.glob('*.gif')
    for path in paths:
        webm_path = path.replace(".gif", ".webm")
        if os.path.exists(webm_path) and not force:
            print(f"Webm already exists for {path}")
        else:
            print(f"Converting {path} to webm")
            if path.endswith('csgo.gif'):
                subprocess.run(['ffmpeg', '-y', '-i', path, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '20', '-b:v', '1M', f'{path.replace(".gif", ".webm")}'])
            else:
                subprocess.run(['ffmpeg', '-y', '-i', path, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '30', f'{path.replace(".gif", ".webm")}'])
            print(f"Converted {path} to webm")

        mp4_path = path.replace(".gif", ".mp4")
        if os.path.exists(mp4_path) and not force:
            print(f"MP4 already exists for {path}")
        else:
            print(f"Converting {path} to mp4")
            subprocess.run(['ffmpeg', '-y', '-i', path, '-movflags', 'faststart', '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', f'{path.replace(".gif", ".mp4")}'])
            print(f"Converted {path} to mp4")


if __name__ == '__main__':
    force = False
    # paths = generate_thumbnail_gifs(force=force)
    convert_gifs(force=force)
