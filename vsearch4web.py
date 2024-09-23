from flask import Flask, render_template, request, session, copy_current_request_context
from vsearch import search4letters
from ua_parser import user_agent_parser
from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError
from checker import check_logged_in
from threading import Thread
from time import sleep

app = Flask(__name__)
app.config['dbconfig'] = {'host': '127.0.0.1',
                'user': 'vsearch',
                'password': 'vsearchpasswd',
                'database': 'vsearchlogDB' }
app.secret_key = 'YouWillNeverGuess...'
                
@app.route('/')
@app.route('/entry')
def entry_page()->'html':
    return render_template('entry.html', the_title='Welcome to Search4Letters on the Web!')

@app.route('/search4', methods=['POST'])
def do_search()->'html':
    @copy_current_request_context
    def log_request(req:'flask request', res:str)-> None:
        """Log details of the web request and the results."""
        sleep(15)
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """insert into log
                (phrase, letters, ip, browser_string, results)
                values
                (%s, %s, %s, %s, %s)"""
            browser_details = (str(req.user_agent))
            user_browser = user_agent_parser.ParseUserAgent(browser_details)
            browser = user_browser['family']
            cursor.execute(_SQL, (req.form['phrase'], req.form['letters'], req.remote_addr, browser, res, ))

    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results: '
    results = str(search4letters(phrase, letters))
    try:
        t = Thread(target=log_request, args=(request,results))
        t.start()
    except Exception as err:
        print('*****Logging failed with this error: ', str(err))
    return render_template('results.html', the_title=title, the_phrase=phrase, the_letters=letters, the_results=results)
    

@app.route('/login')
def login()->str:
    session['logged_in'] = True
    return 'You are now logged in.'

@app.route('/logout')
def logout()->str:
    session.pop('logged_in')
    return 'You are now logged out.'

@app.route('/viewlog')
@check_logged_in
def view_the_log()->'html':
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """select phrase, letters, ip, browser_string, results from log"""
            cursor.execute(_SQL)
            contents = cursor.fetchall()
        row_titles = ('Phrase', 'Letters', 'Remote Addr', 'User Agent', 'Results')
        return render_template('viewlog.html', the_title='View Log', the_row_titles=row_titles, the_data=contents)
    except ConnectionError as err:
        print('Is your database switched on? Error: ', str(err))
    except CredentialsError as err:
        print('User-ID/Password Issues. Error: ', str(err))
    except SQLError as err:
        print('Is your query correct? Error: ', str(err))
    except Exception as err:
        print('Something went wrong: ', str(err))
    return 'Error'

    
if __name__ == '__main__':
    app.run(debug=True)

    
