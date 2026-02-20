# Bluestreak Box Uploader

Upload Bluestreak MES/QMS certifications to Box.com for customer sharing.

## Features

- Query certifications by Order ID (partial search, minimum 3 characters)
- Select and upload certification documents to Box.com
- Automatic Box folder structure creation: `[OrderID] (PO#[PONumber])/[CertNo]/`
- JWT authentication with Box.com
- Progress tracking with detailed logging
- Auto-upload option when single certification is found
- SQL Server and SQLite database support
- Modern dark theme interface

## Installation

### From Releases

Download the latest installer from [Releases](../../releases) and run `BluestreakBoxUploader_Setup_x.x.x.exe`.

### Run from Source

```bash
# Clone the repository
git clone <repository-url>
cd thepoli

# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# Launch the application
python -m gui.app
```

## Usage

1. **Configure Settings** - Open `File > Settings` (Ctrl+,) to set up:
   - Database connection (SQL Server or SQLite)
   - Box JWT configuration file path
   - Media base path for certification files

2. **Search for Order** - Enter at least 3 characters of an Order ID and click Search

3. **Review Certifications** - The table shows all matching certifications with their media files

4. **Select and Upload** - Check the certifications to upload and click "Upload Selected"

5. **Monitor Progress** - Track uploads in the progress bar and log viewer

## CLI

Development and testing commands are available via `cli.py`:

```bash
# Query certifications for an order
python cli.py query 444337 --sqlite test.db

# Test database connection
python cli.py test-db --sqlite test.db
python cli.py test-db --driver sqlserver --host SERVER --database Bluestreak --username USER --password PASS

# Test Box.com connection
python cli.py test-box --config path/to/box_config.json

# Seed SQLite database with sample data (for testing)
python cli.py seed -o test.db
```

## Configuration

Settings are stored in:
- **Windows**: `%APPDATA%\BluestreakBoxUploader\settings.toml`
- **macOS**: `~/Library/Application Support/BluestreakBoxUploader/settings.toml`
- **Linux**: `~/.config/bluestreakboxuploader/settings.toml`

A local `settings.toml` in the working directory takes precedence (useful for development).

### Box JWT Setup

1. Create a Box application in the [Box Developer Console](https://app.box.com/developers/console)
2. Configure JWT authentication and download the JSON config file
3. Authorize the app in Box Admin Console
4. Set the config file path in the application settings

### Database Setup

Customers must have `cstIntegrationID` set to their Box folder ID to enable uploads.

## Requirements

- Windows 10/11
- SQL Server with ODBC Driver 17, or SQLite for testing
- Box.com JWT application credentials
- Python 3.12+ (for running from source)

## Building

Use `build.py` to create distributable packages:

```bash
# Build with patch version bump (1.0.0 -> 1.0.1)
python build.py

# Build with minor version bump (1.0.0 -> 1.1.0)
python build.py minor

# Build with major version bump (1.0.0 -> 2.0.0)
python build.py major

# Build without version bump
python build.py --no-bump

# Build and create GitHub release
python build.py --release

# Create release only (skip build)
python build.py --release-only
```

Requires [Inno Setup](https://jrsoftware.org/isdl.php) for Windows installer creation.

## License

Private - Burton Industries
