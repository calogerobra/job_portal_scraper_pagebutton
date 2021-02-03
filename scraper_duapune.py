# Import general libraries
import datetime
import pandas as pd
from bs4 import BeautifulSoup as soup
import time
import csv

# Requests package
import requests
requests.packages.urllib3.disable_warnings()
import random

# Improt Selenium packages
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException as NoSuchElementException
from selenium.common.exceptions import WebDriverException as WebDriverException
from selenium.common.exceptions import ElementNotVisibleException as ElementNotVisibleException
from selenium.webdriver.chrome.options import Options



def request_page(url_string, verification, robust):
    """HTTP GET Request to URL.
    Args:
        url_string (str): The URL to request.
        verification: Boolean certificate is to be verified
        robust: If to be run in robust mode to recover blocking
    Returns:
        HTML code
    """
    if robust:
        loop = False
        first = True
        # Scrape contents in recovery mode
        c = 0
        while loop or first:
            first = False
            try:
                uclient = requests.get(url_string, timeout = 60, verify = verification)
                page_html = uclient.text
                loop = False
                return page_html
            except requests.exceptions.ConnectionError:
                c += 10
                print("Request blocked, .. waiting and continuing...")
                time.sleep(random.randint(10,60) + c)
                loop = True
                continue
            except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectTimeout):
                print("Request timed out, .. waiting one minute and continuing...")
                time.sleep(60)
                loop = True
                continue
    else:
        uclient = requests.get(url_string, timeout = 60, verify = verification)
        page_html = uclient.text
        loop = False
        return page_html

def request_page_fromselenium(url_string, driver, robust):
    """ Request HTML source code from Selenium web driver to circumvent mechanisms
    active with HTTP requests
    Args:
        Selenium web driver
        URL string
    Returns:
        HTML code
    """
    if robust:
        loop = False
        first = True
        # Scrape contents in recovery mode
        c = 0
        while loop or first:
            first = False
            try:
                open_webpage(driver, url_string)
                time.sleep(5)
                page_html = driver.page_source
                loop = False
                return page_html
            except WebDriverException:
                c += 10
                print("Web Driver problem, .. waiting and continuing...")
                time.sleep(random.randint(10,60) + c)
                loop = True
                continue
    else:
        open_webpage(driver, url_string)
        time.sleep(5)
        page_html = driver.page_source
        loop = False
        return page_html

