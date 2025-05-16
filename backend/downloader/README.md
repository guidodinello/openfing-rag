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
