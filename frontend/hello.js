let myData; // Declare outside since we can't assign to const before we have the data

async function fetchData() {
  try {
    const response = await fetch('http://localhost:8000/cmc_news');
    const data = await response.json();
    myData = data; // Now we assign the fetched data
    return data;
  } catch (error) {
    console.error('Error:', error);
  }
}

// Usage:
fetchData().then(() => {
  console.log(myData); // Use the data here
});