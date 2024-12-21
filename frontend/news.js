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
document.addEventListener('DOMContentLoaded', function() {
    const coinMarketCapTab = document.querySelector('[data-source="CoinMarketCap"]');
    coinMarketCapTab.classList.add('active');
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
    description.className = 'description';
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

    const container = document.getElementById('newsContainer');
    newsData.forEach(newsItem => {
        container.appendChild(createNewsElement(newsItem));
    });
}

// Example for CoinMarketCap:
const exampleNewsData = [
    {
        timestamp: "1 hours ago",
        title: "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
        description: "The world of cryptocurrencies is in turmoil...",
        links: 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
        sentiments: [
            {
                type: "Positive",
                content: "the article presents a reasonable and wellsubstantiated case..."
            },
            {
                type: "Negative",
                content: "the article also presents concerns about..."
            }
        ]
    },
    {
        timestamp: "1 hours ago",
        title: "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
        description: "The world of cryptocurrencies is in turmoil...",
        links: 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
        sentiments: [
            {
                type: "Negative",
                content: "the article also presents concerns about..."
            }
        ]
    },
    {
        timestamp: "1 hours ago",
        title: "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
        description: "The world of cryptocurrencies is in turmoil...",
        link: 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
        sentiments: [
            {
                type: "Positive",
                content: "the article presents a reasonable and wellsubstantiated case..."
            }
        ]
    },
    {
        timestamp: "1 hours ago",
        title: "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
        description: "The world of cryptocurrencies is in turmoil...",
        link: 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
        sentiments: [
            {
                type: "Positive",
                content: "the article presents a reasonable and wellsubstantiated case..."
            },
            {
                type: "Negative",
                content: "the article also presents concerns about..."
            }
        ]
    },
];
// Example for X:
const xNewsData = [
    {
        timestamp: "2 hours ago",
        title: "X Platform News Example",
        description: "@userid",
        link: 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
        sentiments: [
            {
                type: "Positive",
                content: "Positive sentiment from X..."
            }
        ]
    },
];

// Load initial news
loadNews(exampleNewsData);

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