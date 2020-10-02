"""A Python project to work on the language"""
import csv # to export results as a CSV file
import shutil # to download images
import os # to be able to create/check directories
import requests # needed to get the webpage passed to bs4
from bs4 import BeautifulSoup #needed to map the webpages


class Scraper:
    """gathering informations on books.toscrape.com and exporting them as CSV"""
    def __init__(self):
        """self init of the scraper"""
        self.root_url = "http://books.toscrape.com/index.html"
        self.categories_url = "http://books.toscrape.com/catalogue/category/books/"
        self.catalogue = "http://books.toscrape.com/catalogue/"
        self.category_list = []
        self.books_url = []
        self.csv_lines = []
        self.category_index = 0
        # check if the folders exist, if not, create them
        if not os.path.isdir("CSV"):
            os.makedirs("CSV")
        if not os.path.isdir("images"):
            os.makedirs("images")

    def create_categories(self):
        """Run on the homepage of the website to gather all categories."""
        html_page = requests.get(self.root_url)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        # For each link in the page we extract the URL and replace the root link to the http one
        for cat in soup.find_all("div", {"class": "side_categories"}):
            for link in cat.find_all('a'):
                self.category_list.append(str(link)[34:].split('/', 1)[0])
        # the first category is a link to the root, need to be dropped
        self.category_list.pop(0)


    def create_urls(self):
        """In the provided category, return a list of URL to the product pages for the books"""
        current_url = self.categories_url+self.category_list[self.category_index]+"/index.html"
        print(f"Scraping books in : {self.category_list[self.category_index]}...")
        # Creating a list of URL for each book by gathering them from a Category page
        while True:
            # Creating the soup for each page (one if there is less than 21 books in the category)
            html_page = requests.get(current_url)
            soup = BeautifulSoup(html_page.text, 'html.parser')
            # For each link in the page we extract the URL and replace the root link to the http one
            for link in soup.find_all('h3'):
                self.books_url.append(self.catalogue + str(link)[22:].split('"', 1)[0])
            next_url = str(soup.find("li", {"class": "next"}))[26:].split('"', 1)[0]
            if not next_url:
                break
            current_url = self.categories_url+self.category_list[self.category_index]+next_url

    def scrape(self):
        """with the product page link provided, gather every information to the list 'csv_lines'"""
        for product_page_url in self.books_url:
            soup = BeautifulSoup(requests.get(product_page_url).text, 'html.parser')

            # extracting all the TR attributes as they'll be used later for needed results:
            # 0 UPC 1 product type 2 price (excl. tax) 3 Price (incl. tax)
            # 4 tax 5 Availability 6 Number of reviews
            results = []
            for i in soup.find_all('tr'):
                results.append(i.find('td').getText())

            universal_product_code = results[0]
            title = soup.find('h1').getText()
            # prices have a weird character in front of them, needs to be removed
            price_including_tax = results[3][2:]
            price_excluding_tax = results[2][2:]
            # removing the text around the numbers of units available
            number_available = results[5][10:-11]
            # product description is the 4th <p> re-using results as we don't need it anymore
            results = []
            for i in soup.find_all('p'):
                results.append(i.getText())
            product_description = results[3]
            # category is in the the 3rd <li> re-using results as we don't need it anymore
            results = []
            for i in soup.find_all('li'):
                results.append(i.getText())
            # removing the new lines before and after the text
            category = results[2][1:-1]
            # removing the first chracters of the string and what's after the 1st remaining "
            review_rating = str(soup.find("p", {"class": "star-rating"}))[22:].split('"', 1)[0]
            # the URL to the image is based on the website, translated by removing the first 6 chars
            image_url = "http://books.toscrape.com/" + soup.find('img')['src'][6:]

            self.csv_lines.append([product_page_url,
                                   universal_product_code,
                                   title,
                                   price_including_tax,
                                   price_excluding_tax,
                                   number_available,
                                   product_description,
                                   category,
                                   review_rating,
                                   image_url])
            self.save_images(product_page_url, image_url)

    @classmethod
    def save_images(cls, product_page_url, image_url):
        """for each book, we save it's cover image to the Images folder"""
        request = requests.get(image_url, stream = True)
        if request.status_code == 200:
            # we put all image files in the image folder
            # we use the name in the product page URL as the title is often too long
            # we pick the fileformat from the url in case they are not all .jpg
            with open("images/" +
                        product_page_url[36:-11].split('_')[0] +
                        "." + image_url.split('.')[-1], 'wb') as file:
                request.raw.decode_content = True
                shutil.copyfileobj(request.raw, file)


    def save_to_csv(self):
        """Rwith the data gathered to the list 'csv_lines', export it to a CSV"""
        #creating the filename
        filename = "CSV/" + self.category_list[self.category_index].split('_')[0] + ".csv"
        # writing the headers in the CSV file
        with open(filename, 'w', newline='', encoding="latin-1") as csvfile:
            writer = csv.writer(csvfile)
            header = ["product_page_url",
                      "universal_ product_code (upc)",
                      "title", "price_including_tax",
                      "price_excluding_tax",
                      "number_available",
                      "product_description",
                      "category",
                      "review_rating",
                      "image_url"]
            writer.writerow(header)
            #writing all the lines from the existing list
            for book in self.csv_lines:
                writer.writerow(book)

    def run(self):
        """Run everything in order"""
        self.create_categories()
        for _ in self.category_list:
            self.create_urls()
            self.scrape()
            self.save_to_csv()

            # getting ready for the next category
            self.category_index += 1
            self.books_url = []
            self.csv_lines = []


if __name__ == "__main__":
    scraper = Scraper()
    scraper.run()
