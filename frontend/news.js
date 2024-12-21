document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-item').forEach(link => {
            link.classList.remove('active');
        });
        e.currentTarget.classList.add('active');
        
        // Clear existing news
        const container = document.getElementById('newsContainer');
        container.innerHTML = '';
        
        // Load news based on selected source
        const source = e.currentTarget.dataset.source;
        if (source === 'CoinMarketCap') {
            loadNews(exampleNewsData);
        } else if (source === 'X') {
            loadNews(xNewsData);
        }
    });
});

// Set CoinMarketCap as default and load its news
document.addEventListener('DOMContentLoaded', async function() {
    const coinMarketCapTab = document.querySelector('[data-source="CoinMarketCap"]');
    coinMarketCapTab.classList.add('active');
    
    // Wait for both datasets to load
    await Promise.all([getCmcData(), getXData()]);
    
    // Load the default news source (CoinMarketCap)
    loadNews(exampleNewsData);
});

function createSentimentElement(sentiment) {
    const sentimentDiv = document.createElement('div');
    sentimentDiv.className = `sentiment ${sentiment.type.toLowerCase()}`;
    
    const header = document.createElement('div');
    header.className = `sentiment-header ${sentiment.type.toLowerCase()}`;
    header.textContent = sentiment.type;
    
    const content = document.createElement('div');
    content.className = `sentiment-content ${sentiment.type.toLowerCase()}`;
    content.textContent = sentiment.content;
    
    sentimentDiv.appendChild(header);
    sentimentDiv.appendChild(content);

    return sentimentDiv;
}

// Function to create a news element
function createNewsElement(newsItem) {
    const newsDiv = document.createElement('div');
    newsDiv.className = 'news';

    newsDiv.addEventListener('click', () => {
        const newsLink = newsItem.link || newsItem.links;
        if (newsLink) {
            window.open(newsLink, '_blank');
        }
    });
    
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = newsItem.timestamp;
    
    const title = document.createElement('div');
    title.className = 'title';
    title.textContent = newsItem.title;
    
    const description = document.createElement('div');
    description.className = 'content';
    description.textContent = newsItem.description;
    
    newsDiv.appendChild(timestamp);
    newsDiv.appendChild(title);
    newsDiv.appendChild(description);
    
    // Add sentiments if they exist
    if (newsItem.sentiments) {
        newsItem.sentiments.forEach(sentiment => {
            newsDiv.appendChild(createSentimentElement(sentiment));
        });
    }
    
    return newsDiv;
}

// Function to load news
function loadNews(newsData) {
    if (!newsData || newsData.length === 0) return; // Guard clause for empty data
    const container = document.getElementById('newsContainer');
    newsData.forEach(newsItem => {
        container.appendChild(createNewsElement(newsItem));
    });
}

// Fetch CoinMarketCap data
let exampleNewsData = [];
let xNewsData = [];
async function getCmcData() {
    try {
        const response = await fetch('http://localhost:8000/cmc_news');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        exampleNewsData = data;
    } catch (error) {
        console.error('Error fetching CoinMarketCap data:', error);
    }
}

// Fetch X data
async function getXData() {
    try {
        const response = await fetch('http://localhost:8000/x_news');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        xNewsData = data;
    } catch (error) {
        console.error('Error fetching X data:', error);
    }
}

// Optional: Infinite scroll implementation
let isLoading = false;
document.querySelector('.load-news').addEventListener('scroll', function(e) {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    
    if (scrollTop + clientHeight >= scrollHeight - 5 && !isLoading) {
        isLoading = true;
        
        // Here you would fetch more news from your crawler
        // Example:
        // fetchMoreNews().then(newData => {
        //     loadNews(newData);
        //     isLoading = false;
        // });
    }
});
