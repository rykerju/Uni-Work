# -*- coding: utf-8 -*-
import json
import os
import fitz
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import cv2
from logging import getLogger as get_logger
from flask import Flask, request,Response


app = Flask(__name__)

# 处理中文编码
app.config['JSON_AS_ASCII'] = False


# 跨域支持
def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

app.after_request(after_request)


def batch_handle(dirname, func):
    files = os.listdir(dirname)
    for file in files:
        func(dirname+'/'+file,)


def pdf_rm_layers(pdfpath,):
    get_logger().info('start to pdf ===== >pdf_rm_layers:{path}'.format(path=pdfpath))
    os.system('python -m pdflayers {pdf_file_path} rmed_layers.pdf --show \'6.说明\' \'A-text-C\' \'2\''
              .format(pdf_file_path=pdfpath))


def pdf_to_img(pdfpath, output_path='pdf_to_img', zoom_x=5, zoom_y=5, rotation_angle=0):
    # 打开PDF文件
    get_logger().info('start to pdf ===== >img:{path}'.format(path=pdfpath))
    pdf = fitz.open(pdfpath)
    # 逐页读取PDF
    for pg in range(0, pdf.pageCount):
        page = pdf[pg]
        # 设置缩放和旋转系数
        trans = fitz.Matrix(zoom_x, zoom_y).preRotate(rotation_angle)
        pm = page.getPixmap(matrix=trans, alpha=False)
        # 开始写图像
        pm.writePNG(output_path+".png")
    pdf.close()


def resize_img(imgpath,outputname='resized_img.png'):
    get_logger().info('start to resize_img:{path}'.format(path=imgpath))
    img = cv2.imread(imgpath)
    width = 2048
    height = 1536
    width = 7168
    height = 5376
    '''
    width = 14336
    height = 10752
'''
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    cv2.imwrite(outputname, resized)


def ocr_handle(img_path, output_txt_path='result_data', output_img_path='result_img', file=None):
    get_logger().info('start to ocr'.format(img_path))
    ocr = PaddleOCR(use_angle_cls=True, max_text_length=4,
                    use_gpu=False)
    result = ocr.ocr(img_path, cls=True)
    '''
    a = []
    for i in result:
        a.append(i)
    '''
    res = {'result': '200'}
    b = []
    for i in result:
        a = {}
        a["pixel"] = i[0]
        a["seat_number"] = i[1][0]
        b.append(a)
    res["elements"] = b
    res = json.dumps(res)
    f1 = open('res.json', 'w')
    f1.write(res)
    f1.close()
    image = Image.open(img_path).convert('RGB')
    boxes = [line[0] for line in result]
    '''
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    '''
    im_show = draw_ocr(image, boxes, font_path='simfang.ttf')  # txts, scores, font_path='simfang.ttf')
    im_show = Image.fromarray(im_show)
    im_show.save(output_img_path+'.png')


def main(pdfpath):
    pdf_rm_layers(pdfpath)
    pdf_to_img(pdfpath, output_path='or_to_img')
    pdf_to_img('rmed_layers.pdf')
    resize_img('or_to_img.png', 'or_to_img.png')
    resize_img('pdf_to_img.png', 'pdf_to_img.png')
    res = ocr_handle('pdf_to_img.png')
    return res


@app.route("/pdf_info", methods=["GET", "POST"])
def excel_info_():
    if request.method == "POST":
        #  获取参数用request.form，获取文件用request.files
        file = request.files.get('file')
        print(file)
        if not file:
            return {"code": '401', "message": "缺少参数"}

        file.save('file.pdf')
        main('file.pdf')
         #return json.dumps({"code": '200', "message": result}, ensure_ascii=False)
        with open('res.json', 'r') as f2:
            res = f2.read()
        return res
    else:
        return {"code": '403', "message": "仅支持post方法"}


@app.route("/images/result/result_img.png")
def get_frame():
    # 图片上传保存的路径
    with open('result_img.png', 'rb') as f:
        image = f.read()
        result = Response(image, mimetype="image/jpg")
        return result


@app.route("/images/result/result_img_org.png")
def get_frame1():
    # 图片上传保存的路径
    with open('or_to_img.png', 'rb') as f:
        image = f.read()
        result = Response(image, mimetype="image/jpg")
        return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)