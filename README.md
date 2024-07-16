# Rclone Python Script

This script allows you to manage data transfer between rclone remotes, including freeing up space and copying files while respecting a specified space limit.

## Features

- Copy data between specified rclone remotes
- Free up space in the source remote by moving data to other remotes
- Compare and create folders between remotes
- Check and delete duplicate files

## Requirements

- Python 3.9 or higher
- Docker (optional)

## Installation

### Clone the Repository

```bash
git clone https://github.com/mau671/rclone-sync-script.git
cd rclone-sync-script
```
### Prepare Configuration

Ensure you have an `rclone.conf` file with your rclone configuration. The script will use this file to connect to your rclone remotes.

## Usage

### Arguments

- `--remotes` (required): Comma-separated list of remotes to use.
- `--limit` (optional): Space limit in TB (default is 10).
- `--free` (optional): Free up space in the source remote by moving data to other remotes.
- `--config` (required): Path to the rclone.conf file.

### Running with Docker

1. **Build the Docker image**:
    ```bash
    docker build -t rclone-sync-script .
    ```

2. **Run the Docker container**:
    ```bash
    docker run --rm -v $(pwd)/rclone.conf:/app/rclone.conf rclone-sync-script --remotes "remote1,remote2" --config /app/rclone.conf --limit 10
    ```

    Replace `remote1,remote2` with your actual rclone remote names. The `--limit` argument specifies the space limit in TB.

### Example

To free up space in the source remote:

```bash
docker run --rm -v $(pwd)/rclone.conf:/app/rclone.conf rclone-sync-script --remotes "remote1,remote2" --config /app/rclone.conf --limit 10 --free "remote"
```

## Development

If you want to contribute to the project or run the script locally without Docker, ensure you have Python 3.9 or higher installed and follow these steps:

1. **Install dependencies**:

    pip install -r requirements.txt

2. **Run the script**:

    python main.py --remotes "remote1,remote2" --config ./rclone.conf --limit 10

## License

This project is licensed under the MIT License.
