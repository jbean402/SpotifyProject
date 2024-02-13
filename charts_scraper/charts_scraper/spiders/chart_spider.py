import scrapy 
from scrapy.LinkExtractors import LinkExtractor 
from bs4 import BeautifulSoup 

# testing bs 
with open("index.html") as fp: 
    soup = BeautifulSoup(fp) 


class ChartSpider (scrapy.Spider): 
    name = "chartspider" 
    
    # only allowed to crawl here 
    allowed_domains = "https://kworb.net/spotify/"
    
    start_urls = [ "https://kworb.net/spotify/" ]
    
    deny_urls = [ "https://kworb.net/spotify/country/global_daily.html", 
                "https://kworb.net/spotify/country/global_daily_totals.html", 
                "https://kworb.net/spotify/country/global_weekly.html", 
                "https://kworb.net/spotify/country/global_weekly_totals.html"
                ] 
    
    #using the link extractor to grab all the links 
    link_extractor = LinkExtractor(allow="https://kworb.net/spotify/", deny=deny_urls) 
    
    def parse(self, response): 
        
        # recording the country of the current page 
        current_country = response.url.split("/")[2] 
        
        # getting all the country links for the current page 
        weekly_country_links = self.link_extractor.extract_links(response)
        
        # getting the weekly links 
        for links in weekly_country_links: 
            add_url = response.css('tr > td.mp.text > a:nth-child(3)::attr(href)')
            
            
        