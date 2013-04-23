from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os



class SuPostSpider(BaseSpider):
    name = "supost"
    allowed_domains = ["supost.com"]
    start_urls = ["http://www.supost.com/search/index/3"]
    
    # gives html code to find specific nodes related to housing
    email_entry = u"""<div style="background-color:#f5f5f5;font-family:arial;border-top:1px solid #e5e5e5;padding:4px 0 5px 32px">
  <a href="{link}" style="color:15c;text-decoration:none" target="_blank">
    {title}
  </a>
</div>

<ul>
  <div style="font-family:arial;padding:10px 20px 14px 20px;margin:0">
    <span style="color:#222222;font-weight:bold">
      {date}
    </span> 
    <br/>
    {description}    
  </div>
</ul>
"""
    links = 'links.txt'
    email = 'posts.html'

    gmail_user = "supostsender@gmail.com"
    gmail_pwd = "turntable"


    def parse(self, response):
        send_emails = True
        try:
            with open(self.links):
                pass
        except IOError:
            open(self.links, 'a')
            #If this is the first time the file is created do not send emails
            send_emails = False;
            
        hxs = HtmlXPathSelector(response)
        results = hxs.select('//*[@id="results-anchor"]/*/a')

        for result in results:
            title = result.select('text()').extract()[0].strip()
            link = 'http://www.supost.com' + result.select('@href').extract()[0].strip()

            exists = False

                
            #check to see if we have already looked at this page
            for line in open(self.links):
                if link in line:
                    exists = True
                    break
        
            #If we have not seen the page before add it to the links list
            if exists == False:            
                request = Request(link, callback=self.get_description)
                request.meta['title'] = title
                request.meta['link'] = link
                request.meta['send_emails'] = send_emails
                yield request
                

        
            
    def get_description(self, response):
        title = response.meta['title'].encode('utf8', 'ignore')
        link = response.meta['link'].encode('utf8', 'ignore') 
        send_emails = response.meta['send_emails']

        open(self.links, 'a').write(link+"\n")

        #Parse the page for the description
        hxs = HtmlXPathSelector(response)
        p = hxs.select('//*[@class="post-text"]/p/text()').extract()
        description = '<br/><br/>'.join(p).encode('utf8', 'ignore')
        date = hxs.select('//*[@class="item-date"]/span/text()').extract()[0].strip().encode('utf8', 'ignore')
        
        try:
            html = self.email_entry.encode('utf8', 'ignore').format(link=link, title=title, date=date, description=description)
            #send the email if this is not the first run
            if send_emails:
                self.gmail("supostreceiver@gmail.com", title, html)
        except UnicodeDecodeError as e:
            print "Error with " + link + " " + e.reason
        
        


    def gmail(self, to, subject, text):
        msg = MIMEMultipart()
        
        msg['From'] = self.gmail_user
        msg['To'] = to 
        msg['Subject'] = subject

        msg.attach(MIMEText(text, 'html'))
        
        mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(self.gmail_user, self.gmail_pwd)
        mailServer.sendmail(self.gmail_user, to.split('; '), msg.as_string())
        
        mailServer.close()
