import urllib
import urllib2
import ClientCookie
import simplejson
import os
from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)

@app.route('/',methods=['POST'])
def start():
    username = None
    password = None

    # Get the POST paramters
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    else:
        return 'Invalid request.'

    # Root url for the account service
    root_url = 'https://keys.kent.edu:44220/ePROD'

    # Retrieve the login page.
    url = root_url + '/twbkwbis.P_WWWLogin'
    req = urllib2.Request(url)
    response = ClientCookie.urlopen(req)
    the_page = response.read()

    # Login into the service.
    url = root_url + '/twbkwbis.P_ValLogin'
    values = {'sid':username,'PIN':password}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()

    # Get the HTML for the schedule page.
    url = root_url + '/bwskfshd.P_CrseSchdDetl'
    values = {'term_in':'201280'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()

    # Instantiate the parser and fed it some HTML.
    soup = BeautifulSoup(the_page, "lxml")
    # Instantiate the schedule list and course dictionary.
    schedule = []
    course = {}

    # Locate all the tables that have the course information.
    # Note: Course information comes in pairs of tables so a flag is used to ensure both we parsed first.
    tables = soup.find_all('table','datadisplaytable')
    second_table_proccessed = False

    for table in tables:
        keys = table.find_all('th', 'ddlabel')
        if len(keys) == 0:
            keys = table.find_all('th', 'ddheader')
            second_table_proccessed = True
        # Course title is only found in the table with the "ddlabels".
        else:
            course['Course'] = str(table.find('caption').text)

        values = table.find_all('td', 'dddefault')
        for i in range(0,len(keys)-1):
            course[str(keys[i].text)] = str(values[i].text.strip())

        # Add the course dictionary to the list and reset the dictionary.
        if second_table_proccessed == True:
            schedule.append(course)
            second_table_proccessed = False
            course = {}

    # Return the schedule as a json.
    return simplejson.dumps(schedule)

@app.route("/flashcash/",methods=['GET'])
def get_flashcash():
    # Root url for the account service
    root_url = 'https://services.jsatech.com'
    
    # STAGE 1
    url = root_url + '/login.php';
    values = {'cid':40,'save':1,'loginphrase':'cfullmer','password':'Gyroman1','x':1,'y':1}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()
    key_index = the_page.rfind('window.location.href=')
    login_url = the_page[key_index + 22:key_index + 97]
    key_cid = the_page[key_index + 32:key_index + 78]
    key = the_page[key_index + 32:key_index + 70]
    print login_url
    
    #STAGE 2
    url = root_url + login_url;
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()
    print the_page
    
    #STAGE 3
    url = root_url + '/login-check.php' + key;
    print url
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()
    print the_page
    
    #STAGE 4
    url = root_url + '/index.php' + key_cid;
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()
    print the_page
    print the_page[the_page.rfind('Current Balance:'):the_page.rfind('Current Balance:') + 28]
    
    url = root_url + '/logout.php' + key_cid;
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()
    print the_page
    return "hello world"

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
