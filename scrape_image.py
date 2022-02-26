"""Scraper to get an image URL from wikipedia, based on the search term.

Run the script using a command like `python scrape_image.py "search_string"`,
  to return a URL for the image from the search string.

  Example:
  `python scrape_image.py "Snoop Dogg"`
  Returns:
  https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Snoop_Dogg_2019_by_Glenn_Francis.jpg/220px-Snoop_Dogg_2019_by_Glenn_Francis.jpg
"""

from bs4 import BeautifulSoup, Tag
from requests import get
from sys import argv
import re

def get_wiki_page_id(search_term: str) -> int:
  """Gets the id of the first Wikipedia page returned from a search,
  using the input search term.

  Args:
      search_term (str): string to search for, using additional identifiers is
      helpful.
        e.g., searching "washington" is ambiguous, so searching for
        "washington state", "george washington", etc. will return a better
        result

  Returns:
      int: page_id of the wikipedia page
  """

  base_url = "https://en.wikipedia.org/w/api.php"
  search_params = {
    "action": "query",
    "list":"search",
    "srsearch": search_term,
    "format": "json"
    }
  search_response = get(
    url=base_url, params=search_params
  )
  response = search_response.json()
  page_id = response["query"]["search"][0]["pageid"]
  return page_id

def get_wiki_image_url(page_id: int) -> str:
  """Accepts a page id and returns a URL for the page's infobox image, or
  another image on the page if one is not available.

  Args:
      page_id (int): id of the wikipedia article

  Returns:
      str: url of the image
  """
  base_url = "https://en.wikipedia.org/"
  # Get the soup fo the page
  page_content = BeautifulSoup(
    get(
    url=base_url + "?curid=" + str(page_id)
  ).content, "html.parser")

  # The infobox is in a table with it's own class. One of the rows contains the
  # 'infobox-image' which is what we are looking for here. We can grab the
  # image source from there.

  infobox = page_content.find("table", {"class": "infobox"})
  image_element = infobox.find("td", {"class": "infobox-image"})

  # Sometimes the infobox doesn't contain an image and image_element is None.
  # In that case, we'll find the first good image we can.
  if image_element:
    image_url = image_element.findChild("a")["href"]
  else:
    image_url = page_content.find_all(viewable_image)[0].parent["href"]

  # Wikipedia has pages for images that contain multiple pieces of info
  # We can get the actual image URL in its highest quality there
  image_page_content = BeautifulSoup(
    get(
    url=base_url + image_url
  ).content, "html.parser")
  image_parent = image_page_content.find("div", {"class": "fullImageLink"})
  image_url = image_parent.find("a").find("img")["src"]
  if not re.search("http", image_url):
    image_url = "https:" + image_url
  return image_url

def viewable_image(tag: Tag) -> bool:
  """Function to only return images of type png, jpg, gif

  Args:
      tag (Tag): Tag to check against. This can be used with find_all()

  Returns:
      bool: true if the tag contains an iage source with a file type of png,
      jpg, or gif
  """
  regex_viewable = "(jpg|jpeg|gif|png)$"
  # The image page for these uses .svg.png files, which we're okay with.
  # We just don't want the file extension to be svg
  regex_not_viewable = "^((?!svg).)*$"
  return tag.name == "img" \
    and re.search(regex_not_viewable, tag["src"].lower()) \
    and re.search(regex_viewable, tag["src"].lower()) \
    and tag["alt"] != "dagger"



def main():
  page_id = get_wiki_page_id(argv[1])
  image_url = get_wiki_image_url(page_id)
  print(image_url)

if __name__ == "__main__":
  main()
