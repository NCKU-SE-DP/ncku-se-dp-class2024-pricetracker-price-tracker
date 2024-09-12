# Price Tracker

A web application for tracking product prices over time, scraping news, and providing users with an interactive platform to analyze price trends and discuss related news. The project is built using Vue.js for the front-end and FastAPI for the back-end.

## Features

- **Price Trend Analysis**: Visualize price changes of various products over time with interactive charts.
- **News Scraping**: Automatically scrape news related to commodity prices.
- **User Registration and Login**: Allow users to create accounts and log in, to upvote the news.
- **Generative AI for News Summarization**: Use AI to quickly summarize news content for better user understanding.

## Tech Stack

- **Front-End**: Vue.js
- **Back-End**: FastAPI
- **Database**: SQLite (development)
- **APIs and Libraries**:
  - Axios for HTTP requests
  - Chart.js for data visualization
  - Beautiful Soup for web scraping
  - OpenAI API for generative AI functions
- **Deployment**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Node.js (version 14.x or higher)
- Python 3.8 or higher
- Docker and Docker Compose

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/NCKU-SE-DP/price-tracker.git
   cd price-tracker
   ```
2. Run with Docker
   ```
   docker-compose up
   ```

### Usage
Open your web browser and go to http://localhost:8080 to access the frontend.
Use the navigation bar to explore features like price trend analysis, news browsing.
Go to http://localhost:8000/docs to access the backend documents.

### License
This project is licensed under the MIT License. See the [LICENSE](https://github.com/NCKU-SE-DP/price-tracker/blob/main/LICENSE) file for details.



