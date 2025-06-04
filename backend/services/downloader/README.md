# OpenFing Audio Downloader

A Python module to download videos from [OpenFing](https://open.fing.edu.uy/) and extract their audio.

## Features

- Download videos from OpenFing courses
- Extract audio in your preferred format
- Concurrent downloads

## Installation and Usage


- Install and run as a package:
```
pip install -e .
openfing-dl --help
```

- Runn directly from the source:
```
python -m downloader.cli --help
```


## Command Line Options

- `--start`: Starting class number (default: 1)
- `--end`: Ending class number (default: 30)
- `--output`: Directory to save audio files (default: `./audios`)
- `--workers`: Number of concurrent downloads (default: 3)
- `--codec`: Audio codec to use (default: "best")
- `--quality`: Audio quality (0-10, 0=best) (default: "0")
- `--verbose`: Enable verbose logging


## PREFECT
0. Login
```
uvx prefect-cloud login
```

1. Schedule flow run
```
❯ uv run src/openfing_audio_dl/prefect_integration.py

Your flow 'download-flow' is being served and polling for scheduled runs!

To trigger a run for this flow, use the following command:

        $ prefect deployment run 'download-flow/scheduled-downloader'

You can also run your flow via the Prefect UI: https://app.prefect.cloud/account/4856e295-dd17-4cc8-a176-f040fe83e4fa/workspace/4122af19-eb70-4c2b-bbab-24bbea13d3bd/deployments/deployment/ccf820c1-1105-4108-8617-08e1cdf3d04b

```
