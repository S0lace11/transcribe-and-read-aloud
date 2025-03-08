from werkzeug.utils import secure_filename
filename = secure_filename("What does ‘cap’ or ‘no cap’ mean in everyday speech？ #shorts.mp4")
print(filename)  # 检查输出