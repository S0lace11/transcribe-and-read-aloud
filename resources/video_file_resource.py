from flask import send_from_directory, abort
from flask_restful import Resource
import os

class VideoFileResource(Resource):
    def get(self, filename):
        # 1. 【安全性】验证 filename，防止路径遍历攻击
        if ".." in filename or not filename:
            abort(400, description="Invalid filename")

        # 2. 构造 records 目录的绝对路径
        base_dir = os.getcwd()  # 获取当前工作目录 (通常是 Flask 应用的根目录)
        records_dir = os.path.abspath(os.path.join(base_dir, 'records'))

        # 3. 构建文件的绝对路径
        abs_path = os.path.abspath(os.path.join(records_dir, filename))

        # 4. 【安全性】确保文件路径在 records 目录下
        if not abs_path.startswith(records_dir + os.sep) and abs_path != records_dir:
            abort(403, description="Access denied")  # 403 Forbidden

        # 5. 拆分目录和文件名
        directory, filename = os.path.split(abs_path)

        # 6. 使用 send_from_directory 发送文件
        return send_from_directory(directory, filename)