# GENEA 2022 BVH Visualizer
<p align="center">
  <img src="demo.gif" alt="example from visualization server">
  <br>
  <i>Example output from the visualization server</i>
</p>


This repository provides scripts that can be used to visualize BVH files (with optional audio). These scripts were developed for the [GENEA Challenge 2022](https://genea-workshop.github.io/2022/), and enables reproducing the visualizations used for the challenge stimuli.
The system integrates Docker and Blender to provide a free and easy-to-use solution across all Docker-compatible platforms.
The server consists of several containers which are launched together with the docker-compose command described below.
The components are:
* web: this is an HTTP server which receives render requests and places them on a "celery" queue to be processed.
* worker: this takes jobs from the "celery" queue and works on them. Each worker runs one Blender process, so increasing the amount of workers adds more parallelization
* monitor: this is a monitoring tool for celery. Default username is `user` and password is `password` (can be changed by setting `FLOWER_USER` and `FLOWER_PWD` when starting the docker-compose command)
* redis: needed for celery

## Important notes / Requirements
1. The visualizer currently does not support systems with an ARM architecture (like Mac M1). The issue stems from an ongoing [bug in QEMU](https://gitlab.com/qemu-project/qemu/-/issues/750), an emulation engine integrated into Docker, which messes with one of Blender's libraries.
2. You must install *Docker 20.10.14* (or later) on your machine.
3. If passing an audio file with your HTTP request to the server, make sure the audio file is **equal or longer** than the video duration. The combining of video and audio streams uses the shortest stream, so a shorter audio will shorten the duration of the video.
4. If you encounter any issues with the server or visualizer, please file an Issue in the repo. I will do my best to address it as soon as possible :)


## Build and start visualization server
First you need to install docker-compose:
`sudo apt  install docker-compose` (on Ubuntu)

You might want to edit some of the default parameters, such as render resolution and fps, in the `.env` file. The variable `VISUALIZATION_MODE` switches between upper body and full body camera modes, by setting its value to 0 and 1 respectively.

Then to start the server run `docker-compose up --build`

In order to run several (for example 3) workers (Blender renderers, which allows to parallelize rendering, run `docker-compose up --build --scale worker=3`

The `-d` flag can also be passed in order to run the server in the background. Logs can then be accessed by running `docker-compose logs -f`. Additionally it's possible to rebuild just the worker or API containers with minimal disruption in the running server by running for example `docker-compose up -d --no-deps --scale worker=2 --build worker`. This will rebuild the worker container and stop the old ones and start 2 new ones.

## Use the visualization server
The server is HTTP-based and works by uploading a bvh file (and optionally audio). You will then receive a "job id" which you can poll in order to see the progress of your rendering. When it is finished you will receive a URL to a video file that you can download. 
Below are some examples using `curl` and in the file `example.py` there is a full python (3.7) example of how this can be used.

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
* `{"result": FILE_URL, "state": "SUCCESS"}`: The job ended successfully and the video is available at `http://SERVER_URL/[FILE_URL]`.
* `{"result": ERROR_MSG, "state": "FAILURE"}`: The job ended with a failure and the error message is given in `results`.

In order to retrieve the video, run `curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/[FILE_URL] -o result.mp4`. Please note that the server will delete the file after you retrieve it, so you can only retrieve it once!

## Replicating the GENEA Challenge 2022 visualizations
The parameters in the enclosed `.env` file correspond to the those used for rendering the final evaluation stimuli of the GENEA Challenge, for ease of replication. As long as you clone this repo, build it using Docker, and input the BVH files used for the final visualization, you should be able to reproduce the results.
