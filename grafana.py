import time
import json
import re
import logging
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_text(text):
    # Remove tags HTML
    text = re.sub(r'<[^>]+>', text)
    # Remove quebras de linha e espaços extras
    text = re.sub(r'\s+', text).strip()
    return text

# Function to extract job details from the job detail page
def extract_job_details(page):
    job_details = {}

    try:
        # Extract Title
        title_element = page.query_selector('h1.app-title')
        job_details['title'] = title_element.inner_text().strip() if title_element else 'No title found'

        # Extract Location
        location_element = page.query_selector('div.location')
        job_details['location'] = location_element.inner_text().strip() if location_element else 'No location found'

        # Extract Description
        description_elements = page.query_selector_all('#content p')
        job_details['description'] = [el.inner_text().strip() for el in description_elements if el.inner_text().strip() != "&nbsp;"] if description_elements else 'No description found'

        # Extract Responsibilities
        responsibilities_elements = page.query_selector_all('#content ul li')
        job_details['responsibilities'] = [el.inner_text().strip() for el in responsibilities_elements] if responsibilities_elements else 'No responsibilities found'

        # Extract All List Items in #content
        list_elements = page.query_selector_all('#content ul li')
        job_details['list_items'] = [el.inner_text().strip() for el in list_elements] if list_elements else 'No list items found'

        # Extract "About Grafana Labs"
        about_element = page.query_selector('div.content-conclusion div:has-text("About Grafana Labs")')
        job_details['about'] = about_element.inner_text().strip() if about_element else 'No about found'

        # Extract Benefits
        benefits_element = page.query_selector('div.content-conclusion div:has-text("Benefits:")')
        job_details['benefits'] = benefits_element.inner_text().strip() if benefits_element else 'No benefits found'
        
        # Extract "Equal Opportunity Employer"
        opportunity_element = page.query_selector('div:has-text("Equal Opportunity Employer:")')
        job_details['opportunity'] = opportunity_element.inner_text().strip() if opportunity_element else 'No opportunity information found'

        # Extract Application URL
        application_url_element = page.query_selector('#apply_button')
        apply_url = application_url_element.get_attribute('href') if application_url_element else 'No application URL found'
        job_details['applyURL'] = urljoin(page.url, apply_url) if application_url_element else 'No application URL found'

        job_details['company'] = 'Grafana'

        # Extract JSON-LD Schema
        json_ld_element = page.query_selector('script[type="application/ld+json"]')
        if json_ld_element:
            json_data = json_ld_element.inner_text()
            try:
                schema_data = json.loads(json_data)
                job_details['jsonSchema'] = schema_data  # Append the entire JSON-LD as a nested dictionary
            except json.JSONDecodeError:
                logging.error("Error decoding JSON-LD schema")
        
        logging.debug("Extracted job details")
    except Exception as e:
        logging.error("Error extracting job details: %s", e)

    return job_details

def scrape_jobs(max_pages=1):
    job_listings = []
    page_counter = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://grafana.com/about/careers/open-positions/')
        logging.info("Navigated to job listings page")

        while True:
            try:
                # Wait for the job listings to load
                page.wait_for_selector('div.col')

                # Find all job listing elements
                listing_elements = page.query_selector_all('div.col')
                logging.info(f"Found {len(listing_elements)} job listing elements on page {page_counter + 1}")

                # Extract details for each job listing
                for listing in listing_elements:
                    href = listing.query_selector('a.card-resource').get_attribute('href')
                    if href:
                        try:
                            job_url = href
                            new_page = browser.new_page()
                            new_page.goto(job_url)
                            new_page.wait_for_selector('h1.app-title', timeout=10000)
                            job_details = extract_job_details(new_page)
                            job_listings.append(job_details)
                            new_page.close()
                            time.sleep(1)
                        except Exception as e:
                            logging.error("Error processing listing: %s", e)
                            continue

                # Increment page counter
                page_counter += 1
                if page_counter >= max_pages:
                    break

                # Check for the next page button and navigate
                next_button = page.query_selector('button[aria-label="Next page"]')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    page.wait_for_timeout(2000)  # Adjust this as necessary for the page to load
                else:
                    break

            except Exception as e:
                logging.error("Error during scraping: %s", e)
                break

        browser.close()

    # Save the job listings to a JSON file
    with open('grafana_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('Job listings have been scraped and saved to grafana_job_listings.json')

# Execute the scraping function with a limit of 2 pages for testing
scrape_jobs(max_pages=1)
