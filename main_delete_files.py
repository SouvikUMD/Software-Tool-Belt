from app import app
from flask import Flask, flash, request, redirect, render_template, Blueprint
from flask import send_file
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import io
from io import BytesIO
from PIL import Image
import base64
from Helpers import *
#import aspose.words as aw
from PyPDF2 import PdfFileReader, PdfFileWriter
import os
from spire.pdf.common import *
from spire.pdf import *



main = Blueprint(
    'main', __name__,
)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'pdf', 'docx', 'PDF'])
# Initialize flask  and create sqlite database
app = Flask(__name__)

# Creating the upload folder
#upload_folder = r"C:\Users\prama\OneDrive\Documents\Apps\Combine_Blur_Grayscale_Resize_Web_App"
#upload_folder = os.path.dirname(os.path.abspath(__file__)) + r"\uploads"
upload_folder = "/home/softwaretoolbelt/Software-Tool-Belt/uploads"
#upload_folder = r"C:\Users\prama\OneDrive\Documents\Apps\Combine_Blur_Grayscale_Resize_Web_App\uploads"
print("upload_folder path: ", upload_folder)
#download_folder = os.path.dirname(os.path.abspath(__file__)) +  r"\downloads"
download_folder = "/home/softwaretoolbelt/Software-Tool-Belt/downloads"
print("download_folder path: ", download_folder)
#upload_folder = r"C:\Users\prama\OneDrive\Documents\Apps\uploads"
#upload_folder = r"uploads"
#download_folder = r"downloads"

#if not os.path.exists(upload_folder):
#   os.mkdir(upload_folder)

#if not os.path.exists(download_folder):
#   os.mkdir(download_folder)
   
# Max size of the file
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

# Configuring the upload folder
app.config['UPLOAD_FOLDER'] = upload_folder
#app.config['DOWNLOAD_FOLDER'] = download_folder


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template("home.html")
                

@app.route('/resize')
def upload_form_resize():
    return render_template('upload_resize.html')


@app.route('/resize', methods=['GET', 'POST'])
def upload_image_resize():
    images = []
    height = request.form.get("dim1")
    print("height: ", height)
    height = int(height)
    length = request.form.get("dim2")
    length = int(length)
    print("length: ", length)

    
    for file in request.files.getlist("file[]"):
        print("***************************")
        print("image: ", file)
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filestr = file.read()
            npimg = np.frombuffer(filestr, np.uint8)
            image = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)
            ratio = image.shape[0] / 500.0
            orig = image.copy()
            image = Helpers.resize(image, height = 500)

            img_resized = cv2.resize(image, (height, length))
            file_object = io.BytesIO()
            img= Image.fromarray(Helpers.resize(img_resized,width=500))
            img.save(file_object, 'PNG')
            base64img = "data:image/png;base64,"+base64.b64encode(file_object
                                 .getvalue()).decode('ascii')
            images.append([base64img])

    print("New image size:", img_resized.shape)
    return render_template('upload_resize.html', images=images )
    #return render_template(url_for('upload_form_resize'))


@app.route('/blur')
def upload_form_blur():
    return render_template('upload_blur.html')

@app.route('/blur', methods=['POST'])
def upload_image_blur():
    images = []
    for file in request.files.getlist("file[]"):
        print("***************************")
        print("image: ", file)
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filestr = file.read()
            npimg = np.frombuffer(filestr, np.uint8)
            image = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)
            ratio = image.shape[0] / 500.0
            orig = image.copy()
            image = Helpers.resize(image, height = 500)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            fm = cv2.Laplacian(gray, cv2.CV_64F).var()
            result = "Not Blurry"

            if fm < 100:
                result = "Blurry"

            sharpness_value = "{:.0f}".format(fm)
            message = [result,sharpness_value]

            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            file_object = io.BytesIO()
            img= Image.fromarray(Helpers.resize(img,width=500))
            img.save(file_object, 'PNG')
            base64img = "data:image/png;base64,"+base64.b64encode(file_object.getvalue()).decode('ascii')
            images.append([message,base64img])

    #print("images:", len(images))
    return render_template('upload_blur.html', images=images)

@app.route('/grayscale')
def upload_form():
    return render_template('upload_grayscale.html')

@app.route('/pdftoword')
def upload_form_pdftoword():
    return render_template('upload_pdftoword3.html')

# Sending the file to the user
def download(filename):
    #output_stream = open(app.config['DOWNLOAD_FOLDER'] + filename, 'wb')
    #output.write(output_stream)
    #return send_file(filename, download_name=download_folder,
    #                 as_attachment=True)
    return send_file(filename, as_attachment=True)

def delete_files(directory, extensions):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                file_path = os.path.join(root, file)
                os.remove(file_path)

@app.route('/pdftoword/Clear_Directory_Path', methods = ['POST'])
def delete_files_route():
    print("At delete_files_route")
    if request.method == 'POST':
        target_directories = [upload_folder, download_folder] # Replace with your directory
        extensions_to_delete = ['.pdf', '.PDF', '.docx']
        for directory in target_directories:
            delete_files(directory, extensions_to_delete)
        return 'Files deleted successfully!'


@app.route('/pdftoword', methods = ['POST'])
def uploadfile():
   print("At Upload File")
   if request.method == 'POST': # check if the method is post
      f = request.files['file'] # get the file from the files object
      # Saving the file in the required destination
      if allowed_file(f.filename):
         f.save(os.path.join(app.config['UPLOAD_FOLDER'],
                             secure_filename(f.filename))) # this will secure the file
         filename = f.filename.split(".")
         doc = PdfDocument()
         doc.LoadFromFile(upload_folder + "/{}".format(f.filename))
         #doc.LoadFromFile(upload_folder + r"\{}".format(f.filename))
         doc.ConvertOptions.SetPdfToDocOptions(True, True)
         #doc.SaveToFile(download_folder + r"\{}.docx".format(filename[0]))
         #doc.SaveToFile(upload_folder + r"\{}.docx".format(filename[0]), 
         #               FileFormat.DOCX)
         #doc.SaveToFile(upload_folder + "\{}.docx".format(filename[0]), 
         #               FileFormat.DOCX)
         doc.SaveToFile(download_folder + "/{}.docx".format(filename[0]), 
                        FileFormat.DOCX)
         #doc.save(r"\{}.docx".format(filename[0]))
         #doc.Close()
         #return download("{}.docx".format(filename[0]))
         return send_file(download_folder + "/{}.docx".format(filename[0]),
                          as_attachment=True)
         #return send_file(upload_folder + r"\{}.docx".format(filename[0]), 
         #                 as_attachment=True)
         #return doc
      else:
         return 'The file extension is not allowed'


@app.route('/grayscale', methods=['POST'])
def upload_image():
    images = []
    for file in request.files.getlist("file[]"):
        print("***************************")
        print("image: ", file)
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filestr = file.read()
            npimg = np.frombuffer(filestr, np.uint8)
            image = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)
            ratio = image.shape[0] / 500.0
            orig = image.copy()
            image = Helpers.resize(image, height = 500)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            file_object = io.BytesIO()
            img= Image.fromarray(Helpers.resize(gray,width=500))
            img.save(file_object, 'PNG')
            base64img = "data:image/png;base64,"+base64.b64encode(file_object.getvalue()).decode('ascii')
            images.append([base64img])

    #print("images:", len(images))
    return render_template('upload_grayscale.html', images=images )
    

if __name__ == "__main__":
    app.run(debug=True)
