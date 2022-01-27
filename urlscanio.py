import requests
import json
from requests.exceptions import HTTPError
import bs4
from bs4 import BeautifulSoup as bs
import time
from datetime import datetime

class URLSCANIO:
    def __init__(self) -> None:
        self.api_key = None
        self.search_url = None
        self.quota_url = None
        self.quota_resp = None
        self.queries = []
        self.output = {}
        self.sequence = 0
        self.executed = []
        self.html_files = []
        self.outfilename = None
        self.get_api_info()
        self.get_queries()
        
    def get_api_info(self):
        with open('api_info.json', 'r') as config_file:
            config_data = json.load(config_file)
        self.search_url, self.quota_url = config_data["api"]["search_url"], config_data["api"]["quota_url"]  
        self.api_key = config_data["api"]["api_key"]

    def get_queries(self):
        with open("queries.txt", "r") as f:
            queries = f.read()
        queries = queries.split(",")
        queries = [i for i in queries if i]
        if len(queries) == 0:
            print("Queries.txt file is empty!")
            exit()
        self.queries = [i for i in queries if i]

    def get_limit_quota(self):    
        headers = {
            'Content-Type': 'application/json',
            'API-key': self.api_key
        }
        try:
            response = requests.get(self.quota_url, headers=headers)
            status = response.status_code
            if status == 200:
                jsonresp = response.json()
                self.quota_resp = jsonresp.get("limits").get("search")
            else:
                print("Error calling API:", status)

        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'Other error occurred: {err}')
    
    def start_query(self):
        #generate output filename with timestamp
        timestamp = datetime.utcnow()
        timestr = timestamp.strftime("%Y%m%d-%H%M")
        self.outfilename = "output-" + str(timestr) + ".html"

        with open("templates/template_out.html") as f:
            txt = f.read()
            soup = bs(txt, 'html.parser')

        # create output file 
        with open("output/"+self.outfilename, "w") as outf:
            outf.write(str(soup))

        #generate html file for each query 
        for query in self.queries:
            #keep track of how long does the program needs to sleep for
            sleepy_time = 0

            #get limit quota info
            self.get_limit_quota()
            day_remain = self.quota_resp["day"]["remaining"]
            hour_remain = self.quota_resp["hour"]["remaining"]
            min_remain = self.quota_resp["minute"]["remaining"]

            #if limit hasn't been reached, generate html file
            if day_remain > 0 and hour_remain > 0 and min_remain > 0:
                print("generate html file for result: " + query)
                self.call_search_api(query)
            #if reached minute limit, sleep until it resets
            elif day_remain > 0 and hour_remain > 0 and min_remain == 0:
                seconds = self.get_time_difference("minute")
                #add 10 seconds just in case :D
                sleepy_time += (seconds + 10)
            elif day_remain > 0 and hour_remain == 0:
                seconds = self.get_time_difference("hour")
                sleepy_time += (seconds + 10)
            elif day_remain == 0:
                seconds = self.get_time_difference("day")
                sleepy_time += (seconds + 10) 

            #program sleeps until an API call can be made
            time.sleep(sleepy_time)

        return "Successfully ran all the queries!"

    def get_time_difference(self, t_type):
        #het reset time or the input type
        type_reset = self.quota_resp[t_type]["reset"]
        #get current time in UTC
        current_time = datetime.utcnow()       
        #convert time string to datetime object
        reset_time = datetime.strptime(type_reset,'%Y-%m-%dT%H:%M:%S.%fZ')
        #return total amount of seconds left until next reset
        return (reset_time - current_time).total_seconds()

    def call_search_api(self, query):
        self.output = {}
        headers = {
            'Content-Type': 'application/json',
            'API-key': self.api_key
        }      
        q = {"q": query}
        try:
            response = requests.get(self.search_url, params=q, headers=headers)
            status = response.status_code
            if status == 200:
                jsonresp = response.json()
                #filter and save the response
                self.output[query] = self.filter_data(jsonresp)
                self.executed.append(query)
            else:
                print("Error calling API:", status)
                exit()
    
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            exit()
        except Exception as err:
            print(f'Other error occurred: {err}')
            exit()

        self.generate_html()

    def filter_data(self,data):
        output = {}
        data = data["results"]
        for item in data:
            #remove dead pages from the output
            if item["page"]["status"] != '404':
                #won't save duplicate urls
                output[item["page"]["url"]] = item["screenshot"]
        return output

    def generate_html(self):
        #---------generate single html file for given query---------------
        file_name = "query" + str(self.sequence) + ".html"

        # open template html file for single query
        with open("templates/template_query.html") as f:
            txt = f.read()
            soup1 = bs(txt, 'html.parser')

        #add query as heading 1 
        head1 = soup1.new_tag("h1")
        head1.string = self.executed[-1]
        soup1.html.body.append(head1)

        # generate new tags for url and screenshot
        for url, screenshot in self.output[self.executed[-1]].items():
            head2 = soup1.new_tag("h2")
            head2.string = url
            soup1.html.body.append(head2)
            image = soup1.new_tag("img", src=screenshot)
            soup1.html.body.append(image)

        # save the file 
        with open('html_files/'+file_name, "w") as outf:
            outf.write(str(soup1))
        self.html_files.append(file_name)
        # increment filename sequence
        self.sequence += 1

        #---------update output html file for given query---------------
        # load the main html file template
        with open("output/"+self.outfilename) as f:
            txt = f.read()
            soup = bs(txt, 'html.parser')

        #create drop down menu for execute queries options
        drop_down = soup.find('ul')
        li = bs4.Tag(drop_down, name='li')
        a = bs4.Tag(li, name='a')
        a.attrs['href'] = "../html_files/"+ self.html_files[-1]
        a.insert(0, self.executed[-1])
        li.append(a)
        drop_down.append(li)

        # update the output file 
        with open("output/"+self.outfilename, "w") as outf:
            outf.write(str(soup))

def main():
    obj = URLSCANIO()
    print(obj.start_query())

if __name__ == "__main__":
    main()