def set_driver(webdriverpath, headless):
    """Opens a webpage in Chrome.
    Args:
        url of webpage
        headless parameter
    Returns:
        open and maximized window of Chrome with webpage.
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    elif not headless:
        options.add_argument("--none")
    return webdriver.Chrome(webdriverpath, chrome_options = options)

def create_object_soup(object_link, verification, robust):
    """ Create page soup out of an object link for a product
    Args:
        Object link
        certificate verification parameter
        robustness parameter
    Returns:
        tuple of beautiful soup object and object_link
    """
    object_soup = soup(request_page(object_link, verification, robust), 'html.parser')
    return (object_soup, object_link)

def make_soup(link, verification):
    """ Create soup of listing-specific webpage
    Args:
        object_id
        verification parameter
    Returns:
        soup element containing listings-specific information
    """
    return soup(request_page(link, verification), 'html.parser')

def reveal_all_items(driver):
    """ Reveal all items by clicking on "view all" button
    Args:
        Selenium web driver
    Returns:
        Boolean if all items have been revealed
    """
    hidden = True
    while hidden:
        try:
           time.sleep(random.randint(5,7))
           driver.find_element_by_css_selector('section#listing-home div.col-md-6.customlistinghome > a').click()
        except (NoSuchElementException, ElementNotVisibleException):
           hidden = False
    return True

def open_webpage(driver, url):
    """Opens web page
    Args:
        web driver from previous fct and URL
    Returns:
        opened and maximized webpage
    """
    driver.set_page_load_timeout(60)
    driver.get(url)
    driver.maximize_window()

def extract_listings_pages(first_page_html):
    """ Extract pages using pagecount field on Duapune page
    Args:
        URL
        Robustness parameter
        Certification verification parameter
    Returns:
        listings
    """
    pc_soup = soup(first_page_html, 'html.parser')
    pc_container = pc_soup.findAll('ul', {'class': 'pagination'})[0].findAll('li', {'class': 'page-item'})
    maxpage = int(pc_container[len(pc_container)-2].text)
    return ["https://www.duapune.com/search/advanced/filter?page=" + str(p) for p in range(2, maxpage+1)]


def make_jobs_list(base_url, robust, driver):
    """ Extract item URL links and return list of all item links on web page
    Args:
        Base URL
        Category tuples
        Certificate verification parameter
        Robustness parameter
        Selenium web driver
    Returns:
        Dictionary with item URLs
    """
    print("Start retrieving item links...")
    on_repeat = False
    first_run = True
    item_links = []
    while on_repeat or first_run:
        first_run = False
        open_webpage(driver, base_url)
        if reveal_all_items(driver):
            # Extract first page_html
            first_page_html = driver.page_source
            # Extract page count and loop over pages
            pages = [driver.current_url]
            pages = pages + extract_listings_pages(first_page_html)
            # Loop over pages
            for page in pages:
                time.sleep(1)
                # Within each page extract all links
                open_webpage(driver, page)
                page_html = driver.page_source
                page_soup = soup(page_html, 'html.parser')
                s_link_containers = page_soup.findAll('div', {'class': 'col-md-6 customlistinghome'})[0].findAll('div', {'class': 'job-listing col-md-12 sponsored-listing '})
                p_link_containers = page_soup.findAll('div', {'class': 'col-md-6 customlistinghome'})[0].findAll('div', {'class': 'job-listing col-md-12 premiumBlock simple-listing '})
                p_link_containers = p_link_containers + page_soup.findAll('div', {'class': 'col-md-6 customlistinghome'})[0].findAll('div', {'class': 'job-listing col-md-12 premiumBlockv2 simple-listing '})
                item_links = item_links + [item.findAll('div', {'class', 'mid-conntent'})[0].a['href'] for item in s_link_containers]
                item_links = item_links + [item.findAll('div', {'class', 'mid-conntent'})[0].a['href'] for item in p_link_containers]
                # Check if links where extracted
                try:
                    assert len(item_links) != 0
                    print('Retrieved', len(item_links), 'item links!')
                    on_repeat = False
                except AssertionError:
                    print("No links extracted", "Repeating process...")
                    on_repeat = True
                    break
    return item_links

def create_elements(object_link, verification, robust):
    """Extracts the relevant information form the html container, i.e. object_id,
    Args:
        Object URL
        verification parameter
        robustness parameter
    Returns:
        A dictionary containing the information for one listing.
    """
    object_soup = create_object_soup(object_link, verification, robust)[0]
    # Parse contents
    try:
        company_name = object_soup.findAll('div',
                                           {'class': 'col-md-12 company-details'})[0].findAll('h3',
                                           {'class': 'c-name'})[0].text
    except:
        company_name = ""
    try:
        job_title = object_soup.findAll('div', {'class': 'row block-listings'})[0].findAll('div', {'id': 'listing-home'})[0].div.div.h1.a.text
    except:
        job_title = ""
    try:
        object_id = object_soup.findAll('div', {'class': 'row block-listings'})[0].findAll('div', {'id': 'listing-home'})[0].div.div.h1.small.text.replace('Kodi Punës: ','')
    except:
        object_id = ""
    try:
        job_city = object_soup.findAll('div', {'class': 'row block-listings'})[0].findAll('div', {'class': 'job-details'})[0].findAll("span", {'class': 'location'})[0].text.strip()
    except:
        job_city = ""
    try:
        expiration_date = object_soup.findAll('div', {'class': 'row block-listings'})[0].findAll('div', {'class': 'job-details'})[0].findAll("span", {'class': 'time'})[0].text.replace(' ', '')
    except:
        expiration_date = ""
    try:
        content_containers = object_soup.findAll('div', {'class': 'row block-listings'})[0].findAll('div', {'class': 'main-content-wrap'})[0].findAll('div', {'class': 'row'})
        assert len(content_containers) > 0
    except:
        content_containers = []
    try:
        assert content_containers[0].findAll('span')[0].text == 'Kategoria e Punës / Profesioni'
        job_category = content_containers[0].findAll('span')[1].text
    except:
        job_category = ''
    try:
        assert content_containers[1].findAll('span')[0].text == 'Tipi i punës'
        contract_type = content_containers[1].findAll('span')[1].text
    except:
        contract_type = ''
    try:
        assert content_containers[2].findAll('div', {'class': 'col-xs-6'})[0].text.strip('\n') == 'Eksperiencë'
        experience_requirement = content_containers[2].findAll('div', {'class': 'col-xs-6'})[1].text.strip('\n')
    except:
        experience_requirement = ''
    try:
        assert content_containers[3].findAll('div', {'class': 'col-xs-6'})[0].text.strip('\n') ==  'Kërkohet foto'
        photo_requirement = content_containers[3].findAll('div', {'class': 'col-xs-6'})[1].text.strip('\n')
    except:
        photo_requirement = ''
    try:
        assert content_containers[4].findAll('div', {'class': 'col-xs-6'})[0].text.strip('\n') ==  'Letër interesi'
        cl_requirement = content_containers[4].findAll('div', {'class': 'col-xs-6'})[1].text.strip('\n')
    except:
        cl_requirement = ''
    try:
        assert content_containers[5].findAll('span')[0].text == 'Rroga mujore'
        monthly_salary = content_containers[5].findAll('span')[1].text.strip("\n")
    except:
        monthly_salary = ''
    try:
        job_description = object_soup.findAll('div', {'class': 'main-content-wrap'})[1].text
    except:
        job_description = ""
    object_link = object_link
    page_html = object_soup.prettify()
    # Create a dictionary as output
    return dict([("object_link", object_link),
                 ("job_title", job_title),
                 ("company_name", company_name),
                 ("object_id", object_id),
                 ("job_city", job_city),
                 ("expiration_date", expiration_date),
                 ("job_description", job_description),
                 ("job_category", job_category),
                 ("contract_type", contract_type),
                 ("experience_requirement", experience_requirement),
                 ("monthly_salary", monthly_salary),
                 ("cl_requirement",cl_requirement),
                 ("photo_requirement", photo_requirement),
                 ("page_html", page_html)])

def scrape_duapune(verification, robust, item_links):
    """Scraper for Duapune job portal based on specified parameters.
    In the following we would like to extract all the containers containing
    the information of one listing upon revealing all items. For this purpose we try to parse through
    the html text and search for all elements of interest.
    Args:
        verification parameter
        robustness parameter
        item_links object
    Returns:
        Appended pandas dataframe with crawled content.
    """
    # Define dictionary for output
    input_dict = {}
    frames = []
    counter = 0
    #skipper = 0
    # Loop links
    for item_link in item_links:
        time.sleep(random.randint(1,2))
        print('Parsing URL', item_link)
        # Set scraping time
        now = datetime.datetime.now()
        try:
            input_dict.update(create_elements(item_link, verification, robust))
            time.sleep(0.5)
            # Create a dataframe
            df = pd.DataFrame(data = input_dict, index =[now])
            df.index.names = ['scraping_time']
            frames.append(df)
        except requests.exceptions.ConnectionError:
            error_message = "Connection was interrupted, waiting a few moments before continuing..."
            print(error_message)
            time.sleep(random.randint(2,5) + counter)
            continue
    return pd.concat(frames).drop_duplicates(subset = 'object_link')

def main():
    """ Note: Set parameters in this function
    """
    # Set time stamp
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Set scraping parameters
    base_url = 'https://www.duapune.com/'
    robust = True
    webdriverpath = "C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_scraper_pagebutton\\chromedriver.exe"

    # Set up a web driver
    driver = set_driver(webdriverpath, False)

    # Start timer
    start_time = time.time() # Capture start and end time for performance

    # Set verification setting for certifiates of webpage. Check later also certification
    verification = True

    # Execute functions for scraping
    start_time = time.time() # Capture start and end time for performance
    item_links = make_jobs_list(base_url, robust, driver)
    driver.close()
    appended_data = scrape_duapune(verification, robust, item_links)

    # Split off HTML code if required
    #appended_data = appended_data.drop("page_html", 1)

    # Write output to Excel
    print("Writing to Excel file...")
    time.sleep(1)
    output_path = 'C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_scraper_pagebutton\\data\\daily_scraping\\'

    file_name = '_'.join([output_path +
    str(now_str), 'duapune.xlsx'])
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    appended_data.to_excel(writer, sheet_name = 'jobs')
    writer.save()

    # Write to CSV
    print("Writing to CSV file...")
    appended_data.to_csv(file_name.replace('.xlsx', '.csv'), sep =";",quoting=csv.QUOTE_ALL)

    end_time = time.time()
    duration = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))

    # For interaction and error handling
    final_text = "Your query was successful! Time elapsed:" + str(duration)
    print(final_text)
    time.sleep(0.5)

# Execute scraping
if __name__ == "__main__":
    main()





