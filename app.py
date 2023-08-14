from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, send_file, session,url_for
import os
import random
import string
import pandas as pd
import openpyxl
import hashlib
from pymongo.mongo_client import MongoClient
import mysql
import pymysql
app = Flask(__name__)

# Set a secret key for the application
app.secret_key = '123'
#client = MongoClient("mongodb+srv://user_31:user31@cluster0.a5fjsp4.mongodb.net/?retryWrites=true&w=majority")
#db = client['user_database']

#try:
   # client.admin.command('ping')
   # print("Pinged your deployment. You successfully connected to MongoDB!")
#except Exception as e:
    #print(e)
# Establish a connection to the MySQL database
db = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='vocab1',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# Set the upload folder path
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set the static folder path
app.config['STATIC_FOLDER'] = 'static'

# Get the list of files in the upload folder
files = os.listdir(app.config['UPLOAD_FOLDER'])

# Iterate over each file in the list and delete it
for file in files:
    os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))

def fetch_user_metadata(user_id):
    try:
        conn = mysql.connector.connect(**db)
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT username, email FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user_metadata = cursor.fetchone()  # Assuming only one user is fetched
        
        return user_metadata
    except mysql.connector.Error as err:
        print(f"Error fetching user metadata: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            with db.cursor() as cursor:
                sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
                cursor.execute(sql, (username, hashed_password))
                db.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return str(e)

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            with db.cursor() as cursor:
                sql = "SELECT * FROM users WHERE username=%s AND password=%s"
                cursor.execute(sql, (username, hashed_password))
                user = cursor.fetchone()
                if user:
                    session['username'] = username
                    return redirect(url_for('profile'))
                else:
                    return "Invalid login credentials. Please try again."
        except Exception as e:
            return str(e)

    return render_template('signin.html')

@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        
        return redirect(url_for('base'))
    else:
        return redirect(url_for('login'))
        

    



@app.route("/call_<name>", methods=['POST', 'GET'])
def sample(name):
    num = name
    # Retrieve the uploaded files
    folder_path = os.path.join(app.config['STATIC_FOLDER'], "pre-loaded", f"Call {num}")
    
    

    # Do something with the uploaded files

    # Generate a random filename for the Excel file
    # filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) + '.xlsx'
    filename = f"{num}.xlsx"
    
    # Set the path where the Excel file will be saved
    excel_file_path = os.path.join(folder_path, f"{num}.xlsx")
    
    # Save the Excel file to the specified path
    #excel_file.save(excel_file_path)

    # Replace the file extension to '.wav' for the WAV file
    filename = filename.replace(".xlsx", ".wav")
    
    # Set the path where the WAV file will be saved
    wav_file_path = os.path.join(folder_path, f"{num}.wav")
    
    # Save the WAV file to the specified path
    #wav_file.save(wav_file_path)

    # Store the paths of the uploaded files in the session for later use
    session['excel_file_path'] = excel_file_path
    session['wav_file_path'] = wav_file_path

    # Redirect the user to the "/render" route
    return redirect("/tool")

@app.route('/get_user_metadata', methods=['GET'])
def get_user_metadata():
    # Replace this with actual database query to fetch user metadata
    user_metadata = {
        'username': 'example_user',
        'email': 'user@example.com'
        # ... other user metadata
    }
    return jsonify(user_metadata)



@app.route("/tool", methods=['POST','GET'])
def home():
    # Retrieve the paths of the uploaded Excel and WAV files from the session
    excel = session.get("excel_file_path")
    wav_path = session.get("wav_file_path")
    
    # Read the Excel file using pandas
    df = pd.read_excel(excel)
    
    # Extract the columns from the DataFrame
    columns = df.columns[0:]
    
    # Extract the data from the DataFrame
    data = df.iloc[:, 0:].values.tolist()
    
    # Create a set of unique speaker IDs from the "speaker_id" column in the Excel file
    options = set(df["speaker_id"].unique())
    
    # Add additional options to the set
    options = options.union({'agent', 'speaker'})
    
    # Convert the set to a list
    options = list(options)
    languages=["english","hindi"]

    ## Set the type of colummns and initial zoom
    uneditable=[1,2,3,5,7,8]
    editable=[6]
    zoom=float(df[columns[1]].iloc[-1])
    zoom=zoom/5
    if zoom>1000:
        zoom=1000
    # Render the 'index.html' template and pass the variables to it
    return render_template('tool.html', columns=columns, data=data, wav_path=wav_path, options=options,languages=languages,editable=editable,uneditable=uneditable, zoom=zoom)



@app.route("/")
def index():
    return render_template('signin.html')
    
@app.route("/base")
def base():
    ## get list of preloaded files
    file_names=os.listdir("static/pre-loaded")
    for i in range(len(file_names)):
        file_names[i]="Call "+str(i+1)
    return render_template("home.html",filenames=file_names)


@app.route('/save', methods=['POST','GET'])
def save():
    # Retrieve the JSON data from the request
    data = request.get_json()

    # Create an empty dictionary to store the data
    out_dict = {}

    # Read the Excel file using pandas
    df = pd.read_excel(session.get("excel_file_path"))

    # Get the number of rows and columns in the DataFrame
    [rows, cols] = df.shape

    # Iterate over each column in the DataFrame
    for i in range(0, cols):
        # Create a key in the dictionary for each column
        out_dict[data["data_0_" + str(i + 1)]] = []

    # Iterate over each row and column in the JSON data
    for i in range(rows):
        for j in range(0, cols):
            # Append the value to the corresponding column key in the dictionary
            out_dict[data["data_0_" + str(j + 1)]].append(data["data_" + str(i + 1) + "_" + str(j + 1)])

    # Create a new DataFrame from the dictionary
    final_df = pd.DataFrame(out_dict)

    # Overwrite the existing Excel file with the updated DataFrame
    final_df.to_excel(session.get('excel_file_path'), index=False)

    # Return a success message
    return "Success"


@app.route("/done", methods=['POST','GET'])
def done():
    # Retrieve the path of the saved Excel file from the session
    excel_file_path = session.get('excel_file_path')
    
    # Send the file as a download to the user
    return send_file(excel_file_path, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True, port=7000)
