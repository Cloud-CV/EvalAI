# Docker Installation on M1 Mac

## Prerequisites

- macOS 11.0 or later
- Apple Silicon (M1) chip

## Installation Steps

1. **Install Homebrew** (if not already installed):
    ```sh
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

2. **Install Docker**:
    ```sh
    brew install --cask docker
    ```

3. **Start Docker**:
    - Open Docker from the Applications folder or use Spotlight search.
    - Follow the on-screen instructions to complete the setup.

4. **Verify Installation**:
    ```sh
    docker --version
    ```

    You should see the Docker version information.

## Additional Configuration

- **Increase Memory and CPU Allocation**:
    - Open Docker Desktop.
    - Go to Preferences > Resources.
    - Adjust the CPU and memory allocation as needed.

- **Enable Rosetta 2** (if required for x86/amd64 images):
    ```sh
    softwareupdate --install-rosetta
    ```

## Troubleshooting

- **Docker Not Starting**:
    - Ensure that virtualization is enabled in the BIOS.
    - Restart your Mac and try again.

- **Performance Issues**:
    - Allocate more resources to Docker in the Preferences > Resources section.
    - Ensure that your macOS and Docker are up to date.

For more detailed instructions, refer to the [official Docker documentation](https://docs.docker.com/docker-for-mac/apple-silicon/).