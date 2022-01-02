import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from PIL import Image
import pyheif
import io
import logging 
from img_processing import image_to_text


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("upload_form.html")

class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        file1 = self.request.files['file1'][0]
        original_fname = file1['filename']
        with open("uploads/" + original_fname, 'wb') as output_file:
            output_file.write(file1['body'])
        
            
        result = image_to_text(original_fname)
        print(result)
        self.render("results.html", result=result, path = "text_detection/" + "processed_" + original_fname)

class ConvertHandler(tornado.web.RequestHandler):
    def post(self):
        print(self.request)
        logger = logging.getLogger('tornado.application')
        logger.setLevel(logging.INFO)
        logger.info(type(self.request.files['files']))
        print(type(self.request.files['files'][0]))
        file1 = self.request.files['files'][0]
        img = convertFile(file1)
        self.write(img)
        # self.write(file1['body'])
        self.set_header("Content-type",  "image/png")
        self.finish()


settings = {
# 'template_path': 'templates',
'static_path': 'static',
"xsrf_cookies": False

}


application = tornado.web.Application([
   (r"/", IndexHandler),
            (r"/upload", UploadHandler),
            (r"/convert", ConvertHandler),
            (r"/text_detection/(.*)", tornado.web.StaticFileHandler, {'path': "text_detection"})

], debug=True,**settings)


def convertFile(file):
    heif_file = pyheif.read(file.body)
    image = Image.frombytes(
        heif_file.mode, 
        heif_file.size, 
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    # image.save('uploads/hello.png', format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

print ("Server started.")
if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
