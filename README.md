# GENEA 2022 BVH Visualizer
<p align="center">
  <img src="demo.gif" alt="example from visualization server">
  <br>
  <i>Example output from the visualization server</i>
</p>

## Table of Contents
- [Introduction](#introduction)
- [Server Solution](#server-solution)
  * [Limitations](#limitations)
  * [Build and start visualization server](#build-and-start-visualization-server)
  * [Using the visualization server](#using-the-visualization-server)
  * [example.py](#examplepy)
- [Blender Script](#blender-script)
  * [Using Blender UI](#using-blender-ui)
  * [Using command line](#using-command-line)
- [Replicating the GENEA Challenge 2022 visualizations](#replicating-the-genea-challenge-2022-visualizations)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

## Introduction

This repository contains code that can be used to visualize BVH files (with optional audio) using Docker, Blender, and FFMPEG. The code was developed for the [GENEA Challenge 2022](https://genea-workshop.github.io/2022/), and enables reproducing the visualizations used for the challenge stimuli on most platforms. The system integrates Docker and Blender to provide a free and easy-to-use solution that requires as little manual setup as possible. Currently, we provide three interfaces that you can use to access the visualizations:

- Server, hosted by the GENEA organizers at http://129.192.81.125/
- Server, hosted locally by you using the files from this repository
- Blender scripts, for working directly with your own Blender installation

For each BVH file, two videos are produced:

- full body : the avatar body is visible from below the knees to the head, with the original animation data left unchanged
- upper body : the avatar body is visible from above the knees to the head, slightly zoomed in, and the hips position locked at (0,0) with its height left unchanged

## Server Solution

*Most of the information below is needed to set up the server yourself. If you just want to use the GENEA-hosted server, go [here](#examplepy).*

The Docker server consists of several containers which are launched together with the `docker-compose` command described below. The containers are:
* web: this is an HTTP server which receives render requests and places them on a "celery" queue to be processed.
* worker: this takes jobs from the "celery" queue and works on them. Each worker runs one Blender process, so increasing the amount of workers adds more parallelization
* monitor: this is a monitoring tool for celery. Default username is `user` and password is `password` (can be changed by setting `FLOWER_USER` and `FLOWER_PWD` when starting the docker-compose command)
* redis: needed for celery

### Limitations
1. The visualizer currently **does not support ARM systems**, like Mac M1. The issue stems from an ongoing [bug in QEMU](https://gitlab.com/qemu-project/qemu/-/issues/750), an emulation engine integrated into Docker, which messes with one of Blender's libraries.
2. For the server-based solution, you must install **Docker 20.10.14** (or later) on your machine.
3. For the Blender script-based solution, you must install **Blender 2.93.9** on your machine. *Other versions are not guaranteed to work!*
4. If passing an audio file with your HTTP request to the server, make sure the audio file is **equal or longer** than the video duration. The combining of video and audio streams uses the shortest stream, so a shorter audio will shorten the duration of the final video.

If you encounter any issues with the server or visualizer, please file an Issue in the repo. I will do my best to address it as soon as possible :)

### Build and start visualization server
First you need to install docker-compose:
`sudo apt  install docker-compose` (on Ubuntu)

You might want to edit some of the default parameters, such as the render resolution, in the `.env` file.

Then to start the server run `docker-compose up --build`

In order to run several (for example 3) workers (Blender renderers, which allows to parallelize rendering, run `docker-compose up --build --scale worker=3`

The `-d` flag can also be passed in order to run the server in the background. Logs can then be accessed by running `docker-compose logs -f`. Additionally it's possible to rebuild just the worker or API containers with minimal disruption in the running server by running for example `docker-compose up -d --no-deps --scale worker=2 --build worker`. This will rebuild the worker container and stop the old ones and start 2 new ones.

### Using the visualization server
The server is HTTP-based and works by uploading a bvh file, and optionally audio. You will then receive a "job id" which you can poll in order to see the progress of your rendering. When it is finished, you will receive two video file URLs that you can download. Below are some examples using `curl` and in the file `example.py` there is a full python (3.7) example of how this can be used.

Since the server is available publicly online, a simple authentication system is included – just pass in the token `j7HgTkwt24yKWfHPpFG3eoydJK6syAsz` with each request. This can be changed by modifying `USER_TOKEN` in `.env`.

For a simple usage example, you can see a full python script in `example.py`.

Otherwise, you can follow the detailed instructions on how to use the visualization server provided below.

Depending on where you host the visualization, `SERVER_URL` might be different. If you just are running it locally on your machine you can use `127.0.0.1` but otherwise you would use the ip address to the machine that is hosting the server.

```curl -XPOST -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" -F "file=@/path/to/bvh/file.bvh" http://SERVER_URL/render``` 
will return a URI to the current job `/jobid/[JOB_ID]`.

`curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/jobid/[JOB_ID]` will return the current job state, which might be any of:
* `{result": {"jobs_in_queue": X}, "state": "PENDING"}`: Which means the job is in the queue and waiting to be rendered. The `jobs_in_queue` property is the total number of jobs waiting to be executed. The order of job execution is not guaranteed, which means that this number does not reflect how many jobs there are before the current job, but rather reflects if the server is currently busy or not.
* `{result": null, "state": "PROCESSING"}`: The job is currently being processed. Depending on the file size this might take a while, but this acknowledges that the server has started to working on the request.
* `{result":{"current": X, "total": Y}, "state": "RENDERING"}`: The job is currently being rendered, this is the last stage of the process. `current` shows which is the last rendered frame and `total` shows how many frames in total this job will render.
* `{result": null, "state": "COMBINING A/V"}`: The job is currently combining video and audio streams. This can occur only if an audio file was passed to the server alongside the BVH file.
* `{"result": FILE_URL, "state": "SUCCESS"}`: The job ended successfully and the video is available at `http://SERVER_URL/[FILE_URL]`.
* `{"result": ERROR_MSG, "state": "FAILURE"}`: The job ended with a failure and the error message is given in `results`.

In order to retrieve the video, run `curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/[FILE_URL] -o result.mp4`. Please note that the server will delete the file after you retrieve it, so you can only retrieve it once!

### example.py

For the GENEA-hosted server at http://129.192.81.125/, the majority of the steps above have been done already. All you need to do is to contact the server and send your own files for rendering. The included `example.py` file provides an example for doing so, which you can call with a command like this:

`python ./example.py <path to .BVH file> --audio_file <path to .WAV file> --output <path where videos will be saved> --server_url <IP where the server is hosted>`

**To contact the GENEA-hosted server**, and render a BVH file with audio, you may write a command like this:

`python ./example.py "C:\Users\Wolf\Documents\NN_Output\BVH_Files\mocap.bvh" --audio_file "C:\Users\Wolf\Documents\NN_Output\WAV_Files\audio.wav" --output "C:\Users\Wolf\Documents\NN_Output\Rendered\" --server_url http://129.192.81.125`

Note: The solution currently does not support the manual setting of number of frames to render from the client (`example.py`). Instead, make sure your BVH file is as long as you need it to, since this is what will get rendered by the server (capped at 2 minutes or 3600 frames).

## Blender Script

This repository provides a [minimal release](https://github.com/TeoNikolov/genea_visualizer/releases/tag/minimal-release-v1) of the GENEA visualization tool, in the form of a Blender script that you can use directly with Blender through the command line or Blender's user interface. This release is useful if you have Blender installed on your system and you want to play around with the visualizer. Note that while the release should  behave the same as the final visualizer (i.e. the one used during evaluation), **it is possible that some of the code, or default settings, change** over the next few months. Because the maintenance of this script is lower priority, you might prefer to use the server-based solution (either GENEA-hosted or self-hosted) to avoid potentially outdated code.

### Using Blender UI

1. Make sure you have `Blender 2.93.9` (other versions may work, but this is not guaranteed).
2. Extract the .zip contents to a directory of your choice.
3. Start `Blender` and navigate to the `Scripting` panel above the 3D viewport.
4. In the panel on the right of the 3D viewport, press `Open` to navigate to the script directory and open `GENEA_script_wip.py`.
5. Tweak the settings in `main()` on `line 200` , under the `if` statement - make sure to specify full paths for the BVH and WAV files, including the extension and drive label.
6. When ready, run the script by pressing the "play" button at the top to render the scene (this can take a while, so try with fewer frames first).
7. The rendered video will be output to the `output` directory, next to the script file.

### Using command line
It is likely that your machine learning pipeline outputs a bunch of BVH and WAV files, such as during hyperparameter optimization. Instead of processing each BVH/WAV file pair separately through Blender's UI yourself, call Blender with [command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) like this:

`"<path to Blender executable>" -b --python "<path to Blender .py script>" -- --input "<path to BVH file>" --input_audio "<path to WAV file>" --video`

On Windows, you may write something like this:

`& "C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" -b --python ./blender_render.py -- --input "C:\Users\Wolf\Documents\NN_Output\BVH_files\mocap.bvh" --input_audio "C:\Users\Wolf\Documents\NN_Output\audio.wav" --video --output_dir "C:\Users\Wolf\Documents\NN_Output\Rendered\"`

Tip: Tweak `--duration <frame count>`, `--res_x <value>`, and `--res_y <value>`, to smaller values to decrease render time and speed up your testing.

## Replicating the GENEA Challenge 2022 visualizations
The parameters in the enclosed `.env` file correspond to the those used for rendering the final evaluation stimuli of the GENEA Challenge 2022, for ease of replication. As long as you clone this repo, build it using Docker, and input the BVH files used for the final visualization, you should be able to reproduce the results. You could also use the [minimal release](https://github.com/TeoNikolov/genea_visualizer/releases/tag/minimal-release-v1) of the GENEA visualization tool directly with Blender, but maintaining the release is lower priority, and it may not reflect potential changes. It is preferable to use the Dockerized solution instead.
