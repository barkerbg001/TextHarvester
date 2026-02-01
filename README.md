# Text Harvester

A FastAPI-based service that extracts structured invoice data from PDF and image files. Choose **Groq** (cloud LLM) or **Ollama** (local LLM)—both use Tesseract OCR for text extraction and return the same structured JSON schema.

## Features

- 📄 **PDF Text Extraction**: Extracts text directly from PDF documents using PyMuPDF
- 🖼️ **Image OCR**: Optical Character Recognition for JPEG and PNG images using Tesseract
- 🤖 **Dual LLM Backends**:
  - **Groq**: Cloud API (Llama 3.3 70B)—fast, requires `GROQ_API_KEY`
  - **Ollama**: Local models (Llama 3, Mistral, etc.)—no API key, runs on your machine
- ✅ **Schema Validation**: Automatic validation with Pydantic models ensuring data integrity
- 🐳 **Docker Support**: Containerized deployment with automatic Tesseract installation
- 🌐 **Cross-Platform Support**: Works on Windows, macOS, and Linux with automatic Tesseract path detection
- 🔄 **Auto-Configuration**: Automatically detects Tesseract installation paths across different platforms

## Prerequisites

### For Local Development
- Python 3.8 or higher
- Tesseract OCR (version 5.x recommended)
- **Groq**: Groq API key (set in `.env`) — [Get one](https://console.groq.com/)
- **Ollama** (optional): Install and run Ollama locally for the `/ollama` routes

### For Docker Deployment
- Docker Desktop (or Docker Engine)
- Ollama installed and running on the host machine (for Ollama routes)

## Quick Start with Docker (Recommended)

### 1. Install Ollama on Your Host Machine

Download and install Ollama from: https://ollama.com/download

After installation, pull a model:

```bash
ollama pull llama3
```

You can use other models like `llama3.2`, `mistral`, `codellama`, etc.

### 2. Start Ollama

Make sure Ollama is running on your host machine:

```bash
ollama serve
```

Or on macOS/Windows, the Ollama app runs automatically in the background.

### 3. Build and Run the Docker Container

```bash
# Build the Docker image
docker build -t textharvester .

# Run the container
docker run --rm -p 8000:8000 textharvester
```

The API will be available at: `http://localhost:8000`

**Note**: The Docker container is configured to connect to Ollama running on your host machine via `host.docker.internal`. This works automatically with Docker Desktop on macOS and Windows.

### 4. Test the API

**Groq** (requires `GROQ_API_KEY` in `.env` inside the container or passed at run time):

```bash
curl -X POST "http://localhost:8000/groq/process-invoice" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-invoice.pdf"
```

**Ollama** (local; ensure Ollama is running on the host):

```bash
curl -X POST "http://localhost:8000/ollama/process-invoice" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-invoice.pdf"
```

## Local Development Setup

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd TextHarvester
```

Or download and extract the project to your desired location.

### 2. Install Python Dependencies

Create a virtual environment (recommended):

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

#### Windows

**Option A - Using Chocolatey:**
```bash
choco install tesseract
```

**Option B - Manual Installation:**
1. Download the installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run `tesseract-ocr-w64-setup-5.x.x.exe`
3. Install to default location: `C:\Program Files\Tesseract-OCR`
4. The application will automatically detect this path

#### macOS

**Using Homebrew:**
```bash
brew install tesseract
```

The application checks common paths: `/usr/local/bin/tesseract`, `/opt/homebrew/bin/tesseract`, `/usr/bin/tesseract`

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr
```

#### Linux (Fedora/RHEL)

```bash
sudo dnf install tesseract
```

### 4. Configure Groq (optional, for `/groq` routes)

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from: https://console.groq.com/

### 5. Install Ollama (optional, for `/ollama` routes)

Download and install Ollama from: https://ollama.com/download

After installation, pull a model:

```bash
ollama pull llama3
```

You can use other models like `mistral`, `llama3.2`, `codellama`, etc.

## Running the Application

### 1. Start Ollama

Make sure Ollama is running:

```bash
ollama serve
```

Or on macOS/Windows, the Ollama app runs automatically in the background.

### 2. Start the FastAPI Server

```bash
uvicorn main:app --reload
```

The `--reload` flag enables auto-reload on code changes (useful for development).

The API will be available at: `http://127.0.0.1:8000`

### Accessing the API Documentation

- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

## API Usage

The app exposes two routers. Both endpoints accept the same file types and return the same response schema.

| Router | Endpoint | Backend | API Key |
|--------|----------|---------|---------|
| Groq   | `POST /groq/process-invoice`   | Groq (Llama 3.3 70B) | `GROQ_API_KEY` in `.env` |
| Ollama | `POST /ollama/process-invoice` | Local Ollama (e.g. llama3) | None |

**Supported file formats (both endpoints):**
- `application/pdf` - PDF documents
- `image/jpeg` - JPEG images
- `image/png` - PNG images

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (binary file upload)

**Response Schema (same for both):**
```json
{
  "doc_number": "INV-12345",
  "supplier": "ACME Corp",
  "business_unit": "Sales Department",
  "items": [
    {
      "description": "Product A",
      "quantity": 2.0,
      "unit_price": 50.0,
      "total": 100.0
    }
  ],
  "subtotal": 100.0,
  "tax_amount": 10.0,
  "total_amount": 110.0
}
```

**Field Descriptions:**
- `doc_number`: Invoice or reference number (required)
- `supplier`: Name of the vendor or supplier (required)
- `business_unit`: Internal department/unit location (optional)
- `items`: Array of invoice line items with description, quantity, unit_price, and total
- `subtotal`: Subtotal amount before tax (required)
- `tax_amount`: Tax amount (required)
- `total_amount`: Total amount including tax (required)

### Example using cURL

**Groq:**
```bash
curl -X POST "http://localhost:8000/groq/process-invoice" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf"
```

**Ollama:**
```bash
curl -X POST "http://localhost:8000/ollama/process-invoice" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf"
```

### Example using Python

```python
import requests

# Groq
url = "http://localhost:8000/groq/process-invoice"
files = {"file": open("invoice.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())

# Ollama
url = "http://localhost:8000/ollama/process-invoice"
response = requests.post(url, files=files)
print(response.json())
```

### Example using JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

// Groq
fetch('http://localhost:8000/groq/process-invoice', { method: 'POST', body: formData })
  .then(r => r.json()).then(console.log);

// Ollama
fetch('http://localhost:8000/ollama/process-invoice', { method: 'POST', body: formData })
  .then(r => r.json()).then(console.log);
```

## How It Works

1. **File Upload**: The client sends a PDF or image to either `/groq/process-invoice` or `/ollama/process-invoice`.
2. **Text Extraction**: 
   - For PDFs: PyMuPDF extracts text from the document.
   - For images: Tesseract OCR extracts text from the image.
3. **AI Processing**: 
   - **Groq**: Extracted text is sent to Groq’s Llama 3.3 70B with a JSON schema; response is natively JSON.
   - **Ollama**: Extracted text is sent to your local Ollama model (e.g. llama3); response is cleaned (markdown code blocks removed) and parsed as JSON.
4. **Data Validation**: The parsed JSON is validated against the shared Pydantic schema.
5. **Response**: Structured invoice data is returned, or a detailed error if validation or parsing fails.

## Docker Configuration

The Dockerfile includes:
- Python 3.12 slim base image
- Tesseract OCR and English language pack pre-installed
- All Python dependencies from `requirements.txt`
- Environment variable `OLLAMA_HOST` set to `http://host.docker.internal:11434` to connect to Ollama on the host machine

### Docker Build Options

**Standard build:**
```bash
docker build -t textharvester .
```

**Build with custom tag:**
```bash
docker build -t textharvester:latest .
```

**Run with custom port:**
```bash
docker run --rm -p 8080:8000 textharvester
```

### Docker Compose (Optional)

You can create a `docker-compose.yml` file to orchestrate both services:

```yaml
version: '3.8'

services:
  textharvester:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

volumes:
  ollama_data:
```

Then run:
```bash
docker-compose up
```

## Troubleshooting

### Tesseract Not Found

If you get a "tesseract is not installed" error:

1. **Verify installation:**
   ```bash
   tesseract --version
   ```

2. **Check automatic detection:**
   The application automatically checks common installation paths. If Tesseract is installed in a non-standard location, edit `main.py` and add your Tesseract path to the `possible_paths` list in the `configure_tesseract()` function.

3. **Windows specific:**
   Ensure Tesseract is installed in one of these locations:
   - `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
   - `C:\Tesseract-OCR\tesseract.exe`

4. **Docker:**
   Tesseract is pre-installed in the Docker image, so this shouldn't be an issue when using Docker.

### Empty Text Extraction

If you get "No readable text found in document":

- **For PDFs**: 
  - Ensure it's not a scanned PDF (image-only). Scanned PDFs should be converted to images first
  - Try opening the PDF in a text editor to verify it contains extractable text
- **For images**: 
  - Ensure the image is clear and readable
  - Higher resolution images generally produce better OCR results
  - Ensure good contrast between text and background
- **General**: 
  - Check if Tesseract is properly installed and accessible
  - Verify the file is not corrupted

### Ollama Connection Error

If you get a connection error:

1. **Verify Ollama is running:**
   ```bash
   ollama list
   ```
   If this fails, start Ollama with `ollama serve`

2. **Check Ollama status:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Docker-specific:**
   - Ensure Ollama is running on your host machine (not inside Docker)
   - Verify `host.docker.internal` is accessible from your container
   - On Linux, you may need to use `--add-host=host.docker.internal:host-gateway` when running the container:
     ```bash
     docker run --rm -p 8000:8000 --add-host=host.docker.internal:host-gateway textharvester
     ```

### Groq API Key / Model Errors

- Ensure `.env` contains `GROQ_API_KEY` and the server was restarted after adding it.
- If the Groq model name changes, update `routers/groq_router.py` (e.g. `model="llama-3.3-70b-versatile"`). See: https://console.groq.com/docs/models

### Ollama Model Not Found

If you get a model not found error when using `/ollama/process-invoice`:

1. **List available models:**
   ```bash
   ollama list
   ```

2. **Pull the required model:**
   ```bash
   ollama pull llama3
   ```

3. **Use a different model:** Edit `routers/ollama_router.py` and change the `model` argument in the `ollama.chat()` call (e.g. `model="llama3"` to `model="mistral"`).

   Available models: https://ollama.com/library

### Schema Validation Errors

If you get validation errors about missing fields:

- The LLM may have returned incomplete data
- Check the raw text extraction quality—poor OCR can lead to incomplete extraction
- **Ollama**: Try a different model in `routers/ollama_router.py` (e.g. mistral)
- **Ollama**: The app detects if the LLM returns a schema definition instead of data and returns a clear error

### Port Already in Use

If port 8000 is already in use:

**Local development:**
```bash
uvicorn main:app --reload --port 8001
```

**Docker:**
```bash
docker run --rm -p 8001:8000 textharvester
```

## Project Structure

```
TextHarvester/
├── main.py              # FastAPI app, Tesseract config, router registration
├── schemas.py           # Shared Pydantic models (InvoiceItem, InvoiceSchema)
├── utils.py             # Shared text extraction (PDF, image OCR)
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configuration
├── .env                 # GROQ_API_KEY (create this; not in repo)
├── .gitignore
├── README.md
├── routers/
│   ├── __init__.py
│   ├── groq_router.py   # POST /groq/process-invoice (Groq LLM)
│   └── ollama_router.py # POST /ollama/process-invoice (Ollama local)
└── samples/             # Sample invoice files (optional)
```

## Dependencies

The project uses the following key dependencies (see `requirements.txt` for versions):

- **FastAPI** (≥0.109.0): Web framework
- **Uvicorn** (≥0.27.0): ASGI server
- **python-multipart** (≥0.0.6): File uploads
- **PyMuPDF** (≥1.23.0): PDF text extraction
- **pytesseract** (≥0.3.10): Tesseract OCR wrapper
- **Pillow** (≥10.2.0): Image processing
- **ollama** (≥0.4.0): Ollama Python client (local LLM)
- **groq** (≥0.4.0): Groq API client (cloud LLM)
- **python-dotenv** (≥1.0.0): Load `.env` for `GROQ_API_KEY`
- **Pydantic** (≥2.5.0): Data validation

## Technical Details

### LLM Backends

| Backend | Model | Config |
|---------|--------|--------|
| **Groq** | Llama 3.3 70B Versatile | `routers/groq_router.py`; `GROQ_API_KEY` in `.env` |
| **Ollama** | e.g. llama3 | `routers/ollama_router.py`; run `ollama serve` and pull a model |

Both use an accountant-style system prompt and return JSON validated against the same Pydantic schema. Ollama responses are cleaned of markdown code blocks and checked to ensure the LLM returned data, not a schema definition.

### OCR Configuration

- **Engine**: Tesseract OCR
- **Auto-detection**: Automatically finds Tesseract installation across platforms
- **Supported Languages**: Default (English), can be extended with language packs
- **Docker**: Tesseract pre-installed with English language pack

### Data Validation

- Uses Pydantic v2 for schema validation
- Automatic type conversion and validation
- Clear error messages for invalid data
- Handles markdown code blocks in LLM responses
- Validates that LLM returns actual data, not schema definitions

### Docker Architecture

- **Base Image**: Python 3.12 slim (Debian-based)
- **System Dependencies**: Tesseract OCR, English language pack, graphics libraries
- **Network**: Connects to Ollama on host via `host.docker.internal:11434`
- **Port**: Exposes port 8000 for FastAPI

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues related to:

- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **Groq**: https://console.groq.com/docs
- **Ollama**: https://ollama.com/ | https://github.com/ollama/ollama
- **FastAPI**: https://fastapi.tiangolo.com/
- **PyMuPDF**: https://pymupdf.readthedocs.io/
- **Docker**: https://docs.docker.com/

## Acknowledgments

- Groq for fast cloud LLM inference
- Ollama for local LLM inference
- Tesseract OCR team for the OCR engine
- FastAPI for the web framework
- Docker for containerization support