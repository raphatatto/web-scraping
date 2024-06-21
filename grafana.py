from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time

# Initialize the browser (Chrome in this case)
driver = webdriver.Chrome()

# Open the desired URL
driver.get('https://grafana.com/about/careers/open-positions/')

# Wait for a while to ensure that dynamic content is loaded
time.sleep(5)

# Get the HTML of the loaded page
html = driver.page_source

# Close the browser
driver.quit()

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find all <h5> elements on the page
list_companies = soup.find_all('h5')

# Extract the text from each <h5> element and store it in a list
results = [company.get_text(strip=True) for company in list_companies]

# Save the results to a JSON file
with open('companies.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

# Print the results
for company in results:
    print(company)

# Print the total number of <h5> elements found
print(f'Total number of h5 on the page: {len(results)}')

# Open and read the JSON file
with open('companies.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Print the content read from the JSON file
print("Content of the JSON file:")
for item in data:
    print(item)
