# Job Search Gmail Monitor

A smart email monitoring tool that helps you stay on top of job applications, interview requests, and recruiter outreach during your job search.

## Features

- 🔍 **Smart Detection**: Combines keyword matching, subject pattern analysis, and AI classification
- 📧 **Email Summaries**: Receive digestible email reports of job-related messages
- 📱 **SMS Alerts**: Optional SMS notifications for urgent interview requests
- ⚙️ **Configurable**: Easy customization via config file
- 🔒 **Secure**: Read-only Gmail access, credentials never committed

## Quick Start

### Prerequisites

- Python 3.8+
- Gmail account
- Google Cloud Project (free tier works fine)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/job-search-gmail-monitor.git
cd job-search-gmail-monitor
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Gmail API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials as `credentials.json` and place in `config/` directory

5. Configure settings:
```bash
cp config/settings.example.yaml config/settings.yaml
# Edit settings.yaml with your preferences
```

6. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Usage

Run the monitor:
```bash
python src/main.py
```

Run in daemon mode (checks periodically):
```bash
python src/main.py --daemon --interval 300  # Check every 5 minutes
```

## Configuration

Edit `config/settings.yaml` to customize:

- Keywords to match
- Email subject patterns
- Notification preferences
- AI classification threshold
- Companies/domains to track

## Project Structure

```
job-search-gmail-monitor/
├── src/
│   ├── main.py              # Entry point
│   ├── gmail_client.py      # Gmail API wrapper
│   ├── classifier.py        # Email classification logic
│   ├── notifier.py          # Notification handlers
│   └── utils.py             # Helper functions
├── config/
│   ├── settings.yaml        # User configuration
│   └── credentials.json     # Gmail API credentials (gitignored)
├── tests/
│   └── test_classifier.py   # Unit tests
├── logs/                    # Application logs (gitignored)
├── .env                     # Environment variables (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

## Security Notes

- Never commit `credentials.json`, `.env`, or `token.pickle` files
- The app only requests read-only access to Gmail
- All sensitive data is stored locally

## Contributing

Pull requests welcome! Please ensure tests pass before submitting.

## License

MIT License - feel free to use and modify as needed.
