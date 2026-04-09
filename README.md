# NetGen AI

A Python web application that uses Claude AI to generate synthetic network data rows based on an uploaded dataset. Upload a CSV, analyze its schema, and generate realistic new rows that match your data's patterns, value ranges, and distributions.

## Features

- **CSV Upload & Analysis** — Upload any CSV file and instantly view its schema, data types, and sample rows in a paginated table.
- **AI-Powered Generation** — Claude analyzes your dataset and generates realistic synthetic rows that follow the same patterns and distributions.
- **Validation Preview** — Compare generated rows side-by-side with real data before appending.
- **Export** — Download the augmented dataset as a new CSV file.

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## Installation

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd Netgen-AI
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up your API key by creating a `.env` file in the project root:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your Anthropic API key:

   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

## Running the App

```bash
python app.py
```

The app will start at **http://127.0.0.1:5000**.

## Usage

1. **Upload** — Open the app in your browser and upload a CSV file using the drag-and-drop zone or file browser.
2. **Review** — View the dataset table with column schema, data types, and paginated rows.
3. **Generate** — Enter the number of synthetic rows to generate (1–100) and click "Generate Rows". Claude AI will analyze your data and create new matching rows.
4. **Validate** — Preview the generated rows (highlighted in green) alongside real sample rows for comparison.
5. **Confirm or Discard** — Click "Confirm & Append" to add the rows to your dataset, or "Discard" to throw them away.
6. **Download** — After confirming, download the augmented CSV file from the dataset page.

## Project Structure

```
Netgen-AI/
├── app.py              # Flask routes and main application
├── ai_generator.py     # Claude API integration
├── data_handler.py     # CSV parsing, appending, saving with pandas
├── templates/
│   ├── base.html       # Base layout with navbar
│   ├── index.html      # Upload page
│   ├── dataset.html    # Dataset display + generate button
│   └── preview.html    # Preview generated rows + confirm/discard
├── static/
│   ├── style.css       # Application styling
│   └── script.js       # Frontend JavaScript
├── uploads/            # Temporary storage for uploaded CSVs
├── outputs/            # Augmented CSV downloads
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Environment Variables

| Variable            | Description                        |
|---------------------|------------------------------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required)  |

## Error Handling

- Invalid file types are rejected with a user-facing message.
- Claude API errors are caught and displayed as flash messages.
- Malformed JSON responses from Claude are retried once automatically; if still invalid, an error message is shown.
