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
        
        # loop through the iterable links for each country 
        for link in response.css('tr'):
            
            #gets the weekly html link 
            weekly_link = response.css('td.mp.text > a:nth-child(3)::attr(href)').get() 
            
            if weekly_link: 
                yield scrapy.follow(weekly_link, callback = self.parse_weekly(self, response)) 
                
    def parse_weekly(self, response): 
        
        # getting the rank, song name, artist name 
        rank = response.css('td.np').get() 
        song_name = response.css('tr > td.text.mp a:nth-child(2)::attr(href)').get()
        artist_name = response.css('tr > td.text.mp a:first-child::attr(href)').get()
        
                                    
                                    
                                
            
            
