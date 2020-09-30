from bs4 import BeautifulSoup
import requests
import csv


class Scraper:
    def __init__(self):
        self.category_url = "http://books.toscrape.com/catalogue/category/books/sequential-art_5/"
        self.current_url = self.category_url + "index.html"
        # Creating a list of URL for each book by gathering them from a Category page
        self.books_url = []
        self.csv_lines = []

    def create_urls(self):
        while True:
            # Creating the soup for each page (only one if there is less than 21 books in the category)
            html_page = requests.get(self.current_url)
            soup = BeautifulSoup(html_page.text, 'html.parser')
            # For each link in the page we extract the URL and replace the root link to the http one
            for link in soup.find_all('h3'):
                self.books_url.append("http://books.toscrape.com/catalogue/" + str(link)[22:].split('"',1)[0])
            next_url = str(soup.find("li", {"class": "next"}))[26:].split('"',1)[0]
            if not next_url:
                break
            self.current_url = self.category_url + next_url

    def scrape(self):
        for link in self.books_url:
            product_page_url = link
            html_page = requests.get(product_page_url)
            soup = BeautifulSoup(html_page.text, 'html.parser')

            # extracting all the TR attributes as they'll be used later for needed results:
            # (0 = UPC, 1 = product type, 2 = price (excl. tax), 3 = Price (incl. tax), 4 = tax, 5 = Availability, 6 = Number of reviews)
            list = []
            for i in soup.find_all('tr'):
                result = i.find('td')
                list.append(result.getText())

            universal_product_code = list[0]
            title = soup.find('h1').getText()
            # prices have a weird character in front of them, needs to be removed
            price_including_tax = list[3][1:]
            price_excluding_tax = list[2][1:]
            #removing the text around the numbers of units available
            number_available = list[5][10:-11]
            #product description is the 4th <p> tag, we re-use the list var as we don't need it anymore
            list = []
            for i in soup.find_all('p'):
                result = i.getText()
                list.append(result)
            product_description = list[3]
            #category is the text of the 3rd <li> tag, we re-use the list var as we don't need it anymore.
            list = []
            for i in soup.find_all('li'):
                result = i.getText()
                list.append(result)
            # removing the new lines before and after the text
            category = list[2][1:-1]
            # removing the first chracters of the string and what's after the 1st remaining "
            review_rating = str(soup.find("p", {"class": "star-rating"}))[22:].split('"',1)[0]
            image_url = soup.find('img')['src']

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
            print([product_page_url,
                        universal_product_code,
                        title,
                        price_including_tax,
                        price_excluding_tax,
                        number_available,
                        product_description,
                        category,
                        review_rating,
                        image_url])

    def save_to_csv(self):
        # writing the headers in the CSV file
        with open('books.csv', 'w', newline='',encoding="utf-8") as csvfile:
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
            for book in self.csv_lines:
                writer.writerow(book)
    
    def run(self):
        self.create_urls()
        self.scrape()
        self.save_to_csv()


if __name__ == "__main__":
    scraper = Scraper()
    scraper.run()
