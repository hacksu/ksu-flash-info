import urllib
import urllib2
import ClientCookie
import simplejson
import os
from functools import wraps
from bs4 import BeautifulSoup
from flask import Flask, request, current_app, make_response
from functools import update_wrapper
from datetime import timedelta

app = Flask(__name__)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function


@app.route('/schedule/',methods=['POST','GET'])
@support_jsonp
@crossdomain(origin='*')
def start():
    username = None
    password = None

    # Get the POST paramters
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    else:
        username = request.args['username']
        password = request.args['password']

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

@app.route('/info/',methods=['POST','GET'])
@support_jsonp
@crossdomain(origin='*')
def info():
    username = None
    password = None

    # Get the POST paramters
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    else:
        username = request.args['username']
        password = request.args['password']

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
    url = root_url + '/bwskgstu.P_StuInfo'
    values = {'term_in':'201280'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = ClientCookie.urlopen(req)
    the_page = response.read()

    # Instantiate the parser and fed it some HTML.
    soup = BeautifulSoup(the_page, "lxml")
    # Instantiate the schedule list and course dictionary.
    wrapper = []
    info = {}

    # Locate all the tables that have the course information.
    # Note: Course information comes in pairs of tables so a flag is used to ensure both we parsed first.
    tables = soup.find_all('table','datadisplaytable')
    
    for table in tables:
        keys = table.find_all('th', 'ddlabel')
        # Info title is only found in the table with the "ddlabels".
        info['info'] = str(table.find('caption').text)

        values = table.find_all('td', 'dddefault')
        
        j = 0
        
        for i in range(0,len(keys)-1):
            if info['info'].find('Student') >= 0:
                j = i + 3
            else:
                j = i
            
            if j >= len(values):
                break
            
            info[str(keys[i].text)] = str(values[j].text.strip())

        # Add the course dictionary to the list and reset the dictionary.
        wrapper.append(info)
        info = {}

    # Return the schedule as a json.
    return simplejson.dumps(wrapper)


@app.route("/flashcash/",methods=['POST','GET'])
@support_jsonp
@crossdomain(origin='*')
def get_flashcash():
    # Root url for the account service
    root_url = 'https://services.jsatech.com'

    username = None
    password = None

    # Get the POST paramters
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    else:
        username = request.args['username']
        password = request.args['password']

    # STAGE 1
    url = root_url + '/login.php?cid=40&';
    values = {'cid':'40','save':'1','loginphrase': username,'password': password,'x':'1','y':'1'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    response.close()
    
    key_index = the_page.rfind('window.location.href=')
    login_url = the_page[key_index + 22:key_index + 97]
    key_cid = the_page[key_index + 32:key_index + 78]
    key = the_page[key_index + 32:key_index + 70]

    #STAGE 2
    url = root_url + login_url
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    response.close()
    #print the_page

    #STAGE 3
    url = root_url + '/login-check.php' + key;
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    response.close()
        
    #STAGE 4
    url = root_url + '/index.php' + key_cid;
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    response.close()
    
    # YES I KNOW IT DOESN"T MAKE SENSE! DON"T ASK!
    url = root_url + '/index.php' + key_cid;
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    response.close()
    raw_balance =  the_page[the_page.find('Current Balance:'):]
    flash_cash = {}
    flash_cash['flash_cash'] = raw_balance[17:raw_balance.find('</b>')]
    
    meal_plan = {}
    meal_plan['meal_plan'] = '0.00'
        
    # Get the user's meal plan as well.
    if raw_balance.count("Current Balance:") == 2:
        raw_balance =  the_page[the_page.rfind('Current Balance:'):]
        meal_plan['meal_plan'] = raw_balance[17:raw_balance.find('</b>')]

    url = root_url + '/logout.php' + key_cid;
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    response.close()
    
    # Construct a json object to return
    balance = [];
    balance.append(meal_plan)
    balance.append(flash_cash)    
    return simplejson.dumps(balance)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
