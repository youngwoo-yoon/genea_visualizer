# user-study

This repository contains all the scripts for generating the configuration json files to run the user study. 
There are currently four folders: 
- audio: folder containing audios from the test split
- bvh: containing folders with systems and their BVH submissions
- json_output: output folder with N JSON files
- scripts:
    - json generation script
    - audio_low_pass script
    - statistical analysis script, takes json output and generates statistics and figures
    - audio and video merge script
    - bvh to video script that relies on the visualization pipeline
    - script that generates mismatching videos
    - database backup dump script
- short_videos
- videos