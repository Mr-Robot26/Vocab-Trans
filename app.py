from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, send_file, session,url_for
import os
import random
import string
import pandas as pd
import openpyxl
import hashlib
from pymongo.mongo_client import MongoClient

app = Flask(__name__)

# Set a secret key for the application
app.secret_key = '123'
client = MongoClient("mongodb+srv://user_31:user31@cluster0.a5fjsp4.mongodb.net/?retryWrites=true&w=majority")
db = client['user_database']

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Set the upload folder path
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set the static folder path
app.config['STATIC_FOLDER'] = 'static'

# Get the list of files in the upload folder
files = os.listdir(app.config['UPLOAD_FOLDER'])

# Iterate over each file in the list and delete it
for file in files:
    os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = {
            'username': username,
            'password': hashed_password
        }

        db.users.insert_one(user)
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = db.users.find_one({'username': username, 'password': hashed_password})

        if user:
            session['username'] = username
            return redirect(url_for('profile'))
        else:
            return "Invalid login credentials. Please try again."

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
   
    csv_file_path= os.path.join(folder_path, f"{num}.csv")
    
    # Save the WAV file to the specified path
    #wav_file.save(wav_file_path)

    # Store the paths of the uploaded files in the session for later use
    session['excel_file_path'] = excel_file_path
    session['wav_file_path'] = wav_file_path
    session['csv_file_path']=csv_file_path
    session['folder_path']=folder_path
    print(session['folder_path'])
    
    

    # Redirect the user to the "/render" route
    return redirect("/tool")
    



@app.route("/tool", methods=['POST','GET'])
def home():
    # Retrieve the paths of the uploaded Excel and WAV files from the session
    excel = session.get("excel_file_path")
    wav_path = session.get("wav_file_path")
    
    # Read the Excel file using pandas
    df = pd.read_excel(excel)
    
    # Extract the columns from the DataFrame
    columns = df.columns[0:]
    columns = df.columns.tolist()  # Convert Index object to a list
    print("Before:", columns)
    
# Insert an extra column name
    extra_column_name = "Flag"
    columns.insert(9, extra_column_name)
    columns=['start time', 'end time', 'speaker id', 'act id', 'transcript', 'actual transcript','language', 'actual language', 'Flag']

    print("After:", columns)
    df[['start time', 'end time']] = df[['start time', 'end time']].round(1)
    if 'id' in df.columns:
       df=df.drop(['id'],axis=1)
    # Extract the data from the DataFrame
    data = df.iloc[:, 0:].values.tolist()
    
    # Create a set of unique speaker IDs from the "speaker_id" column in the Excel file
    options = set(df["speaker id"].unique())
    
    # Add additional options to the set
    options = options.union({'agent', 'speaker'})
    
    # Convert the set to a list
    options = list(options)
    languages=["english","hindi"]

    ## Set the type of colummns and initial zoom
    uneditable=[1,2,3,5,7]
    editable=[6]
    zoom=float(df[columns[1]].iloc[-1])
    zoom=zoom/5
    if zoom>1000:
        zoom=1000
    # Render the 'index.html' template and pass the variables to it
    return render_template('toolold.html', columns=columns, data=data, wav_path=wav_path, options=options,languages=languages,editable=editable,uneditable=uneditable, zoom=zoom)


@app.route("/")
def index():
    return render_template('signin.html')
    
@app.route("/base")
def base():
    ## get list of preloaded files
    name=1
    num = name
    # Retrieve the uploaded files
    folder_path = os.path.join(app.config['STATIC_FOLDER'], "pre-loaded", f"Call {num}")
    session['folder_path']=folder_path
    file_names=os.listdir("static/pre-loaded")
    
    error_file=[]
    for i in range(len(file_names)):
        file_names[i]="Call "+str(i+1)
        path=session['folder_path'][:-1]+str(i+1)
        if  'reason.txt' in os.listdir(path) :
           with open(path+'/reason.txt', 'r') as file:
            if file.read() !='':
                error_file.append("Call "+str(i+1))
              
            
    return render_template("home.html",filenames=file_names,error_file=error_file)


@app.route('/save', methods=['POST','GET'])
def save():
    # Retrieve the JSON data from the request
    print('******************************df.shape********************************************')
    data = request.get_json()
    print('******************************df.shape********************************************')
    # Create an empty dictionary to store the data
    out_dict = {}

    # Read the Excel file using pandas
    df = pd.read_excel(session.get("excel_file_path"))
    if 'id' in df.columns:
        df=df.drop(['id'],axis=1)
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

    final_df.to_csv(session.get('csv_file_path'), index=False)
    
   
   
    # Return a success message
    return "Success"

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    
    selected_option = data['selectedOption']
    
    
    # Process the selected option (you can replace this with your own logic)
    if selected_option == 'cancel':
        result = 'Action canceled.'
    else:
        result = selected_option
   
    print(result)
    file_path=session['folder_path']+"/reason.txt"
    with open(file_path, 'w') as file:
            file.write(result)
            print(f"Text saved to {file_path} successfully.")
    return redirect(url_for('base'))

    
    
    
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
