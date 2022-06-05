# Copyright 2020 by Patrik Jonell.
# All rights reserved.
# This file is part of the GENEA visualizer,
# and is released under the GPLv3 License. Please see the LICENSE
# file that should have been included as part of this package.


import requests
from pathlib import Path
import time
import json
import os

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('bvh_file', type=Path)
# parser.add_argument("--server_url", default="http://129.192.81.125:80")
parser.add_argument('-s', '--server_url', default="http://localhost:5001")
parser.add_argument('-a', '--audio_file', help="The filepath to a chosen .wav audio file.", type=Path)
parser.add_argument('-r', '--rotate', help='Set to "cw" to rotate avatar 90 degrees clockwise, "ccw" for 90 degrees counter-clockwise, "flip" for 180-degree rotation, and leave at "default" for no rotation (or ignore the flag).',type=str, choices=['default', 'cw', 'ccw', 'flip'], default='default')
parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=Path)

args = parser.parse_args()

server_url = args.server_url
bvh_file = args.bvh_file
audio_file = args.audio_file

headers = {"Authorization": "Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz"}

files = {"bvh_file": (bvh_file.name, bvh_file.open())}
if audio_file:
	files['audio_file'] = (audio_file.name, audio_file.open('rb'))

req_data = {'p_rotate': args.rotate}

render_request = requests.post(
	f"{server_url}/render",
	params=req_data,
	files=files,
	headers=headers,
)
job_uri = render_request.text

done = False
while not done:
	resp = requests.get(server_url + job_uri, headers=headers)
	resp.raise_for_status()

	response = resp.json()
	
	if response["state"] == "PENDING":
		jobs_in_queue = response["result"]["jobs_in_queue"]
		print(f"pending.. {jobs_in_queue} jobs currently in queue")
	
	elif response["state"] == "PROCESSING":
		print("Processing the file (this can take a while depending on file size)")
	
	elif response["state"] == "RENDERING":
		current = response["result"]["current"]
		total = response["result"]["total"]
		print(f"Rendering BVH: {int(current/total*100)}% done ({current}/{total} frames)")

	elif response["state"] == "COMBINING A/V":
		print(f"Combining audio with video. Your video will be ready soon!")

	elif response["state"] == "SUCCESS":
		result = json.loads(response["result"])
		file_url_1 = result['files'][0]
		file_url_2 = result['files'][1]
		done = True
		print("Done!")
		break

	elif response["state"] == "FAILURE":
		raise Exception(response["result"])
	else:
		print(response)
		raise Exception("should not happen..")
	time.sleep(5)

output_dir = args.output_dir.resolve() if args.output_dir is not None else Path(os.path.realpath(__file__)).parents[0] / "output"
if not os.path.exists(output_dir):
	os.mkdir(output_dir)
output_file_1 = output_dir / Path(str(bvh_file.stem) + '_UB').with_suffix(".mp4")
output_file_2 = output_dir / Path(str(bvh_file.stem) + '_FB').with_suffix(".mp4")
video_1 = requests.get(server_url + file_url_1, headers=headers).content
video_2 = requests.get(server_url + file_url_2, headers=headers).content
output_file_1.write_bytes(video_1)
output_file_2.write_bytes(video_2)